# DTL-Global Platform

AI-powered client onboarding platform for DTL-Global technology consulting.

**Official website domain:** [dtl-global.org](https://dtl-global.org). Transactional email uses `onboarding@dtl-global.org` (see `DTL_MASTER_PLAN.md` Appendix A).

## Overview

This platform automates the process of onboarding small and medium business clients with:
- Professional websites (built with Rocket.new, deployed to AWS)
- HubSpot CRM (customized per industry)
- Stripe payment processing (via Stripe Connect)
- Custom email (Google Workspace or Microsoft 365)
- AI-powered features (chatbots, bid generation, SEO optimization)

## Architecture

100% serverless on AWS:
- **Compute:** Lambda (Python 3.12)
- **API:** API Gateway (REST)
- **Database:** DynamoDB
- **Storage:** S3
- **CDN:** CloudFront
- **DNS:** Route 53
- **Email:** SES
- **CI/CD:** CodePipeline + CodeBuild
- **IaC:** AWS CDK (Python)

## Project Structure

```
dtl-global-platform/
├── DTL_MASTER_PLAN.md    # Single source of truth for the entire build
├── scripts/              # Setup and utility scripts
├── cdk/                  # AWS CDK infrastructure
├── engine/               # Lambda function source code
│   ├── shared/           # Shared modules (API wrappers, config)
│   ├── handlers/         # Lambda handlers (one per endpoint)
│   └── templates/        # Industry templates (JSON)
└── tests/                # Test files
```

## Getting Started

1. Read DTL_MASTER_PLAN.md — it contains the complete specification
2. Read **[docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)** — current HubSpot, Stripe, and Anthropic credential setup
3. Copy `.env.example` to `.env` and fill in your API keys
4. Follow the phases in order (Phase 0 through Phase 6)

### Phase 0 — HubSpot & Stripe (local scripts)

**HubSpot:** use the **developer platform 2025.2** project in **`hubspot/dtl-global-platform-app/`** (CLI upload + install → copy static token). Not legacy apps. **Stripe:** test secret key. Details: [docs/AUTHENTICATION.md](docs/AUTHENTICATION.md).

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt
set -a && source .env && set +a      # load env vars (bash/zsh)
python scripts/phase0_hubspot_setup.py && python scripts/phase0_hubspot_verify.py
python scripts/phase0_stripe_setup.py && python scripts/phase0_stripe_verify.py
```

Gate: both verify scripts print `RESULT: ALL CHECKS PASSED`. See DTL_MASTER_PLAN.md Section 7.5.

## Build Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Bootstrap | Project setup, rules, skills | Complete |
| 0 | HubSpot and Stripe setup | Ready (run scripts above) |
| 1 | CDK infrastructure | Not started |
| 2 | Lambda functions | Not started |
| 3 | AI layer | Not started |
| 4 | Website deployment | Not started |
| 5 | Add-on modules | Not started |
| 6 | End-to-end testing | Not started |

## Tech Stack

- **Language:** Python 3.12+
- **IaC:** AWS CDK
- **AI (production):** Claude Haiku 4.5 (Anthropic direct API)
- **AI (development):** Claude Sonnet 4 (Cursor)
- **CRM:** HubSpot API
- **Payments:** Stripe + Stripe Connect
- **Websites:** Rocket.new, GitHub, S3/CloudFront