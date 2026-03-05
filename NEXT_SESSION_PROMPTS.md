# Next Session Prompts — saas-sec-agents

## Current State (2026-03-07)

- **Repo:** `https://github.com/dfirs1car1o/saas-sec-agents` — branch `main` (clean, CI green)
- **Last commit:** `e148e44` — Workday protocol upgrade (OAuth 2.0, BLUEPRINT.md)
- **Local path:** `/Users/jerijuar/saas-sec-agents` — Python 3.13.7, `.venv/`
- **Pipeline:** 7 steps, verified end-to-end. Live org: cyber-coach-dev (48.4% RED)
- **Phase status:** A/B/C done. Phase E (Workday connector implementation) is next.

---

## Prompt 1: Standard session start

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md for full context.
Repo is at /Users/jerijuar/saas-sec-agents on main branch (clean).
Run: pytest tests/ -v && python3 scripts/validate_env.py to confirm environment.
```

---

## Prompt 2: Phase E — Implement Workday connector

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md and
skills/workday_connect/BLUEPRINT.md for full context.

Implement skills/workday_connect/workday_connect.py:
- OAuth 2.0 Client Credentials auth (get_oauth_token function)
- OSCAL-catalog-driven collection loop (parse workday_catalog.json)
- Dispatch by collection-method: rest / soap / raas / manual
- Graceful degradation: RaaS 404 → not_applicable; SOAP 403 → partial
- --dry-run flag (no network calls)
- Validate output against schemas/baseline_assessment_schema.json

Start with: WireMock stub server for dev (no live Workday tenant needed).
docker run -d --name workday-mock -p 8080:8080 \
  -v ./tests/workday_mocks:/home/wiremock/mappings wiremock/wiremock:latest

Build stubs for at least: OAuth token endpoint, WD-IAM-001 (raas),
WD-IAM-002 (soap), WD-IAM-007 (rest), WD-CKM-002 (manual).
Add pytest tests in tests/test_workday_connect.py.
```

---

## Prompt 3: Live Salesforce assessment

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md.

Run a live assessment against the Salesforce org in .env:
  agent-loop run --env dev --org cyber-coach-dev --approve-critical

Verify:
- All 7 pipeline steps fire (finish() called at end)
- sscf_report.json overall_score vs baseline 48.4% RED
- nist_review.json produced and overall != "block"
- Both reports written (remediation_report.md + security_assessment.md + .docx)
```

---

## Prompt 4: Add ServiceNow as third platform

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md.

We want to add ServiceNow as a third supported platform, following the same
pattern as Salesforce (SBS) and Workday (WSCC):

1. Research ServiceNow security controls — what does a benchmark look like?
   (authentication, access control, data security, audit logging, etc.)
2. Create config/servicenow/servicenow_catalog.json (OSCAL 1.1.2)
   Target: 20-25 controls covering IAM, CON, LOG, DSP, TDR, GOV
3. Create config/servicenow/servicenow_to_sscf_mapping.yaml
4. Create skills/servicenow_connect/BLUEPRINT.md
   Auth: OAuth 2.0 Client Credentials (ServiceNow REST API)
5. schemas/baseline_assessment_schema.json already supports platform="servicenow"

Dry-run first; defer implementation to Phase F.
```

---

## Prompt 5: NIST AI RMF deep review on live outputs

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md.

Run nist-review against the latest cyber-coach-dev assessment:
  nist-review assess \
    --gap-analysis docs/oscal-salesforce-poc/generated/cyber-coach-dev/2026-03-04/gap_analysis.json \
    --backlog docs/oscal-salesforce-poc/generated/cyber-coach-dev/2026-03-04/backlog.json \
    --out /tmp/nist_review_live.json

Review verdict (GOVERN/MAP/MEASURE/MANAGE).
If overall=block, identify blocking_issues and what would need to remediate.
Compare to the dry-run stub (GOVERN=pass, MAP=partial, MEASURE=pass, MANAGE=partial).
```

---

## Prompt 6: Onboard a colleague

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md.

A new contributor is joining: GitHub username compliance-rehab (already in CODEOWNERS).
1. Verify they can: git clone → pip install -e . → pytest tests/ -v (12/12)
2. Walk through the wiki onboarding (docs/wiki/Onboarding.md)
3. Enable enforce_admins on main branch protection (currently bypassed)
4. Review docs/CONTRIBUTING.md — update if anything is outdated
```

---

## Prompt 7: Phase D — CCM regulatory table in report-gen

```
Continue work on saas-sec-agents. Read NEXT_SESSION.md.

Implement Phase D: add a CCM v4.1 regulatory crosswalk table to governance reports.

The sscf_to_ccm_mapping.yaml already maps SSCF controls → CCM controls with
regulatory_highlights (SOX, HIPAA, SOC2, ISO 27001, NIST 800-53, PCI DSS, GDPR).

The gap_map script (scripts/oscal_gap_map.py) needs to read this file and
populate ccm_controls in each sscf_mapping item of the backlog.

report-gen (skills/report_gen/report_gen.py) needs a new section in the
security audience report: "Regulatory Crosswalk" table showing:
  Control ID | SSCF Domain | CCM Control | SOX | HIPAA | SOC2 | ISO27001

Start with dry-run; validate against baseline_assessment_schema.json v2
(ccm_controls array is already in the schema spec).
```
