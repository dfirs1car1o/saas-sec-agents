# Security Configuration Baseline
## Salesforce Event Monitoring and Transaction Security Policies (TSP)

**Organization:** Acme Corp  
**Version:** 1.0  
**Effective Date:** February 24, 2026  
**Owner:** SaaS Security Team (Corporate Information Security - Corporate Business)  
**Classification:** Internal Use Only

## 1. Executive Context
This document defines the minimum Salesforce security baseline for Event Monitoring and Transaction Security Policies (TSP) across Acme Corp US, Canada, and UK orgs.

Executive outcomes:
- Detect and contain high-risk access and data movement behavior quickly.
- Keep control settings consistent by control ID across regions.
- Surface drift and response status in dashboards for operational and governance decisions.

Operating model:
- Define expected control values by control ID.
- Continuously monitor control and event telemetry through enterprise pipelines.
- Detect and triage baseline drift.
- Report status through role-based dashboards.

## 2. SaaS Security Pillars (Primary Anchor)
This baseline is organized around SaaS security pillars, with CSA SSCF as the foundational control framework.

| SaaS Security Pillar | What It Means in This Baseline | CSA SSCF Alignment |
|---|---|---|
| Identity and Access Security | Detect and prevent unauthorized access, impersonation, privilege abuse | IAM, Access Control |
| Data Protection and Exfiltration Control | Detect/block risky exports, API extraction, and large file movement | Data Security, DLP |
| Threat Detection and Response | Real-time policies and alerting for suspicious behavior | Monitoring, Threat Detection and Response |
| Configuration and Change Governance | Detect risky admin/config changes and enforce change windows | Change/Configuration Management |
| Assurance, Auditability, and Compliance | Evidence-driven control operation and exception governance | Governance, Risk, Compliance, Auditability |

## 3. Governance and Roles
| Role | Responsibility |
|---|---|
| Salesforce Platform Owner | Approves configuration changes and operating readiness |
| Salesforce Administrator Team | Implements and maintains Event Monitoring and TSP settings |
| SaaS Security Team | Owns baseline requirements, risk acceptance, and exception approvals |
| Security Operations Monitoring Team | Monitors alerts, triages incidents, and drives remediation |
| Data Engineering | Maintains pipeline reliability and dashboard data quality |
| GRC and Audit | Validates evidence and compliance posture |

## 4. Event Monitoring Baseline
### 4.1 Platform Enablement Requirements
| Control / Setting | Required Value | Risk | Evidence |
|---|---|---|---|
| Salesforce Shield / Event Monitoring | Enabled in all production orgs | Critical | License + setup evidence |
| Event log retention | Minimum 30 days in platform; target 365 days in monitoring storage | High | Retention policy and storage evidence |
| Real-Time Event Monitoring | Enabled | High | RTEM policy inventory |
| SIEM/data forwarding | Enabled to central monitoring and control pipeline | Critical | Pipeline health and dashboard status |
| Event Monitoring Analytics | Enabled for security/admin workflows | Medium | Deployment evidence |

### 4.2 Required Event Types and Thresholds
| Event Type | Security Use Case | Priority | Baseline Threshold |
|---|---|---|---|
| LoginEvent | Credential abuse, brute force, impossible travel | Critical | 5 failed logins per 10 minutes per source |
| LoginAsEvent | Unauthorized impersonation | Critical | Any occurrence |
| ReportEvent | Mass data access | High | >5,000 rows/session |
| ReportExportEvent | Data exfiltration via export | Critical | Any export by non-approved role |
| ApiEvent | API abuse and scripted extraction | High | >10,000 records/session |
| PermissionSetEvent | Privilege escalation | Critical | Any privileged assignment |
| SetupAuditTrailEvent | Risky configuration change | High | Any change outside approved window |
| BulkApiResultEvent | Bulk extraction/upsert anomalies | High | >50,000 records |
| ContentDocumentLinkEvent | Sensitive file mass activity | Medium | >50 files/hour |
| SearchEvent | PII/sensitive record harvesting | Medium | >200 searches/hour |

## 5. Transaction Security Policy (TSP) Baseline
### 5.1 Required TSPs (Enabled in Production)
| Policy Name | Event Type | Action | Priority | Baseline Logic |
|---|---|---|---|---|
| Block Mass Report Export | ReportEvent | Block + Notify | Critical | rows_downloaded > 5000 and role not allowlisted |
| Block API Bulk Extract | ApiEvent | Block + Notify | Critical | queryRows > 10000 per session |
| Notify Privilege Escalation | PermissionSetEvent | Notify + Case | Critical | Any privileged set assignment |
| Block Untrusted Country Login | LoginEvent | Block + Notify | High | country not in approved geo list |
| Alert After-Hours Admin Change | SetupAuditTrailEvent | Notify + Case | High | admin change outside approved window |
| Block Unauthorized LoginAs | LoginAsEvent | Block + Notify | Critical | actor not in approved impersonator list |
| Alert High Anomaly Score | LoginAnomalyEvent | Notify | High | score >= 75 |

