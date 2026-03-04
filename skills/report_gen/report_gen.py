"""
report-gen — LLM-driven governance output skill.

Document structure (all sections except LLM narrative are Python-rendered):

  [Gate banner]           — ⛔/🚩 if NIST verdict is block/flag
  Executive Scorecard     — overall score + severity × status matrix   [HARNESS]
  Domain Posture          — ASCII bar chart of SSCF domain scores      [HARNESS]
  Immediate Actions       — top-10 critical/fail findings              [HARNESS]
  Executive Summary       — LLM narrative: what it means, business risk [LLM]
  Remediation Roadmap     — LLM narrative: priorities, owners, timeline [LLM]
  Full Control Matrix     — sorted findings table                      [HARNESS]
  NIST AI RMF Review      — governance gate, function table, recs      [HARNESS]

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
# Severity / status sort order
# ---------------------------------------------------------------------------

_SEV_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
_STA_ORDER = {"fail": 0, "partial": 1, "pass": 2, "not_applicable": 3}
_SEV_ICON = {"critical": "🔴", "high": "🟠", "moderate": "🟡", "low": "🔵"}
_STA_ICON = {"fail": "❌", "partial": "⚠️", "pass": "✅", "not_applicable": "—"}

# ---------------------------------------------------------------------------
# System prompts — LLM writes narrative only; all tables injected by harness
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS: dict[str, str] = {
    "app-owner": (
        "You are a security consultant writing a plain-English remediation report for an application owner. "
        "No jargon. Write two sections only:\n"
        "1. ## Executive Summary — 2-3 paragraphs: what was assessed, what the score means in business terms, "
        "and the single most important thing they must do first.\n"
        "2. ## What Happens Next — clear, numbered list of owner actions with deadlines.\n"
        "Do NOT write any tables, charts, or control IDs — those are rendered separately. "
        "Do NOT include a NIST AI RMF section."
    ),
    "security": (
        "You are a security governance analyst writing for a Security Team security review board. "
        "Write two sections only:\n"
        "1. ## Executive Summary — 2-3 paragraphs: assessment scope, overall posture, "
        "the key risk drivers behind the score, and governance implications.\n"
        "2. ## Risk Analysis — business and regulatory impact of each RED domain, "
        "critical control failures, and remediation priority rationale.\n"
        "Reference control IDs and SSCF domains by name where relevant. Be precise and technical. "
        "Do NOT write any findings tables, domain score tables, or charts — those are pre-rendered. "
        "Do NOT include a NIST AI RMF section — it is appended as the final section."
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


def _sorted_findings(items: list[dict]) -> list[dict]:
    """Sort findings: fail before partial before pass, critical before high before moderate."""
    return sorted(
        items,
        key=lambda x: (
            _STA_ORDER.get(x.get("status", ""), 9),
            _SEV_ORDER.get(x.get("severity", ""), 9),
        ),
    )


def _build_user_message(
    backlog: dict[str, Any],
    sscf: dict[str, Any] | None,
    nist: dict[str, Any] | None,
    audience: str,
    org: str,
    title: str,
) -> str:
    """Minimal context for the LLM — enough for narrative, no duplication of pre-rendered tables."""
    all_items = backlog.get("mapped_items", [])
    assessed = [i for i in all_items if i.get("status") not in ("not_applicable",)]

    lines = [
        f"Assessment Title: {title}",
        f"Org: {org}",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Assessment ID: {backlog.get('assessment_id', 'unknown')}",
        f"Total controls assessed: {len(assessed)} of {len(all_items)}",
    ]

    if sscf:
        score = sscf.get("overall_score")
        status = sscf.get("overall_status", "unknown")
        if score is not None:
            lines.append(f"Overall Score: {score:.1%} ({status.upper()})")

        # Domain summary for narrative context
        domains = sscf.get("domains", [])
        red = [d["domain"] for d in domains if d.get("status") == "red"]
        amber = [d["domain"] for d in domains if d.get("status") == "amber"]
        if red:
            lines.append(f"RED domains: {', '.join(red)}")
        if amber:
            lines.append(f"AMBER domains: {', '.join(amber)}")

    # Critical and high fails for narrative context
    priority = [i for i in assessed if i.get("status") == "fail" and i.get("severity") in ("critical", "high")]
    if priority:
        lines.append(f"\nCritical/High failures ({len(priority)}):")
        for i in priority:
            lines.append(
                f"  - {i.get('sbs_control_id', '?')} [{i.get('severity', '?').upper()}]: "
                f"{i.get('sbs_title', i.get('remediation', ''))[:80]}"
            )

    if nist:
        review = nist.get("nist_ai_rmf_review", nist)
        overall = review.get("overall", "unknown")
        lines.append(
            f"\nNIST AI RMF context: overall={overall} "
            f"(govern={review.get('govern', {}).get('status', '?')}, "
            f"manage={review.get('manage', {}).get('status', '?')})"
        )

    lines.append(
        "\nAll findings tables, domain charts, and the NIST section are pre-rendered "
        "and will be injected into the document — do not write them."
    )
    lines.append(f"\nWrite the {audience} narrative sections described in your instructions.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Python-rendered report sections
# ---------------------------------------------------------------------------


def _render_executive_scorecard(backlog: dict, sscf: dict | None, org: str, title: str) -> str:
    """Overall score badge + severity × status matrix."""
    items = backlog.get("mapped_items", [])
    assessed = [i for i in items if i.get("status") != "not_applicable"]

    # Severity × status counts
    sevs = ["critical", "high", "moderate", "low"]
    stas = ["fail", "partial", "pass"]
    matrix: dict[str, dict[str, int]] = {s: {t: 0 for t in stas} for s in sevs}
    for item in assessed:
        sev = item.get("severity", "")
        sta = item.get("status", "")
        if sev in matrix and sta in matrix[sev]:
            matrix[sev][sta] += 1

    overall_score = sscf.get("overall_score") if sscf else None
    overall_status = (sscf.get("overall_status") or "unknown").upper() if sscf else "UNKNOWN"
    status_icon = {"RED": "🔴", "AMBER": "🟡", "GREEN": "🟢"}.get(overall_status, "⚪")
    score_str = f"{overall_score:.1%}" if overall_score is not None else "N/A"

    na_count = len(items) - len(assessed)
    lines = [
        f"# {title}",
        "",
        f"**Org:** {org} &nbsp;|&nbsp; "
        f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d')} &nbsp;|&nbsp; "
        f"**Assessment ID:** {backlog.get('assessment_id', 'unknown')}",
        "",
        "---",
        "",
        "## Executive Scorecard",
        "",
        f"### {status_icon} Overall Posture: {score_str} — {overall_status}",
        "",
        "| Severity | ❌ Fail | ⚠️ Partial | ✅ Pass |",
        "|----------|---------|-----------|--------|",
    ]
    for sev in sevs:
        row = matrix[sev]
        if any(row.values()):
            icon = _SEV_ICON.get(sev, "")
            lines.append(
                f"| {icon} **{sev.capitalize()}** "
                f"| {row['fail'] or '—'} "
                f"| {row['partial'] or '—'} "
                f"| {row['pass'] or '—'} |"
            )
    lines += [
        "",
        f"*{len(assessed)} controls assessed · {na_count} not assessable via API · {len(items)} total in catalog*",
        "",
    ]
    return "\n".join(lines)


def _render_domain_chart(sscf: dict) -> str:
    """ASCII bar chart of SSCF domain scores."""
    domains = sscf.get("domains", [])
    if not domains:
        return ""

    bar_width = 20
    status_icon = {"green": "✅", "amber": "⚠️", "red": "❌", "not_assessed": "—"}

    lines = [
        "## Domain Posture",
        "",
        "```",
    ]

    max_name = max(len(d["domain"].replace("_", " ").title()) for d in domains)

    for d in domains:
        name = d["domain"].replace("_", " ").title()
        score = d.get("score")
        status = d.get("status", "not_assessed")
        icon = status_icon.get(status, "—")

        if score is not None:
            filled = round(score * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            pct = f"{score:.0%}"
            status_label = status.upper()
        else:
            bar = "─" * bar_width
            pct = "N/A"
            status_label = "NOT ASSESSED"

        lines.append(f"  {name:<{max_name}}  {bar}  {pct:>4}  {icon} {status_label}")

    lines += ["```", ""]
    return "\n".join(lines)


def _render_priority_findings(backlog: dict, n: int = 10) -> str:
    """Top-N findings sorted critical/fail first."""
    items = backlog.get("mapped_items", [])
    actionable = [i for i in items if i.get("status") in ("fail", "partial")]
    sorted_items = _sorted_findings(actionable)[:n]

    if not sorted_items:
        return ""

    lines = [
        f"## Immediate Actions — Top {len(sorted_items)} Priority Findings",
        "",
        "| # | Control | Severity | Status | Required Action | Due Date |",
        "|---|---------|----------|--------|----------------|----------|",
    ]
    for idx, item in enumerate(sorted_items, 1):
        cid = item.get("sbs_control_id", "?")
        sev = item.get("severity", "?")
        sta = item.get("status", "?")
        sev_icon = _SEV_ICON.get(sev, "")
        sta_icon = _STA_ICON.get(sta, "")
        action = item.get("remediation") or item.get("sbs_title") or "See control catalog"
        action = action[:70] + "…" if len(action) > 70 else action
        due = item.get("due_date") or "—"
        lines.append(
            f"| {idx} | `{cid}` | {sev_icon} {sev.capitalize()} | {sta_icon} {sta.capitalize()} | {action} | {due} |"
        )

    lines.append("")
    return "\n".join(lines)


def _render_full_matrix(backlog: dict) -> str:
    """Complete sorted findings table — critical/fail first."""
    items = backlog.get("mapped_items", [])
    sorted_items = _sorted_findings(items)

    lines = [
        "## Full Control Matrix",
        "",
        "| Control | Severity | Status | Confidence | Due Date | Owner |",
        "|---------|----------|--------|------------|----------|-------|",
    ]
    for item in sorted_items:
        cid = item.get("sbs_control_id", "?")
        sev = item.get("severity", "?")
        sta = item.get("status", "?")
        sev_icon = _SEV_ICON.get(sev, "")
        sta_icon = _STA_ICON.get(sta, "")
        conf = item.get("mapping_confidence", "—")
        due = item.get("due_date") or "—"
        owner = item.get("owner", "—")
        lines.append(
            f"| `{cid}` | {sev_icon} {sev.capitalize()} | {sta_icon} {sta.capitalize()} | {conf} | {due} | {owner} |"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# NIST section renderer
# ---------------------------------------------------------------------------

_NIST_STATUS_ICON = {"pass": "✅", "partial": "⚠️", "fail": "❌"}
_NIST_OVERALL_ICON = {"block": "⛔", "flag": "🚩", "pass": "✅"}
_NIST_GATE_BANNERS = {
    "block": (
        "> ⛔ **GOVERNANCE GATE: BLOCKED**  \n"
        "> This assessment has been flagged by the NIST AI RMF reviewer. "
        "Do not distribute this report until blocking issues are resolved. "
        "See the NIST AI RMF Governance Review section at the end of this document.\n"
    ),
    "flag": (
        "> 🚩 **GOVERNANCE FLAG: REVIEW REQUIRED**  \n"
        "> The NIST AI RMF reviewer has raised issues requiring attention before this report "
        "is submitted for Security Team review. See the NIST AI RMF Governance Review section at the end.\n"
    ),
}
_NIST_APPOWNER_NOTE = {
    "block": (
        "> ⛔ **Note:** This security assessment has been blocked by an internal governance review. "
        "Your remediation plan is valid, but the overall report cannot be submitted to the security team "
        "until governance issues are resolved. Your security architect will follow up.\n"
    ),
    "flag": (
        "> 🚩 **Note:** This security assessment has been flagged for governance review. "
        "Your action plan below is accurate — please proceed with remediation. "
        "Your security architect may follow up with additional questions.\n"
    ),
}


def _render_nist_section(nist: dict[str, Any]) -> str:
    review = nist.get("nist_ai_rmf_review", nist)
    overall = review.get("overall", "unknown").lower()
    overall_icon = _NIST_OVERALL_ICON.get(overall, "ℹ️")
    reviewed_at = review.get("reviewed_at_utc", "unknown")
    reviewer = review.get("reviewer", "nist-reviewer")

    lines = [
        "---",
        "",
        "## NIST AI RMF Governance Review",
        "",
        f"### {overall_icon} Overall Verdict: {overall.upper()}",
        "",
        "| Function | Status | Notes |",
        "|---|---|---|",
    ]
    for fn in ["govern", "map", "measure", "manage"]:
        data = review.get(fn, {})
        status = data.get("status", "unknown")
        icon = _NIST_STATUS_ICON.get(status, "—")
        notes = data.get("notes", "—")
        lines.append(f"| **{fn.upper()}** | {icon} {status.upper()} | {notes} |")

    blocking = review.get("blocking_issues", [])
    if blocking:
        lines += ["", "### Blocking Issues", ""]
        for i, issue in enumerate(blocking, 1):
            lines.append(f"{i}. {issue}")

    recs = review.get("recommendations", [])
    if recs:
        lines += ["", "### Recommendations", ""]
        for i, rec in enumerate(recs, 1):
            lines.append(f"{i}. {rec}")

    lines += [
        "",
        f"*Reviewed: {reviewed_at} — Reviewer: {reviewer}*",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mock templates (for --mock-llm / CI)
# ---------------------------------------------------------------------------

_MOCK_TEMPLATES: dict[str, str] = {
    "app-owner": (
        "## Executive Summary\n\nMock report for testing.\n\n"
        "## What Happens Next\n\nRemediate items above within SLA windows.\n"
    ),
    "security": (
        "## Executive Summary\n\nMock security report for testing.\n\n"
        "## Risk Analysis\n\nCritical failures in identity and logging domains require immediate attention.\n"
    ),
}


def _call_llm(system_prompt: str, user_msg: str, model: str, mock: bool = False) -> str:
    if mock:
        audience = "security" if "Security Team" in system_prompt else "app-owner"
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
        max_completion_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    )
    return response.choices[0].message.content.strip()


def _run_pandoc(md_path: Path, docx_path: Path) -> None:
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
    """Generate an executive governance report (Markdown + DOCX for security audience).

    Structure:
      Scorecard + Domain Chart + Priority Findings [HARNESS]
      Executive Summary + Risk Analysis            [LLM]
      Full Control Matrix                          [HARNESS]
      NIST AI RMF Governance Review                [HARNESS]
    """
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

    # ── NIST gate banner ─────────────────────────────────────────────────────
    banner = ""
    nist_section = ""
    if nist_data:
        review = nist_data.get("nist_ai_rmf_review", nist_data)
        overall = review.get("overall", "").lower()
        if audience == "security":
            banner = _NIST_GATE_BANNERS.get(overall, "")
            nist_section = _render_nist_section(nist_data)
            click.echo(f"report-gen: NIST verdict={overall.upper()}", err=True)
        elif audience == "app-owner":
            banner = _NIST_APPOWNER_NOTE.get(overall, "")

    # ── Python-rendered structural sections ──────────────────────────────────
    scorecard = _render_executive_scorecard(backlog_data, sscf_data, org, report_title)
    domain_chart = _render_domain_chart(sscf_data) if sscf_data else ""
    priority = _render_priority_findings(backlog_data)
    full_matrix = _render_full_matrix(backlog_data)

    # ── LLM narrative ────────────────────────────────────────────────────────
    system_prompt = _SYSTEM_PROMPTS[audience]
    user_msg = _build_user_message(backlog_data, sscf_data, nist_data, audience, org, report_title)
    llm_narrative = _call_llm(system_prompt, user_msg, model, mock=mock_llm)

    # ── Assemble document ────────────────────────────────────────────────────
    parts = [p for p in [banner, scorecard, domain_chart, priority, llm_narrative, full_matrix, nist_section] if p]
    markdown = "\n\n".join(parts)

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
