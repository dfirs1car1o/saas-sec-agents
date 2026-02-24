# Next Session Prompts (Current Restart Pack)

## Current State Snapshot
- Repo: `/Users/jerijuar/multiagent-azure`
- Branch: `main`
- Remote: `git@github.com-443:SiCar10mw/multiagent-azure.git`
- Git state: `main...origin/main` (fully synced).
- Primary workstream: `OSCAL POC for Salesforce` with SBS + CSA SSCF mapping.
- GitHub CLI auth: restored and working for `gh run` commands.

## What Is Completed
- Salesforce baseline v1.0 deliverable updated (MD + DOCX).
- OSCAL scaffold implemented:
  - `config/oscal-salesforce/*`
  - `scripts/oscal_import_sbs.py`
  - `scripts/oscal_gap_map.py`
  - `scripts/oscal_smoke_test.sh`
  - `docs/oscal-salesforce-poc/*`
- Collector-style mock run generated and committed:
  - mock input: `docs/oscal-salesforce-poc/examples/gap-analysis-salesforce-collector-mock.json`
  - `docs/oscal-salesforce-poc/generated/sbs_controls.json`
  - `docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog.json`
  - `docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix.md`
- Brutal-critic remediation backlog created:
  - `docs/reviews/2026-02-24-brutal-critic-backlog.md`
- Security checks are now strict:
  - tfsec fails on `HIGH+` findings.
  - checkov hard-fails on `HIGH,CRITICAL`; soft-fails on `LOW,MEDIUM`.

## Prompt 1: Resume Exactly Where We Left Off
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION_PROMPTS.md.
First, confirm current GitHub Actions security-checks behavior after commit d5f3aa7:
- tfsec minimum severity HIGH
- checkov hard_fail_on HIGH,CRITICAL
Then check for any HIGH/CRITICAL findings and propose remediation PRs.
```

## Prompt 2: Run OSCAL Pipeline with Real Gap Data
```text
Use the OSCAL pipeline in /Users/jerijuar/multiagent-azure with my real Salesforce gap-analysis JSON.
Run oscal_gap_map.py against real input and regenerate:
- docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog.json
- docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix.md
Keep SBS to CSA SSCF mapping enabled.
```

## Prompt 3: Start Sandbox Collector Implementation
```text
Implement the first read-only Salesforce collector stub that emits schema-compatible findings.
Start with Authentication/Access controls and output findings to baseline_assessment_schema.json shape.
Save under scripts/ and docs/oscal-salesforce-poc/.
```

## Prompt 4: Work Through Brutal-Critic Backlog
```text
Use docs/reviews/2026-02-24-brutal-critic-backlog.md as the source of truth.
Start with BC-001, BC-002, BC-003 in order, with minimal safe increments and verification after each.
```

## First Commands To Run Next Session
```bash
git -C /Users/jerijuar/multiagent-azure status -sb
git -C /Users/jerijuar/multiagent-azure log --oneline -n 8
cd /Users/jerijuar/multiagent-azure && unset GITHUB_TOKEN; gh run list --workflow security-checks.yml --limit 8
```
