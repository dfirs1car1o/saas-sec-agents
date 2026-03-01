# SaaS Baseline Exception Process

Use this process when a baseline control cannot be implemented on schedule or is not technically feasible.

## Exception Eligibility
- Business constraint blocks immediate remediation.
- Platform limitation prevents direct implementation.
- Compensating controls can reduce risk to acceptable level.

## Required Exception Record
1. Control ID and platform
2. SSCF mapping (`domain`, `control_id`)
3. Risk statement and impact
4. Compensating controls
5. Exception owner
6. Expiration date (mandatory)
7. Remediation target date and milestones
8. Approver(s): CorpIS risk authority

## Approval Workflow
1. Submit exception request with evidence.
2. BSS validates technical details and compensating controls.
3. CorpIS reviews risk impact and approves/rejects.
4. If approved, exception is time-bound and tracked.

## SLA and Expiry Rules
- Critical control exceptions: max 30 days
- High control exceptions: max 60 days
- Medium/Low exceptions: max 90 days
- Expired exceptions auto-escalate to CorpIS and platform owner

## Monitoring
- Weekly exception review by BSS
- Monthly risk review with CorpIS governance
- Automatic alerts for exceptions nearing expiry (T-14 days)

## Closure Criteria
- Control remediated and validated
- Evidence attached
- Exception status set to closed
- Change recorded in `CHANGELOG.md`

