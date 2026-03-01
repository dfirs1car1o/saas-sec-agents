# Salesforce Security Baseline v1
## Event Monitoring + Transaction Security Policies

## 1. Purpose
Define the first production-ready Salesforce security baseline for Acme Corp's SaaS Risk Program, aligned to CSA SSCF and CorpIS governance.

## 2. Scope
- Platform: Salesforce
- Focus: Event Monitoring and Transaction Security Policies
- Environments: Production first, then lower environments for validation and drift checks

## 3. Baseline Control Objectives
1. Ensure high-fidelity audit/event telemetry is continuously captured and exported.
2. Enforce policy-based prevention or alerting for high-risk user and API behavior.
3. Provide audit-grade evidence mapped to SSCF controls.

## 4. Configuration Baseline

### 4.1 Event Monitoring
- Event Monitoring must be enabled.
- Minimum retention target: 180 days.
- Required event classes:
  - Login/Logout events
  - API events
  - Report export/data movement events
  - URI and application request events
  - Setup/admin change events
- SIEM export must run continuously with maximum 15-minute latency.

### 4.2 Transaction Security Policies
Required policy set:
1. Impossible travel login policy (Critical, Block)
2. Suspicious data export policy (Critical, Block)
3. API behavior anomaly policy (High, Notify/Challenge)
4. Privileged admin risky-action policy (High, Notify)

Implementation rules:
- Critical blocking policies require CorpIS approval.
- All policies run in monitor mode before block mode in production.
- Exceptions must follow `docs/saas-baseline/exception-process.md`.

## 5. SSCF Mapping
Primary mappings:
- `SSCF-LOG-001` Security Telemetry Enablement
- `SSCF-LOG-002` Administrative and Configuration Audit Logging
- `SSCF-TDR-001` Real-Time Threat Policy Enforcement
- `SSCF-IAM-001` Multi-Factor Authentication Enforcement
- `SSCF-DSP-002` Data Export and Exfiltration Controls
- `SSCF-CKM-001` API Credential and Token Lifecycle

## 6. Operating Requirements
- Owner: SaaS Security Team
- Approver: Corporate Information Security
- Execution support: Salesforce platform owners and Security Operations
- Monthly assessment cadence with schema output:
  - `schemas/baseline_assessment_schema.json`

## 7. Release Validation (RV)
1. Event Monitoring data present for all required event classes.
2. SIEM receives events with expected fields and timestamps.
3. Transaction Security policies tested with approved simulation scenarios.
4. Critical policy actions verified in non-production before prod enablement.
5. Rollback path tested (policy disable/revert + evidence confirmation).

## 8. Backout
- Immediately switch blocking policies to alert-only where operational instability is observed.
- Revert to prior approved policy version.
- Document rollback in changelog and quarterly report.

## 9. Source of Truth
- Machine-readable baseline profile:
  - `config/saas_baseline_profiles/salesforce_em_tsp_baseline_v1.yaml`

