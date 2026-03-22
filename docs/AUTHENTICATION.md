# Authentication and MCP setup — DTL-Global Platform

This guide matches **DTL_MASTER_PLAN.md** (bootstrap Section 0.5, Phase 0.5, Appendix C). Use **`.env` locally** (never committed) and **AWS SSM Parameter Store** (`/dtl-global-platform/...`) for Lambdas.

---

## HubSpot — token and hubspotcli MCP

| Topic | Detail |
|--------|--------|
| **Token** | **Private App** or developer-platform **static auth** token — CRM REST API Bearer token. Repo app: `hubspot/dtl-global-platform-app/` (upload → install → **Auth** tab). |
| **Local env** | `HUBSPOT_ACCESS_TOKEN` — see `.env.example`. |

### HubSpot CLI (`@hubspot/cli`)

1. Install: `npm install -g @hubspot/cli`
2. Authenticate: `hs auth` (follow prompts; use a Personal Access Key from HubSpot if needed)
3. Enable MCP for IDE tooling: `hs mcp enable`
4. Restart **Cursor** so it picks up the HubSpot MCP server

Python scripts and Lambdas use the **HubSpot API** with the token above; MCP is for IDE exploration only (`DTL_MASTER_PLAN.md` Section 5).

---

## Stripe — SANDBOX keys, Cursor MCP, production switch

| Topic | Detail |
|--------|--------|
| **Phase 0 scripts** | Use **test mode** secret keys only: `sk_test_...` |
| **Never** | Run setup scripts or store **`sk_live_`** in SSM until you intentionally go live (`DTL_MASTER_PLAN.md` Section 4) |

### Local `.env`

1. [Stripe Dashboard](https://dashboard.stripe.com/) → enable **Test mode**
2. **Developers → API keys** → Secret key (`sk_test_...`) → `STRIPE_SECRET_KEY`
3. **Connect → Settings** → Connect client id → `STRIPE_CONNECT_CLIENT_ID` if used

### Stripe MCP (Cursor native)

1. **Cursor Settings → MCP**
2. Add **Stripe** (native integration)
3. Authenticate with a **TEST** secret key (`sk_test_...`) only

### Switching SANDBOX → production

1. Obtain **`sk_live_...`** from Dashboard (**Live mode** → **Developers → API keys**).
2. Put the live secret in SSM (adjust profile/region as needed):

   ```bash
   aws ssm put-parameter \
     --name "/dtl-global-platform/stripe/secret" \
     --value "sk_live_xxx" \
     --type SecureString \
     --overwrite
   ```

3. Redeploy infrastructure so Lambdas read the updated parameter (e.g. `cdk deploy`).
4. Rotate keys in Stripe and SSM together when you rotate credentials.

---

## Anthropic (Claude)

1. Create an API key at [console.anthropic.com](https://console.anthropic.com/)
2. Local: `ANTHROPIC_API_KEY` in `.env`
3. Production: store under SSM path below; Lambdas resolve via env param reference (`DTL_MASTER_PLAN.md` Section 9.4)

---

## AWS SSM Parameter Store (`/dtl-global-platform/`)

All five parameters are **SecureString**. Use `scripts/setup_ssm_parameters.py` and `scripts/verify_ssm_parameters.py` — do not paste real values into docs or commits.

| Parameter | Purpose |
|-----------|---------|
| `/dtl-global-platform/hubspot/token` | HubSpot Private App / static access token |
| `/dtl-global-platform/stripe/secret` | Stripe secret — **`sk_test_...` until launch**; `sk_live_...` only when going live |
| `/dtl-global-platform/stripe/connect_client_id` | Stripe Connect client ID (`ca_...`) |
| `/dtl-global-platform/anthropic/api_key` | Anthropic API key (`sk-ant-...`) |
| `/dtl-global-platform/github/codestar_connection_arn` | Existing AWS CodeStar Connections ARN for GitHub |

Naming matches the repository name **dtl-global-platform** (`DTL_MASTER_PLAN.md` Appendix C).

---

## GitHub and CodeStar

- **`gh` CLI:** `gh auth login` once; use `gh auth status` to confirm.
- **CodeStar:** Create the GitHub connection in AWS (Developer Tools → **Connections**), then store the connection **ARN** in `/dtl-global-platform/github/codestar_connection_arn` for CodePipeline.

---

## Quick checklist

- [ ] HubSpot: token in `.env`; `hs auth`; `hs mcp enable`; Cursor restarted
- [ ] Stripe: `sk_test_` only for scripts; Stripe MCP in Cursor uses test key
- [ ] Anthropic: key in `.env` for local dev
- [ ] SSM: all five `/dtl-global-platform/...` parameters created (setup script) before production Lambdas
- [ ] GitHub: `gh` authenticated; CodeStar ARN in SSM when using pipelines
