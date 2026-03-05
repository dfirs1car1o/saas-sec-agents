# Workday Connect — Collector Blueprint

**Skill:** `workday_connect`
**Phase:** C (Blueprint / dry-run only)
**Status:** Blueprint complete — implementation deferred to Phase E
**Schema:** `schemas/baseline_assessment_schema.json` v2, `"platform": "workday"`

---

## Purpose

`workday_connect` is the data collector for Workday HCM/Finance tenant security assessments. It reads security configuration via Workday Web Services (WWS) SOAP API and pre-configured Reports-as-a-Service (RaaS) endpoints. It outputs a v2-schema-compliant assessment JSON that feeds into `oscal-assess` → `oscal_gap_map.py` → `sscf-benchmark` → `report-gen`.

The collector is **read-only**. It never modifies tenant configuration.

---

## Tenant Setup Requirements

### 1. Integration System User (ISU)

Create a dedicated ISU for the security collector:

| Field | Value |
|---|---|
| User Name | `svc_security_assessor@tenant` |
| Account Type | Integration System User |
| Disallow UI Sessions | **Enabled** (required) |
| Session Timeout | 60 minutes |

> WD-IAM-002 check: `Disallow UI Sessions` must be `true`. If the ISU used by the collector itself does not have this set, the collector raises a configuration warning in its own output.

### 2. Integration System Security Group (ISSG)

Create an ISSG and assign the ISU:

| Field | Value |
|---|---|
| Security Group Name | `SG_Security_Assessor` |
| Group Type | Integration System Security Group |
| Members | `svc_security_assessor` |

### 3. Required Domain Security Policy Permissions

Grant **Get** (read-only) on the following domain security policies. All grants are view-only. No Put/Modify permissions are required or permitted.

| Domain Security Policy | Used By Controls |
|---|---|
| Security Configuration | WD-IAM-001, WD-IAM-005, WD-IAM-006, WD-CON-001–006 |
| Integration System Security | WD-IAM-002, WD-IAM-008 |
| Maintain: Authentication Policies | WD-IAM-003, WD-CON-006 |
| Identity Provider | WD-IAM-004 |
| Workday Account | WD-IAM-007 |
| System Auditing | WD-LOG-001–005 |
| Security Logging | WD-LOG-001, WD-LOG-002 |
| Tenant Setup – Security | WD-CKM-001, WD-CKM-002 |
| Integration System User | WD-CKM-003 |
| Maintain: Business Process Security Policies | WD-IAM-006 |
| Manage: Business Process Definitions | WD-TDR-002 |
| Sensitive | WD-DSP-001, WD-DSP-004 |
| Worker Data: Workers | WD-DSP-001 |
| Security Groups | WD-IAM-005 |
| Maintain: Security Policies (Pending) | WD-GOV-001 |
| Set Up: Security | WD-GOV-002 |

### 4. RaaS Report Pre-Configuration (Optional)

Several controls are collected via pre-built Custom Reports configured as RaaS endpoints. If these reports are not pre-configured, the collector degrades gracefully (see Graceful Degradation section).

| Report Name (suggested) | Used By |
|---|---|
| `RPT_Inactive_Workday_Accounts` | WD-IAM-007 |
| `RPT_Failed_Signon_Events` | WD-LOG-003 |
| `RPT_Security_Config_Changes` | WD-GOV-002 |

---

## Authentication Methods

### Primary: SOAP WS-Security BasicAuth

Used for all WWS SOAP API calls (configuration reads, security group queries, system data).

```
WSDL base: https://{tenant}.workday.com/ccx/service/{tenant}/{service}/{version}
Auth:       WS-Security UsernameToken (BasicAuth over TLS)
TLS:        Required. TLS 1.2+ enforced on Workday side.
```

Environment variables:
```
WD_TENANT          — Workday tenant ID (e.g., acme_dpt1)
WD_USERNAME        — ISU username (e.g., svc_security_assessor@acme_dpt1)
WD_PASSWORD        — ISU password (never logged, never written to disk)
WD_API_VERSION     — WWS version, e.g. v40.0 (default: v40.0)
WD_BASE_URL        — optional override; defaults to https://{tenant}.workday.com
```

### Secondary: OAuth 2.0 (Client Credentials)

Used for REST API calls when a Workday REST API Client is registered. Not required for baseline collection — all 30 controls are accessible via SOAP or RaaS.

```
WD_OAUTH_CLIENT_ID
WD_OAUTH_CLIENT_SECRET
WD_OAUTH_TOKEN_URL
```

---

## Collection Method Taxonomy

Each control in `workday_catalog.json` declares its `collection-method` prop:

| Method | Meaning | Collector behavior |
|---|---|---|
| `soap` | Readable via WWS SOAP API | Call `soap_service` + `soap_operation`; parse response |
| `raas` | Readable via pre-configured RaaS endpoint | GET `{base_url}/ccx/service/customreport2/{tenant}/{report}?format=json` |
| `manual` | Requires manual questionnaire | Return `not_applicable` with `collection_method_note` |

