# Next Session Prompts — saas-sec-agents

## Current State
- Repo: `https://github.com/dfirs1car1o/saas-sec-agents`
- Branch: `main` (all phases + fixes merged, CI green)
- Local path: `/Users/jerijuar/saas-sec-agents`
- Pipeline: 7 steps, verified working end-to-end in dry-run
- Last dry run: ~35% RED, 4 critical fails, 7 tool calls, nist_review.json + PDF/DOCX generated

---

## Prompt 1: Review dry-run PDF and DOCX output

```text
Resume from /Users/jerijuar/saas-sec-agents/NEXT_SESSION.md.

Run the full dry run and show me the PDF and DOCX output for review:

  cd /Users/jerijuar/saas-sec-agents
  agent-loop run --dry-run --env dev --org test-org

The generated files will be in:
  docs/oscal-salesforce-poc/generated/test-org/<today's date>/
    test-org_security_assessment.pdf
    test-org_security_assessment.docx
    test-org_remediation_report.md

Read and display the PDF so I can review the formatting.
Report any issues with: NIST AI RMF section wrapping, SSCF heatmap N/A rows,
Top Findings table, SBS ID column widths, status colour coding.
```

---

## Prompt 2: Live Salesforce org assessment

```text
Resume from /Users/jerijuar/saas-sec-agents/NEXT_SESSION.md.

Dry run verified. Run a live assessment against the Salesforce sandbox in .env.
Make sure SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN, SF_DOMAIN=test are set.

  agent-loop run --env test --org <alias>

Review sscf_report.json overall_score vs dry-run baseline (~35% RED).
Check that all 7 pipeline steps fired and nist_review.json was produced.
Open the generated PDF for review.
```

---

## Prompt 3: Colleague onboarding

```text
Resume from /Users/jerijuar/saas-sec-agents/NEXT_SESSION.md.

A new contributor is joining. Their GitHub username is: <username>
1. Add them to .github/CODEOWNERS
2. Enable enforce_admins on the main branch protection rule
3. Walk through the onboarding steps in docs/CONTRIBUTING.md
4. Verify they can run: git clone → pip install -e . → pytest tests/ -v → dry run
```

---

## Prompt 4: NIST AI RMF deep review

```text
Resume from /Users/jerijuar/saas-sec-agents/NEXT_SESSION.md.

Run a live NIST AI RMF review (not dry-run) against the latest assessment outputs:

  nist-review assess \
    --gap-analysis docs/oscal-salesforce-poc/generated/test-org/<date>/gap_analysis.json \
    --backlog docs/oscal-salesforce-poc/generated/test-org/<date>/backlog.json \
    --out /tmp/nist_review_live.json

Review the verdict (GOVERN/MAP/MEASURE/MANAGE) and compare to the dry-run stub.
If overall=block, identify blocking_issues and remediate before live org delivery.
```

---

## Known Bash Tool Issue (new session fixes this)

The Bash tool in the previous session was stuck on the old working directory
`/Users/jerijuar/multiagent-azure` (folder was renamed to `/Users/jerijuar/saas-sec-agents`).
**Starting a new Claude Code session in `/Users/jerijuar/saas-sec-agents` fixes this.**
