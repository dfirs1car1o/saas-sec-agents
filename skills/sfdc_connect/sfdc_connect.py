"""
sfdc-connect — Salesforce org configuration collector for OSCAL/SBS/SSCF assessment.

Read-only. Never writes to any Salesforce org. Credentials sourced from environment only.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from typing import Any

import click
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

REQUIRED_ENV = ("SF_USERNAME", "SF_PASSWORD", "SF_SECURITY_TOKEN")


def _check_env() -> None:
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if missing:
        click.echo(
            f"ERROR: Missing required env vars: {', '.join(missing)}\nCopy .env.example to .env and fill in values.",
            err=True,
        )
        sys.exit(1)


def _connect() -> Any:
    """Return an authenticated Salesforce client (read-only use only)."""
    try:
        from simple_salesforce import Salesforce
    except ImportError:
        click.echo("ERROR: simple-salesforce not installed. Run: uv pip install simple-salesforce", err=True)
        sys.exit(1)

    _check_env()
    return Salesforce(
        username=os.environ["SF_USERNAME"],
        password=os.environ["SF_PASSWORD"],
        security_token=os.environ.get("SF_SECURITY_TOKEN", ""),
        domain=os.environ.get("SF_DOMAIN", "login"),
        instance_url=os.environ.get("SF_INSTANCE_URL") or None,
    )


def _result_envelope(org: str, env: str, scope: str, data: Any) -> dict:
    return {
        "org": org,
        "env": env,
        "collected_at_utc": datetime.now(UTC).isoformat(),
        "scope": scope,
        "raw": data,
    }


def _write_output(result: dict, out: str | None) -> None:
    payload = json.dumps(result, indent=2, default=str)
    if out:
        with open(out, "w") as f:
            f.write(payload)
        click.echo(f"Wrote {len(result.get('raw', {}))} items → {out}")
    else:
        click.echo(payload)


# ---------------------------------------------------------------------------
# Scope collectors
# ---------------------------------------------------------------------------


def collect_auth(sf: Any) -> dict:
    """Auth: SSO, MFA, login IP ranges, session settings."""
    data: dict[str, Any] = {}

    # Session settings via Tooling API (not available via standard SOQL)
    try:
        tooling_result = sf.restful(
            "tooling/query",
            params={
                "q": "SELECT SessionTimeout, RequireHttps, ForceLogoutOnSessionTimeout,"
                " LockSessionsToDomain FROM SecuritySettings LIMIT 1"
            },
        )
        data["session_settings"] = tooling_result
    except Exception as exc:
        data["session_settings"] = {"error": str(exc), "note": "Requires Tooling API access"}

    # MFA enforcement via Tooling API (Identity Verification setting)
    try:
        mfa_result = sf.restful(
            "tooling/query",
            params={
                "q": "SELECT MultiFactorAuthenticationForUserUI, MultiFactorAuthenticationForUserUIBlock"
                " FROM OrganizationSettings LIMIT 1"
            },
        )
        data["mfa_org_settings"] = mfa_result
    except Exception as exc:
        data["mfa_org_settings"] = {"error": str(exc), "note": "OrganizationSettings MFA fields require API v57+"}

    # Identity providers (SSO config)
    try:
        data["sso_providers"] = sf.query_all("SELECT Id, Name, SamlVersion, IsEnabled FROM SamlSsoConfig")
    except Exception:
        data["sso_providers"] = {"totalSize": 0, "records": []}

    # Login IP ranges (trusted IPs)
    try:
        data["login_ip_ranges"] = sf.query_all("SELECT Id, ProfileId, StartAddress, EndAddress FROM LoginIpRange")
    except Exception:
        data["login_ip_ranges"] = {"totalSize": 0, "records": []}

    # MFA: check if MFA is enforced via connected app or org setting
    try:
        data["mfa_policies"] = sf.query_all(
            "SELECT Id, DeveloperName, IsEnabled FROM TransactionSecurityPolicy WHERE ActionConfig LIKE '%TwoFactor%'"
        )
    except Exception:
        data["mfa_policies"] = {"totalSize": 0, "records": []}

    return data


def collect_access(sf: Any) -> dict:
    """Access: profiles with system admin, permission sets, connected apps."""
    data: dict[str, Any] = {}

    # Profiles with system admin or modify all data
    data["admin_profiles"] = sf.query_all(
        "SELECT Id, Name, PermissionsModifyAllData, PermissionsManageUsers, "
        "PermissionsViewAllData FROM Profile WHERE PermissionsModifyAllData = true "
        "OR PermissionsManageUsers = true ORDER BY Name"
    )

    # Permission sets with elevated permissions
    data["elevated_permission_sets"] = sf.query_all(
        "SELECT Id, Name, Label, PermissionsModifyAllData, PermissionsViewAllData, "
        "PermissionsManageUsers FROM PermissionSet WHERE PermissionsModifyAllData = true "
        "OR PermissionsManageUsers = true ORDER BY Name"
    )

    # Connected apps (OAuth clients)
    data["connected_apps"] = sf.query_all(
        "SELECT Id, Name, OptionsAllowAdminApprovedUsersOnly, OptionsRefreshTokenValidityMetric "
        "FROM ConnectedApplication ORDER BY Name"
    )

    return data


def collect_event_monitoring(sf: Any) -> dict:
    """Event Monitoring: storage, enabled event types."""
    data: dict[str, Any] = {}

    # Event log file types available (indicates what monitoring is enabled)
    data["event_log_types"] = sf.query_all(
        "SELECT EventType, LogDate, LogFileLength FROM EventLogFile "
        "WHERE LogDate = LAST_N_DAYS:7 GROUP BY EventType, LogDate, LogFileLength"
    )

    # Check field audit trail / field history (metadata count as proxy)
    try:
        data["field_history_retention"] = sf.query_all(
            "SELECT Id, EntityDefinition.QualifiedApiName FROM FieldDefinition "
            "WHERE IsAiPredictionField = false AND IsHistoryTracked = true LIMIT 100"
        )
    except Exception:
        data["field_history_retention"] = {"totalSize": 0, "records": []}

    return data


def collect_transaction_security(sf: Any) -> dict:
    """Transaction Security Policies (automated threat response rules)."""
    return {
        "policies": sf.query_all(
            "SELECT Id, DeveloperName, ResourceName, EventName, IsEnabled, "
            "ExecutionUserId, BlockMessage FROM TransactionSecurityPolicy ORDER BY EventName"
        )
    }


def collect_integrations(sf: Any) -> dict:
    """Named credentials and remote site settings (outbound integration points)."""
    data: dict[str, Any] = {}

    data["named_credentials"] = sf.query_all(
        "SELECT Id, DeveloperName, Endpoint, AuthenticationProtocol FROM NamedCredential ORDER BY DeveloperName"
    )

    data["remote_site_settings"] = sf.query_all(
        "SELECT Id, SiteName, EndpointUrl, IsActive, DisableProtocolSecurity FROM RemoteProxy ORDER BY SiteName"
    )

    return data


def collect_oauth(sf: Any) -> dict:
    """OAuth policies on connected apps."""
    return {
        "connected_app_oauth_policies": sf.query_all(
            "SELECT Id, Name, OptionsAllowAdminApprovedUsersOnly, PermittedUsersPolicyEnum, "
            "RefreshTokenPolicyEnum FROM ConnectedApplication ORDER BY Name"
        )
    }


def collect_secconf(sf: Any) -> dict:
    """Security health check baseline score."""
    try:
        data = sf.query_all("SELECT Score, LastModifiedDate FROM SecurityHealthCheck LIMIT 1")
    except Exception:
        data = {"note": "SecurityHealthCheck not available via SOQL — check Setup > Security Health Check in UI"}
    return {"health_check": data}


SCOPE_COLLECTORS = {
    "auth": collect_auth,
    "access": collect_access,
    "event-monitoring": collect_event_monitoring,
    "transaction-security": collect_transaction_security,
    "integrations": collect_integrations,
    "oauth": collect_oauth,
    "secconf": collect_secconf,
}

VALID_SCOPES = list(SCOPE_COLLECTORS.keys()) + ["all"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """sfdc-connect — read-only Salesforce org config collector for security assessment."""


@cli.command()
@click.option("--org", default=None, help="Org alias or instance URL (overrides SF_INSTANCE_URL in .env)")
@click.option("--scope", required=True, type=click.Choice(VALID_SCOPES, case_sensitive=False), help="What to collect")
@click.option("--out", default=None, help="Output JSON file path (default: stdout)")
@click.option("--env", default="dev", type=click.Choice(["dev", "test", "prod"]), help="Environment label")
@click.option("--timeout", default=60, help="API timeout in seconds")
@click.option("--dry-run", is_flag=True, help="Print what would be collected without calling API")
def collect(org: str | None, scope: str, out: str | None, env: str, timeout: int, dry_run: bool) -> None:
    """Collect security-relevant configuration from a Salesforce org."""
    org_label = org or os.getenv("SFDC_ORG_ALIAS", os.getenv("SF_INSTANCE_URL", "unknown"))

    if dry_run:
        scopes_to_run = list(SCOPE_COLLECTORS.keys()) if scope == "all" else [scope]
        click.echo(f"DRY RUN — would collect: {scopes_to_run} from org: {org_label}")
        click.echo(f"Output: {out or 'stdout'}")
        return

    sf = _connect()
    if org:
        # Override instance URL if explicit org URL provided
        sf.sf_instance = org.replace("https://", "").rstrip("/")

    scopes_to_run = list(SCOPE_COLLECTORS.keys()) if scope == "all" else [scope]
    combined: dict[str, Any] = {}

    for s in scopes_to_run:
        click.echo(f"  collecting: {s}", err=True)
        try:
            combined[s] = SCOPE_COLLECTORS[s](sf)
        except Exception as exc:
            combined[s] = {"error": str(exc)}
            click.echo(f"  WARNING: {s} failed — {exc}", err=True)

    result = _result_envelope(org_label, env, scope, combined)
    _write_output(result, out)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Skip actual connection, just validate env vars are set")
def auth(dry_run: bool) -> None:
    """Test authentication to the Salesforce org."""
    if dry_run:
        missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
        if missing:
            click.echo(f"FAIL — missing env vars: {', '.join(missing)}", err=True)
            sys.exit(1)
        click.echo("OK — all required env vars set (dry-run, no connection made)")
        return

    sf = _connect()
    org_info = sf.query_all("SELECT Id, Name, OrganizationType FROM Organization LIMIT 1")
    if org_info["totalSize"] == 1:
        rec = org_info["records"][0]
        click.echo(f"OK — connected to: {rec['Name']} ({rec['OrganizationType']}) id={rec['Id']}")
    else:
        click.echo("WARN — connected but could not retrieve org info")


@cli.command("org-info")
@click.option("--out", default=None, help="Output JSON file path (default: stdout)")
def org_info(out: str | None) -> None:
    """Retrieve basic org metadata (name, edition, features, limits)."""
    sf = _connect()

    data: dict[str, Any] = {}
    data["organization"] = sf.query_all(
        "SELECT Id, Name, OrganizationType, InstanceName, IsSandbox, "
        "LanguageLocaleKey, TimeZoneSidKey, UsedLicenses FROM Organization LIMIT 1"
    )
    data["limits"] = sf.limits()

    result = _result_envelope(
        org=os.getenv("SF_INSTANCE_URL", "unknown"),
        env="dev",
        scope="org-info",
        data=data,
    )
    _write_output(result, out)


if __name__ == "__main__":
    cli()
