# Exception Record: UK Salesforce Partial Copy (Data Classification + Data Masking)

## Exception Metadata
- Exception ID: `UK-SF-PARTIALCOPY-EXC-2026-02-24`
- Platform: `Salesforce`
- Jurisdiction: `UK`
- Request Date: `2026-02-24`
- Effective Date: `2026-02-24`
- Expiration Date: `2026-04-25` (60 days, high-risk exception limit)
- Exception Owner: `Salesforce Platform Owner (UK)`
- Risk Owner: `Business Security Services`

## Scope (Strictly Limited)
- In scope:
  - Salesforce **partial copy** refreshes for UK team non-production environments.
  - Gaps related only to:
    1. Data classification completeness
    2. Data masking coverage/consistency
- Out of scope:
  - Any exception for identity/access controls, logging controls, or production data access controls.

## Control Gap Definition
1. **Data Classification Gap**
   - Not all copied data fields/objects are mapped to approved classification labels before refresh.
2. **Data Masking Gap**
   - Not all in-scope sensitive fields are consistently masked in non-production after partial copy.

## SSCF Mapping
- `SSCF-DSP-001` (Sensitive Data Access Control)
  - Mapping rationale: classification governs handling and access safeguards.
- `SSCF-DSP-002` (Data Export and Exfiltration Controls)
  - Mapping rationale: masking reduces non-production exposure and leakage impact.

## Risk Statement
Without full classification and masking controls, UK non-production refreshes may expose sensitive data classes to broader internal audiences than intended, increasing privacy and compliance risk. Business continuity requires continued refresh cadence for testing and delivery.

## Compensating Controls (Mandatory While Exception Is Active)
1. **Refresh Data Minimization Gate**
   - UK refresh requests must exclude known high-sensitivity objects/fields unless explicitly approved per refresh.
2. **High-Risk Field Exclusion List**
   - Enforce a deny-list for special category data and high-sensitivity identifiers from partial copy jobs.
3. **Restricted Non-Prod Access**
   - Non-production access limited to named UK delivery roles; no broad role inheritance.
4. **Enhanced Monitoring for Non-Prod Data Access**
   - Weekly review of access events and anomalous bulk/report extraction in UK non-production orgs.
5. **Short Data Retention for Refreshed Non-Prod Data**
   - Retain refreshed data only for defined test window; purge on schedule.
6. **No Downstream Export of Refreshed Data**
   - Prohibit export of refreshed non-production datasets to unmanaged tools/locations.
7. **Manual Masking Verification Sample**
   - Per refresh, verify masking outcomes on a control sample of in-scope sensitive fields.
8. **DPO/GRC Visibility**
   - Exception status and refresh activity included in monthly UK governance review.

## Operating Conditions
- Refreshes may continue only if all compensating controls are active.
- Any security incident involving non-production copied data triggers immediate exception review and potential suspension.
- Exception auto-expires on `2026-04-25` unless formally renewed.

## Remediation Plan and Milestones
1. By `2026-03-10`:
   - Finalize UK data classification inventory for all objects/fields included in partial copy.
2. By `2026-03-24`:
   - Implement masking rules for all high/critical classification fields in partial copy scope.
3. By `2026-04-10`:
   - Validate masking coverage and classification enforcement in two consecutive refresh cycles.
4. By `2026-04-25`:
   - Close exception if evidence confirms control implementation and sustained operation.

## Monitoring and Reporting
- Weekly: BSS + UK Salesforce owner review active refreshes, masking sample results, and anomalies.
- Monthly: GIS/GRC governance checkpoint with DPO visibility.
- T-14 days to expiry: automatic escalation to exception owner, GIS, and business sponsor.

## Approval
- Business Owner (UK Salesforce): `____________________`
- BSS Validation: `____________________`
- GIS Risk Authority Approval: `____________________`
- UK Privacy/DPO Acknowledgement: `____________________`
- Approval Date: `____________________`

## Closure Criteria
- Classification controls implemented and evidenced for all in-scope refresh data.
- Masking controls implemented and evidenced for all in-scope sensitive fields.
- Two consecutive compliant refresh cycles completed.
- Exception status set to `closed` and closure recorded in changelog/governance artifacts.