---

## Per-Control Collection Reference

### IAM Controls

| Control | Method | WWS Service | Operation / Report | Key Fields |
|---|---|---|---|---|
| WD-IAM-001 | soap | Human_Resources | Get_Security_Groups | Domain assignments per group; check overprivilege |
| WD-IAM-002 | soap | Human_Resources | Get_Integration_System_Users | `Disallow_UI_Sessions` field |
| WD-IAM-003 | soap | Human_Resources | Get_Authentication_Policies | `Multi_Factor_Authentication_Required` |
| WD-IAM-004 | soap | Human_Resources | Get_Authentication_Policies | `Authentication_Policy_Type` = `SSO` |
| WD-IAM-005 | soap | Human_Resources | Get_Security_Groups | `Security_Group_Administrators`; verify non-empty |
| WD-IAM-006 | soap | Human_Resources | Get_Business_Process_Security_Policies | SOD separation per business process |
| WD-IAM-007 | raas | — | `RPT_Inactive_Workday_Accounts` | Accounts with last login > 90 days |
| WD-IAM-008 | soap | Human_Resources | Get_API_Client_Scopes | OAuth client `Scope` list; flag overpermissive |

### Configuration Hardening Controls

| Control | Method | WWS Service | Operation | Key Fields |
|---|---|---|---|---|
| WD-CON-001 | soap | Human_Resources | Get_Password_Rules | `Minimum_Password_Length`, `Complexity_Requirements` |
| WD-CON-002 | soap | Human_Resources | Get_Password_Rules | `Password_Expiration_Days`, `Password_History_Count` |
| WD-CON-003 | soap | Human_Resources | Get_Session_Timeout_Settings | `Session_Timeout_Minutes` |
| WD-CON-004 | soap | Human_Resources | Get_Account_Lockout_Settings | `Lockout_Threshold`, `Lockout_Duration_Minutes` |
| WD-CON-005 | soap | Human_Resources | Get_IP_Range_Settings | `Allowed_IP_Ranges` list; empty = no restriction |
| WD-CON-006 | soap | Human_Resources | Get_Authentication_Policies | Coverage: count policies, verify `Apply_To_All_Users` |

### Logging and Monitoring Controls

| Control | Method | WWS Service | Operation / Report | Key Fields |
|---|---|---|---|---|
| WD-LOG-001 | soap | Human_Resources | Get_Workday_Account | `User_Activity_Logging_Enabled` |
| WD-LOG-002 | soap | Human_Resources | Get_SignOn_Events | Query last 30d sign-on audit data; verify accessible |
| WD-LOG-003 | raas | — | `RPT_Failed_Signon_Events` | Count failed events by user in last 30d |
| WD-LOG-004 | soap | Human_Resources | Get_Audit_Logs | Administrative action log availability check |
| WD-LOG-005 | soap | Human_Resources | Get_Audit_Retention_Settings | `Audit_Log_Retention_Days`; pass if >= 365 |

### Cryptography and Key Management Controls

| Control | Method | WWS Service | Operation | Key Fields |
|---|---|---|---|---|
| WD-CKM-001 | soap | Human_Resources | Get_Tenant_Setup_Security | `Require_TLS_For_API`, `WS_Security_Required` |
| WD-CKM-002 | manual | — | — | BYOK requires manual tenant admin confirmation |
| WD-CKM-003 | soap | Human_Resources | Get_Integration_System_Users | ISU `Password_Last_Changed_Date`; flag if > 365d |

### Data Security and Privacy Controls

| Control | Method | WWS Service | Operation | Key Fields |
|---|---|---|---|---|
| WD-DSP-001 | soap | Human_Resources | Get_Security_Groups | Sensitive domain (Compensation, SSN, Benefits) members |
| WD-DSP-002 | soap | Human_Resources | Get_Workday_Account | `Allow_Data_Export`, export permission flags |
| WD-DSP-003 | soap | Human_Resources | Get_API_Client_Scopes | Integration scope breadth; flag if `All_Workday_Data` |
| WD-DSP-004 | soap | Human_Resources | Get_Security_Groups | PII field access domains; group membership count |

### Threat Detection and Response Controls

| Control | Method | WWS Service | Operation | Key Fields |
|---|---|---|---|---|
| WD-TDR-001 | soap | Human_Resources | Get_Authentication_Policies | `Failed_Login_Alert_Threshold`, alert routing configured |
| WD-TDR-002 | soap | Human_Resources | Get_Business_Process_Definitions | Approval step count per process; flag single-approver |

### Governance and Compliance Controls

| Control | Method | WWS Service | Operation / Report | Key Fields |
|---|---|---|---|---|
| WD-GOV-001 | soap | Human_Resources | Get_Security_Policies | `Pending_Security_Policies` list; pass if empty |
| WD-GOV-002 | raas | — | `RPT_Security_Config_Changes` | Changes in last 90d with approver; flag no-approver |

---

## Graceful Degradation

### RaaS Not Pre-Configured

