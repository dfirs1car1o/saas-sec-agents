# Skill Reference

All 5 CLI skills. Each is a Python CLI installed by `pip install -e .` and callable from the shell or from the agent orchestrator via `tool_use`.

---

## sfdc-connect

**Binary:** `sfdc-connect`
**File:** `skills/sfdc_connect/sfdc_connect.py`
**Purpose:** Authenticates to a Salesforce org and collects security-relevant configuration.

### Commands

```bash
sfdc-connect collect --scope all --org my-org [--dry-run] [--out PATH]
sfdc-connect auth --dry-run   # test auth only, no collection
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--scope` | `all` | What to collect: `all`, `auth`, `permissions`, `network`, `oauth` |
| `--org` | `unknown-org` | Org alias for output path naming |
| `--dry-run` | off | Use synthetic weak-org data, no real Salesforce connection |
| `--out` | auto | Output path (`docs/.../generated/<org>/sfdc_raw.json`) |

### What It Collects

| API | Data | Purpose |
|---|---|---|
| Tooling API `SecuritySettings` | Session timeout, MFA, IP restrictions, cert auth | AUTH controls |
| REST `AuthProvider` | SSO/OAuth providers | OAUTH controls |
| REST `PermissionSet` | Named permissions, dangerous grants | ACS controls |
| REST `Profile` | Admin-equivalent profiles | ACS controls |
| REST `NetworkAccess` | Trusted IP ranges | ACS controls |
| REST `ConnectedApp` | OAuth clients, scopes, token policy | OAUTH controls |

### Auth Method

`simple-salesforce` with username + password + security token. Credentials from `SF_USERNAME`, `SF_PASSWORD`, `SF_SECURITY_TOKEN`, `SF_DOMAIN`.

---

## oscal-assess

**Binary:** `oscal-assess`
**File:** `skills/oscal_assess/oscal_assess.py`
**Purpose:** Evaluates 45 SBS controls against the collected org configuration.

### Commands

```bash
oscal-assess assess --collector-output sfdc_raw.json --org my-org [--out PATH]
```

### Rule Engine

| Rule type | Count | Logic |
|---|---|---|
| Explicit deterministic | 11 | Direct config check → pass/fail (AUTH-001, ACS-001–004, INT, OAUTH-001–002, DATA-004, SECCONF, DEP-003) |
| Structural partial | 8 | Config present but ambiguous → partial (ACS-005–012, OAUTH-003–004, DATA-001–003) |
| Not applicable | 26 | Outside sfdc-connect scope (CODE, CPORTAL, FILE, DEP, FDNS) |

**Conservative rule:** Only `pass` when definitive. When ambiguous → `partial`.

### Output

`gap_analysis.json`:
```json
{
  "assessment_id": "sfdc-assess-my-org-dev",
  "generated_at_utc": "2026-03-02T15:00:00Z",
  "findings": [
    {
      "control_id": "SBS-AUTH-001",
      "status": "fail",
      "severity": "critical",
      "owner": "security-team",
      "evidence_ref": "collector://salesforce/dev/SBS-AUTH-001/snapshot-2026-03-02"
    }
  ]
}
```

---

## sscf-benchmark

**Binary:** `sscf-benchmark`
**File:** `skills/sscf_benchmark/sscf_benchmark.py`
**Purpose:** Maps SBS findings to SSCF domains and calculates domain maturity scores.

### Commands

```bash
sscf-benchmark benchmark --backlog backlog.json --org my-org [--out PATH]
```

### Scoring

```
domain_score = (pass_count + 0.5 * partial_count) / total_controls_in_domain
overall_score = weighted_average(domain_scores)

Status:
  overall_score >= 0.70 → GREEN
  0.40 <= overall_score < 0.70 → AMBER
  overall_score < 0.40 → RED
```

### Output

