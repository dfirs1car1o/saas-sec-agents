"""
report-gen — LLM-driven governance output skill.

Generates a Markdown report via OpenAI chat completions, then converts to DOCX
via pandoc for the security audience. PDF output is dropped entirely.

Usage:
    report-gen generate --backlog <path> --audience app-owner|security --out <path>
    report-gen generate --backlog <path> --audience security --sscf-benchmark <path> \\
        --nist-review <path> --out <path>
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv

_REPO = Path(__file__).resolve().parents[2]
load_dotenv(_REPO / ".env")

# ---------------------------------------------------------------------------
# System prompts per audience
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS: dict[str, str] = {
    "app-owner": (
        "You are a security consultant writing a plain-English remediation report for an application owner. "
        "No jargon. Every finding must have a specific action, a responsible team, and a deadline. "
        "Format as Markdown with clear sections: Executive Summary, Priority Findings, Remediation Roadmap."
    ),
    "security": (
        "You are a security governance analyst writing a technical assessment report for a security review board. "
        "Include OSCAL/SBS control IDs, SSCF domain scores, NIST AI RMF verdict, evidence references, "
        "mapping confidence levels, and a prioritised remediation backlog. "
        "Format as Markdown. Be precise and technical."
    ),
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


def _build_user_message(
    backlog: dict[str, Any],
    sscf: dict[str, Any] | None,
    nist: dict[str, Any] | None,
    audience: str,
    org: str,
    title: str,
) -> str:
    """Assemble the structured prompt payload sent to the LLM."""
    # Top 30 findings to stay within token budget; not_applicable collected separately
    all_items = backlog.get("mapped_items", [])
    items = [i for i in all_items if i.get("status") != "not_applicable"][:30]
    not_applicable = [i for i in all_items if i.get("status") == "not_applicable"]

    lines = [
        f"Assessment Title: {title}",
        f"Org: {org}",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Assessment ID: {backlog.get('assessment_id', 'unknown')}",
    ]

    if sscf:
        score = sscf.get("overall_score")
        status = sscf.get("overall_status", "unknown")
        if score is not None:
            lines.append(f"Overall Score: {score:.1%} ({status})")

    lines.append("\n## Findings (top 30 assessed)")
    lines.append(json.dumps(items, indent=2))

    if sscf:
        lines.append("\n## SSCF Domain Scores")
        lines.append(json.dumps(sscf.get("domains", sscf), indent=2))

    if nist:
        lines.append("\n## NIST AI RMF Verdict")
        lines.append(json.dumps(nist, indent=2))

    if not_applicable:
        na_lines = [
            f"- {i.get('control_id', '?')}: {i.get('reason', 'Not assessable via API')}" for i in not_applicable
        ]
        lines.append("\n## Controls Not Assessed via API")
        lines.extend(na_lines)

    lines.append(f"\nWrite a complete {audience} governance report in Markdown.")
    return "\n".join(lines)


_MOCK_TEMPLATES: dict[str, str] = {
    "app-owner": (
        "# Executive Summary\n\nMock report for testing.\n\n"
        "## Critical and High Findings\n\n"
        "| Control | Status | Action |\n|---|---|---|\n| SBS-AUTH-001 | Fail | Enable MFA |\n\n"
        "## What Happens Next\n\nRemediate items above within SLA windows.\n\n"
        "## Appendix: Full Control Matrix\n\n| Control | Status |\n|---|---|\n| SBS-AUTH-001 | Fail |\n"
    ),
    "security": (
        "# Assessment Metadata\n\nMock security report for testing.\n\n"
        "## Summary Metrics\n\nOverall: 48.4% RED\n\n"
        "## Full Control Matrix\n\n| Control | Status |\n|---|---|\n| SBS-AUTH-001 | Fail |\n\n"
        "## SSCF Domain Heatmap\n\n| Domain | Score |\n|---|---|\n| identity_access_management | 50% |\n\n"
        "## NIST AI RMF Compliance Note\n\n[PENDING NIST REVIEW]\n"
    ),
}


def _call_llm(system_prompt: str, user_msg: str, model: str, mock: bool = False) -> str:
    """Call OpenAI chat completions; return the full Markdown string."""
    if mock:
        audience = "security" if "security governance" in system_prompt else "app-owner"
        return _MOCK_TEMPLATES[audience]

    try:
        import openai
    except ImportError:
        click.echo("ERROR: openai package not installed. Run: pip install openai", err=True)
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        click.echo("ERROR: OPENAI_API_KEY not set.", err=True)
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    return response.choices[0].message.content.strip()


def _run_pandoc(md_path: Path, docx_path: Path) -> None:
    """Convert Markdown → DOCX via pandoc. Uses reference template if present."""
    template = Path(__file__).parent / "report_template.docx"
    cmd = ["pandoc", str(md_path), "-o", str(docx_path)]
    if template.exists():
        cmd += ["--reference-doc", str(template)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
    except FileNotFoundError:
        click.echo("WARNING: pandoc not found — DOCX not generated. Install pandoc to enable.", err=True)
    except subprocess.CalledProcessError as exc:
        click.echo(f"WARNING: pandoc failed: {exc.stderr.decode()}", err=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """report-gen — LLM-driven governance report generator."""


@cli.command()
@click.option("--backlog", required=True, help="Path to backlog.json from oscal_gap_map.")
@click.option(
    "--audience",
    required=True,
    type=click.Choice(["app-owner", "security"]),
    help="Report audience.",
)
@click.option("--out", required=True, help="Output file path (.md).")
@click.option("--sscf-benchmark", "sscf_benchmark", default=None, help="Path to sscf_report.json.")
@click.option("--nist-review", "nist_review", default=None, help="Path to nist_review.json.")
@click.option("--org-alias", "org_alias", default=None, help="Org alias for report header.")
@click.option("--title", default=None, help="Custom report title.")
@click.option("--dry-run", is_flag=True, help="Print plan without writing files.")
@click.option("--mock-llm", is_flag=True, help="Use deterministic template output (no API call). For testing.")
def generate(
    backlog: str,
    audience: str,
    out: str,
    sscf_benchmark: str | None,
    nist_review: str | None,
    org_alias: str | None,
    title: str | None,
    dry_run: bool,
    mock_llm: bool,
) -> None:
    """Generate a governance report via LLM (Markdown + DOCX for security audience)."""
    out_path = Path(out)
    if not out_path.suffix:
        out_path = out_path.with_suffix(".md")

    org = org_alias or "unknown-org"
    report_title = title or f"Salesforce Security Governance Assessment — {org}"
    model = os.getenv("LLM_MODEL_REPORTER", "gpt-4o-mini")

    if dry_run:
        click.echo(f"report-gen [DRY-RUN]: would write {out_path}", err=True)
        if audience == "security":
            click.echo(f"report-gen [DRY-RUN]: would also write {out_path.with_suffix('.docx')}", err=True)
        return

    backlog_data = _load_json(backlog)
    sscf_data = _load_json(sscf_benchmark) if sscf_benchmark else None
    nist_data = _load_json(nist_review) if nist_review else None

    system_prompt = _SYSTEM_PROMPTS[audience]
    user_msg = _build_user_message(backlog_data, sscf_data, nist_data, audience, org, report_title)

    markdown = _call_llm(system_prompt, user_msg, model, mock=mock_llm)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown)
    click.echo(f"report-gen: wrote {out_path}", err=True)

    if audience == "security":
        docx_path = out_path.with_suffix(".docx")
        _run_pandoc(out_path, docx_path)
        if docx_path.exists():
            click.echo(f"report-gen: wrote {docx_path}", err=True)


if __name__ == "__main__":
    cli()
