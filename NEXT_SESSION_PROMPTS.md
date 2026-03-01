# Next Session Prompts — saas-sec-agents

## Current State
- Repo: `https://github.com/dfirs1car1o/saas-sec-agents`
- Branch: `main` (all 5 phases merged)
- Local path: `/Users/jerijuar/multiagent-azure`

## What Is Complete
- Phase 1: sfdc-connect CLI + full CI/CD security stack (PR #1)
- Phase 2: oscal-assess + sscf-benchmark CLIs — full assessment pipeline (PR #2)
- Phase 3: agent-loop harness + Mem0+Qdrant session memory (PR #3)
- Phase 4: report-gen DOCX/MD governance skill (PR #4)
- Phase 5: auto-regenerating architecture diagram + PR template (PR #5)
- Corporate data scrub: CDW → Acme Corp, BSS → SaaS Security Team, GIS → CorpIS
- All agent prompts current: orchestrator routing table + reporter CLI examples updated

## One Thing Needed Before Dry Run
Set `ANTHROPIC_API_KEY` in `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```
Create at: https://console.anthropic.com/settings/keys

---

## Prompt 1: First Dry Run
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
All 5 phases are complete and merged to main.
Run the first end-to-end dry run:

  agent-loop run --dry-run --env dev --org test-org

Expected pipeline: sfdc_connect_collect → oscal_assess_assess → oscal_gap_map
  → sscf_benchmark_benchmark → report_gen_generate (app-owner + gis)

Review all output files in docs/oscal-salesforce-poc/generated/test-org/<date>/
and the deliverables in docs/oscal-salesforce-poc/deliverables/.
If anything fails, diagnose and fix before moving to a live org.
```

## Prompt 2: Live Org Assessment
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
Dry run has passed. Run a live assessment against the Salesforce org in .env.

Start Qdrant for session memory:
  docker run -d -p 6333:6333 qdrant/qdrant

Then:
  agent-loop run --env prod --org <alias>

Review sscf_report.json and compare overall_score to the dry-run baseline (~0.34, RED).
Generate deliverables for both audiences using report_gen_generate.
```

## Prompt 3: NIST AI RMF Validation Pass
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
Run the nist-reviewer context against the latest sscf_report.json and backlog.json.
Check that all AI-assisted findings include uncertainty flags and human-review gates.
Update any findings missing NIST AI RMF GOVERN/MAP/MEASURE/MANAGE annotations.
Then regenerate the CorpIS governance report with the nist-review JSON as input:
  report-gen generate --backlog ... --audience gis --nist-review nist_review.json --out ...
```

## Prompt 4: Colleague Onboarding
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
A new contributor is joining. Review docs/CONTRIBUTING.md.
Add their GitHub username to .github/CODEOWNERS and enable enforce_admins on branch protection.
Walk through: git clone → pip install -e . → docker run qdrant → pytest tests/ -v → dry run.
```

## Last Known Pipeline Run Metrics (dry-run weak-org, Phase 2)
- Controls assessed: 45
- Pass: ~24, Fail: ~9, Partial: ~12, Not Applicable: ~0
- SSCF overall_score: ~0.34 → overall_status: RED
- SSCF domains scored: 7
- Dry-run deliverables: docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog_latest.json
