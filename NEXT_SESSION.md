# Next Session Checkpoint — 2026-03-03

## Session Summary

This session completed:
- **JWT Bearer Auth** (`SF_AUTH_METHOD=jwt`) — full implementation in sfdc-connect, live verified against cyber-coach-dev org
- **SOQL query fixes** — 5 broken field names fixed (SecuritySettings Metadata blob, event-monitoring GROUP BY, transaction-security IsEnabled, integrations AuthenticationProtocol, oauth PermittedUsersPolicyEnum)
- **NIST max_tokens fix** — bumped 1024→2048; LLM was cutting JSON mid-response, all 4 dimensions now return real verdicts
- **NIST regex fallback** — added re.search() fallback for responses with markdown fence preamble
- **First live full pipeline run** — 48.4% RED, 1 critical fail (SBS-AUTH-001), NIST verdict: block (4 issues)
- **4 GitHub Issues opened** — #10, #11, #12, #13 (NIST MANAGE/MAP/GOVERN/MEASURE fixes)
- **Issue #10 fixed** — `due_date` auto-populated in oscal-assess (critical=7d, high=30d, moderate=90d, low=180d)
- **Issue #11 fixed** — `data_source` + `ai_generated_findings_notice` added to gap_analysis.json output
- **CI ruff fix** — harness/ files reformatted (loop.py, memory.py, tools.py)
- **Not Assessed Controls section** — PDF/DOCX/MD reports now include a dedicated section listing the 15 API-unassessable controls with reason + how-to-assess guidance
- **manual_controls_questionnaire.py** — new script for collecting manual evidence for those 15 controls; supports interactive + `--answers` file + `--merge` back into gap_analysis

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

---

## Open GitHub Issues

| Issue | Title | Priority | Status |
|---|---|---|---|
| #10 | NIST MANAGE-BLOCK: Assign due_date to all critical/high fail findings | P1 | ✅ Fixed (commit 257bd76) |
| #11 | NIST MAP-BLOCK: Declare live vs mock collection in assessment output | P1 | ✅ Fixed (commit 257bd76) |
| #12 | NIST GOVERN-PARTIAL: Replace team-level owner with named individual | P2 | Open |
| #13 | NIST MEASURE-PARTIAL: Recalibrate mapping_confidence variance | P2 | Open |

---

## Current State

- **Branch:** `main`
- **Last commit:** `7c4e5ac`
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
   ├── 2. oscal_assess_assess      → gap_analysis.json  (+ data_source, due_date, ai_notice)
   ├── 3. oscal_gap_map            → backlog.json + matrix.md
   ├── 4. sscf_benchmark_benchmark → sscf_report.json
   ├── 5. nist_review_assess       → nist_review.json
   ├── 6. report_gen_generate      (audience=app-owner)  → {org}_remediation_report.md
   └── 7. report_gen_generate      (audience=security)   → {org}_security_assessment.md/.docx/.pdf
```

All outputs: `docs/oscal-salesforce-poc/generated/<org>/<date>/`

Reports now include a "Controls Not Assessed via API" section with reason + how-to-assess for
all 15 not_applicable controls.

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
| logging_monitoring | 0% | 🔴 RED |
| configuration_hardening | 33% | 🔴 RED |
| identity_access_management | 50% | 🟡 AMBER |
| data_security_privacy | 50% | 🟡 AMBER |
| cryptography_key_management | 70% | 🟡 AMBER |
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
