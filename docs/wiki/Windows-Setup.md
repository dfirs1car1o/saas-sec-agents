# Windows Setup — Corporate Machine with VS Code

This guide is written for a corporate Windows machine where:
- VS Code is already installed
- You may **not** have admin rights
- Docker is not available or not allowed
- WSL is not required
- You are running against a real Salesforce org

---

## What You Need

| Tool | Required | Notes |
|---|---|---|
| VS Code | ✅ Already installed | |
| Python 3.11+ | ✅ Must install | User-level install — no admin required |
| Git | ✅ Must install | User-level install — no admin required |
| Docker | ❌ Not needed | `QDRANT_IN_MEMORY=1` replaces it |
| WSL | ❌ Not needed | Pipeline is pure Python |
| Node.js | ❌ Not needed | |
| Claude Code CLI | ❌ Not needed | Only `ANTHROPIC_API_KEY` is required |

---

## Step 1 — Install Python 3.11+

1. Go to **https://www.python.org/downloads/windows/**
2. Download the latest **Python 3.11.x** (or 3.12.x) **Windows installer (64-bit)**
3. Run the installer:
   - ✅ Check **"Add python.exe to PATH"** at the bottom of the first screen
   - Click **"Install Now"** (user-level install — no admin needed)

Verify in VS Code's terminal:
```powershell
python --version
# Python 3.11.x
```

> **Corporate proxy note:** If your machine routes through a corporate proxy, Python installer usually works without configuration. If not, ask IT for the proxy address — you'll need it for Step 4.

---

## Step 2 — Install Git

1. Go to **https://git-scm.com/download/win**
2. Download and run the installer — default options are fine
3. VS Code will automatically detect Git after installation

Verify:
```powershell
git --version
# git version 2.x.x
```

> **Alternative:** If Git is already on your machine (check with `git --version` first), skip this step.

---

## Step 3 — Clone the Repo in VS Code

1. Open VS Code
2. Press **Ctrl+Shift+P** → type **"Git: Clone"** → Enter
3. Paste the repo URL:
   ```
   https://github.com/dfirs1car1o/saas-sec-agents.git
   ```
4. Choose a folder (e.g., `C:\Users\YourName\Projects\`)
5. VS Code will ask **"Open cloned repository?"** — click **Yes**

---

## Step 4 — Open the Integrated Terminal

In VS Code: **Terminal → New Terminal** (or **Ctrl+`**)

This opens a PowerShell terminal at the repo root. All commands below run here.

> **Tip:** If you see `PS C:\Users\YourName\Projects\saas-sec-agents>` you're in the right place.

---

## Step 5 — Install Python Dependencies

```powershell
pip install -e .
pip install pytest pytest-mock PyYAML click
```

This installs all pipeline tools (`sfdc-connect`, `oscal-assess`, `sscf-benchmark`, `report-gen`, `agent-loop`) as runnable commands.

Verify:
```powershell
agent-loop --help
sfdc-connect --help
```

> **Corporate proxy — pip can't reach the internet?**
> ```powershell
> pip install -e . --proxy http://your-proxy-server:port
> ```
> Ask your IT department for the proxy address and port if needed.

---

## Step 6 — Create Your `.env` File

In VS Code's Explorer panel (left sidebar), right-click `.env.example` → **Copy**, then right-click the root folder → **Paste**, then rename the copy to `.env`.

Or in the terminal:
```powershell
copy .env.example .env
```

Now open `.env` in VS Code and fill in your values:

```ini
# ── Anthropic (required for agent-loop) ──────────────────────
ANTHROPIC_API_KEY=sk-ant-...

# ── Salesforce org credentials ────────────────────────────────
SF_USERNAME=your.name@yourcompany.com
SF_PASSWORD=YourSalesforcePassword
SF_SECURITY_TOKEN=YourSecurityToken
SF_DOMAIN=test           # "test" for sandbox orgs (recommended starting point); use "login" for production
SF_INSTANCE_URL=https://yourorg--sandbox.sandbox.my.salesforce.com

# ── Session memory (no Docker needed) ─────────────────────────
QDRANT_IN_MEMORY=1
```

> **Where to get these values:**
> - `ANTHROPIC_API_KEY` — from https://console.anthropic.com → API Keys
> - `SF_USERNAME` / `SF_PASSWORD` — your Salesforce sandbox login credentials (same as production unless your admin set a separate sandbox user)
> - `SF_SECURITY_TOKEN` — in Salesforce sandbox: **Settings → My Personal Information → Reset My Security Token** (token is emailed to you). Leave blank if your org uses trusted IP ranges. Note: sandbox and production have separate security tokens.
> - `SF_DOMAIN` — use `test` for sandbox (default), `login` for production
> - `SF_INSTANCE_URL` — the URL you use to log into the **sandbox** (e.g., `https://yourorg--dev.sandbox.my.salesforce.com`). Find it by logging into the sandbox and copying the browser URL.