`sscf_report.json`:
```json
{
  "org": "my-org",
  "overall_score": 0.348,
  "overall_status": "RED",
  "domain_scores": {
    "IAM": 0.25,
    "DATA": 0.40,
    "OPS": 0.50
  },
  "top_gaps": ["SBS-AUTH-001", "SBS-ACS-001", "SBS-OAUTH-001"]
}
```

---

## report-gen

**Binary:** `report-gen`
**File:** `skills/report_gen/report_gen.py`
**Purpose:** Generates audience-specific governance reports from assessment data.

### Commands

```bash
# App owner report (Markdown)
report-gen generate \
    --backlog backlog.json \
    --sscf-report sscf_report.json \
    --audience app-owner \
    --org my-org \
    --out report-app-owner.md

# Security governance report (Markdown + DOCX + PDF)
report-gen generate \
    --backlog backlog.json \
    --sscf-report sscf_report.json \
    --audience security \
    --org my-org \
    --out report-security.md
```

### Audiences

| Audience | Formats | Contents |
|---|---|---|
| `app-owner` | Markdown | Remediation backlog, control gaps by severity, owner assignments |
| `security` | Markdown + DOCX + PDF | Executive summary, SSCF heatmap, full finding details, NIST AI RMF note |

### DOCX Template Engine

Uses `docxtpl` (LGPL-2.1, Python Jinja2 wrapper for python-docx). Template: `skills/report_gen/templates/security_report.docx`.

---

## oscal_gap_map.py (Script, Not CLI)

**File:** `scripts/oscal_gap_map.py`
**Not installed as a CLI binary** — run directly with `python3`.

```bash
python3 scripts/oscal_gap_map.py \
    --gap-analysis gap_analysis.json \
    --org my-org \
    --out-json backlog.json
```

Maps `gap_analysis.json` findings to SSCF controls using `config/oscal-salesforce/sbs_to_sscf_mapping.yaml`. Produces `backlog.json` with remediation items and SSCF control references.

Controls starting with `SBS-` are looked up directly — no `control_mapping.yaml` needed.

---

## nist-review

**Binary:** `nist-review`
**Source:** `skills/nist_review/nist_review.py`
**Purpose:** Validates multi-agent assessment outputs against NIST AI RMF 1.0 (Govern, Map, Measure, Manage) and produces a structured verdict JSON.

### Command

```bash
nist-review assess \
  --gap-analysis <path/to/gap_analysis.json> \
  --backlog      <path/to/backlog.json> \
  --out          <path/to/nist_review.json> \
  [--dry-run]
```

### Options

| Option | Required | Description |
|---|---|---|
| `--gap-analysis` | Yes (live) | Path to `gap_analysis.json` from `oscal-assess` |
| `--backlog` | Yes (live) | Path to `backlog.json` from `oscal_gap_map` |
| `--out` | Yes | Output path for `nist_review.json` |
| `--dry-run` | No | Produce realistic stub verdict without calling the API |

### Output format

```json
{
  "nist_ai_rmf_review": {
    "assessment_id": "sfdc-assess-...",
    "reviewed_at_utc": "2026-03-03T...",
    "govern":  { "status": "pass|partial|fail", "notes": "..." },
    "map":     { "status": "pass|partial|fail", "notes": "..." },
    "measure": { "status": "pass|partial|fail", "notes": "..." },
    "manage":  { "status": "pass|partial|fail", "notes": "..." },
    "overall": "clear|flag|block",
    "blocking_issues": [],
    "recommendations": ["..."]
  }
}
```

### Live mode

In live mode (`--dry-run` omitted), calls `claude-sonnet-4-6` with `agents/nist-reviewer.md` as system prompt. Input JSONs are truncated to 6 000 chars each to stay within the token budget. Requires `ANTHROPIC_API_KEY`.

### Dry-run mode

Emits a realistic weak-org stub verdict: GOVERN=pass, MAP=partial, MEASURE=pass, MANAGE=partial, overall=flag. Does not call the Anthropic API.