When a required RaaS report returns 404 or is inaccessible:

```json
{
  "control_id": "WD-IAM-007",
  "status": "not_applicable",
  "severity": "moderate",
  "evidence_source": "RaaS GET RPT_Inactive_Workday_Accounts",
  "observed_value": null,
  "remediation": "Pre-configure the RaaS report RPT_Inactive_Workday_Accounts and rerun the collector.",
  "platform_data": {
    "collection_method": "raas",
    "collection_method_note": "RaaS report not pre-configured. Control requires manual review.",
    "raas_available": false
  },
  "sscf_mappings": [...]
}
```

### Manual Controls

Controls with `collection_method: manual` always return `not_applicable` with an explanatory note. They are included in the output for completeness but excluded from automated pass/fail scoring:

```json
{
  "control_id": "WD-CKM-002",
  "status": "not_applicable",
  "evidence_source": "manual questionnaire required",
  "platform_data": {
    "collection_method": "manual",
    "collection_method_note": "BYOK configuration requires confirmation from Workday tenant administrator via manual questionnaire."
  }
}
```

### SOAP API Permission Denied

When the ISU lacks domain permission for a SOAP call, log the denial and return partial:

```json
{
  "control_id": "WD-DSP-001",
  "status": "partial",
  "evidence_source": "Get_Security_Groups — SOAP (permission denied)",
  "platform_data": {
    "collection_method": "soap",
    "soap_error": "PERMISSION_DENIED: Sensitive domain not granted to ISSG SG_Security_Assessor"
  }
}
```

---

## Dry-Run Mode

`--dry-run` prints the collection plan without making any API calls:

```
$ python3 skills/workday_connect/workday_connect.py --dry-run

DRY-RUN: Workday Connect Collection Plan
Tenant:  acme_dpt1
Auth:    SOAP WS-Security BasicAuth
Controls in scope: 30 (27 soap/raas, 1 manual, 2 raas-dependent)

  WD-IAM-001  soap   Get_Security_Groups                   ✓ in scope
  WD-IAM-002  soap   Get_Integration_System_Users          ✓ in scope
  WD-IAM-003  soap   Get_Authentication_Policies           ✓ in scope
  WD-IAM-004  soap   Get_Authentication_Policies           ✓ in scope
  WD-IAM-005  soap   Get_Security_Groups                   ✓ in scope
  WD-IAM-006  soap   Get_Business_Process_Security_Policies ✓ in scope
  WD-IAM-007  raas   RPT_Inactive_Workday_Accounts         * raas-dependent
  WD-IAM-008  soap   Get_API_Client_Scopes                 ✓ in scope
  ...
  WD-CKM-002  manual (questionnaire)                        - not_applicable
  ...

Would write: docs/oscal-salesforce-poc/generated/workday_raw.json
```

---

## Output Format

The collector writes a `baseline_assessment_schema.json` v2 compliant file:

```json
{
  "schema_version": "2.0",
  "assessment_id": "wd-assess-20260307-001",
  "platform": "workday",
  "oscal_catalog_ref": "config/workday/workday_catalog.json",
  "assessment_time_utc": "2026-03-07T12:00:00Z",
  "environment": "prod",
  "assessor": "workday-connect v0.1.0",
  "assessment_owner": "Jane Smith",
  "data_source": "workday-connect SOAP WWS v40.0 + RaaS",
  "ai_generated_findings_notice": "Findings produced by automated collector workday-connect. Requires human review before use in audit evidence.",
  "assessment_scope": {
    "controls_in_scope": 30,
    "controls_excluded": 1,
    "exclusion_reasons": ["WD-CKM-002 requires manual BYOK confirmation"]
  },
  "findings": [...]
}
```

Output file: `docs/oscal-salesforce-poc/generated/workday_raw.json`

---

## Pipeline Integration

```
workday_connect → oscal-assess → oscal_gap_map.py → sscf-benchmark → nist-review → report-gen
     ↓
workday_raw.json
```

The gap map step reads `workday_to_sscf_mapping.yaml` to enrich each finding with SSCF domain scores and CCM regulatory references. No changes to downstream pipeline are required — platform field is set to `"workday"` and the schema is v2 compliant.

---

## Implementation Notes (Phase E)

When implementing `workday_connect.py`:

1. Use `zeep` (Python SOAP library) for WWS calls. Do not hand-roll SOAP XML.
2. Parse the OSCAL catalog (`workday_catalog.json`) to drive the collection loop — do not hardcode control IDs.
3. Read `collection-method`, `soap-service`, `soap-operation`, `raas-report` props from each OSCAL control.
4. Validate output against `schemas/baseline_assessment_schema.json` before writing.
5. Honor `--dry-run` flag by short-circuiting before any network call.
6. Never log `WD_PASSWORD` or `WD_OAUTH_CLIENT_SECRET`.

Key pip dependencies:
```
zeep          # SOAP client
pyyaml        # mapping file parsing
jsonschema    # output validation
requests      # RaaS HTTP GET
python-dotenv # env loading
```
