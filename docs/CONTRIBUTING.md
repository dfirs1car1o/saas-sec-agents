# Contributing — SaaS Security Multi-Agent System

This guide covers everything a new contributor needs to get the repo running locally, understand the architecture, and start contributing safely.

---

## Prerequisites

### Required Software

| Tool | Version | Install |
|---|---|---|
| Python | ≥ 3.11 | [python.org](https://python.org) or `brew install python@3.11` |
| Docker Desktop | ≥ 4.x | [docker.com/get-docker](https://www.docker.com/get-docker/) |
| Git | any recent | pre-installed on macOS/Linux |
| GitHub CLI (`gh`) | ≥ 2.x | `brew install gh` |
| Node.js | ≥ 18 (for hooks) | `brew install node` |

### Python Package Manager

This repo supports both `pip` and `uv`. `uv` is faster but optional:

```bash
# pip (standard)
pip install -e .
pip install pytest pytest-mock PyYAML click ruff bandit

# uv (faster, optional)
pip install uv
uv sync
```

### Docker Containers Required at Runtime

| Container | Purpose | Command |
|---|---|---|
| `qdrant/qdrant` | Session memory (Mem0 backend) | `docker run -d -p 6333:6333 qdrant/qdrant` |

> **CI note:** Qdrant is not run in CI. Tests mock Mem0 via `QDRANT_IN_MEMORY=1` env var.

---

## Initial Setup

```bash
# 1. Clone
git clone git@github.com:dfirs1car1o/saas-sec-agents.git
cd saas-sec-agents

# 2. Install Python dependencies
pip install -e .
pip install pytest pytest-mock PyYAML click ruff bandit

# 3. Copy and fill .env
cp .env.example .env
# Edit .env — see Environment Variables section below

# 4. Start Qdrant (for session memory)
docker run -d -p 6333:6333 qdrant/qdrant

# 5. Verify everything works
python3 -m pytest tests/ -v
agent-loop run --help
sfdc-connect --help
oscal-assess --help
sscf-benchmark --help
```

---

## Environment Variables

Copy `.env.example` to `.env` and populate:

```bash
# Anthropic API (required for agent-loop)
ANTHROPIC_API_KEY=sk-ant-...

# Salesforce org credentials (required for live assessment — skip for dry-run)
SF_USERNAME=your@email.com
SF_PASSWORD=yourpassword
SF_SECURITY_TOKEN=yourtoken
SF_DOMAIN=login                    # or 'test' for sandbox
SF_INSTANCE_URL=https://yourorg.salesforce.com  # optional override

# Org alias used in output file paths
SFDC_ORG_ALIAS=my-org-alias

# Qdrant (optional — defaults shown)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_IN_MEMORY=0                 # set to 1 to skip Docker entirely
```

> **Never commit `.env`** — it is in `.gitignore`. Never put credentials in any Python file or commit message.

---

## Project Structure

```
saas-sec-agents/
├── mission.md                  ← Agent identity + authorized scope. Read this first.
├── AGENTS.md                   ← Master agent roster and routing logic
├── CLAUDE.md                   ← Claude Code session instructions
│
├── agents/                     ← Per-agent role definitions (markdown + YAML frontmatter)
│   ├── orchestrator.md         ← claude-opus-4-6: loop control, routing
│   ├── collector.md            ← claude-sonnet-4-6: Salesforce API extraction
│   ├── assessor.md             ← claude-sonnet-4-6: OSCAL/SBS control mapping
│   ├── reporter.md             ← claude-haiku-4-5: governance output generation
│   └── nist-reviewer.md        ← claude-sonnet-4-6: NIST AI RMF validation
│
├── harness/                    ← Agentic orchestration loop (Phase 3)
│   ├── agents.py               ← AgentConfig dataclass + ORCHESTRATOR definition
│   ├── tools.py                ← Anthropic tool schemas + subprocess dispatchers
│   ├── memory.py               ← Mem0+Qdrant session memory
│   └── loop.py                 ← agent-loop CLI entry point
│
├── skills/                     ← CLI tools (each installable as a command)
│   ├── sfdc_connect/           ← sfdc-connect: Salesforce org collector
│   ├── oscal_assess/           ← oscal-assess: SBS control assessor
│   ├── sscf_benchmark/         ← sscf-benchmark: SSCF domain scorer
│   └── report-gen/             ← report-gen: DOCX/MD governance output (Phase 4)
│
├── scripts/                    ← Python helper scripts
│   ├── oscal_gap_map.py        ← Maps findings → SSCF controls → backlog
│   ├── oscal_import_sbs.py     ← Imports SBS XML catalog to JSON
│   ├── intake_questionnaire.py ← Intake form CLI
│   └── validate_env.py         ← Pre-flight environment check
│
├── config/
│   ├── oscal-salesforce/       ← Control mappings: SBS → SSCF
│   └── sscf_control_index.yaml ← Canonical SSCF control reference
│
├── contexts/                   ← System prompt context modes (assess/review/research)
├── prompts/                    ← Prompting patterns and examples
├── schemas/                    ← JSON schemas for output validation
├── docs/                       ← Architecture docs, deliverables, generated evidence
├── tests/                      ← pytest smoke tests
└── .github/workflows/          ← CI: ruff, bandit, pip-audit, gitleaks, pytest, CodeQL
```

---

## Pipeline

The full assessment pipeline (all stages are CLI tools):

```
sfdc-connect collect --scope all --out sfdc_raw.json
        ↓
oscal-assess assess --collector-output sfdc_raw.json --out gap_analysis.json
        ↓
python scripts/oscal_gap_map.py --gap-analysis gap_analysis.json --out-json backlog.json
        ↓
sscf-benchmark benchmark --backlog backlog.json --out sscf_report.json
```

**Orchestrated via `agent-loop`** (Phase 3): `claude-opus-4-6` calls these tools automatically via `tool_use`.

**Dry-run** (no live Salesforce org needed):
```bash
agent-loop run --dry-run --env dev --org my-test-org
```

---

## Running the Full Pipeline (Dry-Run)

No Salesforce org or Anthropic API needed for the pipeline smoke tests:

```bash
pytest tests/test_pipeline_smoke.py -v
```

For the agentic loop dry-run (needs `ANTHROPIC_API_KEY`):
```bash
# Start Qdrant first (or set QDRANT_IN_MEMORY=1 to skip Docker)
docker run -d -p 6333:6333 qdrant/qdrant

# Run
agent-loop run --dry-run --env dev --org test-org
```

Expected output: `overall_score ~34%, status: RED` (weak-org stub data).

---

## CI Stack

All checks run on every PR:

| Check | Tool | What fails it |
|---|---|---|
| Lint | `ruff check + format` | Any E/F/I/UP violations, line > 120 chars |
| SAST | `bandit -lll -ii` | HIGH severity findings |
| Dependency CVEs | `pip-audit` | Known CVEs in installed packages |
| Secret scan | `gitleaks` | Credentials, tokens, API keys in code |
| Tests | `pytest tests/ -v` | Any test failure |
| Pre-flight | `validate_env.py --ci` | Missing required layout/packages |
| Static analysis | CodeQL | Python security patterns |
| AI code review | CodeRabbit Pro | PR-level review comments |

**All checks must be green before merging to `main`.**

---

## Docker MCP Toolkit (Optional — Local Dev Only)

The repo uses the [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/) for optional local MCP server support (not required for core pipeline):

```bash
# Install Docker Desktop with MCP Toolkit
# Enable in Docker Desktop → Settings → Beta Features → MCP Toolkit

# MCP gateway runs on port 19473 (SSE transport)
# Configure in Claude Code settings if using MCP tools locally
```

This is optional — all core pipeline tools are CLI-based, not MCP-dependent.

---

## Security Rules (Non-Negotiable)

1. **Read-only against Salesforce.** No writes to any org under any circumstances.
2. **No credentials in code.** All secrets via `.env` or environment variables only.
3. **Evidence stays in `docs/oscal-salesforce-poc/generated/`** — never `/tmp` or outside the repo.
4. **All findings reference an `assessment_id` and `generated_at_utc` timestamp.**
5. **Critical/fail gate:** `agent-loop` will block output if `status=fail AND severity=critical` unless `--approve-critical` is passed.

---

## Branch / PR Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, run tests
pytest tests/ -v
ruff check skills/ scripts/ harness/

# Commit (conventional commits required)
git commit -m "feat(skill): description

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

# Push and open PR
git push -u origin feature/your-feature-name
gh pr create
```

**1 PR review required** before merge. Branch protection is enforced on `main`.

---

## Phase Roadmap

| Phase | Status | Deliverable |
|---|---|---|
| 1 | ✅ Done | `sfdc-connect` CLI + full CI stack |
| 2 | ✅ Done | `oscal-assess` + `sscf-benchmark` CLIs |
| 3 | ✅ Done | `agent-loop` harness + Mem0 session memory |
| 4 | 🔜 Next | `report-gen` DOCX/MD governance output pipeline |

---

## Getting Help

- Read `mission.md` — agent identity and authorized scope
- Read `AGENTS.md` — full agent roster and routing logic
- Run `<command> --help` on any CLI tool
- Open an issue on GitHub for bugs or questions
