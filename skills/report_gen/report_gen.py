"""
report-gen — governance output skill.

Converts assessment backlog (+ optional sscf benchmark / nist review) into:
  - Plain-language Markdown or DOCX for application owners
  - Technical Markdown or DOCX for CorpIS / governance review

Usage:
    report-gen generate --backlog <path> --audience app-owner|gis --out <path>
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DELIVERABLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "oscal-salesforce-poc" / "deliverables"

_SEVERITY_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}

# DOCX cell shading colours (OOXML hex, no #)
_FILL_PASS = None  # no fill
_FILL_PARTIAL = "FFF2CC"  # yellow
_FILL_FAIL = "FFE0E0"  # red


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def _load_backlog(path: str | Path) -> dict[str, Any]:
    """Load and return the backlog JSON. Exits on error."""
    p = Path(path)
    if not p.exists():
        click.echo(f"ERROR: backlog file not found: {p}", err=True)
        sys.exit(1)
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        click.echo(f"ERROR: invalid JSON in backlog: {exc}", err=True)
        sys.exit(1)


def _load_optional(path: str | Path | None) -> dict[str, Any] | None:
    """Load optional supplementary JSON; return None if path not given or missing."""
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        click.echo(f"WARNING: optional file not found (skipping): {p}", err=True)
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        click.echo(f"WARNING: could not parse {p}: {exc} (skipping)", err=True)
        return None


# ---------------------------------------------------------------------------
# Context assembly
# ---------------------------------------------------------------------------


def _build_context(
    backlog: dict[str, Any],
    sscf_report: dict[str, Any] | None,
    nist_review: dict[str, Any] | None,
    audience: str,
    title: str,
    org_alias: str,
) -> dict[str, Any]:
    """Assemble the template context dict from raw data sources."""
    items: list[dict[str, Any]] = backlog.get("mapped_items", [])

    summary_raw = backlog.get("summary", {})
    status_counts = summary_raw.get("status_counts", {})
    summary = {
        "total": summary_raw.get("findings_total", len(items)),
        "pass": status_counts.get("pass", 0),
        "fail": status_counts.get("fail", 0),
        "partial": status_counts.get("partial", 0),
        "not_applicable": status_counts.get("not_applicable", 0),
    }

    # Critical/High failures — sorted by severity then control_id
    critical_high = [
        i for i in items if i.get("status") in ("fail", "partial") and i.get("severity") in ("critical", "high")
    ]
    critical_high.sort(key=lambda x: (_SEVERITY_ORDER.get(x.get("severity", "low"), 99), x.get("sbs_control_id", "")))

    return {
        "assessment_id": backlog.get("assessment_id", "unknown"),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "org_alias": org_alias or backlog.get("org", "unknown"),
        "title": title,
        "audience": audience,
        "summary": summary,
        "critical_high_findings": critical_high,
        "all_findings": items,
        "sscf_domains": (sscf_report or {}).get("domains", []),
        "nist_rmf": nist_review,
        # passthrough for GIS metadata block
        "catalog_version": backlog.get("catalog_version", ""),
        "framework": backlog.get("framework", "CSA_SSCF"),
        "sscf_overall_score": (sscf_report or {}).get("overall_score"),
        "sscf_overall_status": (sscf_report or {}).get("overall_status"),
    }


# ---------------------------------------------------------------------------
# Executive summary text — user contribution point
# ---------------------------------------------------------------------------


def _executive_summary_text(ctx: dict[str, Any]) -> str:
    """Return a plain-language paragraph summarising the org's security posture.

    This is called from the app-owner Executive Summary section. The tone and
    technical depth here determine how non-technical stakeholders understand risk.

    TODO: Implement this function. Consider:
    - How much Salesforce jargon is appropriate for an app owner audience?
    - Should it name specific failing controls or speak in plain-language categories?
    - Should it include a risk rating (e.g. "HIGH RISK") or remain neutral in tone?

    Parameters
    ----------
    ctx : dict
        The assembled context with keys: assessment_id, org_alias, summary,
        critical_high_findings, sscf_overall_score, sscf_overall_status.

    Returns
    -------
    str
        One paragraph of plain English for the Executive Summary section.
    """
    s = ctx["summary"]
    total_scoreable = s["pass"] + s["fail"] + s["partial"]
    pass_pct = round(100 * s["pass"] / total_scoreable) if total_scoreable else 0
    critical_count = len([f for f in ctx["critical_high_findings"] if f.get("severity") == "critical"])
    high_count = len([f for f in ctx["critical_high_findings"] if f.get("severity") == "high"])

    lines = [
        f"This assessment evaluated {s['total']} security controls for the Salesforce org "
        f'"{ctx["org_alias"]}". '
        f"Of the scoreable controls, {pass_pct}% are passing, with {s['fail']} control(s) failing "
        f"and {s['partial']} requiring partial remediation.",
    ]

    if critical_count:
        lines.append(
            f"There are {critical_count} critical finding(s) that require immediate attention "
            "to prevent potential security incidents or compliance violations."
        )
    if high_count:
        lines.append(
            f"Additionally, {high_count} high-severity finding(s) should be addressed within the next 30 days."
        )

    if not critical_count and not high_count:
        lines.append("No critical or high-severity findings were identified in this assessment.")

    return " ".join(lines)


# ---------------------------------------------------------------------------
# Markdown writer
# ---------------------------------------------------------------------------

_STATUS_EMOJI = {"pass": "✅", "fail": "❌", "partial": "⚠️", "not_applicable": "—"}


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render a simple GFM Markdown table."""
    sep = ["-" * max(len(h), 3) for h in headers]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        cells = [str(c).replace("|", "\\|") for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _write_md(ctx: dict[str, Any], out_path: Path) -> None:  # noqa: C901
    """Write Markdown governance report to out_path."""
    audience = ctx["audience"]
    lines: list[str] = []

    if audience == "app-owner":
        # ── Section 1: Executive Summary ────────────────────────────────────
        lines.append(f"# {ctx['title']}")
        lines.append("")
        lines.append(
            f"**Assessment ID:** {ctx['assessment_id']}  \n"
            f"**Generated:** {ctx['generated_at_utc']}  \n"
            f"**Org:** {ctx['org_alias']}"
        )
        lines.append("")
        lines.append("# Executive Summary")
        lines.append("")
        lines.append(_executive_summary_text(ctx))
        lines.append("")

        s = ctx["summary"]
        lines.append(
            _md_table(
                ["Total Controls", "Pass", "Fail", "Partial", "Not Applicable"],
                [[s["total"], s["pass"], s["fail"], s["partial"], s["not_applicable"]]],
            )
        )
        lines.append("")

        # ── Section 2: Critical and High Findings ───────────────────────────
        lines.append("## Critical and High Findings")
        lines.append("")
        ch = ctx["critical_high_findings"]
        if ch:
            rows = [
                [
                    f["sbs_control_id"],
                    f.get("sbs_title", ""),
                    f.get("severity", "").title(),
                    f.get("owner", ""),
                    f.get("due_date", ""),
                    f.get("remediation", "")[:120],
                ]
                for f in ch
            ]
            lines.append(_md_table(["Control", "Title", "Severity", "Owner", "Due Date", "Action"], rows))
        else:
            lines.append("_No critical or high findings._")
        lines.append("")

        # ── Section 3: What Happens Next ────────────────────────────────────
        lines.append("## What Happens Next")
        lines.append("")
        lines.append(
            "1. **Review** the findings table above with your technical team.\n"
            "2. **Prioritise** critical and high findings — these carry the highest risk.\n"
            "3. **Assign owners** for each finding and confirm due dates.\n"
            "4. **Remediate** using the action guidance in the findings table.\n"
            "5. **Re-assess** after remediation to verify controls are passing.\n"
            "6. **Escalate** any findings you cannot remediate within the due date to CorpIS."
        )
        lines.append("")

        # ── Section 4: Appendix — Full Control Matrix ───────────────────────
        lines.append("## Appendix: Full Control Matrix")
        lines.append("")
        rows = [
            [
                f.get("sbs_control_id", ""),
                f.get("sbs_title", ""),
                _STATUS_EMOJI.get(f.get("status", ""), f.get("status", "")),
            ]
            for f in ctx["all_findings"]
        ]
        lines.append(_md_table(["Control ID", "Title", "Status"], rows))
        lines.append("")

    else:  # gis audience
        # ── Section 1: Assessment Metadata ──────────────────────────────────
        lines.append(f"# {ctx['title']}")
        lines.append("")
        lines.append("# Assessment Metadata")
        lines.append("")
        lines.append(
            _md_table(
                ["Field", "Value"],
                [
                    ["Assessment ID", ctx["assessment_id"]],
                    ["Generated (UTC)", ctx["generated_at_utc"]],
                    ["Org / Alias", ctx["org_alias"]],
                    ["Catalog Version", ctx.get("catalog_version", "")],
                    ["Framework", ctx.get("framework", "CSA_SSCF")],
                ],
            )
        )
        lines.append("")

        # ── Section 2: Summary Metrics ──────────────────────────────────────
        lines.append("## Summary Metrics")
        lines.append("")
        s = ctx["summary"]
        metric_rows: list[list[str]] = [
            ["Total Controls", str(s["total"])],
            ["Pass", str(s["pass"])],
            ["Fail", str(s["fail"])],
            ["Partial", str(s["partial"])],
            ["Not Applicable", str(s["not_applicable"])],
        ]
        if ctx.get("sscf_overall_score") is not None:
            metric_rows.append(["SSCF Overall Score", f"{ctx['sscf_overall_score']:.0%}"])
            metric_rows.append(["SSCF Overall Status", (ctx.get("sscf_overall_status") or "").upper()])
        lines.append(_md_table(["Metric", "Value"], metric_rows))
        lines.append("")

        # ── Section 3: Full Control Matrix ──────────────────────────────────
        lines.append("## Full Control Matrix")
        lines.append("")
        rows = []
        for f in ctx["all_findings"]:
            sscf_ids = ", ".join(f.get("sscf_control_ids", []))
            rows.append(
                [
                    f.get("sbs_control_id", ""),
                    f.get("sbs_title", ""),
                    f.get("status", ""),
                    f.get("severity", ""),
                    f.get("owner", ""),
                    f.get("due_date", ""),
                    sscf_ids,
                ]
            )
        lines.append(
            _md_table(
                ["SBS ID", "Title", "Status", "Severity", "Owner", "Due Date", "SSCF Controls"],
                rows,
            )
        )
        lines.append("")

        # ── Section 4: SSCF Domain Heatmap ──────────────────────────────────
        lines.append("## SSCF Domain Heatmap")
        lines.append("")
        domains = ctx.get("sscf_domains", [])
        if domains:
            d_rows = []
            for d in domains:
                d_rows.append(
                    [
                        d.get("domain_id", ""),
                        d.get("domain_label", d.get("domain_id", "")),
                        f"{d.get('score', 0):.0%}",
                        (d.get("status") or "").upper(),
                        str(d.get("fail", 0)),
                        str(d.get("partial", 0)),
                        str(d.get("pass", 0)),
                    ]
                )
            lines.append(
                _md_table(
                    ["Domain ID", "Domain", "Score", "Status", "Fail", "Partial", "Pass"],
                    d_rows,
                )
            )
        else:
            lines.append("_SSCF benchmark not provided — run `sscf-benchmark` to generate domain heatmap._")
        lines.append("")

        # ── Section 5: NIST AI RMF Compliance Note ──────────────────────────
        lines.append("## NIST AI RMF Compliance Note")
        lines.append("")
        nist = ctx.get("nist_rmf")
        if nist:
            for fn in ("GOVERN", "MAP", "MEASURE", "MANAGE"):
                val = nist.get(fn) or nist.get(fn.lower()) or "[not reported]"
                lines.append(f"**{fn}:** {val}  ")
            lines.append("")
        else:
            lines.append("_[PENDING NIST REVIEW]_")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    click.echo(f"  wrote Markdown report → {out_path}", err=True)


# ---------------------------------------------------------------------------
# DOCX writer
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)


