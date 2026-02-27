# Next Session Prompts — saas-sec-agents

## Current State
- Repo: `https://github.com/SiCar10mw/saas-sec-agents`
- Branch: `main`
- Local path: `/Users/jerijuar/multiagent-azure`

## What Is Complete
- Phase 1: OpenClaw agent framework, sfdc-connect CLI, CI/CD security stack
- Architecture blueprint: `docs/architecture-blueprint.md`
- Pre-flight validation script: `scripts/validate_env.py`
- All Azure/DFIR/Terraform content removed
- Security CI: bandit, pip-audit, gitleaks, CodeQL, dependency-review, ruff
- CodeRabbit: `.coderabbit.yaml` (activate at https://coderabbit.ai)
- Dependabot: weekly pip + Actions updates

## Prompt 1: Phase 2 — OSCAL Assessment Pipeline
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
Phase 1 is complete. Repo is SiCar10mw/saas-sec-agents.
Build Phase 2: skills/oscal_assess/oscal_assess.py and skills/sscf_benchmark/sscf_benchmark.py
wrapping the existing scripts/oscal_gap_map.py. End-to-end: sfdc-connect → oscal-assess → backlog.json.
```

## Prompt 2: OSCAL With Real Business Unit Gap File
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION_PROMPTS.md.
Use the OSCAL pipeline with my real Salesforce gap-analysis JSON and regenerate:
- docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog_latest.json
- docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix_latest.md
Then refresh the business-unit deliverable DOCX with run-specific metrics and top remediation priorities.
```

## Prompt 3: GitHub Org Setup
```text
My GitHub org is SiCar10mw. I need to:
1. Enable 2FA requirement for all members (requires admin:org scope — do manually in GitHub org settings)
2. Set Actions permissions to read-only
3. Add my colleague's GitHub username to CODEOWNERS and flip enforce_admins=true on branch protection
4. Activate CodeRabbit at https://coderabbit.ai (requires manual GitHub App install)
```

## Last Known OSCAL Run Metrics
- controls/findings: 45
- mapped: 45 / unmapped: 0 / invalid: 0
- status: 24 pass / 12 partial / 9 fail
