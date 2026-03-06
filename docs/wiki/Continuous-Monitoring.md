# Continuous Monitoring with OpenSearch

Run saas-sec-agents on a cadence, push results to OpenSearch, and watch remediation progress in a dashboard over time.

---

## Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- `.env` file populated with platform credentials

---

## Quick Start

```bash
# 1. Start OpenSearch + Dashboards
docker compose up -d

# 2. Wait ~60s for dashboards to be ready, then visit
open http://localhost:5601

# 3. Run an assessment (Workday dry-run, no real credentials needed)
docker compose run --rm agent \
  python scripts/workday_dry_run_demo.py --org acme-workday --env dev

# 4. Export results to OpenSearch
docker compose run --rm agent \
  python scripts/export_to_opensearch.py --auto --org acme-workday --date 2026-03-06

# 5. Refresh http://localhost:5601 — data appears in Discover
```

---

## Running a Live Assessment

```bash
# Salesforce
docker compose run --rm agent \
  agent-loop run --env dev --org cyber-coach-dev --approve-critical

# Workday (real tenant)
docker compose run --rm agent \
  agent-loop run --platform workday --env dev --org acme --approve-critical
```

Reports land in `./docs/oscal-salesforce-poc/generated/<org>/<date>/` on your host machine (volume-mounted).

---

## Exporting Results

### Auto-discover (easiest)
```bash
python scripts/export_to_opensearch.py --auto --org <org-alias> --date <YYYY-MM-DD>
```

### Explicit paths
```bash
python scripts/export_to_opensearch.py \
  --backlog docs/oscal-salesforce-poc/generated/acme-workday/2026-03-06/workday_backlog.json \
  --sscf    docs/oscal-salesforce-poc/generated/acme-workday/2026-03-06/workday_sscf_report.json \
  --nist    docs/oscal-salesforce-poc/generated/acme-workday/2026-03-06/workday_nist_review.json
```

---

## Indexes

| Index | One doc per | Key fields |
|-------|------------|------------|
| `sscf-runs-YYYY-MM` | Assessment run | org, platform, overall_score, overall_status, nist_verdict, domain scores |
| `sscf-findings-YYYY-MM` | Finding per run | control_id, domain, severity, status, owner, due_date, poam_status |

Monthly indexes keep data volumes manageable. Search across all time with `sscf-runs-*` and `sscf-findings-*`.

---

## Building Dashboards

On first run, two index patterns are auto-imported: `sscf-runs-*` and `sscf-findings-*`.

To build visualizations in OpenSearch Dashboards:

1. Go to `http://localhost:5601 → Visualize → Create visualization`
2. Recommended charts:

| Chart | Index | Config |
|-------|-------|--------|
| Pie — pass/fail/partial breakdown | `sscf-findings-*` | Terms agg on `status` |
| Bar — findings by severity | `sscf-findings-*` | Terms agg on `severity` |
| Line — overall score over time | `sscf-runs-*` | Date histogram on `generated_at_utc`, avg of `overall_score` |
| Bar — domain scores per run | `sscf-runs-*` | Nested agg on `domains.domain` + avg `domains.score` |
| Table — open POA&M items | `sscf-findings-*` | Filter `poam_status:Open OR "In Progress"`, table with control_id, severity, due_date |
| Metric — total open items | `sscf-findings-*` | Count, filter `poam_status:Open` |

3. Once built, export via `Stack Management → Saved Objects → Export` to update `config/opensearch/dashboards.ndjson`

---

## Continuous Monitoring on a Schedule

### GitHub Actions (weekly)
Uncomment `.github/workflows/scheduled-assessment.yml` and set secrets:
- `SF_CONSUMER_KEY` / `SF_PRIVATE_KEY` (Salesforce)
- `WD_CLIENT_ID` / `WD_CLIENT_SECRET` (Workday)
- `OPENSEARCH_URL` (point at your hosted OpenSearch instance)

### Local cron
```bash
# Run every Monday at 8am
0 8 * * 1 cd /path/to/saas-sec-agents && \
  docker compose run --rm agent \
    agent-loop run --platform workday --org acme --approve-critical && \
  docker compose run --rm agent \
    python scripts/export_to_opensearch.py --auto --org acme \
    --date $(date +%Y-%m-%d)
```

---

## Stopping the Stack

```bash
docker compose down          # stop containers, keep data
docker compose down -v       # stop containers AND delete OpenSearch data
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `opensearch-py not installed` | `pip install opensearch-py` or rebuild agent image |
| Dashboard shows no data | Check index exists: `curl http://localhost:9200/_cat/indices` |
| `dashboard-init` exits with error | Dashboards not ready yet — re-run: `docker compose restart dashboard-init` |
| Port 9200 already in use | Change `ports` in compose or stop conflicting service |
| Apple Silicon (M-series) OOM | Reduce `OPENSEARCH_JAVA_OPTS` to `-Xms256m -Xmx256m` in compose |
