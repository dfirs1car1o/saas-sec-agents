# Session Handoff (2026-02-24)

## Context Health
- Conversation context was nearing limit; critical state was persisted to repo files.

## Where To Resume
- `NEXT_SESSION_PROMPTS.md` (repo root) is the canonical restart entry.

## OSCAL POC Status
- End-to-end smoke test is functional (with venv + PyYAML + network access).
- Current generated outputs are collector-style mock results (45 controls mapped).
- SBS is mapped to CSA SSCF in pipeline outputs.
- `oscal_gap_map.py` supports direct `SBS-*` control IDs from collector-style findings.

## Important Files
- `docs/oscal-salesforce-poc/README.md`
- `docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog.json`
- `docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix.md`
- `config/oscal-salesforce/sbs_to_sscf_mapping.yaml`
- `docs/reviews/2026-02-24-brutal-critic-backlog.md`

## Pending Decision
- Decision resolved: security workflow is now strict.
  - tfsec runs with `--minimum-severity HIGH`.
  - checkov `hard_fail_on: HIGH,CRITICAL` and `soft_fail_on: LOW,MEDIUM`.
  - Change pushed in commit `d5f3aa7`.
- No pending unstaged workflow edits remain.
