# Generated Salesforce Baseline Configuration

- Profile ID: `SF-BASELINE-EM-TSP-V1-GENERATED`
- Effective date: `2026-02-24`
- Program: `SaaS Risk Program`

## Scope
- Environments: salesforce-productionuction, salesforce-staging
- Clouds: Sales Cloud, Service Cloud, Experience Cloud

## Event Monitoring
- Retention target: 180 days
- SIEM: SIEM Platform
- Event types: login, logout, api, report_export, uri, setup_audit_trail, apex_execution

## Transaction Security Policies
- `SF-TSP-001` Block impossible travel login event (critical, action=block)
- `SF-TSP-002` Block suspicious report export behavior (critical, action=block)
- `SF-TSP-003` Challenge high-risk API session anomalies (high, action=notify)

## SSCF Controls
- SSCF-LOG-001, SSCF-LOG-002, SSCF-TDR-001, SSCF-IAM-001
