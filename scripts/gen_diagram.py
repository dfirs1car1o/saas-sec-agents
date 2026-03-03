#!/usr/bin/env python3
"""
gen_diagram.py — Generate reference architecture diagram for saas-sec-agents.

Outputs: docs/architecture.png

Shows the 7-agent Claude layer orchestrating 4 Python CLI skills across the
full assessment pipeline:
    sfdc-connect → oscal-assess → oscal_gap_map → sscf-benchmark → report-gen

Security Reviewer is a parallel DevSecOps audit agent — invoked by the
orchestrator on CI/CD and skill changes, not part of the main assessment flow.

SFDC Expert is an on-call specialist — invoked when findings have needs_expert_review=true.

Run manually or automatically via GitHub Actions on every push to main.

Usage:
    python3 scripts/gen_diagram.py

Requires:
    pip install diagrams
    brew install graphviz   # macOS
    apt-get install graphviz  # Linux
"""

from __future__ import annotations

from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.generic.storage import Storage
from diagrams.onprem.compute import Server
from diagrams.programming.flowchart import Document, MultipleDocuments
from diagrams.programming.language import Python
from diagrams.saas.identity import Okta

_OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture"

_GRAPH = {
    "fontsize": "12",
    "bgcolor": "white",
    "pad": "0.6",
    "splines": "ortho",
    "nodesep": "0.6",
    "ranksep": "0.8",
}

_NODE = {"fontsize": "11"}


def main() -> None:
    with Diagram(
        "SaaS Security Agents — Reference Architecture",
        filename=str(_OUT),
        show=False,
        graph_attr=_GRAPH,
        node_attr=_NODE,
        direction="LR",
    ):
        # ── Input ────────────────────────────────────────────────────────────
        with Cluster("Salesforce Org"):
            sfdc = Okta("SFDC Org\n(read-only)")

        # ── Agent Layer ──────────────────────────────────────────────────────
        with Cluster("Agent Layer  (Claude API)"):
            orchestrator = Server("Orchestrator\nOpus 4.6")
            with Cluster("Sub-Agents"):
                collector = Server("Collector\nSonnet 4.6")
                assessor = Server("Assessor\nSonnet 4.6")
                nist_reviewer = Server("NIST Reviewer\nSonnet 4.6")
                reporter = Server("Reporter\nHaiku 4.5")
                security_reviewer = Server("Security Reviewer\nSonnet 4.6")
                sfdc_expert = Server("SFDC Expert\nSonnet 4.6")  # on-call specialist

        # ── Skill CLIs ───────────────────────────────────────────────────────
        with Cluster("Skill CLIs  (Python)"):
            sfdc_connect = Python("sfdc-connect")
            oscal_assess = Python("oscal-assess")
            gap_map = Python("oscal_gap_map.py")
            sscf_bench = Python("sscf-benchmark")
            report_gen = Python("report-gen")

        # ── Generated Artifacts ──────────────────────────────────────────────
        with Cluster("Generated Artifacts"):
            raw_json = Storage("sfdc_raw.json")
            gap_json = Storage("gap_analysis.json")
            backlog_json = Storage("backlog.json")
            sscf_json = Storage("sscf_report.json")

        # ── Governance Deliverables ───────────────────────────────────────────
        with Cluster("Governance Deliverables"):
            app_owner = Document("App Owner\nReport")
            corpis = MultipleDocuments("CorpIS\nGovernance Review")

        # ── Data pipeline (solid arrows) ─────────────────────────────────────
        sfdc >> sfdc_connect >> raw_json
        raw_json >> oscal_assess >> gap_json
        gap_json >> gap_map >> backlog_json
        backlog_json >> sscf_bench >> sscf_json
        backlog_json >> report_gen
        sscf_json >> report_gen
        report_gen >> app_owner
        report_gen >> corpis

        # ── Agent orchestration (dashed arrows) ──────────────────────────────
        dashed = Edge(style="dashed", color="steelblue")
        orchestrator >> dashed >> collector
        orchestrator >> dashed >> assessor
        orchestrator >> dashed >> nist_reviewer
        orchestrator >> dashed >> reporter
        orchestrator >> dashed >> security_reviewer
        orchestrator >> dashed >> sfdc_expert

        collector >> Edge(style="dashed", color="gray") >> sfdc_connect
        assessor >> Edge(style="dashed", color="gray") >> oscal_assess
        assessor >> Edge(style="dashed", color="gray") >> gap_map
        assessor >> Edge(style="dashed", color="gray") >> sscf_bench
        reporter >> Edge(style="dashed", color="gray") >> report_gen

    print(f"diagram written → {_OUT}.png")


if __name__ == "__main__":
    main()