def _apply_cell_fill(cell: Any, fill_hex: str | None) -> None:
    """Apply background shading to a docx table cell."""
    if not fill_hex:
        return
    from docx.oxml import OxmlElement  # type: ignore
    from docx.oxml.ns import qn  # type: ignore

    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tc_pr.append(shd)


def _docx_table(doc: Any, headers: list[str], rows: list[list[str]], status_col: int | None = None) -> None:
    """Add a formatted table to the docx Document."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH  # type: ignore
    from docx.shared import Pt  # type: ignore

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light List Accent 1"

    # Header row
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        para = hdr_cells[i].paragraphs[0]
        run = para.runs[0] if para.runs else para.add_run(h)
        run.bold = True
        run.font.size = Pt(9)

    # Data rows
    _STATUS_FILL = {"pass": _FILL_PASS, "partial": _FILL_PARTIAL, "fail": _FILL_FAIL}
    for r_idx, row in enumerate(rows):
        cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row):
            cells[c_idx].text = str(val)
            for para in cells[c_idx].paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for run in para.runs:
                    run.font.size = Pt(8)
        # Apply status shading if status_col is given
        if status_col is not None and status_col < len(row):
            status_val = str(row[status_col]).lower()
            fill = _STATUS_FILL.get(status_val)
            _apply_cell_fill(cells[status_col], fill)


def _write_docx(ctx: dict[str, Any], out_path: Path) -> None:  # noqa: C901
    """Write DOCX governance report to out_path."""
    try:
        from docx import Document  # type: ignore
    except ImportError:
        click.echo("ERROR: python-docx not available. Install docxtpl>=0.18.0.", err=True)
        sys.exit(1)

    doc = Document()
    audience = ctx["audience"]

    # Title
    doc.add_heading(ctx["title"], level=0)
    doc.add_paragraph(
        f"Assessment ID: {ctx['assessment_id']}  |  Generated: {ctx['generated_at_utc']}  |  Org: {ctx['org_alias']}"
    )

    if audience == "app-owner":
        # Executive Summary
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(_executive_summary_text(ctx))

        s = ctx["summary"]
        doc.add_heading("Summary Metrics", level=2)
        _docx_table(
            doc,
            ["Total Controls", "Pass", "Fail", "Partial", "Not Applicable"],
            [[s["total"], s["pass"], s["fail"], s["partial"], s["not_applicable"]]],
        )

        # Critical and High Findings
        doc.add_heading("Critical and High Findings", level=1)
        ch = ctx["critical_high_findings"]
        if ch:
            rows = [
                [
                    f["sbs_control_id"],
                    f.get("sbs_title", ""),
                    f.get("severity", "").title(),
                    f.get("owner", ""),
                    f.get("due_date", ""),
                    f.get("remediation", "")[:150],
                ]
                for f in ch
            ]
            _docx_table(doc, ["Control", "Title", "Severity", "Owner", "Due Date", "Action"], rows)
        else:
            doc.add_paragraph("No critical or high findings.")

        # What Happens Next
        doc.add_heading("What Happens Next", level=1)
        steps = [
            "Review the findings table above with your technical team.",
            "Prioritise critical and high findings — these carry the highest risk.",
            "Assign owners for each finding and confirm due dates.",
            "Remediate using the action guidance in the findings table.",
            "Re-assess after remediation to verify controls are passing.",
            "Escalate any findings you cannot remediate within the due date to CorpIS.",
        ]
        for i, step in enumerate(steps, 1):
            doc.add_paragraph(f"{i}. {step}")

        # Full Control Matrix
        doc.add_heading("Appendix: Full Control Matrix", level=1)
        rows = [[f.get("sbs_control_id", ""), f.get("sbs_title", ""), f.get("status", "")] for f in ctx["all_findings"]]
        # status is col index 2
        _docx_table(doc, ["Control ID", "Title", "Status"], rows, status_col=2)

    else:  # gis
        # Assessment Metadata
        doc.add_heading("Assessment Metadata", level=1)
        _docx_table(
            doc,
            ["Field", "Value"],
            [
                ["Assessment ID", ctx["assessment_id"]],
                ["Generated (UTC)", ctx["generated_at_utc"]],
                ["Org / Alias", ctx["org_alias"]],
                ["Catalog Version", ctx.get("catalog_version", "")],
                ["Framework", ctx.get("framework", "CSA_SSCF")],
            ],
        )

        # Summary Metrics
        doc.add_heading("Summary Metrics", level=1)
        s = ctx["summary"]
        metric_rows: list[list] = [
            ["Total Controls", s["total"]],
            ["Pass", s["pass"]],
            ["Fail", s["fail"]],
            ["Partial", s["partial"]],
            ["Not Applicable", s["not_applicable"]],
        ]
        if ctx.get("sscf_overall_score") is not None:
            metric_rows.append(["SSCF Overall Score", f"{ctx['sscf_overall_score']:.0%}"])
            metric_rows.append(["SSCF Overall Status", (ctx.get("sscf_overall_status") or "").upper()])
        _docx_table(doc, ["Metric", "Value"], metric_rows)

        # Full Control Matrix
        doc.add_heading("Full Control Matrix", level=1)
        rows = []
        for f in ctx["all_findings"]:
            sscf_ids = ", ".join(f.get("sscf_control_ids", []))
            rows.append(
                [
                    f.get("sbs_control_id", ""),
                    f.get("sbs_title", ""),
                    f.get("status", ""),
                    f.get("severity", ""),
                    f.get("owner", ""),
                    f.get("due_date", ""),
                    sscf_ids,
                ]
            )
        _docx_table(
            doc,
            ["SBS ID", "Title", "Status", "Severity", "Owner", "Due Date", "SSCF Controls"],
            rows,
            status_col=2,
        )

        # SSCF Domain Heatmap
        doc.add_heading("SSCF Domain Heatmap", level=1)
        domains = ctx.get("sscf_domains", [])
        if domains:
            d_rows = [
                [
                    d.get("domain_id", ""),
                    d.get("domain_label", d.get("domain_id", "")),
                    f"{d.get('score', 0):.0%}",
                    (d.get("status") or "").upper(),
                    d.get("fail", 0),
                    d.get("partial", 0),
                    d.get("pass", 0),
                ]
                for d in domains
            ]
            _docx_table(
                doc,
                ["Domain ID", "Domain", "Score", "Status", "Fail", "Partial", "Pass"],
                d_rows,
            )
        else:
            doc.add_paragraph("SSCF benchmark not provided.")

        # NIST AI RMF
        doc.add_heading("NIST AI RMF Compliance Note", level=1)
        nist = ctx.get("nist_rmf")
        if nist:
            for fn in ("GOVERN", "MAP", "MEASURE", "MANAGE"):
                val = nist.get(fn) or nist.get(fn.lower()) or "[not reported]"
                doc.add_paragraph(f"{fn}: {val}")
        else:
            doc.add_paragraph("[PENDING NIST REVIEW]")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    click.echo(f"  wrote DOCX report → {out_path}", err=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """report-gen — governance output skill (DOCX + Markdown)."""


@cli.command()
@click.option(
    "--backlog",
    required=True,
    help="Path to backlog.json produced by oscal_gap_map.py.",
)
@click.option(
    "--audience",
    required=True,
    type=click.Choice(["app-owner", "gis"]),
    help="Report audience: 'app-owner' (plain-language) or 'gis' (technical governance).",
)
@click.option(
    "--out",
    required=True,
    help="Output file path. Extension determines format: .md or .docx.",
)
@click.option(
    "--sscf-benchmark",
    "sscf_benchmark",
    default=None,
    help="Optional path to sscf_report.json (adds domain heatmap to GIS report).",
)
@click.option(
    "--nist-review",
    "nist_review",
    default=None,
    help="Optional path to nist_review.json (adds NIST AI RMF section to GIS report).",
)
@click.option(
    "--title",
    default=None,
    help="Custom report title (auto-generated if omitted).",
)
@click.option(
    "--org-alias",
    "org_alias",
    default=None,
    help="Org alias / identifier (falls back to assessment_id org field).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print what would be generated without writing any files.",
)
def generate(
    backlog: str,
    audience: str,
    out: str,
    sscf_benchmark: str | None,
    nist_review: str | None,
    title: str | None,
    org_alias: str | None,
    dry_run: bool,
) -> None:
    """Generate a governance report from assessment backlog."""
    backlog_data = _load_backlog(backlog)
    sscf_data = _load_optional(sscf_benchmark)
    nist_data = _load_optional(nist_review)

    out_path = Path(out)
    if not out_path.is_absolute():
        out_path = (_DELIVERABLES_DIR / out_path).resolve()

    ext = out_path.suffix.lower()
    if ext not in (".md", ".docx"):
        click.echo(f"ERROR: unsupported output format '{ext}'. Use .md or .docx.", err=True)
        sys.exit(1)

    assessment_id = backlog_data.get("assessment_id", "unknown")
    resolved_org = org_alias or backlog_data.get("org", "unknown")
    date_str = datetime.now(UTC).strftime("%Y-%m-%d")

    auto_title = (
        f"Salesforce Security Assessment — {resolved_org} — {date_str}"
        if audience == "app-owner"
        else f"Salesforce OSCAL/SSCF Governance Review — {resolved_org} — {date_str}"
    )
    resolved_title = title or auto_title

    if dry_run:
        click.echo(
            f"DRY RUN — would generate {ext[1:].upper()} report:\n"
            f"  assessment_id : {assessment_id}\n"
            f"  audience      : {audience}\n"
            f"  title         : {resolved_title}\n"
            f"  output        : {out_path}\n"
            f"  sscf_benchmark: {sscf_benchmark or '(none)'}\n"
            f"  nist_review   : {nist_review or '(none)'}"
        )
        return

    ctx = _build_context(backlog_data, sscf_data, nist_data, audience, resolved_title, resolved_org)

    click.echo(
        f"  generating {ext[1:].upper()} report for audience={audience} assessment={assessment_id}",
        err=True,
    )

    if ext == ".md":
        _write_md(ctx, out_path)
    else:
        _write_docx(ctx, out_path)

    click.echo(f"report-gen: done → {out_path}")


if __name__ == "__main__":
    cli()
