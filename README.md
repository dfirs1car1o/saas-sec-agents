# saas-sec-agents

SaaS Security multi-agent AI system for OSCAL and CSA SSCF assessments across Salesforce and Workday. Produces governance-grade evidence packages for application owners and business security review cycles.

> **New here?** Start with the **[Wiki →](https://github.com/dfirs1car1o/saas-sec-agents/wiki)** for full onboarding instructions, platform-specific setup guides (macOS, Linux, Windows), pipeline walkthroughs, and a complete skill and agent reference.

## What This Is

A read-only, fully automated assessment pipeline that:

1. Connects to SaaS platforms (Salesforce now; Workday blueprint complete) and extracts security-relevant configuration
2. Maps findings to platform OSCAL catalogs → CSA SSCF domains → CCM v4.1 → SOX/HIPAA/SOC2 regulatory crosswalk
3. Generates structured evidence artifacts (JSON, Markdown, DOCX) for governance review
4. Validates AI-assisted outputs against NIST AI RMF 1.0 with blocking gate logic before delivery

This system **never writes to any SaaS org**. All evidence stays in `docs/oscal-salesforce-poc/generated/`.

## Quick Start

**Prerequisites:** Python 3.11+, `pip`

```bash
git clone git@github.com:dfirs1car1o/saas-sec-agents.git
cd saas-sec-agents
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in credentials
```

**Validate environment:**
```bash
python3 scripts/validate_env.py
```

**Run the full pipeline (all 7 steps, live org):**
```bash
agent-loop run --env dev --org <org-alias> --approve-critical
```

**Run individual skills:**
```bash
# Collect Salesforce security configuration
python3 -m skills.sfdc_connect.sfdc_connect collect --scope all --env dev --out /tmp/sfdc_raw.json

# Generate an assessment report without an API key (mock mode)
python3 -m skills.report_gen.report_gen generate \
  --backlog docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog_latest.json \
  --audience security --out /tmp/report.md --mock-llm
```

## Multi-Agent Architecture

```
Human ──► agent-loop run (harness/loop.py)
               │
               └──► Orchestrator (gpt-5.3-chat-latest)
                         │
                         ├── 1. sfdc_connect_collect     → sfdc_raw.json
                         ├── 2. oscal_assess_assess      → gap_analysis.json
                         ├── 3. oscal_gap_map            → backlog.json + matrix.md
                         ├── 4. sscf_benchmark_benchmark → sscf_report.json
                         ├── 5. nist_review_assess       → nist_review.json
                         ├── 6a. report_gen_generate     (audience=app-owner)
                         └── 6b. report_gen_generate     (audience=security) → .md + .docx
```

All agents are OpenAI models. The orchestrator dispatches numbered tool calls to skills (Python CLIs). Agents communicate through JSON evidence files on disk — no shared state or MCP.

| Agent | Model | Role |
|---|---|---|
| Orchestrator | `gpt-5.3-chat-latest` | Plans and dispatches all 7 pipeline steps |
| Collector | `gpt-5.3-chat-latest` | Interprets Salesforce raw data |
| Assessor | `gpt-5.3-chat-latest` | Runs OSCAL gap analysis and benchmarks |
| NIST Reviewer | `gpt-5.3-chat-latest` | Validates outputs; issues block/flag/pass verdicts |
| Reporter | `gpt-4o-mini` | Writes LLM narrative for governance reports |
| Security Reviewer | `gpt-5.3-chat-latest` | DevSecOps audit on CI/CD skill changes |
| SFDC Expert | `gpt-5.3-chat-latest` | On-call specialist for complex Apex/API questions |

## Skills (CLIs)

All tools are CLI-based Python scripts. Each supports `--help` and `--dry-run`.

| Skill | Module | What It Does |
|---|---|---|
| `sfdc-connect` | `skills/sfdc_connect/` | Authenticates + queries Salesforce via REST and Tooling API |
| `oscal-assess` | `skills/oscal_assess/` | Gaps findings against the SBS OSCAL control catalog |
| `sscf-benchmark` | `skills/sscf_benchmark/` | Scores findings by CSA SSCF domain (red/amber/green) |
| `nist-review` | `skills/nist_review/` | NIST AI RMF 1.0 governance gate (govern/map/measure/manage) |
| `report-gen` | `skills/report_gen/` | Generates executive Markdown + DOCX reports |
| `workday-connect` | `skills/workday_connect/` | **Blueprint complete** — Workday HCM/Finance collector (Phase E, implementation pending) |

### Report Structure

Reports are assembled from deterministic Python-rendered sections (no hallucination risk) plus a focused LLM narrative:

```
[Gate banner]                  ← ⛔ block / 🚩 flag if NIST verdict requires it
Executive Scorecard            ← overall score + severity × status matrix
Domain Posture (ASCII chart)   ← bar chart of all SSCF domain scores
Immediate Actions              ← top-10 critical/fail findings, sorted by severity
Executive Summary + Analysis   ← LLM narrative (2 sections only)
Full Control Matrix            ← complete sorted findings table
NIST AI RMF Governance Review  ← govern/map/measure/manage function table + blockers
```

## Control Frameworks

All platform controls chain through SSCF → CCM v4.1 → regulatory crosswalk (SOX, HIPAA, SOC2 TSC, ISO 27001, NIST 800-53, PCI DSS, GDPR).

| Framework | Version | Config File |
|---|---|---|
| Security Benchmark for Salesforce (SBS) | v0.4.1 | `config/oscal-salesforce/sbs_catalog.json` (OSCAL 1.1.2) |
| Workday Security Control Catalog (WSCC) | v0.2.0 | `config/workday/workday_catalog.json` (OSCAL 1.1.2, 30 controls) |
| CSA SSCF | current | `config/sscf/sscf_catalog.json` (OSCAL 1.1.2, 14 controls) |
| CSA CCM | v4.1 | `config/ccm/ccm_v4.1_oscal_ref.yaml` (reference; 197 controls) |
| NIST AI RMF | 1.0 | Applied by `nist-review` skill |

## Repository Layout

```
agents/                   ← Agent definitions (YAML frontmatter + role docs)
config/
  oscal-salesforce/       ← SBS OSCAL catalog (45 controls) + SSCF mapping
  sscf/                   ← SSCF OSCAL catalog (14 controls) + CCM bridge
  ccm/                    ← CCM v4.1 reference pointer
  workday/                ← Workday OSCAL catalog (30 controls) + SSCF mapping
contexts/                 ← System prompts for assess/review/research modes
docs/
  architecture.png        ← Auto-generated reference architecture diagram
  oscal-salesforce-poc/   ← Generated evidence, deliverables, runbooks
  wiki/                   ← Full wiki (14 pages; mirrors GitHub wiki)
harness/                  ← agent-loop CLI (loop.py, tools.py, agents.py, memory.py)
hooks/                    ← Session lifecycle scripts (start/end/compact)
mission.md                ← Agent identity and authorized scope
schemas/
  baseline_assessment_schema.json  ← v2 platform-agnostic assessment schema
scripts/                  ← oscal_gap_map.py, generate_sbs_oscal_catalog.py, validate_env.py
skills/
  sfdc_connect/           ← Salesforce collector
  oscal_assess/           ← OSCAL gap assessor
  sscf_benchmark/         ← SSCF domain scorer
  nist_review/            ← NIST AI RMF gate
  report_gen/             ← Governance report generator
  workday_connect/        ← Workday collector (blueprint; Phase E)
tests/                    ← pytest suite (12 tests, fully offline with --mock-llm)
```

## Authentication

Two Salesforce auth methods are supported. JWT is preferred for production.

**JWT Bearer (preferred):**
```bash
SF_AUTH_METHOD=jwt
SF_CONSUMER_KEY=<consumer-key>
SF_PRIVATE_KEY_PATH=/path/to/salesforce_jwt_private.pem
SF_DOMAIN=login
```

**SOAP (username/password):**
```bash
SF_USERNAME=...
SF_PASSWORD=...
SF_SECURITY_TOKEN=...
SF_DOMAIN=login
```

## Environment Variables

See `.env.example` for full reference. Minimum required:

```bash
OPENAI_API_KEY=sk-...          # Required for all LLM calls
SF_USERNAME=...                 # Salesforce credentials
SF_AUTH_METHOD=jwt              # or "soap"
QDRANT_IN_MEMORY=1             # Use in-memory Qdrant (no server needed)
MEMORY_ENABLED=0               # Disable Mem0 by default
```

## Security

- Read-only against all Salesforce orgs by default. No writes without explicit human approval.
- Credentials sourced from environment only — never passed as CLI flags or logged.
- All generated evidence written to `docs/oscal-salesforce-poc/generated/` — never to `/tmp`.
- AI outputs validated by the `nist-review` skill before delivery. Block verdict stops report distribution.

## Development

```bash
source .venv/bin/activate
ruff check skills/ harness/    # lint
bandit -r skills/ harness/     # SAST
pip-audit                      # dependency CVEs
pytest tests/ -v               # 12 tests (offline, no API key needed)
```

CI stack: ruff · bandit · pip-audit · gitleaks · pytest · CodeQL · CodeRabbit Pro · dependency-review.

All PRs require one reviewer approval. Branch protection enforces no force pushes to `main`.
