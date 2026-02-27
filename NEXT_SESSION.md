# Next Session Checkpoint — 2026-02-27 (Phase 1 FULLY CLOSED)

## Session Summary

Phase 1 fully closed. PR #1 merged to main with all CI checks green.
Full CI stack operational: ruff, bandit, pip-audit, gitleaks CLI, pytest, validate_env, CodeQL, CodeRabbit Pro.
Three CI bugs fixed during session (setuptools flat-layout, ruff format, gitleaks license).
Ready to build Phase 2: oscal-assess + sscf-benchmark CLIs.

---

## Phase 1 Status: DONE ✓ (PR #1 merged)

### CI Stack (All Green on main)

| Check | Tool | Notes |
|---|---|---|
| Lint | ruff check + ruff format | line-length=120, select E/F/I/UP |
| SAST | bandit -lll -ii | HIGH severity = hard fail |
| SAST inline | bandit annotations on PR | MEDIUM surfaced as PR comments |
| Dependency CVEs | pip-audit | Runs after pip install -e . |
| Secret scan | gitleaks CLI v8.21.2 | Free CLI, not paid gitleaks-action |
| Tests | pytest | Skips gracefully if no tests/ dir |
| Pre-flight | validate_env.py --ci --json | Non-credential checks only in CI |
| Static analysis | CodeQL Python | Weekly + PR scans |
| AI code review | CodeRabbit Pro | .coderabbit.yaml with SF-specific rules |
| Dependency review | dependency-review | Blocks HIGH/CRITICAL CVEs on PRs |

### Bugs Fixed During CI Hardening

1. `setuptools flat-layout` — `pip install -e .` refused to build (7 top-level dirs).
   Fix: `[tool.setuptools.packages.find] include = ["skills*"]` in pyproject.toml

2. `ruff format` — ran `ruff check --fix` but not `ruff format`. 4 files reformatted.

3. `gitleaks-action@v2` — requires paid GITLEAKS_LICENSE for orgs.
   Fix: replaced with direct gitleaks CLI install in security-checks.yml

4. `validate_env --json` — mixed human-readable stdout with JSON, broke json.load().
   Fix: redirect all prints to stderr when --json active; CI captures stdout only.

### GitHub Org State (dfirs1car1o)

| Check | Status |
|---|---|
| Secret scanning | ✅ org-wide |
| Push protection | ✅ org-wide |
| Branch protection (main) | ✅ 1 review required, no force push |
| Dependabot | ✅ enabled |
| 2FA enforcement | ✅ confirmed by user |
| Actions permissions | ✅ GitHub-owned + verified creators only |
| CodeRabbit Pro | ✅ installed, CODERABBIT_API_KEY in org secrets |
| enforce_admins | ⚠️ off — flip when colleague added to CODEOWNERS |

---

## Architecture Reference

### Pipeline (Phase 2 target)

```
sfdc-connect collect --scope all --out sfdc_raw.json
    ↓
oscal-assess --collector-output sfdc_raw.json --controls sbs_controls.json --out gap_analysis.json
    ↓
scripts/oscal_gap_map.py --controls sbs_controls.json --gap-analysis gap_analysis.json
                          --mapping control_mapping.yaml --sscf-map sbs_to_sscf_mapping.yaml
                          --out-md matrix.md --out-json backlog.json
    ↓
sscf-benchmark --backlog backlog.json --sscf-index config/sscf_control_index.yaml --out sscf_report.json
```

### Gap-Analysis JSON Format (input to oscal_gap_map.py)

```json
{
  "assessment_id": "string",
  "findings": [
    {
      "control_id": "SBS-AUTH-001",
      "status": "pass|fail|partial|not_applicable",
      "severity": "critical|high|medium|low",
      "owner": "string",
      "due_date": "YYYY-MM-DD",
      "remediation": "string",
      "evidence_ref": "collector://salesforce/<env>/<control_id>/snapshot-<date>"
    }
  ]
}
```

If `control_id` starts with `SBS-`, oscal_gap_map treats it as a direct mapping (no control_mapping.yaml lookup needed).

### Key Config Files

| File | Purpose |
|---|---|
| `config/oscal-salesforce/sbs_source.yaml` | SBS XML source URL + release pin (v0.4.1) |
| `config/oscal-salesforce/control_mapping.yaml` | Legacy control ID → SBS control ID mapping |
| `config/oscal-salesforce/sbs_to_sscf_mapping.yaml` | SBS category → SSCF domain/control mapping |
| `config/sscf_control_index.yaml` | Canonical SSCF control reference |
| `docs/oscal-salesforce-poc/generated/sbs_controls.json` | Imported SBS catalog (45 controls, v0.4.1) |

### Existing POC Output (reference for format)

`docs/oscal-salesforce-poc/generated/salesforce_oscal_backlog.json` — 45 controls, 24 pass / 9 fail / 12 partial
`docs/oscal-salesforce-poc/generated/salesforce_oscal_gap_matrix.md` — markdown matrix

---

## Phase 2 Plan (NEXT)

### What to Build

