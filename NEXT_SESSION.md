# Next Session Checkpoint — 2026-03-04

## Session Summary

This session completed:
- **Issue #12 fixed** — `assessment_owner` named individual field added to oscal-assess (`--assessment-owner` flag), flows through `gap_analysis.json` → `backlog.json` → report metadata (MD/DOCX/PDF)
- **Issue #13 fixed** — `mapping_confidence` variance: `pass`/`fail` → `high`, `partial` → `medium`, `not_applicable` → `low` (replaces uniform `"high"` across all 45 findings)
- **All 4 NIST issues closed** — #10 #11 #12 #13 all resolved
- **Wiki onboarding expanded** — macOS Silicon, Linux (Ubuntu + Fedora/RHEL), WSL2 sections; JWT setup steps; 12/12 test count; PDF in output table
- **sfdc-expert agent committed** — `agents/sfdc-expert.md` (Sonnet 4.6, on-call Apex/admin specialist)
- **apex-scripts/README.md committed** — safety rules and approval flow for staged Apex scripts
- **`.gitignore` updated** — `deliverables/` directory excluded (generated report artifacts)

---

## Phase Status

| Phase | Status | Deliverable |
|---|---|---|
| Phase 1 | ✅ Done | sfdc-connect CLI + CI stack |
| Phase 2 | ✅ Done | oscal-assess + sscf-benchmark CLIs |
| Phase 3 | ✅ Done | agent-loop harness + Mem0 + Qdrant |
| Phase 4 | ✅ Done | report-gen DOCX/MD/PDF skill |
| Phase 5 | ✅ Done | architecture diagram auto-generation |
| Phase 6 | ✅ Done | security-reviewer agent, CI hardening |
| JWT Auth | ✅ Done | JWT Bearer Flow, live verified |
| Live run | ✅ Done | First real org assessment complete |
| NIST #10/#11 | ✅ Done | due_date auto-populated, data_source declared |
| Not Assessed section | ✅ Done | PDF/DOCX/MD all include not-assessed controls block |
| NIST #12/#13 | ✅ Done | assessment_owner field + mapping_confidence variance |
| Wiki onboarding | ✅ Done | macOS Silicon + Linux + WSL2 platform sections |
| sfdc-expert agent | ✅ Done | agents/sfdc-expert.md + apex-scripts/README.md |

---

## GitHub Issues — All Resolved

| Issue | Title | Priority | Status |
|---|---|---|---|
| #10 | NIST MANAGE-BLOCK: Assign due_date to all critical/high fail findings | P1 | ✅ Fixed (commit 257bd76) |
| #11 | NIST MAP-BLOCK: Declare live vs mock collection in assessment output | P1 | ✅ Fixed (commit 257bd76) |
| #12 | NIST GOVERN-PARTIAL: Replace team-level owner with named individual | P2 | ✅ Fixed (commit faab601) |
| #13 | NIST MEASURE-PARTIAL: Recalibrate mapping_confidence variance | P2 | ✅ Fixed (commit faab601) |

**No open issues. No open PRs.**

---

## Current State

- **Branch:** `main`
- **Last commit:** `faab601`
- **Local path:** `/Users/jerijuar/saas-sec-agents`
- **Tests:** 12/12 passing
- **CI:** All workflows green (ci, codeql, security-checks, sbom, actions-security, diagram)
- **Org:** cyber-coach-dev (`orgfarm-7ecec127cc-dev-ed.develop.my.salesforce.com`)
- **Auth:** JWT Bearer (`SF_AUTH_METHOD=jwt` in .env, key at `~/salesforce_jwt_private.pem`)

---

## Full 7-Step Pipeline

```
agent-loop run --env dev --org cyber-coach-dev --approve-critical
   │
   ├── 1. sfdc_connect_collect     → sfdc_raw.json
   ├── 2. oscal_assess_assess      → gap_analysis.json  (+ data_source, due_date, ai_notice, assessment_owner)
   ├── 3. oscal_gap_map            → backlog.json + matrix.md  (+ assessment_owner, confidence variance)
   ├── 4. sscf_benchmark_benchmark → sscf_report.json
   ├── 5. nist_review_assess       → nist_review.json
   ├── 6. report_gen_generate      (audience=app-owner)  → {org}_remediation_report.md
   └── 7. report_gen_generate      (audience=security)   → {org}_security_assessment.md/.docx/.pdf
```

All outputs: `docs/oscal-salesforce-poc/generated/<org>/<date>/`

Reports include:
- "Controls Not Assessed via API" section (15 API-unassessable controls, reason + how-to-assess)
- Assessment Metadata table with Assessment Owner row

---

## Manual Controls Questionnaire

For the 15 controls that cannot be assessed via API, run:

```bash
# Interactive — walk through all 15 controls
python3 scripts/manual_controls_questionnaire.py --org cyber-coach-dev --env dev \
    --merge docs/oscal-salesforce-poc/generated/cyber-coach-dev/<date>/gap_analysis.json

# Non-interactive — supply pre-filled answers JSON
python3 scripts/manual_controls_questionnaire.py --org cyber-coach-dev \
    --answers answers.json \
    --merge docs/oscal-salesforce-poc/generated/cyber-coach-dev/<date>/gap_analysis.json
```

---

## Live Assessment Results (2026-03-03, cyber-coach-dev)

| Domain | Score | Status |
|---|---|---|
| logging_monitoring | 0% | RED |
| configuration_hardening | 33% | RED |
| identity_access_management | 50% | AMBER |
| data_security_privacy | 50% | AMBER |
| cryptography_key_management | 70% | AMBER |
| governance_risk_compliance | N/A | — |
| threat_detection_response | N/A | — |

**Overall: 48.4% RED** | Critical fails: SBS-AUTH-001 | NIST: block

---

## Resume Commands

```bash
cd /Users/jerijuar/saas-sec-agents
git checkout main && git pull
python3 -m pytest tests/ -v                             # 12/12
agent-loop run --env dev --org cyber-coach-dev --approve-critical
```

---

## Secondary Fixes (not yet in issues)

- `RemoteProxy` SOQL not supported — needs Tooling API or Metadata API approach
- `OrganizationSettings` MFA fields inaccessible via Tooling API on dev orgs
- Report `--out` relative path resolves into `deliverables/` subdirectory — fix `_DELIVERABLES_DIR` logic in report_gen.py

---

## Environment Variables (.env)

```bash
ANTHROPIC_API_KEY=sk-ant-...
SF_USERNAME=jj.4445251c0b95@agentforce.com
SF_AUTH_METHOD=jwt
SF_CONSUMER_KEY=3MVG9Htw...          # in .env
SF_PRIVATE_KEY_PATH=/Users/jerijuar/salesforce_jwt_private.pem
SF_DOMAIN=login
QDRANT_IN_MEMORY=1
MEMORY_ENABLED=0
```
