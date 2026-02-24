# Next Session Prompts (Codex Restart Pack)

## Current State Snapshot
- Repo: `/Users/jerijuar/multiagent-azure`
- Branch: `main`
- Remote: `git@github.com-443:SiCar10mw/multiagent-azure.git`
- Git state: `main...origin/main [ahead 2]`
- Unpushed commits:
  - `b62f084` Add Salesforce Event Monitoring/TSP baseline deliverable docx
  - `88c146d` Refine Salesforce baseline with SaaS pillars, CSA SSCF, and UK/CAN overlay
- Network blocker: local DNS cannot resolve `github.com` / `ssh.github.com`

## Key Deliverable Files
- `/Users/jerijuar/Downloads/CDW_Salesforce_EventMonitoring_TSP_Baseline_v1.0.docx`
- `/Users/jerijuar/multiagent-azure/docs/saas-baseline/deliverables/CDW_Salesforce_EventMonitoring_TSP_Baseline_v1.0.docx`
- `/Users/jerijuar/multiagent-azure/docs/saas-baseline/deliverables/CDW_Salesforce_EventMonitoring_TSP_Baseline_v1.0.md`

## Prompt 1: Resume + Recovery (Use First)
```text
Resume from /Users/jerijuar/multiagent-azure/NEXT_SESSION_PROMPTS.md.
First, diagnose and fix local DNS/network so github.com resolves, then push the 2 pending commits on main.
After push succeeds, verify remote includes commits b62f084 and 88c146d.
Do not change document names. Keep v1.0 naming.
```

## Prompt 2: Continue Baseline Improvement
```text
Continue refining the Salesforce Event Monitoring + TSP baseline deliverable in docs/saas-baseline/deliverables.
Keep SaaS Security Pillars and CSA SSCF as primary anchors.
Keep UK and Canada regulatory overlay with references.
Improve executive readability only (headings, concise tables, action-oriented wording), no scope creep.
```

## Prompt 3: Meeting-Ready Pack
```text
Create a concise meeting pack from the current baseline:
1) one-page executive summary,
2) control matrix table (control ID, owner, drift KPI, SLA),
3) implementation next-30-days plan.
Save under docs/saas-baseline/meeting-pack and keep repo-private wording.
```

## Prompt 4: If Push Still Fails
```text
Push is failing because github hostname resolution is broken.
Use a step-by-step DNS triage and provide exact terminal commands for my active network interface.
Then re-test ssh to git@github.com-443 and push.
```

## First Commands To Run Next Session
```bash
git -C /Users/jerijuar/multiagent-azure status -sb
git -C /Users/jerijuar/multiagent-azure log --oneline -n 5
git -C /Users/jerijuar/multiagent-azure remote -v
ping -c 1 github.com || true
ssh -T git@github.com-443 || true
```