> **Security:** `.env` is in `.gitignore` — it will never be committed to Git. Never share it or paste it anywhere.

---

## Step 7 — Verify Your Environment

```powershell
python scripts\validate_env.py
```

Expected output:
```
  PASS  [python] Python 3.11.x
  PASS  [git] git version 2.x.x
  PASS  [.env] .env file exists
  PASS  [ANTHROPIC_API_KEY] Anthropic API key — set (sk-a****)
  PASS  [SF_USERNAME] Salesforce username — set (your*****)
  PASS  [qdrant] QDRANT_IN_MEMORY=1 — in-process Qdrant, no Docker container needed
  PASS  [sfdc-connect-module] sfdc-connect --help OK

  ENVIRONMENT READY.
```

---

## Step 8 — Test with a Dry Run (No Real Salesforce Connection)

Before running against your real org, verify the full pipeline works:

```powershell
agent-loop run --dry-run --env dev --org test-org
```

Expected:
```
agent-loop [DRY-RUN]: org=test-org env=dev
  [tool] sfdc_connect_collect(...)
  [tool] oscal_assess_assess(...)
  [tool] oscal_gap_map(...)
  [tool] sscf_benchmark_benchmark(...)
  [tool] report_gen_generate(...)  ← app-owner report
  [tool] report_gen_generate(...)  ← GIS report

============================================================
Assessment complete (5 turn(s))
overall_score : 34.8%
critical_fails: 4
============================================================
```

Reports are written to:
```
docs\oscal-salesforce-poc\generated\test-org\
```

Open these in VS Code to review the output before running live.

---

## Step 9 — Run Against Your Real Salesforce Org

```powershell
agent-loop run --env prod --org your-org-name
```

Replace `your-org-name` with any label you want (used for output folder naming).

For a **sandbox**:
```powershell
agent-loop run --env dev --org your-org-sandbox
```

> **Critical findings gate:** If the pipeline finds `status=fail AND severity=critical` findings, it will stop and ask for review. To approve and continue:
> ```powershell
> agent-loop run --env prod --org your-org-name --approve-critical
> ```

---

## Output Files

After a live run, open the reports directly in VS Code:

```
docs\oscal-salesforce-poc\generated\your-org-name\
  ├── sfdc_raw.json           ← raw Salesforce config snapshot
  ├── gap_analysis.json       ← control findings (pass/fail/partial)
  ├── backlog.json            ← remediation backlog
  ├── sscf_report.json        ← SSCF domain scorecard
  ├── report_app_owner.md     ← app owner remediation report
  ├── report_gis.md           ← CorpIS governance report (Markdown)
  ├── report_gis.docx         ← CorpIS governance report (Word)
  └── loop_result.json        ← run metadata
```

The `.docx` file can be opened directly in Microsoft Word. The `.md` files render in VS Code with **Ctrl+Shift+V**.

---

## VS Code Recommended Extensions

Install these from the Extensions panel (**Ctrl+Shift+X**):

| Extension | Publisher | Why |
|---|---|---|
| Python | Microsoft | Syntax highlighting, linting, IntelliSense |
| Pylance | Microsoft | Type checking, autocomplete |
| Markdown Preview Enhanced | Yiyi Wang | Preview `.md` reports in VS Code |
| GitLens | GitKraken | Better git history and blame |

---

## Troubleshooting on Windows

### `agent-loop: command not found` / `not recognized`

```powershell
pip install -e .
# Then close and reopen the VS Code terminal
```

If still not found, run it as a module:
```powershell
python -m harness.loop run --dry-run --env dev --org test-org
```

### `python: command not found`

Python wasn't added to PATH during install. Fix:
1. Uninstall Python via **Settings → Apps**
2. Re-run the installer and check **"Add python.exe to PATH"**

Or find Python manually:
```powershell
where python
# C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe
```

### pip install fails with SSL or proxy error

```powershell
# With corporate proxy
pip install -e . --proxy http://proxy.yourcompany.com:8080

# With self-signed corporate cert (if SSL errors)
pip install -e . --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

Ask IT for your proxy address if unsure.

### Salesforce login fails

- Double-check `SF_DOMAIN=login` for production, `SF_DOMAIN=test` for sandbox
- Security token: reset it at **Salesforce → Settings → Reset My Security Token**
- If your company uses SSO to log into Salesforce, you may need a **connected app API user** with username/password auth — ask your Salesforce admin

### PowerShell execution policy error

```powershell
# If you see "running scripts is disabled on this system"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Path separator issues (backslash vs forward slash)

The pipeline uses Python's `pathlib` internally, which handles Windows paths correctly. If you see path errors in output, report as a bug.

---

## What the Pipeline Does NOT Touch on Your Machine

- No registry changes
- No system files
- No network configuration
- No Salesforce data is written — **read-only** against your org
- All output stays inside the `docs\oscal-salesforce-poc\generated\` folder
- The only outbound connections are:
  - `api.anthropic.com` (LLM calls using your API key)
  - Your Salesforce org's REST/Tooling API endpoints
