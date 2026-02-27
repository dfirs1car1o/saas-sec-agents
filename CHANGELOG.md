# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog format and semantic versioning intent:
- `Added` for new features
- `Changed` for changes in existing behavior
- `Fixed` for bug fixes
- `Security` for hardening and security controls
- `Removed` for now removed features

## [Unreleased]

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
