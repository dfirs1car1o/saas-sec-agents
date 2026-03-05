# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog format and semantic versioning intent:
- `Added` for new features
- `Changed` for changes in existing behavior
- `Fixed` for bug fixes
- `Security` for hardening and security controls
- `Removed` for now removed features

## [Unreleased]

### 2026-03-07 — OSCAL catalogs, schema v2, Workday blueprint

#### Added
- `config/sscf/sscf_catalog.json` — OSCAL 1.1.2 SSCF catalog (7 domain groups, 14 controls with full statement/guidance/objective parts)
- `config/sscf/sscf_to_ccm_mapping.yaml` — SSCF→CCM v4.1 bridge; 14 entries with `regulatory_highlights` (SOX, HIPAA, SOC2, ISO 27001, NIST 800-53, PCI DSS, GDPR)
- `config/ccm/ccm_v4.1_oscal_ref.yaml` — Reference pointer to CSA CCM v4.1 published OSCAL catalog (197 controls, 17 regulatory standards); no copy needed
- `config/oscal-salesforce/sbs_catalog.json` — SBS OSCAL 1.1.2 catalog (11 groups, 45 controls); generated from `sbs_controls.json`
- `config/oscal-salesforce/sbs_profile.json` — OSCAL profile expressing SBS as implementation of SSCF catalog
- `scripts/generate_sbs_oscal_catalog.py` — Python conversion script: `sbs_controls.json` → OSCAL 1.1.2 catalog
- `config/workday/workday_catalog.json` v0.2.0 — OSCAL 1.1.2 Workday Security Control Catalog (30 controls, 7 domain groups, full audit procedures/remediation, soap/raas/manual/rest collection methods)
- `config/workday/workday_to_sscf_mapping.yaml` — All 30 Workday controls mapped to SSCF domains and control IDs
- `skills/workday_connect/BLUEPRINT.md` — Full Workday connector specification (ISU/ISSG setup, OAuth 2.0 auth, per-control API reference, graceful degradation, WireMock dev environment)
- `skills/workday_connect/__init__.py` — Package placeholder

#### Changed
- `schemas/baseline_assessment_schema.json` → v2: added `schema_version` (const "2.0"), `assessment_owner`, `data_source`, `ai_generated_findings_notice`, `oscal_catalog_ref`, `assessment_scope`, `mapping_confidence`, `ccm_controls`, `platform_data`; fixed severity enum `"medium"` → `"moderate"`
- `config/workday/workday_catalog.json`: upgraded auth from WS-Security BasicAuth to OAuth 2.0 Client Credentials (universal); WD-IAM-007 changed from `soap` to `rest` (`/staffing/v6/workers`)

#### Security
- Workday connector protocol hardened: OAuth 2.0 Client Credentials replaces WS-Security BasicAuth; no password credentials transmitted; all transports (REST, SOAP, RaaS) use short-lived Bearer tokens

### 2026-03-07 — Open issues resolved (commit 48bc739)

#### Added
- `harness/tools.py` — `finish()` tool: orchestrator calls to signal pipeline completion; loop breaks on `pipeline_complete: true` sentinel
- `harness/loop.py` — `pipeline_complete` sentinel detection; `_MAX_TURNS` bumped 12→14

#### Fixed
- `skills/sfdc_connect/sfdc_connect.py` — `collect_integrations()` now uses Tooling API for RemoteProxy/RemoteSiteSettings before SOQL fallback
- `agents/orchestrator.md` — routing table corrected; `.pdf` removed; `finish()` added at end of sequence

#### Changed
- `.github/CODEOWNERS` — `@compliance-rehab` added to `skills/**` and `config/**`

### 2026-03-03
- feat: add `nist-review` CLI skill (`skills/nist_review/`) with dry-run and live Anthropic mode
- feat: wire `nist_review_assess` as pipeline step 5 in `harness/loop.py`
- fix: PDF `_kv_table` uses `multi_cell()` — NIST notes now wrap instead of truncating
- fix: `sbom.yml` — remove `git push` to protected branch; upload SBOM as CI artifact instead
- fix: `diagram.yml` — remove `git push`; verify committed diagram is up-to-date instead
- fix: `ci.yml` — add `fpdf2` to LGPL allowlist (LGPL-3.0 acceptable for internal tooling)
- fix: pin `actions/upload-artifact` to commit SHA `ea165f8d` (v4.6.2) in diagram + sbom workflows
- fix: ruff format on `report_gen.py`, `nist_review.py`, and test files

