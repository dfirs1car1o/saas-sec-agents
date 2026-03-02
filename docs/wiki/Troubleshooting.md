# Troubleshooting

Common errors and their fixes.

---

## `agent-loop: command not found`

```bash
pip install -e .
```
Then verify: `which agent-loop`

---

## `ANTHROPIC_API_KEY not set` or `AuthenticationError`

1. Check `.env` has `ANTHROPIC_API_KEY=sk-ant-...`
2. Verify `load_dotenv` is being called: `harness/loop.py` calls `load_dotenv(_REPO / ".env")` at import time
3. Check the key starts with `sk-ant-` — Anthropic API keys use this prefix
4. Check the key hasn't expired or been revoked at console.anthropic.com

---

## `Salesforce login failed` / `SalesforceAuthenticationFailed`

1. Check `SF_USERNAME`, `SF_PASSWORD`, `SF_SECURITY_TOKEN` are set correctly in `.env`
2. For sandbox orgs: `SF_DOMAIN=test` (not `login`)
3. Security token: append it to your password if your org's IP isn't trusted, or leave blank if it is
4. Try authenticating manually: `sfdc-connect auth --dry-run`

---

## Session memory / Qdrant errors

```
[memory] unavailable: Connection refused
```

**Fix:** Add `QDRANT_IN_MEMORY=1` to `.env`. This uses an in-process Qdrant store — no Docker container needed.

```bash
echo "QDRANT_IN_MEMORY=1" >> .env
```

If you want persistent cross-session memory instead:
```bash
docker run -d -p 6333:6333 qdrant/qdrant
# Then in .env:
QDRANT_IN_MEMORY=0
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## `ModuleNotFoundError: No module named 'skills'`

```bash
pip install -e .
```
The `skills` package requires editable install (`-e`) to be importable.

---

## Output files land in `generated/unknown-org/`

Cause: the `org` parameter wasn't passed to every tool call.

Fix: Use `agent-loop run --org <name>` — the task prompt now includes:
```
IMPORTANT: Pass org='<org>' to every tool call so all outputs land in the same directory.
```

If you're calling CLIs directly, add `--org my-org` to each command.

---

## `max_tokens reached` or loop stops early

The orchestrator hit the `max_tokens=4096` limit on a single response. This is rare but can happen on very verbose tool outputs.

Workaround:
- Retry — the loop will usually recover
- Use `--task` to provide a more focused task prompt with fewer pipeline stages

---

## `Reached max turns (20)` warning

The pipeline ran 20 turns without completing. Most common cause: the orchestrator is waiting for human input it can't get.

Fix: If running dry-run, the task prompt should already include the dry-run bypass instruction. Check `harness/loop.py` task construction for the `dry_gate_note` string.

---

## pytest failures

```
ImportError: cannot import name 'cli' from 'harness.loop'
```

Fix:
```bash
pip install -e . && pip install pytest pytest-mock PyYAML click
```

Note: `[tool.uv]` dev-dependencies in `pyproject.toml` are not installed by plain `pip install`. You must install test dependencies explicitly.

---

## CI: `validate_env` fails on credential checks

This is expected in CI — the environment check job intentionally skips credential checks:
```python
cred_skip = {"SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN", "ANTHROPIC_API_KEY", ...}
```

If non-credential checks fail (e.g., `repo-layout`, `sfdc-connect-module`), run:
```bash
pip install -e .
python3 scripts/validate_env.py --fix
```

---

## CI: `zizmor` flags an unpinned action I just added

Replace the tag reference with a full commit SHA:
```bash
# Find the SHA for a specific tag
gh api repos/<owner>/<repo>/commits/<tag> --jq '.sha'
```

Then update your workflow:
```yaml
uses: owner/action@<full-sha>  # vX.Y.Z
```

---

## CI: `actionlint` fails with SC2016

If you have Go template syntax (`{{$var}}`) in a `run:` block and shellcheck flags it:
```yaml
- name: My step
  run: |
    # shellcheck disable=SC2016
    actionlint -format '{{range $err := .}}...{{end}}'
```

---

## CI: `pip-licenses` flags a new LGPL dependency

1. Check if it's a transitive dep: `pip show <package>`
2. If it's a direct dep you added: either replace it with a non-copyleft alternative, or add to the `lgpl_allowlist` in `ci.yml` with a review comment explaining why it's acceptable

---

## Getting Help

- Run `<command> --help` on any CLI tool
- Read `mission.md` — agent identity and scope constraints
- Read `AGENTS.md` — full routing logic
- Open a GitHub issue for bugs
