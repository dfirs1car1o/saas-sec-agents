# Configuration Reference

All environment variables, configuration files, and YAML schemas used by this system.

---

## Environment Variables (`.env`)

### Required for Live Assessment

| Variable | Description | Example |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key for LLM calls | `sk-ant-api03-...` |
| `SF_USERNAME` | Salesforce login username | `admin@mycompany.com` |
| `SF_PASSWORD` | Salesforce login password | `MyPassword123` |
| `SF_SECURITY_TOKEN` | Salesforce security token (appended to password for non-trusted IPs) | `AbcDef123...` |

### Optional / Override

| Variable | Default | Description |
|---|---|---|
| `SF_DOMAIN` | `login` | Use `test` for sandbox orgs |
| `SF_INSTANCE_URL` | Auto-detected | Override if using a custom domain |
| `SFDC_ORG_ALIAS` | `default` | Used in output file path naming |
| `QDRANT_IN_MEMORY` | `1` | `1` = in-process (no Docker); `0` = use QDRANT_HOST |
| `QDRANT_HOST` | unset | Qdrant container hostname (only if `QDRANT_IN_MEMORY=0`) |
| `QDRANT_PORT` | `6333` | Qdrant container port |

### QDRANT_IN_MEMORY Values

All of these are treated as "enabled":
- `1`, `true`, `yes`, `on` (case-insensitive)

---

## Configuration Files

### `config/oscal-salesforce/sbs_source.yaml`

**Purpose:** Defines the 45 SBS (Salesforce Baseline Security) controls.

**Schema:**
```yaml
controls:
  - id: SBS-AUTH-001
    title: "MFA Enforcement"
    description: "..."
    category: AUTH
    severity: critical
```

### `config/oscal-salesforce/sbs_to_sscf_mapping.yaml`

**Purpose:** Maps SBS control categories to SSCF domains.

**Schema:**
```yaml
SBS-AUTH:
  sscf_domain: IAM
  sscf_controls:
    - IAM-001
    - IAM-002
```

### `config/oscal-salesforce/control_mapping.yaml`

**Purpose:** Detailed control-level mapping for the gap map script.

### `config/sscf_control_index.yaml`

**Purpose:** Canonical SSCF control reference. Source of truth for all SSCF control IDs and domain assignments.

**Schema:**
```yaml
domains:
  - id: IAM
    name: "Identity and Access Management"
    controls:
      - id: IAM-001
        title: "..."
        weight: 1.0
```

---

## Output Schema

### `schemas/baseline_assessment_schema.json`

**Required fields on every finding:**

```json
{
  "assessment_id": "sfdc-assess-myorg-prod-loop",
  "generated_at_utc": "2026-03-02T15:00:00Z",
  "findings": [
    {
      "control_id": "SBS-AUTH-001",
      "status": "fail",
      "severity": "critical",
      "owner": "security-team",
      "evidence_ref": "collector://salesforce/prod/SBS-AUTH-001/snapshot-2026-03-02"
    }
  ]
}
```

**Status values:** `pass` | `fail` | `partial` | `not_applicable`

**Severity values:** `critical` | `high` | `medium` | `low`

---

## Gap Analysis JSON Format

Input to `oscal_gap_map.py`:

```json
{
  "assessment_id": "string",
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

If `control_id` starts with `SBS-`, the gap map does a direct lookup — `control_mapping.yaml` is not needed.

---

## Agent Frontmatter Schema

Every file in `agents/` has YAML frontmatter:

```yaml
---
name: agent-name
description: |
  What this agent does and when to invoke it.
model: claude-sonnet-4-6
tools:
  - sfdc_connect_collect
  - oscal_assess_assess
proactive_triggers:
  - "Weekly drift check"
---
```

**Model options:**
- `claude-opus-4-6` — orchestrator only
- `claude-sonnet-4-6` — collector, assessor, nist-reviewer, security-reviewer
- `claude-haiku-4-5-20251001` — reporter (use dated ID for reproducibility)

---

## pyproject.toml Sections

```toml
[project.scripts]
# CLI entry points installed by pip install -e .
sfdc-connect = "skills.sfdc_connect.sfdc_connect:cli"
oscal-assess  = "skills.oscal_assess.oscal_assess:cli"
sscf-benchmark = "skills.sscf_benchmark.sscf_benchmark:cli"
agent-loop    = "harness.loop:cli"
report-gen    = "skills.report_gen.report_gen:cli"

[tool.setuptools.packages.find]
# Required for editable install to find skills.*
include = ["skills*", "harness*"]

[tool.uv]
# Dev deps (not installed by plain pip — must install explicitly in CI)
dev-dependencies = [
  "ruff>=0.6.0",
  "pytest>=8.0.0",
  "pytest-mock>=3.14.0",
  "diagrams>=0.23.4",
  "zizmor>=1.0.0",
  "pip-licenses>=5.0.0",
  "cyclonedx-bom>=4.0.0",
]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```