### 2026-03-02 (PDF + branding)
- feat: configurable report title via `REPORT_GOVERNANCE_TITLE` env var
- feat: configurable org display name via `REPORT_ORG_DISPLAY_NAME` env var
- feat: org-named output files (`{org}_security_assessment.pdf/.docx/.md`, `{org}_remediation_report.md`)
- feat: `SFDC_ORG_ALIAS` and `SFDC_ENV` env vars as defaults for `agent-loop run`
- fix: PDF SBS ID column widened to 32 mm (SBS-CPORTAL-001 / SBS-SECCONF-001 no longer truncated)
- fix: SSCF domains with 0 scoreable controls show N/A instead of misleading 100% GREEN
- fix: report-gen dispatcher resolves relative `--out` against backlog directory (fixes unknown-org path bug)
- fix: PDF Top Findings section added before Full Control Matrix
- fix: PDF status values title-cased; Unicode symbols mapped to ASCII equivalents

### Changed (2026-03-02 — GitHub Actions upgrades)
- `actions/checkout` v4 → v6 (PR #6)
- `actions/setup-python` v5 → v6 (PR #7)
- `github/codeql-action` v3 → v4 (PR #8)

### Fixed (2026-03-02 — lint)
- `harness/tools.py` — shortened `org` property description strings to satisfy ruff E501 (line-length=120)

### Fixed (2026-03-01 — post-dry-run bugs)
- `harness/loop.py` — added `load_dotenv(_REPO / ".env")` so `ANTHROPIC_API_KEY` is loaded before API client init
- `harness/memory.py` — added HuggingFace embedder fallback when `OPENAI_API_KEY` is absent (Mem0 was defaulting to OpenAI)
- `harness/tools.py` — added `org` property to `oscal_assess_assess`, `oscal_gap_map`, `sscf_benchmark_benchmark` schemas; orchestrator can now pass org alias so artifacts land in `generated/<org>/` not `generated/unknown-org/`
- `harness/loop.py` — default task prompt updated: passes `org` in every tool call, adds report generation as step 5, includes dry-run note to bypass orchestrator prompt quality gate

### Added (Phase 5 — 2026-03-01)
- `scripts/gen_diagram.py` — Python diagrams-as-code script generating `docs/architecture.png`
- `.github/workflows/diagram.yml` — GitHub Action that auto-regenerates the architecture diagram on push to main when skills/harness/scripts/agents/config change; commits back with `[skip ci]`
- `docs/architecture.png` — initial reference architecture diagram (5-agent + 4-skill pipeline)
- `.github/pull_request_template.md` — updated to embed architecture diagram at top of every PR

### Added (Phase 4 — 2026-03-01)
- `skills/report_gen/report_gen.py` — governance output CLI: `report-gen generate`
  - Two audiences: `app-owner` (plain-language executive report) and `gis` (Security Team technical review)
  - Two formats: `.md` (Markdown) and `.docx` (programmatic python-docx with status cell shading)
  - Sections: Executive Summary, Critical/High Findings, What Happens Next, Full Control Matrix, SSCF Domain Heatmap, NIST AI RMF Note
- `tests/test_report_gen.py` — 3 smoke tests (app-owner MD, Security Team MD with SSCF, DOCX magic-byte validation)
- `harness/tools.py` — added `report_gen_generate` tool schema and `_dispatch_report_gen` dispatcher
- `pyproject.toml` — added `report-gen` entry point and `diagrams>=0.23.4` dev dependency

### Fixed (2026-03-01)
- `agents/reporter.md` — corrected CLI invocation (removed non-existent `--template` flag; now shows tool call JSON examples)
- `agents/orchestrator.md` — routing table updated to show exact tool call sequence including `report_gen_generate`
- `harness/agents.py` — added `report_gen_generate` to ORCHESTRATOR tool_names list

### Added (Phase 3 — 2026-02-27)
- `harness/loop.py` — 20-turn ReAct agentic loop, critical/fail safety gate, `agent-loop run` CLI entry point
- `harness/tools.py` — Anthropic tool schemas + subprocess dispatchers for all 4 pipeline stages
- `harness/memory.py` — Mem0+Qdrant session memory: `build_client / load_memories / save_assessment`
- `harness/agents.py` — ORCHESTRATOR AgentConfig (claude-opus-4-6, mission.md + orchestrator.md system prompt)
- `tests/test_harness_dry_run.py` — 3 harness smoke tests (tool dispatch order, error handler, API key plumbing)
- `docs/CONTRIBUTING.md` — full contributor wiki (setup, Docker deps, env vars, pipeline, CI docs)
- Corporate data scrub: CDW → Acme Corp, BSS → SaaS Security Team, GIS → Security Team across 33 files

### Added
- OpenClaw agent framework: mission.md, AGENTS.md, 5 agent definitions, 4 skill SKILL.md files
- `skills/sfdc_connect/sfdc_connect.py` — read-only Salesforce collector CLI (7 scopes, Tooling API)
- Agent architecture: orchestrator-workers pattern with NIST AI RMF auditing layer
- `contexts/` — system prompts for assess/review/research modes
- `hooks/hooks.json` — session lifecycle (start/end/compact)
- `prompts/README.md` — prompting playbook and anti-patterns
- `docs/architecture-blueprint.md` — full agent/skill/model breakdown with system diagram
- `scripts/validate_env.py` — pre-flight check script for local system requirements
- `.coderabbit.yaml` — AI code review with Salesforce-specific security instructions
- `.github/dependabot.yml` — weekly pip + Actions dependency updates
- `.github/workflows/ci.yml` — ruff, bandit, pip-audit, pytest
- `.github/workflows/codeql.yml` — weekly + PR CodeQL semantic analysis
- `.github/workflows/dependency-review.yml` — block PRs introducing HIGH/CRITICAL CVEs
- `.env.example` and `setup.sh` for colleague onboarding

### Changed
- `pyproject.toml`: removed Azure/FastAPI deps, added anthropic + simple-salesforce + click
- `README.md`: full rewrite for saas-sec-agents identity and architecture
- `.github/workflows/security-checks.yml`: replaced Terraform checks with bandit + pip-audit + gitleaks
- `.github/workflows/pr-inline-review.yml`: replaced tflint with ruff + bandit inline annotations
- `CODEOWNERS`: updated with agents/, mission.md, skills/, config/, generated/ ownership

### Removed
- `app/` — FastAPI model router (Azure/DFIR scaffold, not relevant to OSCAL/SSCF system)
- `infra/terraform/` — Azure infrastructure (not relevant to this system)
- `.github/workflows/terraform-plan.yml` — Terraform CI
- `.github/workflows/terraform-apply.yml` — Terraform CI
- `.github/workflows/cloud-mcp-plan.yml` — Azure MCP CI
- `docs/architecture.md` — Azure + Copilot Studio architecture doc
- `docs/azure-tenant-bootstrap.md` — Azure tenant setup doc
- `docs/cloud-mcp-architecture.md` — Azure cloud MCP architecture
- `docs/sift-worker-runbook.md` — SIFT/DFIR worker runbook
- `docs/sample-data-catalog.md` — Azure evidence plane catalog

### Security
- Branch protection on main: 1 PR review required, no force push, stale review dismissal
- Secret scanning and push protection: enabled org-wide
- Dependabot alerts and auto-fix: enabled
- CodeQL analysis: weekly + PR trigger, scoped to skills/ and scripts/
- Dependency review: blocks HIGH/CRITICAL CVE introductions at PR time
- Gitleaks: full-history secret scanning on every push and PR

## [0.1.0] - 2026-02-23

### Added
- CSA SSCF-aligned SaaS baseline controls for Salesforce, ServiceNow, and Workday
- `config/sscf_control_index.yaml` and `schemas/baseline_assessment_schema.json`
- `docs/saas-baseline/` — exception process, RACI, intake template, meeting pack
- OSCAL pipeline scripts: `scripts/oscal_gap_map.py`, `scripts/oscal_import_sbs.py`
- OSCAL control mappings: `config/oscal-salesforce/`
- End-to-end OSCAL example outputs in `docs/oscal-salesforce-poc/generated/`
- UK Salesforce partial copy exception record
