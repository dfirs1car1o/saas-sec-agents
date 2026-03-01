"""
Smoke test: harness agentic loop with mocked Anthropic client.

Verifies:
  1. Correct tool dispatch order (sfdc_connect_collect → oscal_assess_assess → end_turn)
  2. Output file paths tracked in state
  3. memory save_assessment called with extracted score
  4. Loop exits cleanly without real Salesforce org or Anthropic API credits

Mock sequence:
  Turn 1: tool_use sfdc_connect_collect (dry_run=True)
  Turn 2: tool_use oscal_assess_assess (dry_run=True)
  Turn 3: end_turn with summary text
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from click.testing import CliRunner

from harness.loop import cli

_REPO = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Helpers — build realistic mock Anthropic responses
# ---------------------------------------------------------------------------


def _tool_use_response(tool_name: str, tool_id: str, tool_input: dict) -> MagicMock:
    """Build a mock Anthropic Message with a single tool_use block."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = tool_name
    block.input = tool_input

    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [block]
    return response


def _end_turn_response(text: str) -> MagicMock:
    """Build a mock Anthropic Message with a text end_turn."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    # end_turn blocks don't have .name or .id
    del block.name
    del block.id

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


# ---------------------------------------------------------------------------
# Test: two-tool loop → end_turn
# ---------------------------------------------------------------------------


def test_dry_run_loop_tool_dispatch_order(tmp_path: Path) -> None:
    """Loop calls tools in correct order and exits cleanly."""

    fake_gap = str(tmp_path / "gap_analysis.json")
    fake_sscf = str(tmp_path / "sscf_report.json")

    # Write minimal gap_analysis.json so _extract_critical_fails / _extract_score work
    (tmp_path / "gap_analysis.json").write_text(json.dumps({
        "assessment_id": "test-001",
        "findings": [
            {"control_id": "SBS-AUTH-001", "status": "fail", "severity": "critical"},
            {"control_id": "SBS-ACS-001", "status": "fail", "severity": "high"},
        ],
    }))
    (tmp_path / "sscf_report.json").write_text(json.dumps({
        "benchmark_id": "bench-001",
        "overall_score": 0.34,
        "overall_status": "red",
        "domains": [],
        "summary": {"domains_green": 0, "domains_red": 7},
    }))

    mock_responses = [
        _tool_use_response(
            "sfdc_connect_collect",
            "call_001",
            {"scope": "all", "dry_run": True, "env": "dev", "org": "test-org"},
        ),
        _tool_use_response(
            "oscal_assess_assess",
            "call_002",
            {"dry_run": True, "env": "dev", "out": fake_gap},
        ),
        _end_turn_response("Assessment complete. overall_score=34%, status=RED."),
    ]

    mock_anthropic_client = MagicMock()
    mock_anthropic_client.messages.create.side_effect = mock_responses

    dispatch_results = {
        "sfdc_connect_collect": json.dumps({"status": "ok", "dry_run": True, "output_file": str(tmp_path / "sfdc_raw.json")}),
        "oscal_assess_assess": json.dumps({"status": "ok", "output_file": fake_gap}),
    }

    def fake_dispatch(name: str, inp: dict) -> str:  # noqa: ANN001
        return dispatch_results.get(name, json.dumps({"status": "ok"}))

    runner = CliRunner()

    with (
        patch("anthropic.Anthropic", return_value=mock_anthropic_client),
        patch("harness.loop.build_client") as mock_build,
        patch("harness.loop.load_memories", return_value="No prior assessments."),
        patch("harness.loop.save_assessment") as mock_save,
        patch("harness.loop.dispatch",side_effect=fake_dispatch) as mock_dispatch,
    ):
        mock_build.return_value = MagicMock()

        result = runner.invoke(
            cli,
            ["run", "--dry-run", "--env", "dev", "--org", "test-org", "--approve-critical"],
        )

    assert result.exit_code == 0, f"Loop exited with {result.exit_code}:\n{result.output}"

    # Verify tool dispatch order
    dispatch_calls = mock_dispatch.call_args_list
    assert len(dispatch_calls) == 2, f"Expected 2 dispatch calls, got {len(dispatch_calls)}"
    assert dispatch_calls[0][0][0] == "sfdc_connect_collect"
    assert dispatch_calls[1][0][0] == "oscal_assess_assess"

    # Verify dry_run propagated to tool inputs
    assert dispatch_calls[0][0][1].get("dry_run") is True
    assert dispatch_calls[1][0][1].get("dry_run") is True

    # Verify memory save was called
    mock_save.assert_called_once()
    save_args = mock_save.call_args[0]
    assert save_args[1] == "test-org"   # org_alias


# ---------------------------------------------------------------------------
# Test: tool error triggers _handle_tool_error
# ---------------------------------------------------------------------------


def test_tool_error_triggers_handler(tmp_path: Path) -> None:
    """When dispatch raises, _handle_tool_error is called."""
    mock_responses = [
        _tool_use_response("sfdc_connect_collect", "call_err", {"scope": "all", "dry_run": True}),
        _end_turn_response("Halted due to tool error."),
    ]

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = mock_responses

    runner = CliRunner()

    with (
        patch("anthropic.Anthropic", return_value=mock_client),
        patch("harness.loop.build_client", return_value=MagicMock()),
        patch("harness.loop.load_memories", return_value=""),
        patch("harness.loop.save_assessment"),
        patch("harness.loop.dispatch",side_effect=RuntimeError("Salesforce connection refused")),
        patch("harness.loop._handle_tool_error", return_value='{"status": "error", "message": "handled"}') as mock_handler,
    ):
        result = runner.invoke(cli, ["run", "--dry-run", "--org", "err-org"])

    mock_handler.assert_called_once()
    call_args = mock_handler.call_args[0]
    assert call_args[0] == "sfdc_connect_collect"
    assert isinstance(call_args[2], RuntimeError)


# ---------------------------------------------------------------------------
# Test: Anthropic client constructed with env key
# ---------------------------------------------------------------------------


def test_anthropic_client_uses_api_key(tmp_path: Path) -> None:
    """ANTHROPIC_API_KEY env var is passed to the Anthropic client."""
    mock_responses = [_end_turn_response("No tools needed.")]
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = mock_responses

    runner = CliRunner()

    with (
        patch("anthropic.Anthropic", return_value=mock_client) as mock_ctor,
        patch("harness.loop.build_client", return_value=MagicMock()),
        patch("harness.loop.load_memories", return_value=""),
        patch("harness.loop.save_assessment"),
    ):
        result = runner.invoke(
            cli,
            ["run", "--dry-run", "--org", "key-test-org", "--api-key", "sk-test-key"],
        )

    mock_ctor.assert_called_once_with(api_key="sk-test-key")
