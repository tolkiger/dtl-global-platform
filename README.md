# DTL-Global Platform

Serverless **client onboarding API** for DTL-Global: HubSpot CRM, Stripe billing, website deploy to S3/CloudFront, DNS, notifications (SES), AI (Anthropic), and add-on endpoints (chatbot, Workspace, WhatsApp, collaboration).

**Specifications:** [`DTL_MASTER_PLAN.md`](DTL_MASTER_PLAN.md) is the single source of truth. **Credentials:** [`docs/AUTHENTICATION.md`](docs/AUTHENTICATION.md).

**Production API (example):** `https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod/` — replace with your deployed API Gateway URL after `cdk deploy`.

---

## What this repository is

| Area | Purpose |
|------|---------|
| **`engine/`** | **Lambda deployment bundle** — Python code API Gateway runs (see below). |
| **`cdk/`** | AWS CDK: **four stacks** (Storage, CDN, API, Pipeline) defining DynamoDB, S3, CloudFront, API Gateway + Lambdas, CodePipeline. |
| **`scripts/`** | Local tooling: Phase 0 HubSpot/Stripe, SSM setup/verify, onboarding helpers, integration tests. |
| **`tests/`** | Automated tests for handlers and production scenarios. |
| **`docs/`** | Authentication notes, operations guides, demos. |

---

## What `engine/` is for

**`engine/` is not a separate repo.** It is the **application code** CDK zips into each Lambda (`Code.from_asset` → `engine/`) — **handlers, shared, templates only** (no vendored wheels in git).

- **`engine/handlers/`** — One module per REST route (e.g. `handler_crm_setup.py` → `POST /crm-setup`). Each file defines `lambda_handler`.
- **`engine/shared/`** — Shared libraries: `config` (SSM), `hubspot_client`, `stripe_client`, `ai_client`, `ses_client`, `route53_client`, `s3_client`.
- **`engine/templates/`** — Industry JSON templates used by onboarding/AI flows.
- **Third-party packages (HubSpot SDK, Stripe, Anthropic, requests, …)** live in a **Lambda layer** built from **`cdk/lambda_layer/requirements.txt`**. CI runs `pip install -t cdk/lambda_layer/python` before `cdk deploy` (`buildspec.yml`). That directory is **gitignored**; do not commit built wheels.

**Local CDK / tests:** install the same pins as the layer, then run tests:

```bash
python3 -m pip install -r cdk/lambda_layer/requirements.txt -t cdk/lambda_layer/python   # layer asset for cdk synth/deploy
python3 -m pip install -r requirements.txt   # dev/test (includes pytest, boto3, etc.)
```

If `cdk/lambda_layer/python/` is missing or empty, **`cdk synth` / `cdk deploy` fails** with an error that tells you to run the `pip install` command above (there is no Docker or container bundling in CDK).

**Flow:** Client → **API Gateway** → **Lambda** (`/var/task` = `engine/` code; `/opt/python` = layer) → **`shared/` clients** → HubSpot, Stripe, AWS APIs, Anthropic, etc.

---

## Architecture (summary)

- **Compute:** AWS Lambda (Python 3.12)
- **API:** API Gateway (REST), **16** POST routes
- **Data:** DynamoDB (templates, clients, state)
- **Storage:** S3 (websites, assets, CSV import)
- **CDN:** CloudFront (client sites)
- **DNS / certs:** Route 53, ACM (as used by handlers)
- **Email:** SES (`SES_FROM_EMAIL` in Lambda env; see plan Appendix A)
- **Secrets:** SSM Parameter Store (`/dtl-global-platform/...`)
- **CI/CD:** CodePipeline + CodeBuild (`buildspec.yml`)

---

## Repository layout

```
dtl-global-platform/
├── DTL_MASTER_PLAN.md      # Full specification and phase gates
├── README.md               # This file
├── buildspec.yml           # CodeBuild: CDK deploy
├── cdk/                    # Infrastructure (app.py + stacks/)
├── cdk/lambda_layer/       # requirements.txt for Lambda layer (python/ is build output, gitignored)
├── engine/                 # Lambda function code only (handlers, shared, templates)
├── scripts/                # Setup, onboarding, and test drivers
├── tests/                  # Pytest / handler tests
├── docs/                   # AUTHENTICATION.md and operations guides
├── customer_projects/      # Optional per-customer JSON / notes
└── hubspot/dtl-global-platform-app/   # HubSpot developer app assets
```

---

## Getting started

1. Read **`DTL_MASTER_PLAN.md`** and **`docs/AUTHENTICATION.md`**.
2. Copy **`.env.example`** to **`.env`** for **local scripts only** (never commit secrets).
3. Phase 0 (local): create HubSpot + Stripe test resources and SSM parameters (see plan §7–8).

Example (after venv + `pip install -r scripts/requirements.txt` and loading `.env`):

```bash
python scripts/phase0_hubspot_setup.py && python scripts/phase0_hubspot_verify.py
python scripts/phase0_stripe_setup.py && python scripts/phase0_stripe_verify.py
python scripts/setup_ssm_parameters.py    # interactive; run once per account
python scripts/verify_ssm_parameters.py
```

**Live Stripe catalog (optional, once):** set `DTL_STRIPE_ALLOW_LIVE=1` and `STRIPE_SECRET_KEY` to `sk_live_...` when seeding production products — see plan §7.2.

**Deploy infrastructure:** from `cdk/`, with AWS credentials configured:

```bash
cd cdk && cdk deploy --all
```

---

## Onboarding and testing scripts

| Script | Role |
|--------|------|
| `production_onboarding.py` | Full automated onboarding from project JSON |
| `automated_customer_onboarding.py` | API-driven onboarding flow |
| `onboard_customer.py` | Company-oriented wrapper |
| `efficient_onboarding.py` | Lightweight local / Cursor-friendly flow |
| `test_real_api_business_center.py` | End-to-end API exercise against prod URL (use carefully with live Stripe) |
| `start_customer_onboarding.py` | Starts a customer onboarding flow (see script docstring) |
| `switch_to_production.py` | Production switch helper (see script and AUTHENTICATION.md) |
| `diagnose_api.py` | API diagnostics helper |

---

## Build phases (status)

High-level alignment with `DTL_MASTER_PLAN.md` — see **Current Progress** in the plan for the canonical table.

| Phase | Focus |
|-------|--------|
| 0 | HubSpot + Stripe + SSM |
| 1 | CDK: four stacks |
| 2 | Lambda handlers + `shared/` |
| 3–5 | AI, deploy, add-ons |
| 6 | End-to-end validation |

---

## Tech stack

- **Python** 3.12+
- **IaC:** AWS CDK (Python)
- **CRM / payments:** HubSpot API, Stripe + Connect
- **AI:** Anthropic Claude (Haiku in production paths per plan)
- **Websites:** GitHub → S3 / CloudFront (Rocket.new or customer repos per onboarding data)

---

## Corporate site

**dtl-global.org** is the corporate site; transactional email for this platform uses the SES identity configured in Lambda (see **`SES_FROM_EMAIL`** in `DTL_MASTER_PLAN.md` Appendix A). Do not confuse customer **client** domains with DTL’s own domain.