### 5.2 TSP Operational Requirements
| Control | Required Value |
|---|---|
| TSP state | Keep enabled in production; do not disable without approved exception |
| Critical policy action | Enforce block action (not notify-only) |
| Alert destination | Route to security monitoring channel and incident queue |
| Deployment process | Require sandbox test, peer review, and change approval |
| Log retention | Retain TSP execution and audit logs for at least 1 year |
| Exception window | Limit to 90 days maximum with compensating controls |

## 6. UK and Canada Regulatory Overlay
This section maps UK and Canada regulatory requirements into baseline operations.

| Jurisdiction | Regulatory Requirement | Baseline Implementation | Dashboard/KPI Evidence |
|---|---|---|---|
| UK | UK GDPR security principle + Article 32 (appropriate technical and organisational measures) | Mandatory monitoring for authentication, admin changes, privilege changes, and exfiltration events; blocking policies for high-risk actions | Control conformance score by UK org; critical drift aging |
| UK | UK restricted transfer obligations and safeguards where applicable | Monitor transfer-related access patterns and geo anomalies; enforce approved transfer paths | Geo-policy violation trend; transfer exception closure SLA |
| Canada (Federal) | PIPEDA safeguards/accountability principles | Control ownership, event visibility, and retention tied to accountable remediation | Control owner completeness; unresolved control drift by age |
| Canada (Federal) | PIPEDA breach reporting + recordkeeping expectations | Ensure logs and policy events are retained and queryable for incident determination and reporting workflows | Breach evidence completeness and response timeliness |
| Québec (where applicable) | Loi 25 transfer/privacy impact assessment expectations for data moving outside Québec | Policy gate for Québec-relevant transfer changes and documented impact assessment workflow | PIA completion status; Québec transfer exceptions and approvals |

## 7. Continuous Monitoring, Drift, and Dashboard Reporting
| Capability | Requirement |
|---|---|
| Baseline state model | Define expected control values by control ID and region (US/CAN/UK) |
| Drift detection | Detect non-compliant values, disabled controls, and missing telemetry |
| Severity model | Use Critical/High/Medium/Low with remediation SLA targets |
| Dashboard views | Provide executive summary, control owner, and regional compliance views |
| Reporting cadence | Run daily operational, weekly tactical, monthly governance, and quarterly formal reviews |

## 8. Operational Cadence
| Frequency | Activity | Owner |
|---|---|---|
| Daily | Verify ingestion freshness, drift detections, and alerting health | Security Operations Monitoring + Data Engineering |
| Weekly | Review dashboard metrics and tune thresholds | SaaS Security Team + Salesforce Admin |
| Monthly | Validate conformance and evidence package readiness | Salesforce Admin + GRC |
| Quarterly | Complete formal baseline review, including UK/CAN overlay | SaaS Security Team + GRC |
| Post-Incident | Perform gap analysis and baseline hardening updates | Incident stakeholders |

## 9. Minimum Evidence Artifacts
- Event Monitoring enablement evidence
- TSP enabled policy export
- Pipeline run history and freshness report
- Drift dashboard snapshots (severity, region, owner)
- Monthly/quarterly review records
- Exception approvals and closure evidence

## 10. References
- Salesforce Security Implementation Guide: https://help.salesforce.com/s/articleView?id=sf.security_impl_guide.htm&type=5
- Salesforce Event Monitoring and Real-Time Event Monitoring docs: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/event_monitoring.htm
- Salesforce Transaction Security docs: https://help.salesforce.com/s/articleView?id=sf.security_transaction_security.htm&type=5
- CSA SSCF overview: https://cloudsecurityalliance.org/artifacts/saas-security-controls-framework-sscf
- UK ICO, A guide to data security: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/security/a-guide-to-data-security/
- UK ICO, International transfers guidance: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/international-transfers/
- UK Data Protection Act 2018: https://www.legislation.gov.uk/ukpga/2018/12/contents
- OPC Canada, PIPEDA requirements in brief: https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda_brief/
- OPC Canada, PIPEDA Principle 7 Safeguards: https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/p_principle/principles/p_safeguards/
- OPC Canada, mandatory breach reporting guidance: https://www.priv.gc.ca/en/privacy-topics/business-privacy/breaches-and-safeguards/privacy-breaches-at-your-business/gd_pb_201810/
- Government of Canada, Breach of Security Safeguards Regulations (SOR/2018-64): https://gazette.gc.ca/rp-pr/p2/2018/2018-04-18/html/sor-dors64-eng.html
- Commission d’accès à l’information du Québec, Loi 25 key changes: https://www.cai.gouv.qc.ca/protection-renseignements-personnels/sujets-et-domaines-dinteret/principaux-changements-loi-25

## 11. Change Log
| Version | Date | Change Summary | Author |
|---|---|---|---|
| 1.0 | 2026-02-24 | Reframed around SaaS Security Pillars + CSA SSCF; added UK/CAN regulatory overlay and references; retained Event Monitoring + TSP baseline scope | Codex |
