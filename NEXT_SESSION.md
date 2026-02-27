# Next Session Checkpoint — 2026-02-27 (Phase 2 FULLY CLOSED)

## Session Summary

Phase 2 fully closed. PR #2 merged to main with all CI checks green.
Two new CLI skills delivered: `oscal-assess` and `sscf-benchmark`.
Full pipeline now works end-to-end without a live Salesforce org.
Also fixed: CI pytest job missing pytest binary (uv dev deps not recognised by pip).

---

## Phase Status

| Phase | Status | PR | Notes |
|---|---|---|---|
| Phase 1 | ✅ DONE | PR #1 merged | sfdc-connect + full CI stack |
| Phase 2 | ✅ DONE | PR #2 merged | oscal-assess + sscf-benchmark CLIs |
| Phase 3 | 🔜 NEXT | — | harness/loop.py + Mem0 + Qdrant |
| Phase 4 | 📋 PLANNED | — | report-gen DOCX pipeline |

---

## CI Stack (All Green on main)

| Check | Tool | Notes |
|---|---|---|
| Lint | ruff check + ruff format | line-length=120, select E/F/I/UP |
| SAST | bandit -lll -ii | HIGH severity = hard fail |
| SAST inline | bandit annotations on PR | MEDIUM surfaced as PR comments |
| Dependency CVEs | pip-audit | Runs after pip install -e . |
| Secret scan | gitleaks CLI v8.21.2 | Free CLI, not paid gitleaks-action |
| Tests | pytest tests/ -v | 3 smoke tests pass in ~350 ms |
| Pre-flight | validate_env.py --ci --json | Non-credential checks only in CI |
| Static analysis | CodeQL Python | Weekly + PR scans |
| AI code review | CodeRabbit Pro | .coderabbit.yaml with SF-specific rules |
| Dependency review | dependency-review | Blocks HIGH/CRITICAL CVEs on PRs |

### Key CI Fixes Applied (do not revert)

1. `[tool.setuptools.packages.find] include = ["skills*"]` — prevents flat-layout error
2. gitleaks CLI not gitleaks-action — free tier, no org license needed
3. validate_env --json routes prints to stderr; CI captures stdout only
4. pytest CI job: `pip install -e . && pip install pytest pytest-mock PyYAML click`
   (`[tool.uv]` dev-dependencies not recognised by pip — must install explicitly)

---

## Architecture Reference

### Pipeline (COMPLETE after Phase 2)

```
sfdc-connect collect --scope all --out sfdc_raw.json
    ↓
oscal-assess assess --collector-output sfdc_raw.json --env dev --out gap_analysis.json
    ↓
scripts/oscal_gap_map.py --controls sbs_controls.json --gap-analysis gap_analysis.json
                          --mapping control_mapping.yaml --sscf-map sbs_to_sscf_mapping.yaml
                          --out-md matrix.md --out-json backlog.json
    ↓
sscf-benchmark benchmark --backlog backlog.json --sscf-index config/sscf_control_index.yaml
                          --out sscf_report.json
```

Dry-run (no live org needed):
```bash
python3 -m skills.oscal_assess.oscal_assess assess --dry-run --env dev --out /tmp/gap.json
python3 scripts/oscal_gap_map.py --controls docs/oscal-salesforce-poc/generated/sbs_controls.json \
  --gap-analysis /tmp/gap.json --mapping config/oscal-salesforce/control_mapping.yaml \
  --sscf-map config/oscal-salesforce/sbs_to_sscf_mapping.yaml \
  --out-md /tmp/matrix.md --out-json /tmp/backlog.json
python3 -m skills.sscf_benchmark.sscf_benchmark benchmark --backlog /tmp/backlog.json \
  --sscf-index config/sscf_control_index.yaml --out /tmp/sscf_report.json
```

Expected dry-run output: overall score ~34%, status RED (weak-org stub).

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

### Assessment Rule Engine (oscal_assess.py)

- 11 controls with explicit deterministic rules (AUTH, ACS-001–004, INT, OAUTH-001–002, DATA-004, SECCONF, DEP-003)
- 8 structural partial rules (ACS-005–012, OAUTH-003–004, DATA-001–003) — scope collected but requires deeper audit
- 26 not_applicable rules (CODE, CPORTAL, FILE, DEP, FDNS, etc.) — outside sfdc-connect API scope
- Conservative ambiguity policy: only emit `pass` when definitively satisfied; ambiguous → `partial`
- Dry-run weak-org: ~40% pass, 30% partial, 30% fail

