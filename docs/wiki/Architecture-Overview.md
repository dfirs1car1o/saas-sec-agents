# Architecture Overview

## Design Philosophy

**OpenClaw**: CLIs not MCPs. Every tool is a Python CLI callable from the shell. No hidden MCP state. No Docker-required infrastructure. The agent loop is a standard Anthropic `tool_use` ReAct loop.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    agent-loop (claude-opus-4-6)          │
│                     Anthropic tool_use ReAct loop        │
│                     max 20 turns, prompt-cached          │
└──────────┬──────────┬──────────┬───────────┬────────────┘
           │          │          │           │
    ┌──────▼──┐ ┌─────▼──┐ ┌────▼──┐ ┌─────▼────┐
    │sfdc-    │ │oscal-  │ │oscal_ │ │sscf-     │
    │connect  │ │assess  │ │gap_map│ │benchmark │
    │(collect)│ │(assess)│ │(map)  │ │(score)   │
    └──────┬──┘ └─────┬──┘ └────┬──┘ └─────┬────┘
           │          │          │           │
    sfdc_  │  gap_    │  back-   │  sscf_   │
    raw.   │  analysis│  log.    │  report. │
    json   │  .json   │  json    │  json    │
           └──────────┴──────────┴──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   report-gen        │
                    │  (claude-haiku-4-5) │
                    │  app-owner MD       │
                    │  gis MD + DOCX      │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   nist-reviewer     │
                    │  (sonnet-4-6)       │
                    │  NIST AI RMF gate   │
                    └────────────────────┘
```

---

## Agent Architecture

### 6 Agents

| Agent | Model | Role | Tools |
|---|---|---|---|
| `orchestrator` | claude-opus-4-6 | Routes tasks, manages the ReAct loop, quality gates | All 5 CLI tools |
| `collector` | claude-sonnet-4-6 | Extracts Salesforce org config via REST/Metadata API | sfdc-connect |
| `assessor` | claude-sonnet-4-6 | Maps findings to OSCAL/SBS/SSCF controls | oscal-assess, oscal_gap_map |
| `reporter` | claude-haiku-4-5-20251001 | Generates DOCX/MD governance outputs | report-gen |
| `nist-reviewer` | claude-sonnet-4-6 | Validates outputs against NIST AI RMF | None (text analysis) |
| `security-reviewer` | claude-sonnet-4-6 | AppSec + DevSecOps review of CI/CD and skills | None (text analysis) |

### Model Assignment Rationale

- **Opus** for the orchestrator: complex routing with incomplete information, quality gates, final assembly
- **Sonnet** for analytical work: API extraction, control mapping, regulatory QA, security review
- **Haiku** for templated output: structured data → formatted report (low-complexity, high-volume)
- **No tools for review agents**: text-only analysis prevents accidental state modification

---

## 4 Skills (CLI Tools)

| Skill | Binary | Purpose |
|---|---|---|
| `sfdc-connect` | `skills/sfdc_connect/sfdc_connect.py` | Authenticates to Salesforce org via REST; collects SecuritySettings, Auth providers, Permission Sets, Network Access, Connected Apps, Profiles |
| `oscal-assess` | `skills/oscal_assess/oscal_assess.py` | Evaluates 45 SBS controls against collected org data; produces findings with status (pass/fail/partial/not_applicable) and severity |
| `sscf-benchmark` | `skills/sscf_benchmark/sscf_benchmark.py` | Maps SBS findings to SSCF domains; calculates domain scores and overall posture (RED/AMBER/GREEN) |
| `report-gen` | `skills/report_gen/report_gen.py` | Generates audience-specific outputs: app-owner Markdown, CorpIS Markdown + DOCX |

---

## Data Flow

```
sfdc-connect collect
    → sfdc_raw.json (Salesforce org snapshot)
        → oscal-assess assess
            → gap_analysis.json (45 SBS control findings)
                → oscal_gap_map.py
                    → backlog.json (remediation items)
                        → sscf-benchmark benchmark
                            → sscf_report.json (domain scorecard)
                                → report-gen generate
                                    → report-app-owner.md
                                    → report-gis.md
                                    → report-gis.docx
```

All outputs land in `docs/oscal-salesforce-poc/generated/<org>/`.

---

## Memory Architecture

Session memory uses **Mem0 + Qdrant**. By default:
- `QDRANT_IN_MEMORY=1` — in-process Qdrant (no Docker needed)
- Memory stores: org alias, prior assessment score, critical findings
- Each new assessment loads prior org context as prefix to the first user message
- This allows the orchestrator to detect regression ("score dropped from 48% to 34%")

For persistent cross-session memory, run a Qdrant container and set `QDRANT_HOST=localhost`.

---

## Control Mapping Architecture

```
Salesforce Config
       ↓
  SBS Controls (45 controls in config/oscal-salesforce/sbs_source.yaml)
       ↓
  SBS → SSCF mapping (config/oscal-salesforce/sbs_to_sscf_mapping.yaml)
       ↓
  SSCF Control Index (config/sscf_control_index.yaml)
       ↓
  Domain Scores (Access Control, Identity, Data, etc.)
```

---

## Key File Locations

| Location | Purpose |
|---|---|
| `mission.md` | Agent identity + authorized scope (loaded every session) |
| `AGENTS.md` | Canonical agent roster |
| `agents/orchestrator.md` | Orchestrator routing table and quality gates |
| `config/sscf_control_index.yaml` | 45 SSCF controls |
| `config/oscal-salesforce/sbs_source.yaml` | SBS control catalog |
| `schemas/baseline_assessment_schema.json` | Required output schema |
| `docs/oscal-salesforce-poc/generated/` | All assessment outputs |
