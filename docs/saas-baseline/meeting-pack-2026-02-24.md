# Meeting Pack: SaaS Baseline Configuration (2026-02-24)

## Objective
Establish a business-approved SaaS Security Configuration Baseline Program aligned to CSA SSCF, starting with Salesforce Event Monitoring and Transaction Security Policies, then extending to ServiceNow and Workday.

## Program Context
- Program: SaaS Risk Program (new)
- Function: SaaS Security Team under Corporate Information Security
- Driver: gap remediation identified security control deficiencies
- Goal: standardize policy -> baseline -> operational enforcement -> evidence

## What Is Already Ready (Repo Artifacts)
- Control framework and mapping method:
  - `docs/saas-baseline/sscf-mapping-method.md`
  - `config/sscf_control_index.yaml`
- Platform baseline catalogs:
  - `config/saas_baseline_controls/salesforce.yaml`
  - `config/saas_baseline_controls/servicenow.yaml`
  - `config/saas_baseline_controls/workday.yaml`
- Governance:
  - `docs/saas-baseline/raci.md`
  - `docs/saas-baseline/exception-process.md`
  - `docs/saas-baseline/quarterly-report-template.md`
  - `docs/saas-baseline/intake-template.md`
- Assessment schema:
  - `schemas/baseline_assessment_schema.json`

## Business SaaS Config Baseline (v1 Draft)

### 1) Salesforce (Priority 1)
#### Event Monitoring Baseline
- Enable required event streams for:
  - login/authentication events
  - API usage events
  - report/data export events
  - setup/admin change events
- Ensure retention and SIEM export path are defined.
- Enforce evidence integrity (case linkage + timestamp + source ref).

#### Transaction Security Policy Baseline
- Mandatory policy use cases:
  - suspicious login behavior
  - impossible travel/geolocation anomalies
  - high-risk API behavior
  - mass report/data export attempts
  - privileged admin behavior anomalies
- Approved actions by severity:
  - Critical: block + immediate Security Operations alert
  - High: challenge/block + security team review
  - Medium: allow + alert + watchlist

### 2) ServiceNow (Priority 2)
- Privileged role governance and recertification
- Admin/configuration audit logging enabled
- Integration token scope + rotation controls
- Security hardening score tracked and remediated

### 3) Workday (Priority 3)
- SSO/MFA and break-glass governance
- Audit stream enabled and retained
- Sensitive data access/export controls
- Integration and role assignment oversight

## Decision Requests for Meeting
1. Confirm baseline scope sequence:
   - Phase A: Salesforce only
   - Phase B: ServiceNow + Workday
2. Confirm policy authority:
   - CorpIS approves control requirements
   - SST runs assurance operations
3. Confirm exception SLAs:
   - Critical 30 days, High 60 days, Medium/Low 90 days
4. Confirm reporting cadence:
   - monthly operational report
   - quarterly governance report

## 30-60-90 Plan (Business View)
- 30 days:
  - finalize baseline requirements and owners
  - run read-only Salesforce assessment
- 60 days:
  - remediate Critical/High Salesforce findings
  - onboard ServiceNow baseline assessment
- 90 days:
  - onboard Workday baseline assessment
  - produce first cross-platform quarterly report

## Risks to Call Out
- Control IDs are provisional and require enterprise naming ratification.
- Platform API access and evidence connectors still need implementation.
- Production enforcement must wait for exception governance sign-off.

## Ask for Approval
Approve this v1 baseline direction so implementation can start with Salesforce Event Monitoring + Transaction Security policy controls.