### Key Config Files

| File | Purpose |
|---|---|
| `config/oscal-salesforce/sbs_source.yaml` | SBS XML source URL + release pin (v0.4.1) |
| `config/oscal-salesforce/control_mapping.yaml` | Legacy control ID → SBS control ID mapping |
| `config/oscal-salesforce/sbs_to_sscf_mapping.yaml` | SBS category → SSCF domain/control mapping |
| `config/sscf_control_index.yaml` | Canonical SSCF control reference |
| `docs/oscal-salesforce-poc/generated/sbs_controls.json` | Imported SBS catalog (45 controls, v0.4.1) |

---

## Phase 3 Plan — Agentic Loop + Memory (NEXT)

### What to Build

**1. `harness/loop.py`** — orchestrator loop using Anthropic SDK
- Runs the 4-stage pipeline against a live org
- Calls agents in sequence: collector → assessor → gap-mapper → benchmarker
- Saves results under `docs/oscal-salesforce-poc/generated/<org>/<date>/`

**2. Session Memory**
- Library: Mem0 + Qdrant (`mem0ai`, `qdrant-client` added to pyproject.toml)
- Memory key = org alias (e.g. "myorg.salesforce.com")
- Enables: "compare to last assessment", "show new failures since last run"
- Reference pattern: DevPulseAI from awesome-llm-apps repo

**3. `harness/agents.py`** — agent definitions (currently just markdown, need Python)
- Orchestrator (claude-opus-4-6): loop control, tool dispatch
- Collector (claude-sonnet-4-6): wraps sfdc-connect CLI
- Assessor (claude-sonnet-4-6): wraps oscal-assess CLI
- Reporter (claude-haiku-4-5): wraps report-gen CLI (Phase 4)

---

## Open Decisions

1. **Colleague GitHub username** — add to CODEOWNERS, then flip enforce_admins=true
2. **Mem0 storage backend** — local Qdrant vs. managed cloud Qdrant for Phase 3
3. **sbs_controls.json freshness** — currently pinned to v0.4.1. Auto-refresh in CI?

---

## Resume Command

```bash
cd /Users/jerijuar/multiagent-azure
git status        # should be clean on main
git log --oneline -5
python3 -m skills.oscal_assess.oscal_assess assess --help
python3 -m skills.sscf_benchmark.sscf_benchmark benchmark --help
```

To start Phase 3:
```
Resume from NEXT_SESSION.md in /Users/jerijuar/multiagent-azure.
Phase 2 is FULLY DONE — PR #2 merged, all CI green (ruff/bandit/pytest/pip-audit/gitleaks).
Repo: dfirs1car1o/saas-sec-agents on GitHub.
Start Phase 3: build harness/loop.py agentic orchestrator + Mem0 session memory.
Phase 3 design is documented in NEXT_SESSION.md.
```

---

## Key Files (Full Repo State)

```
skills/sfdc_connect/sfdc_connect.py         ← Collector CLI (7 scopes, Tooling API) ✅
skills/oscal_assess/oscal_assess.py         ← Assessment engine (45 SBS controls) ✅
skills/sscf_benchmark/sscf_benchmark.py     ← SSCF domain scorer ✅
scripts/oscal_gap_map.py                    ← Gap mapper (DO NOT BREAK)
scripts/oscal_import_sbs.py                 ← SBS XML importer (DO NOT BREAK)
scripts/validate_env.py                     ← Pre-flight check
tests/test_pipeline_smoke.py                ← End-to-end dry-run pipeline tests ✅
config/oscal-salesforce/                    ← Control mappings + SBS source
config/sscf_control_index.yaml              ← SSCF control reference
schemas/baseline_assessment_schema.json     ← Required output schema
docs/oscal-salesforce-poc/generated/        ← All evidence outputs (never /tmp)
.github/workflows/ci.yml                    ← ruff + bandit + pip-audit + pytest + validate_env
.github/workflows/security-checks.yml      ← bandit SAST + pip-audit CVEs + gitleaks
.github/workflows/pr-inline-review.yml     ← Bandit/ruff inline PR annotations
.github/workflows/codeql.yml               ← CodeQL Python weekly + PR
.coderabbit.yaml                           ← CodeRabbit Pro config (SF-specific rules)
pyproject.toml                             ← entry points: sfdc-connect, oscal-assess, sscf-benchmark
```
