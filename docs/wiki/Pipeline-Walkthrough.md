# Pipeline Walkthrough

This page walks through every stage of the assessment pipeline end-to-end, including what each tool does, what it produces, and how the orchestrator connects them.

---

## Stage 0: Pre-flight

Before the pipeline runs, validate your environment:

```bash
python3 scripts/validate_env.py
```

This checks:
- Python ≥ 3.11
- Required Python packages installed
- `.env` file exists with required keys
- Repo layout is correct (mission.md, AGENTS.md, schemas/, etc.)
- Qdrant backend configured (QDRANT_IN_MEMORY=1 or QDRANT_HOST set)

---

## Stage 1: Salesforce Collection (`sfdc-connect`)

**What it does:** Connects to the Salesforce org and snapshots security-relevant configuration.

**Config collected:**
| Salesforce API | What it captures |
|---|---|
| `SecuritySettings` (Tooling API) | Session timeout, IP allowlisting, MFA enforcement, certificate-based auth |
| `AuthProvider` (REST API) | OAuth providers, SSO configurations |
| `PermissionSet` + `Profile` | Admin-equivalent profiles, dangerous permission grants |
| `NetworkAccess` | Trusted IP ranges |
| `ConnectedApp` | OAuth clients, refresh token policy, scopes |

**Command:**
```bash
sfdc-connect collect --scope all --org my-org --out sfdc_raw.json
```

**Output:** `sfdc_raw.json` — structured JSON with all collected config.

**Dry-run mode:**
```bash
sfdc-connect collect --scope all --org my-org --dry-run --out sfdc_raw.json
```
Produces a synthetic weak-org snapshot (no real Salesforce connection needed).

---

## Stage 2: OSCAL Assessment (`oscal-assess`)

**What it does:** Evaluates 45 SBS (Salesforce Baseline Security) controls against the collected config.

**How rules work:**

| Rule type | Count | Logic |
|---|---|---|
| Explicit deterministic | 11 | Direct config check → pass/fail |
| Structural partial | 8 | Config present but incomplete → partial |
| Not applicable | 26 | Outside sfdc-connect scope (CODE, FILE, etc.) |

**Status values:**
- `pass` — control requirement met definitively
- `fail` — control requirement not met
- `partial` — control partially implemented
- `not_applicable` — control outside the assessment scope

**Command:**
```bash
oscal-assess assess --collector-output sfdc_raw.json --org my-org --out gap_analysis.json
```

**Output:** `gap_analysis.json` — findings array with `control_id`, `status`, `severity`, `owner`, `evidence_ref`.

---

## Stage 3: Gap Mapping (`oscal_gap_map.py`)

**What it does:** Maps SBS findings to SSCF control domains; produces a prioritized remediation backlog.

**Mapping path:**
```
SBS control (SBS-AUTH-001)
    → sbs_to_sscf_mapping.yaml
        → SSCF domain (IAM-001, DATA-003, etc.)
            → backlog item with priority score
```

**Command:**
```bash
python3 scripts/oscal_gap_map.py \
    --gap-analysis gap_analysis.json \
    --org my-org \
    --out-json backlog.json
```

**Output:** `backlog.json` — remediation backlog with SSCF control references and priority ordering.

---

## Stage 4: SSCF Benchmark (`sscf-benchmark`)

**What it does:** Calculates maturity scores per SSCF domain and an overall posture rating.

**Scoring:**
- Per-domain score: `(pass + 0.5*partial) / total_controls_in_domain`
- Overall score: weighted average across all domains
- Status thresholds: RED < 40%, AMBER 40–70%, GREEN > 70%

**Command:**
```bash
sscf-benchmark benchmark \
    --backlog backlog.json \
    --org my-org \
    --out sscf_report.json
```

**Output:** `sscf_report.json` — domain scores, overall score, overall status, top gaps.

---

## Stage 5: Report Generation (`report-gen`)

**What it does:** Generates audience-specific governance outputs from the assessment data.

**Two audiences:**

| Audience | Format | Contents |
|---|---|---|
| `app-owner` | Markdown | Remediation backlog, control gaps, severity breakdown |
| `gis` | Markdown + DOCX | Full SSCF heatmap, NIST AI RMF note, executive summary, finding details |

**Commands:**
```bash
# App owner report
report-gen generate \
    --backlog backlog.json \
    --sscf-report sscf_report.json \
    --audience app-owner \
    --org my-org \
    --out report-app-owner.md

# GIS/CorpIS report
report-gen generate \
    --backlog backlog.json \
    --sscf-report sscf_report.json \
    --audience gis \
    --org my-org \
    --out report-gis.md  # also writes report-gis.docx
```

---

## Orchestrated Pipeline (agent-loop)

All 5 stages above run automatically via `agent-loop`. The `claude-opus-4-6` orchestrator decides the sequence, passes outputs between tools, and enforces quality gates.

```bash
# Full live run
agent-loop run --env prod --org mycompany

# Dry-run (no Salesforce, no real API spend on tools)
agent-loop run --dry-run --env dev --org test-org
```

**Turn budget:** 20 turns max. Typical full pipeline: 6–8 turns.

**Quality gates the orchestrator enforces:**
1. `critical/fail` findings require `--approve-critical` to proceed on live runs
2. nist-reviewer must not return a blocking gap
3. Output schema (`schemas/baseline_assessment_schema.json`) must be satisfied
4. `assessment_id` and `generated_at_utc` must be present in all findings
5. security-reviewer CRITICAL/HIGH on CI changes blocks merge

---

## Interpreting the Score

| Score | Status | Meaning |
|---|---|---|
| > 70% | GREEN | Most controls met; minor gaps |
| 40–70% | AMBER | Significant gaps; remediation plan required |
| < 40% | RED | Critical posture deficiencies; immediate action required |

A dry-run with the synthetic weak-org stub produces ~34.8% RED — this is intentional to test the full alert path.
