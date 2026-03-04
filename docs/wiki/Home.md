# saas-sec-agents Wiki

Welcome to the **SaaS Security Multi-Agent System** wiki. Fully automated AI pipeline for Salesforce OSCAL/SSCF security assessments.

---

## Quick Links

| Page | What it covers |
|---|---|
| [Onboarding](Onboarding) | Get running in 10 minutes (any platform) |
| [macOS Setup](macOS-Setup) | Apple Silicon + Intel — step by step |
| [Linux Setup](Linux-Setup) | Ubuntu, Debian, RHEL, WSL2 — step by step |
| [Windows Setup](Windows-Setup) | Corporate Windows machine with VS Code — step by step |
| [Architecture Overview](Architecture-Overview) | How the system is designed |
| [Agent Reference](Agent-Reference) | All 7 agents — roles, models, triggers |
| [Skill Reference](Skill-Reference) | All 5 CLI tools — usage, inputs, outputs |
| [Pipeline Walkthrough](Pipeline-Walkthrough) | Step-by-step: from org → report |
| [CI-CD Reference](CI-CD-Reference) | Every CI job, what it checks, how to fix failures |
| [Security Model](Security-Model) | Rules, gates, escalation paths |
| [Configuration Reference](Configuration-Reference) | All env vars, config files, YAML schemas |
| [Running a Dry Run](Running-a-Dry-Run) | Full pipeline without a live Salesforce org |
| [Troubleshooting](Troubleshooting) | Common errors and fixes |

---

## What This Repo Does

This system connects to Salesforce orgs, runs OSCAL and CSA SSCF security assessments, and generates governance outputs for:
- **Application owners** — remediation backlog with priority actions and due dates (Markdown)
- **Security governance review** — full DOCX + Markdown report with Executive Scorecard, Domain Posture chart, NIST AI RMF review, and sorted control matrix

The pipeline is fully agentic: `gpt-5.2` orchestrates 5 CLI tools and 7 specialist agents over a 12-turn ReAct loop. No human input needed once triggered.

---

## Bare Minimum to Run

```text
Python 3.11+  +  git  +  pip install -e .  +  .env with API keys
```

No Docker. No Node.js. No cloud accounts beyond OpenAI + Salesforce.

---

## Quick Start (Any Platform)

```bash
git clone git@github.com:dfirs1car1o/saas-sec-agents.git
cd saas-sec-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -e . && pip install pytest
cp .env.example .env   # fill in OPENAI_API_KEY + Salesforce credentials
pytest tests/ -v       # 12/12 should pass (offline, no API keys needed)
agent-loop run --dry-run --env dev --org test-org
```

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
| NIST review | ✅ Done | nist-review skill, 7-step pipeline, gate logic |
| JWT Auth | ✅ Done | JWT Bearer flow, live verified |
| sfdc-expert | ✅ Done | On-call Apex/SFDC specialist agent |
| SDK Migration | ✅ Done | Anthropic → OpenAI (gpt-5.2 / gpt-4o-mini) |
| Executive reports | ✅ Done | Python-rendered scorecard, domain chart, sorted matrix |
