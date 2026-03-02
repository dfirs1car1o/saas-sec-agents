"""
nist_review — NIST AI RMF 1.0 review skill.

Validates the multi-agent assessment outputs against NIST AI RMF 1.0
(Govern, Map, Measure, Manage) and produces a structured verdict JSON.

Usage:
    nist-review assess --gap-analysis <path> --backlog <path> --out <path>
    nist-review assess --dry-run --gap-analysis <path> --out <path>
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv

_REPO = Path(__file__).resolve().parents[2]
load_dotenv(_REPO / ".env")

# ---------------------------------------------------------------------------
# Dry-run stub verdict (realistic weak-org scenario)
# ---------------------------------------------------------------------------

_DRY_RUN_VERDICT: dict[str, Any] = {
    "nist_ai_rmf_review": {
        "assessment_id": "sfdc-assess-dry-run",
        "reviewed_at_utc": "",  # filled at runtime
        "reviewer": "nist-reviewer",
        "govern": {
            "status": "pass",
            "notes": (
                "Human accountability defined in mission.md. "
                "Assessment scope bounded to sfdc-connect collector output only. "
                "Override and escalation path documented via --approve-critical flag."
            ),
        },
        "map": {
            "status": "partial",
            "notes": (
                "Dry-run mode clearly noted; no live Salesforce API call made. "
                "AI-generated findings distinguished from human-verified via dry_run flag in assessment_id. "
                "SBS catalog version (0.4.0) documented. "
                "Stub scenario limitations explicitly disclosed in assessment metadata."
            ),
        },
        "measure": {
            "status": "pass",
            "notes": (
                "Mapping confidence tracked via status/severity per finding. "
                "Unmapped controls explicitly listed as not_applicable (13 findings). "
                "SSCF heatmap complete across all 7 domains. "
                "2 domains (Governance Risk Compliance, Threat Detection Response) "
                "have no assessed controls in current SBS catalog -- noted as N/A."
            ),
        },
        "manage": {
            "status": "partial",
            "notes": (
                "Critical findings (4) flagged for human review gate. "
                "Remediation actions provided for all critical/high findings. "
                "Owner and due_date fields absent in dry-run stub scenario -- "
                "required before live assessment delivery to governance committee."
            ),
        },
        "overall": "flag",
        "blocking_issues": [],
        "recommendations": [
            "Add owner and due_date to all critical/fail backlog items before live delivery.",
            "Replace dry-run stub with live sfdc-connect collection before governance committee review.",
        ],
    }
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        click.echo(f"ERROR: file not found: {p}", err=True)
        sys.exit(1)
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        click.echo(f"ERROR: invalid JSON in {p}: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """nist-review — NIST AI RMF 1.0 compliance review skill."""


@cli.command()
@click.option("--gap-analysis", "gap_analysis", default=None, help="Path to gap_analysis.json.")
@click.option("--backlog", default=None, help="Path to backlog.json.")
@click.option("--out", required=True, help="Output path for nist_review.json.")
@click.option("--dry-run", is_flag=True, help="Produce realistic stub verdict without calling the API.")
def assess(gap_analysis: str | None, backlog: str | None, out: str, dry_run: bool) -> None:
    """Run NIST AI RMF review against assessment outputs."""
    out_path = Path(out)

    if dry_run:
        import copy

        verdict = copy.deepcopy(_DRY_RUN_VERDICT)
        verdict["nist_ai_rmf_review"]["reviewed_at_utc"] = datetime.now(UTC).isoformat()
        if gap_analysis:
            try:
                data = _load_json(gap_analysis)
                verdict["nist_ai_rmf_review"]["assessment_id"] = data.get("assessment_id", "sfdc-assess-dry-run")
            except SystemExit:
                pass
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(verdict, indent=2))
        click.echo(f"nist-review [DRY-RUN]: wrote stub verdict -> {out_path}", err=True)
        return

    # Live mode: call Anthropic API with nist-reviewer system prompt
    if not gap_analysis or not backlog:
        click.echo("ERROR: --gap-analysis and --backlog are required for live mode.", err=True)
        sys.exit(1)

    try:
        import anthropic
    except ImportError:
        click.echo("ERROR: anthropic package not installed.", err=True)
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        click.echo("ERROR: ANTHROPIC_API_KEY not set.", err=True)
        sys.exit(1)

    gap_data = _load_json(gap_analysis)
    backlog_data = _load_json(backlog)
    assessment_id = gap_data.get("assessment_id", "unknown")

    reviewer_md = _REPO / "agents" / "nist-reviewer.md"
    system_prompt = (
        reviewer_md.read_text()
        if reviewer_md.exists()
        else (
            "You are a NIST AI RMF 1.0 reviewer. "
            "Validate the assessment outputs against Govern, Map, Measure, Manage functions. "
            "Return ONLY a JSON verdict in the format specified."
        )
    )

    # Truncate large JSONs to stay within token budget
    gap_str = json.dumps(gap_data, indent=2)[:6000]
    backlog_str = json.dumps(backlog_data, indent=2)[:6000]
    user_msg = (
        f"Review these assessment outputs for assessment_id={assessment_id}.\n\n"
        f"<gap_analysis>\n{gap_str}\n</gap_analysis>\n\n"
        f"<backlog>\n{backlog_str}\n</backlog>\n\n"
        "Return ONLY the JSON verdict. No text outside the JSON object."
    )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:])

    try:
        verdict = json.loads(raw)
    except json.JSONDecodeError:
        click.echo(f"WARNING: LLM response not valid JSON. Falling back to flag verdict.\n{raw[:300]}", err=True)
        verdict = {
            "nist_ai_rmf_review": {
                "assessment_id": assessment_id,
                "reviewed_at_utc": datetime.now(UTC).isoformat(),
                "reviewer": "nist-reviewer",
                "govern": {"status": "partial", "notes": "Parse error — manual review required."},
                "map": {"status": "partial", "notes": "Parse error — manual review required."},
                "measure": {"status": "partial", "notes": "Parse error — manual review required."},
                "manage": {"status": "partial", "notes": "Parse error — manual review required."},
                "overall": "flag",
                "blocking_issues": ["LLM response could not be parsed as JSON."],
                "recommendations": [],
            }
        }

    if "nist_ai_rmf_review" in verdict:
        verdict["nist_ai_rmf_review"].setdefault("reviewed_at_utc", datetime.now(UTC).isoformat())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(verdict, indent=2))
    click.echo(f"nist-review: wrote verdict -> {out_path}", err=True)


if __name__ == "__main__":
    cli()