**1. `skills/oscal_assess/oscal_assess.py`**
- Click CLI: `oscal-assess assess`
- `--collector-output` (sfdc-connect JSON)
- `--controls` (sbs_controls.json, default: docs/.../generated/sbs_controls.json)
- `--out` (gap_analysis.json output path)
- `--env` (dev/test/prod label)
- `--dry-run` (emit sample findings without live org data)
- Core logic: rule engine mapping sfdc-connect scope data → SBS control pass/fail/partial
- Scope → SBS control mapping:
  - `auth` scope → SBS-AUTH-* controls (session timeout, MFA, SSO, IP ranges)
  - `access` scope → SBS-ACS-* controls (admin profiles, elevated perm sets, connected apps)
  - `event-monitoring` scope → SBS-INT-*/SBS-LOG-* (event log types, field history)
  - `transaction-security` scope → SBS-TSP-* (policies enabled/disabled)
  - `integrations` scope → SBS-INT-* (named creds, remote sites)
  - `oauth` scope → SBS-OA-* (refresh token policies, admin-approved users)
  - `secconf` scope → SBS-SEC-* (health check score)

**2. `skills/sscf_benchmark/sscf_benchmark.py`**
- Click CLI: `sscf-benchmark benchmark`
- `--backlog` (oscal_gap_map output backlog.json)
- `--sscf-index` (config/sscf_control_index.yaml)
- `--out` (SSCF gap report JSON)
- `--format` (json or markdown)
- Core logic: roll up finding statuses by SSCF domain, compute domain-level score

**3. End-to-end test (--dry-run)**
```bash
python3 -m skills.oscal_assess.oscal_assess assess --dry-run --out /tmp/gap.json
python3 scripts/oscal_gap_map.py --controls docs/oscal-salesforce-poc/generated/sbs_controls.json \
  --gap-analysis /tmp/gap.json --mapping config/oscal-salesforce/control_mapping.yaml \
  --sscf-map config/oscal-salesforce/sbs_to_sscf_mapping.yaml \
  --out-md /tmp/matrix.md --out-json /tmp/backlog.json
python3 -m skills.sscf_benchmark.sscf_benchmark benchmark --backlog /tmp/backlog.json \
  --sscf-index config/sscf_control_index.yaml --out /tmp/sscf_report.json
```

### Phase 3 Plan — Agentic Loop + Memory

- `harness/loop.py` — orchestrator loop using Anthropic SDK
- Memory: Mem0 + Qdrant (mem0ai + qdrant-client added to pyproject.toml at Phase 3)
  - memory key = org alias (e.g. "myorg.salesforce.com")
  - enables: "compare to last assessment", "show new failures since last run"
- Reference: DevPulseAI pattern from awesome-llm-apps repo

---

## Open Decisions

1. **Colleague GitHub username** — add to CODEOWNERS, then flip enforce_admins=true
2. **oscal-assess rule engine depth** — start with structural checks (field present/value matches)
   vs. LLM-assisted interpretation (Phase 3). Phase 2 = deterministic rules only.
3. **sbs_controls.json freshness** — currently pinned to v0.4.1. Add auto-refresh via
   `scripts/oscal_import_sbs.py` to CI? Or keep manual refresh only.

---

## Resume Command

```bash
cd /Users/jerijuar/multiagent-azure
git status        # should be clean on main
git log --oneline -5
python3 -m skills.sfdc_connect.sfdc_connect --help
```

To start Phase 2:
```
Resume from NEXT_SESSION.md in /Users/jerijuar/multiagent-azure.
Phase 1 is FULLY DONE — PR #1 merged, all CI green.
Repo: dfirs1car1o/saas-sec-agents on GitHub.
Start Phase 2: build skills/oscal_assess/oscal_assess.py and skills/sscf_benchmark/sscf_benchmark.py.
Pipeline design and gap-analysis JSON format are documented in NEXT_SESSION.md.
```

---

## Key Files (Full Repo State)

```
skills/sfdc_connect/sfdc_connect.py     ← Collector CLI (7 scopes, Tooling API)
skills/oscal_assess/                    ← TODO Phase 2
skills/sscf_benchmark/                  ← TODO Phase 2
scripts/oscal_gap_map.py                ← Gap mapper (DO NOT BREAK)
scripts/oscal_import_sbs.py             ← SBS XML importer (DO NOT BREAK)
scripts/validate_env.py                 ← Pre-flight check
config/oscal-salesforce/                ← Control mappings + SBS source
config/sscf_control_index.yaml          ← SSCF control reference
schemas/baseline_assessment_schema.json ← Required output schema
docs/oscal-salesforce-poc/generated/    ← All evidence outputs (never /tmp)
.github/workflows/ci.yml                ← ruff + bandit + pip-audit + pytest + validate_env
.github/workflows/security-checks.yml  ← bandit SAST + pip-audit CVEs + gitleaks
.github/workflows/pr-inline-review.yml ← Bandit/ruff inline PR annotations
.github/workflows/codeql.yml            ← CodeQL Python weekly + PR
.coderabbit.yaml                        ← CodeRabbit Pro config (SF-specific rules)
pyproject.toml                          ← packages.find include=["skills*"]
```
