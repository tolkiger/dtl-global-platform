# Authentication and MCP setup — DTL-Global Platform

This document describes how to configure authentication for local development, MCP tooling, and production. Secrets belong in **`.env` locally** (never committed) and **AWS SSM Parameter Store** for Lambda (`DTL_MASTER_PLAN.md`).

---

## 1. HubSpot

### Private App / static token

DTL uses HubSpot CRM APIs with a **Bearer token** from your HubSpot app (developer platform project with static auth in `hubspot/dtl-global-platform-app/`, or a **Private App** token if you use that path for REST access). See that app’s **Auth** tab after install, or **Settings → Integrations → Private Apps** if using a private app.

1. Create or open the app and ensure required CRM scopes are granted.
2. Copy the **access token** (Private App token or static auth token).
3. Set locally: `HUBSPOT_ACCESS_TOKEN=<token>` in `.env` (see `.env.example`).

### HubSpot CLI and MCP (hubspotcli)

1. **Install** the HubSpot CLI globally:  
   `npm install -g @hubspot/cli`
2. **Authenticate:**  
   `hs auth`  
   Follow the prompts to link your HubSpot account (or use account-specific auth per [HubSpot CLI docs](https://developers.hubspot.com/docs/api/developer-tools-overview)).
3. **Enable MCP:**  
   `hs mcp enable`  
   This exposes HubSpot MCP for local tooling.
4. **Cursor:** Restart Cursor after enabling MCP so it can detect the HubSpot MCP server.

---

## 2. Stripe (SANDBOX / TEST first)

Use **test mode** keys only (`sk_test_...`) until you intentionally move to production.

### API keys (local scripts)

1. Open [Stripe Dashboard](https://dashboard.stripe.com/) → **Developers → API keys**.
2. Ensure **Test mode** is on.
3. Reveal the **Secret key** (`sk_test_...`) and set `STRIPE_SECRET_KEY` in `.env`.
4. For Connect, set `STRIPE_CONNECT_CLIENT_ID` from **Connect → Settings** when applicable.

### Stripe MCP (Cursor native)

1. Open **Cursor Settings → MCP**.
2. **Add Stripe** (native integration).
3. Authenticate using your **TEST** secret key (`sk_test_...`).

### Switching to production

1. Obtain **`sk_live_`** keys from Stripe Dashboard (**Live mode** → **Developers → API keys**).
2. Store the live secret in SSM (example — adjust profile/region as needed):

   ```bash
   aws ssm put-parameter --name "/dtl/stripe/secret" --value "sk_live_xxx" --type SecureString --overwrite
   ```

3. **Redeploy** application stacks so Lambdas pick up the updated parameter (e.g. `cdk deploy` for your CDK app).
4. Rotate keys carefully; update SSM and redeploy whenever keys change.

---

## 3. Anthropic (Claude)

1. Open [Anthropic Console](https://console.anthropic.com/).
2. Create an API key under your account.
3. Set `ANTHROPIC_API_KEY` in `.env` for local use, and store the same value in SSM for production Lambdas (see parameters below).

---

## 4. AWS SSM Parameter Store

These parameters hold secrets and configuration for serverless workloads. **Do not commit values.** Use `scripts/setup_ssm_parameters.py` and `scripts/verify_ssm_parameters.py` to manage and check them.

| Parameter name | Purpose |
|----------------|---------|
| `/dtl/hubspot/token` | HubSpot CRM Bearer token |
| `/dtl/stripe/secret` | Stripe secret key (**must be `sk_test_` until production**; then `sk_live_` when approved) |
| `/dtl/stripe/connect_client_id` | Stripe Connect client identifier |
| `/dtl/anthropic/api_key` | Anthropic API key |
| `/dtl/github/codestar_connection_arn` | AWS CodeStar Connections ARN for GitHub |

---

## 5. GitHub

- **`gh` CLI:** Install and run `gh auth login` once so `gh` is authenticated for issues, PRs, and projects.
- **CodeStar connection:** The GitHub ↔ AWS connection ARN is stored at `/dtl/github/codestar_connection_arn` in SSM for pipelines (create the connection in AWS Console → Developer Tools → Connections, then save the ARN in SSM).

---

## Quick checklist

- [ ] HubSpot: token in `.env`; CLI installed; `hs auth`; `hs mcp enable`; Cursor restarted
- [ ] Stripe: `sk_test_` in `.env`; Stripe MCP in Cursor with test key
- [ ] Anthropic: API key from console
- [ ] SSM: all five parameters set (use setup script) before production Lambdas rely on them
- [ ] GitHub: `gh` authenticated; CodeStar ARN in SSM when using CodePipeline
