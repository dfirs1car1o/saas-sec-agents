# Next Session Prompts — saas-sec-agents

## Current State
- Repo: `https://github.com/dfirs1car1o/saas-sec-agents`
- Branch: `main` (Phase 3 PR #3 open, pending merge)
- Local path: `/Users/jerijuar/multiagent-azure`

## What Is Complete
- Phase 1: sfdc-connect CLI + full CI/CD security stack
- Phase 2: oscal-assess + sscf-benchmark CLIs (full pipeline)
- Phase 3: agent-loop harness + Mem0+Qdrant session memory (PR #3 open)
- Corporate data scrub: CDW → Acme Corp, BSS → SaaS Security Team, GIS → CorpIS
- CONTRIBUTING.md wiki: setup guide, Docker deps, env vars, pipeline, CI docs

## Open Items Before Phase 4
1. Set `ANTHROPIC_API_KEY` in `.env` and test `agent-loop run --dry-run`
2. Merge PR #3 once CI is green
3. Add colleague GitHub username to CODEOWNERS + flip `enforce_admins=true`

---

## Prompt 1: Phase 4 — report-gen DOCX Pipeline
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
Phase 3 is complete — PR #3 merged. Repo is dfirs1car1o/saas-sec-agents.
Build Phase 4: skills/report-gen/ — a DOCX + Markdown governance output generator.
Input: sscf_report.json + backlog.json
Output: app-owner DOCX, GIS Markdown summary, evidence package
Use docxtpl (already in deps) against a Word template in docs/templates/.
Wire it as a 5th tool call in harness/tools.py (tool name: report_gen_generate).
```

## Prompt 2: Live Org Assessment
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
Run a live assessment against the Salesforce org in .env.
Start Qdrant: docker run -d -p 6333:6333 qdrant/qdrant
Then: agent-loop run --env dev --org <alias>
Review the sscf_report.json output and compare to the dry-run weak-org baseline.
```

## Prompt 3: Colleague Onboarding
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
A new contributor needs onboarding. Review docs/CONTRIBUTING.md.
Add their GitHub username to CODEOWNERS and enable enforce_admins on branch protection.
Walk through: git clone → pip install -e . → docker run qdrant → pytest tests/ -v
```

## Prompt 4: NIST AI RMF Validation Pass
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION.md.
Run the nist-reviewer agent context against the latest sscf_report.json output.
Check that all AI-assisted findings include uncertainty flags and human-review gates.
Update any agent outputs that are missing NIST AI RMF MAP/MEASURE/MANAGE annotations.
```

## Last Known Pipeline Run Metrics (dry-run weak-org)
- controls/findings: 45
- status breakdown: ~18 fail, ~16 partial, ~11 not_applicable
- overall_score: ~0.34, overall_status: RED
- SSCF domains scored: 7
