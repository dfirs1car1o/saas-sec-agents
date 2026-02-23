# Next Session Checkpoint

## Current State
- Repo: `git@github.com:SiCar10mw/multiagent-azure.git`
- Branch: `main`
- Status: pushed and synced
- Architecture: cloud-first MCP, SIFT image factory scaffold, role-based model/tool policy

## Next Objective (Phase 2)
Set up Azure OIDC and Terraform remote state so CI can run plan/apply workflows.

## Required Inputs From User
1. `AZURE_TENANT_ID`
2. `AZURE_SUBSCRIPTION_ID`
3. Azure region (default `eastus2`)
4. Confirmation of GitHub repo settings access (to add variables/secrets)

## Next Tasks
1. Create Entra app registration for GitHub Actions OIDC.
2. Add federated credentials for repo workflows.
3. Add GitHub repo variables:
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
   - `TF_STATE_RG`
   - `TF_STATE_SA`
   - `TF_STATE_CONTAINER`
   - `TF_STATE_KEY`
4. Run PR to trigger `terraform-plan` and `cloud-mcp-plan`.
5. Review plans and run `terraform-apply` in `dev`.

## Resume Command
```bash
cd /Users/jerijuar/multiagent-azure
git pull
git checkout -b phase-2-azure-oidc
```
