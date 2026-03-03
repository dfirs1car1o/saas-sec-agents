# Onboarding — Get Running in 10 Minutes

## Step 1: Clone & Install

```bash
git clone git@github.com:dfirs1car1o/saas-sec-agents.git
cd saas-sec-agents

# Option A — pip (standard)
pip install -e .
pip install pytest pytest-mock PyYAML click

# Option B — uv (faster, optional)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Step 2: Configure .env

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```bash
# Required for agent loop
ANTHROPIC_API_KEY=sk-ant-...

# Required for live Salesforce assessment
SF_USERNAME=your.name@company.com
SF_PASSWORD=YourSalesforcePassword
SF_SECURITY_TOKEN=YourSecurityToken
SF_DOMAIN=login          # use "test" for sandbox
SF_INSTANCE_URL=https://yourorg.my.salesforce.com

# Memory backend (default: in-process, no Docker needed)
QDRANT_IN_MEMORY=1
```

> **Dry-run mode:** If you don't have a Salesforce org, you can still run the full pipeline with `--dry-run`. Only `ANTHROPIC_API_KEY` is needed.

## Step 3: Verify Your Environment

```bash
python3 scripts/validate_env.py
```

Expected: `ENVIRONMENT READY` or `ENVIRONMENT READY WITH WARNINGS` (credentials missing = expected if using dry-run).

## Step 4: Run the Tests

```bash
QDRANT_IN_MEMORY=1 pytest tests/ -v
```

Expected: 9/9 pass.

## Step 5: Your First Run (Dry-Run)

```bash
agent-loop run --dry-run --env dev --org my-test-org
```

Expected output:
```
agent-loop [DRY-RUN]: org=my-test-org env=dev
  [tool] sfdc_connect_collect(...)
  [tool] oscal_assess_assess(...)
  [tool] oscal_gap_map(...)
  [tool] sscf_benchmark_benchmark(...)
  [tool] report_gen_generate(...)
  [tool] report_gen_generate(...)
============================================================
Assessment complete (N turn(s))
overall_score : 34.8%
critical_fails: 0
============================================================
```

Reports land in: `docs/oscal-salesforce-poc/generated/my-test-org/`

## Step 6 (Optional): Live Assessment

```bash
agent-loop run --env prod --org mycompany-prod
```

This will run against your real Salesforce org. Requires `SF_USERNAME`, `SF_PASSWORD`, `SF_SECURITY_TOKEN` set in `.env`.

---

## What You Get After a Run

| File | Contents |
|---|---|
| `generated/<org>/sfdc_raw.json` | Raw Salesforce org config snapshot |
| `generated/<org>/gap_analysis.json` | OSCAL/SBS control findings (pass/fail/partial) |
| `generated/<org>/backlog.json` | Remediation backlog mapped to SSCF controls |
| `generated/<org>/sscf_report.json` | SSCF domain scorecard (0–100% per domain) |
| `generated/<org>/report-app-owner.md` | App owner remediation report (Markdown) |
| `generated/<org>/report-security.md` | Security governance report (Markdown) |
| `generated/<org>/report-security.docx` | Security governance report (DOCX) |
| `generated/<org>/loop_result.json` | Consolidated run metadata |

---

## Tool Reference (Quick)

```bash
sfdc-connect --help        # Salesforce org connector
oscal-assess --help        # SBS control assessor
sscf-benchmark --help      # SSCF domain scorer
report-gen --help          # Governance report generator
agent-loop --help          # Full pipeline orchestrator
```

---

## Next Steps

- [Architecture Overview](Architecture-Overview) — understand the system design
- [Pipeline Walkthrough](Pipeline-Walkthrough) — step-by-step through each stage
- [Running a Dry Run](Running-a-Dry-Run) — full simulation without Salesforce
