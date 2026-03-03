# saas-sec-agents Wiki

Welcome to the **SaaS Security Multi-Agent System** wiki. This is a fully automated AI pipeline for Salesforce OSCAL/SSCF security assessments.

---

## Quick Links

| Page | What it covers |
|---|---|
| [Onboarding](Onboarding) | Get running in 10 minutes (Mac/Linux) |
| [Windows Setup](Windows-Setup) | Corporate Windows machine with VS Code — step by step |
| [Architecture Overview](Architecture-Overview) | How the system is designed |
| [Agent Reference](Agent-Reference) | All 6 agents — roles, models, triggers |
| [Skill Reference](Skill-Reference) | All 4 CLI tools — usage, inputs, outputs |
| [Pipeline Walkthrough](Pipeline-Walkthrough) | Step-by-step: from org → report |
| [CI-CD Reference](CI-CD-Reference) | Every CI job, what it checks, how to fix failures |
| [Security Model](Security-Model) | Rules, gates, escalation paths |
| [Configuration Reference](Configuration-Reference) | All env vars, config files, YAML schemas |
| [Running a Dry Run](Running-a-Dry-Run) | Full pipeline without a live Salesforce org |
| [Troubleshooting](Troubleshooting) | Common errors and fixes |

---

## What This Repo Does

This system connects to Salesforce orgs, runs OSCAL and CSA SSCF security assessments, and generates governance outputs for:
- **Application owners** — remediation backlog in Markdown
- **CorpIS / GIS review** — full DOCX report with SSCF heatmap and NIST AI RMF compliance note

The pipeline is fully agentic: `claude-opus-4-6` orchestrates 4 CLI tools and 6 specialist agents over a 20-turn ReAct loop. No human input needed once triggered.

---

## Bare Minimum to Run

```text
Python 3.11+  +  git  +  pip install -e .  +  .env with API keys
```

No Docker. No Node.js. No cloud accounts beyond Anthropic + Salesforce.

---

## Current Status

| Phase | Status | Deliverable |
|---|---|---|
| 1 | ✅ Done | `sfdc-connect` CLI + full CI stack |
| 2 | ✅ Done | `oscal-assess` + `sscf-benchmark` CLIs |
| 3 | ✅ Done | `agent-loop` harness + Mem0 session memory |
| 4 | ✅ Done | `report-gen` DOCX/MD governance output |
| 5 | ✅ Done | Auto-regenerating architecture diagram |
| 6 | ✅ Done | CI hardening, security-reviewer agent |
| NIST review + CI fixes | 2026-03-03 | ✅ Done | nist-review skill, 7-step pipeline, CI hardening |
