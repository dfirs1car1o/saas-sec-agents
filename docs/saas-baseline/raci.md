# SaaS Risk Program RACI (Baseline Operations)

## Teams
- `CorpIS`: Corporate Information Security (corporate policy/standards owner)
- `BSS`: SaaS Security Team (program operations owner)
- `SECOPS`: Security Operations / Cyber Defense team
- `APP`: SaaS Application Owners (Salesforce/ServiceNow/Workday)
- `PLAT`: Platform Engineering / IAM / Cloud Platform
- `AUDIT`: Internal Audit / Compliance

## Responsibility Matrix

| Activity | CorpIS | BSS | SECOPS | APP | PLAT | AUDIT |
|---|---|---|---|---|---|---|
| Define policy and security standards | A | C | I | C | C | C |
| Maintain SSCF control mapping index | A | R | C | C | C | I |
| Author SaaS baseline controls | C | A/R | C | C | C | I |
| Run baseline assessments (read-only) | I | A/R | C | C | C | I |
| Validate technical evidence quality | I | R | C | C | C | I |
| Prioritize remediation backlog | C | A/R | C | R | C | I |
| Implement SaaS configuration remediations | I | C | I | A/R | C | I |
| Approve risk exceptions | A | R | C | C | C | C |
| Monitor drift and trigger re-assessments | I | A/R | R | C | C | I |
| Quarterly governance reporting | A | R | C | I | I | C |

## Decision Rights
- Baseline requirement changes: `CorpIS` final approval.
- Remediation execution timing: `BSS` + `APP` joint planning.
- Exception acceptance: `CorpIS` decision with documented risk owner sign-off.
