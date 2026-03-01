# saas-sec-agents

SaaS Security multi-agent AI system for OSCAL and CSA SSCF assessments across Salesforce orgs. Produces governance-grade evidence packages for application owners and CorpIS review cycles.

## What This Is

A read-only assessment pipeline that:
1. Connects to Salesforce orgs via the `sfdc-connect` CLI and extracts security-relevant configuration
2. Maps findings to the Security Benchmark for Salesforce (SBS), OSCAL control catalogs, and CSA SSCF
3. Generates structured evidence artifacts (JSON, Markdown, DOCX) for governance review
4. Validates all AI-assisted outputs against NIST AI RMF 1.0 before delivery

This system never writes to any Salesforce org. All evidence stays in `docs/oscal-salesforce-poc/generated/`.

## Multi-Agent Architecture

```
Human ──► Orchestrator (claude-opus-4-6)
               │
               ├──► Collector (claude-sonnet-4-6)    ← sfdc-connect CLI
               │         ↓
               ├──► Assessor (claude-sonnet-4-6)     ← oscal-assess + sscf-benchmark CLIs
               │         ↓
               ├──► NIST Reviewer (claude-sonnet-4-6) ← AI auditing / output validation
               │         ↓
               └──► Reporter (claude-haiku-4-5)      ← report-gen CLI
                          ↓
             Orchestrator QA gate ──► Human
```

Pattern: **Orchestrator-workers** (not a swarm, not peer-to-peer). Agents communicate through JSON evidence files. The NIST Reviewer is the AI auditing layer — it validates every output for bias, evidence completeness, and confidence calibration before the Reporter finalizes anything.

See `AGENTS.md` for full agent definitions, model assignments, and escalation rules.

## Skills (CLIs)

All tools in this system are CLI-based. Call with `--help` if uncertain.

| Skill | Location | What It Does |
|---|---|---|
| `sfdc-connect` | `skills/sfdc_connect/` | Authenticates + queries Salesforce org (REST + Tooling API). Read-only. |
| `oscal-assess` | `skills/oscal-assess/` | Runs OSCAL gap mapping against SBS control catalog |
| `sscf-benchmark` | `skills/sscf-benchmark/` | Benchmarks findings against CSA SSCF control index |
| `report-gen` | `skills/report-gen/` | Generates DOCX, Markdown, and JSON governance outputs |

## Quick Start

**Prerequisites:** Python 3.11+, `uv`

```bash
git clone git@github.com:dfirs1car1o/saas-sec-agents.git
cd saas-sec-agents
./setup.sh
```

Fill in `.env` with your Salesforce credentials (see `.env.example`).

**Test connection:**
```bash
source .venv/bin/activate
python3 -m skills.sfdc_connect.sfdc_connect auth --dry-run
```

**Run an assessment (auth scope):**
```bash
python3 -m skills.sfdc_connect.sfdc_connect collect \
  --scope auth \
  --env dev \
  --out docs/oscal-salesforce-poc/generated/auth_findings.json
```

## Control Frameworks

| Framework | Version | Source |
|---|---|---|
| Security Benchmark for Salesforce (SBS) | v0.4.1 | `config/oscal-salesforce/sbs_source.yaml` |
| CSA SSCF | current | `config/sscf_control_index.yaml` |
| OSCAL gap mapping | — | `config/oscal-salesforce/control_mapping.yaml` |
| NIST AI RMF | 1.0 | Applied by nist-reviewer agent |

## Repository Layout

```
agents/                   ← Agent definitions (YAML frontmatter + role docs)
config/                   ← Control framework configs and mappings
contexts/                 ← System prompts for assess/review/research modes
docs/
  oscal-salesforce-poc/   ← Generated evidence, deliverables, runbooks
  saas-baseline/          ← Exception process, RACI, meeting packs
hooks/                    ← Session lifecycle scripts (start/end/compact)
mission.md                ← Agent identity and authorized scope (read every session)
prompts/                  ← Prompting playbook and anti-patterns
schemas/                  ← Output schema definitions
scripts/                  ← Standalone Python CLIs for ingestion and gap mapping
skills/                   ← Skill CLIs (sfdc-connect, oscal-assess, etc.)
```

## Security

- Read-only against all Salesforce orgs by default. No writes without explicit human approval.
- Credentials sourced from environment only. Never passed as CLI flags. Never logged.
- All generated evidence written to `docs/oscal-salesforce-poc/generated/` — never to `/tmp`.
- CI: ruff (lint), bandit (SAST), pip-audit (dependency CVEs), CodeQL (semantic analysis).
- AI outputs validated by nist-reviewer agent before delivery.

## Development

```bash
source .venv/bin/activate
ruff check skills/          # lint
bandit -r skills/           # SAST
pip-audit                   # dependency CVEs
pytest tests/               # unit tests (Phase 3)
```

All PRs require one reviewer approval. Branch protection enforces no force pushes to main.
