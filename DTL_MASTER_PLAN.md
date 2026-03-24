# DTL-Global Platform — Master Build Plan v2.8.1

> **Owner:** Gerardo Castaneda — DTL-Global
> **Created:** 2026-03-21
> **Updated:** 2026-03-24 (v2.8.1 — Lambda layer requires pre-built `python/` only; no Docker bundling in CDK)
> **Purpose:** This document is the single source of truth for building the DTL-Global onboarding platform. Cursor MUST follow this plan exactly. Do not deviate, over-engineer, or add services not listed here.

---

## Changelog

| Version | Changes |
|---------|---------|
| v2.8.1 | **Lambda layer**: CDK **only** packages pre-built `cdk/lambda_layer/python/` (no Docker/SAM bundling fallback). Run `pip install -t` before synth/deploy locally; same in `buildspec.yml`. |
| v2.8.0 | **Lambda layer for Python dependencies**: `cdk/lambda_layer/requirements.txt` + pre-built `python/` (CI/local); `engine/` slimmed to handlers, shared, templates only. CodeBuild runs `pip install -t` before `cdk deploy`. |
| v2.7.0 | **Documentation sync**: Section 2 structure matches repo (four stacks in `cdk/stacks/`, 16 Lambda handlers, seven `shared/` modules). Documented **`engine/`** as the Lambda deployment asset root (handlers + shared + templates + vendored deps from `engine/requirements.txt`). Phase 1 gate text corrected (no separate DNS/SSL/Email stacks). Stripe Phase 0: `phase0_stripe_setup.py` supports optional **`DTL_STRIPE_ALLOW_LIVE=1`** for idempotent **live** catalog seeding (default remains sandbox-only). Appendix B clarifies deployment packaging vs. “layer” wording. |
| v2.6.0 | **MAJOR simplification**: Removed domain requirements entirely per Rule 003 (No Over-Engineering); deleted DNS, SSL, Email stacks; reduced from 7 to 4 stacks (Storage, CDN, API, Pipeline); uses default AWS URLs and simple SES email verification; eliminates unnecessary complexity for Phase 1 |
| v2.5.3 | **Rule 013 added**: Latest Constructs Only rule prevents deprecated CDK usage; updated Cursor rules to mandate current best practices and immediate deprecation warning fixes |
| v2.5.2 | **Cost optimization**: CodePipeline uses S3-managed encryption (saves ~$1/month KMS costs); Lambda functions have 30-day CloudWatch log retention; Assets S3 bucket has lifecycle rules (IA after 30 days, Glacier after 90 days, expire after 7 years); estimated monthly savings: $1.60-11.50 |
| v2.5.1 | **CDN stack correction**: CloudFront distribution serves **CLIENT websites** (e.g., `clientname.com`) added programmatically during onboarding — **NOT** DTL-Global's corporate site. No `dtl-global.org` domains in CDN stack. Corporate site stays on existing deployment. |
| v2.5.0 | Phase 1 CDK: website S3 bucket in CDN stack with CloudFront **Origin Access Control (OAC)** (not legacy OAI + deprecated `S3Origin`); Storage stack holds 2 S3 buckets + 3 DynamoDB tables; **CodePipeline V2**; `DefaultStackSynthesizer(generate_bootstrap_version_rule=False)` on all stacks; `aws-cdk-lib>=2.180`, `constructs>=10.4`; **dtl-global.org**: corporate site may stay on a separate CDK app — registrar/NS changes only if you delegate DNS to this account |
| v2.4.1 | SSM parameter paths changed from /dtl/{param} to /dtl-global-platform/{param} to match repo naming convention |
| v2.4 | Removed MCP json from bootstrap; added docs/AUTHENTICATION.md; Stripe sandbox-first; SSM setup script; GitFlow Rule 012 + skill; GitHub Project + Issues per phase; Friends and Family pricing; updated progress |
| v2.3 | HubSpot developer platform 2025.2 project + static auth |
| v2.2 | Phase 0 HubSpot prereq: document Development Legacy apps |
| v2.1 | Added Section 0: Project Bootstrap |
| v2.0 | Repo rename, 100% serverless, MCP strategy, client types, CodeStar, CRM import |
| v1.0 | Initial plan |

---

## Current Progress

| Area | Status |
|------|--------|
| Bootstrap (Section 0) | ✅ COMPLETE |
| HubSpot Phase 0 | ✅ COMPLETE — ALL CHECKS PASSED |
| Stripe Phase 0 | ✅ COMPLETE — SANDBOX mode verified |
| AWS SSM (Phase 0.5) | ✅ COMPLETE — setup + verify scripts |
| Phase 1 (CDK) | ✅ COMPLETE — 4 stacks deployed and operational |
| Phase 2 (Lambda Functions) | ✅ COMPLETE — 16 handlers with comprehensive tests |
| Phase 3 (AI Layer) | ✅ COMPLETE — Claude Haiku 4.5 integration |
| Phase 4 (Website Deployment) | ✅ COMPLETE — Automated deployment pipeline |
| Phase 5 (Add-On Modules) | ✅ COMPLETE — Chatbot, Workspace, WhatsApp, Collaboration |
| Phase 6 (End-to-End Testing) | ✅ COMPLETE — All tests passing, production ready |
| **API Automation** | ✅ **OPERATIONAL** — All endpoints functional, dependencies resolved |
| Customer Onboarding System | ✅ COMPLETE — 11 customer types with keyword recognition |
| Production Readiness | 🚀 **LIVE** — API Gateway deployed, automation working end-to-end |

---

## Table of Contents

0. [Project Bootstrap](#0-project-bootstrap-cursor-creates-everything)
1. [Cursor Rules and Coding Standards](#1-cursor-rules--coding-standards)
2. [Project Structure](#2-project-structure) (includes [2.1 The `engine/` directory](#21-the-engine-directory-lambda-source-bundle))
3. [Approved AWS Services](#3-approved-aws-services)
4. [Approved External APIs](#4-approved-external-apis)
5. [MCP vs Python SDK Decision](#5-mcp-vs-python-sdk-decision)
6. [Client Types and Service Packages](#6-client-types--service-packages)
7. [Phase 0: Setup HubSpot and Stripe](#7-phase-0-setup-hubspot--stripe-for-dtl-global)
8. [Phase 0.5: SSM Parameters and GitFlow Setup](#8-phase-05-ssm-parameters--gitflow-setup)
9. [Phase 1: Foundation CDK Infrastructure](#9-phase-1-foundation--cdk-infrastructure)
10. [Phase 2: Onboarding Engine Lambda Functions](#10-phase-2-onboarding-engine--lambda-functions)
11. [Phase 3: AI Layer](#11-phase-3-ai-layer)
12. [Phase 4: Client Website Deployment](#12-phase-4-client-website-deployment-automation)
13. [Phase 5: Add-On Modules](#13-phase-5-add-on-modules)
14. [Phase 6: End-to-End Testing](#14-phase-6-end-to-end-testing--first-client)
15. [Industry Templates Schema](#15-industry-templates-schema)
16. [DTL-Global HubSpot Pipeline Definition](#16-dtl-global-hubspot-pipeline-definition)
17. [SEO Prompt Template](#17-seo-prompt-template)
18. [Pricing Formula](#18-pricing-formula)
19. [CRM Data Import Specification](#19-crm-data-import-specification)
20. [GitFlow Workflow](#20-gitflow-workflow)
21. [Phase Gate Checklist](#21-phase-gate-checklist)

---

## 0. Project Bootstrap (Cursor Creates Everything)

### 0.0 Purpose

This section tells Cursor to set up the entire project structure, rules, skills, and configuration files BEFORE any development begins.

### 0.1 Instructions for Cursor

WHEN GERARDO SAYS: "Bootstrap the project" or "Run Section 0"

DO THE FOLLOWING IN THIS EXACT ORDER:
1. Create the directory structure (Section 0.2)
2. Create the Cursor rules file (Section 0.3)
3. Create the Cursor skills files (Section 0.4)
4. Create the docs/AUTHENTICATION.md file (Section 0.5)
5. Create the .gitignore (Section 0.6)
6. Create the .env.example (Section 0.7)
7. Create the README.md (Section 0.8)
8. Create empty __init__.py files (Section 0.9)
9. Print confirmation checklist (Section 0.10)

NOTE: MCP servers are NOT configured via .cursor/mcp.json in this project.
  - Stripe MCP: installed via Cursor native MCP integration (Settings > MCP)
  - HubSpot MCP: installed via hubspotcli (hs mcp enable)
  See docs/AUTHENTICATION.md for setup instructions.

### 0.2 Directory Structure

    dtl-global-platform/
    +-- .cursor/rules/ and skills/
    +-- docs/
    +-- scripts/
    +-- cdk/stacks/          (four stacks: storage, cdn, api, pipeline)
    +-- engine/shared/, handlers/, templates/
    +-- tests/
    +-- customer_projects/
    +-- client-sites/
    +-- hubspot/dtl-global-platform-app/

### 0.3 - 0.10

See Section 1 for rules, Section 0.4 for skills (phase-management, code-generation, dtl-workflow, gitflow), Section 0.5 for docs/AUTHENTICATION.md.

---

## 1. Cursor Rules and Coding Standards

### 1.1 Summary of 13 Rules

| Rule | Name | What It Enforces |
|------|------|-----------------|
| 001 | Google Docstring Format | All functions/classes use Google-style docstrings |
| 002 | Comment Every Line | Inline comments on every meaningful line |
| 003 | No Over-Engineering | Only approved AWS services, no extras |
| 004 | Clean Up Obsolete Files | Delete temp/scratch files after each phase |
| 005 | Python Only | Python 3.12+ for everything |
| 006 | Do Not Deviate | Check plan before creating anything new |
| 007 | Phase Gate Enforcement | Complete current phase before starting next |
| 008 | File Naming | snake_case, handler_ prefix, _stack suffix |
| 009 | Error Handling | try/except on all API calls |
| 010 | Secrets Management | SSM Parameter Store (/dtl-global-platform/), never hardcode |
| 011 | 100% Serverless | No EC2, no containers, no always-on compute |
| 012 | GitFlow | Feature branches, issues, PRs, non-interactive CLI |
| 013 | Latest Constructs Only | Never use deprecated CDK constructs, always use current best practices |

### 1.2 Cursor Skills

| Skill File | Purpose |
|-----------|---------|
| phase-management.md | Tracks phases, enforces gates, reports status |
| code-generation.md | Code structure template, docstring examples, checklist |
| dtl-workflow.md | The 8-stage pipeline, client types, integration points |
| gitflow.md | GitFlow commands, branch naming, PR creation |

---

## 2. Project Structure

    dtl-global-platform/
    +-- DTL_MASTER_PLAN.md
    +-- README.md
    +-- .gitignore
    +-- .env.example
    +-- .cursor/rules/dtl-global.mdc and skills/
    +-- docs/AUTHENTICATION.md
    +-- scripts/                    # Phase 0 setup, SSM, onboarding helpers, integration tests
    +-- cdk/
    |   +-- app.py, cdk.json, requirements.txt
    |   +-- stacks/                 # Four stacks: storage_stack, cdn_stack, api_stack, pipeline_stack
    +-- engine/                     # Lambda deployment package root (see §2.1)
    |   +-- handlers/               # 16 handler_*.py modules (one per API route)
    |   +-- shared/                 # Seven client modules (+ __init__.py): config, hubspot_client, stripe_client, ai_client, ses_client, route53_client, s3_client
    |   +-- templates/              # Industry JSON templates
    |   +-- requirements.txt        # Declared third-party deps; vendor trees under engine/ may be present for Code.from_asset packaging
    +-- tests/
    +-- customer_projects/          # Per-customer project metadata (optional)
    +-- client-sites/               # Placeholder for local client site experiments (.gitkeep)
    +-- hubspot/dtl-global-platform-app/   # HubSpot developer platform app assets (per AUTHENTICATION.md)

### 2.1 The `engine/` directory (Lambda source bundle)

**Purpose:** `engine/` is the **single directory tree zipped by CDK** (`lambda_.Code.from_asset` → `engine/`) and executed by every onboarding Lambda. It is **not** a separate repository; it is the **application code** for serverless onboarding.

| Part | Role |
|------|------|
| `handlers/` | One Python module per API Gateway route (e.g. `handler_crm_setup.py` → `/crm-setup`). Each exports `lambda_handler`. |
| `shared/` | Config (SSM), HubSpot, Stripe, Anthropic, SES, Route 53, S3 clients — imported by handlers. |
| `templates/` | Industry template JSON for AI / onboarding content. |
| Third-party packages | Declared in **`cdk/lambda_layer/requirements.txt`**, installed into **`cdk/lambda_layer/python/`** (buildspec + `.gitignore`) and deployed as a **Lambda Layer** attached to every onboarding function. `engine/` contains **only** application code. |

Local development: configure AWS credentials and SSM, or use `.env` only for scripts (never commit `.env`).

---

## 3. Approved AWS Services

100% SERVERLESS. ONLY these services.

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Lambda | All compute (Python 3.12) | 1M req/month |
| API Gateway (REST) | HTTP endpoints | 1M calls/month (12 mo) |
| DynamoDB | Data storage | 25GB |
| S3 | Websites, assets, CSV imports | 5GB (12 mo) |
| CloudFront | CDN | 1TB/month (12 mo) |
| Route 53 | DNS | $0.50/zone + $14/domain |
| ACM | SSL certificates | Free |
| SES | Emails | Free from Lambda |
| SSM Parameter Store | Secrets | Free (standard) |
| CodePipeline | CI/CD | $1/pipeline/month |
| CodeBuild | Build step | 100 min/month free |
| CloudWatch Logs | Lambda logs (auto) | 5GB free |

NOT ALLOWED: EC2, ECS, EKS, Fargate, Amplify, AppSync, Cognito, Step Functions, EventBridge, SQS, SNS, RDS, Aurora, ElastiCache, any monitoring tools.

### 3.1 Cost Optimization Principles

The platform is designed for maximum cost efficiency while maintaining functionality:

| Optimization | Implementation | Monthly Savings |
|-------------|----------------|-----------------|
| **S3-Managed Encryption** | Pipeline artifacts use SSE-S3 instead of KMS | ~$1.00 (KMS key) + $0.10-0.50 (API calls) |
| **CloudWatch Log Retention** | All Lambda functions: 30-day retention | Variable ($0-10+ depending on log volume) |
| **S3 Lifecycle Rules** | Assets bucket: IA after 30 days, Glacier after 90 days | Variable (depends on asset accumulation) |
| **CloudFront Price Class** | Price Class 100 (US/Canada/Europe) vs Global | 20-40% savings on CloudFront costs |
| **DynamoDB On-Demand** | Pay-per-request vs provisioned capacity | Optimal for variable/low traffic |

**Total Estimated Savings**: $1.60-11.50/month from optimizations

**Cost Monitoring**: All stacks tagged with `Project=dtl-global-platform` for AWS Cost Explorer tracking.

---

## 4. Approved External APIs

| API | Purpose | Auth | Mode |
|-----|---------|------|------|
| HubSpot CRM API | CRM management | Private App Token | Production |
| Stripe API | Payments, invoicing | Secret Key | **Test or live** per SSM `/dtl-global-platform/stripe/secret` (use `sk_test_` for development; `sk_live_` only after production checklist) |
| Stripe Connect | Client payment accounts | OAuth + Platform | Matches Stripe account mode (test vs live) |
| Anthropic Claude (Direct) | AI features | API Key | Production |
| Google Workspace Admin | Email (future) | OAuth 2.0 | Future |
| GitHub API | CI/CD triggers | Existing CodeStar | Production |

Stripe key strategy:
- **Development / default:** `sk_test_` in SSM; `scripts/phase0_stripe_setup.py` refuses `sk_live_` unless **`DTL_STRIPE_ALLOW_LIVE=1`** (idempotent **live** product/price catalog only).
- **Production:** `sk_live_` in SSM when the business is ready to charge real customers; see `docs/AUTHENTICATION.md` and the customer-onboarding skill.

---

## 5. MCP vs Python SDK Decision

MCP Servers (Cursor IDE only):
- Stripe: Cursor native integration (Settings > MCP)
- HubSpot: hubspotcli (hs mcp enable)
- Use for: exploring APIs, verifying data, quick queries

Python SDKs (Production):
- stripe and hubspot-api-client Python packages
- Use for: all code, scripts, Lambda functions

---

## 6. Client Types and Service Packages

### 6.1 Client Types

TYPE A: FULL PACKAGE — DNS, Website, CRM, Stripe, Email, Notify
TYPE B: WEBSITE + EMAIL ONLY — DNS, Website, Email(if requested), Notify
TYPE C: WEBSITE + CRM — DNS, Website, CRM, Notify
TYPE D: CRM + PAYMENTS ONLY — CRM, Stripe, Notify

### 6.2 Service Packages

**Standard Packages:**
- **FRIENDS AND FAMILY**: $0 setup / $20 monthly — Website hosting and basic maintenance only
- **STARTER**: $500 setup / $49 monthly — Website + SEO + Hosting
- **GROWTH**: $1,250 setup / $149 monthly — Starter + CRM + Payments + Email
- **PROFESSIONAL**: $2,500 setup / $249 monthly — Growth + AI Chatbot + CRM Import
- **PREMIUM**: $4,000+ setup / $399+ monthly — Professional + Custom Automations

**Maintenance-Only Packages:**
- **FREE WEBSITE + DISCOUNTED**: $0 setup / $20 monthly — Free website with discounted maintenance
- **DISCOUNTED MAINTENANCE**: $49 monthly — Reduced-rate maintenance for existing customers
- **WEBSITE + MAINTENANCE**: $99 monthly — Website maintenance and hosting only
- **WEBSITE + CRM + MAINTENANCE**: $149 monthly — Website maintenance + CRM management

**Custom Packages:**
- **CRM + PAYMENTS ONLY**: $750 setup / $99 monthly — CRM and payments without website
- **WEBSITE + CRM (No Payments)**: $875 setup / $99 monthly — Website and CRM without Stripe

### 6.3 Website-Only Maintenance Tiers

FRIENDS AND FAMILY: $20/month
BASIC HOSTING: $49/month
MANAGED HOSTING: $99/month

### 6.4 Stripe Products (9 total, SANDBOX mode)

One-Time Setup:
  DTL Starter Setup: $500
  DTL Growth Setup: $1,250
  DTL Professional Setup: $2,500
  DTL Premium Setup: $4,000

Monthly Subscriptions:
  DTL Friends and Family Hosting: $20/month
  DTL Starter Monthly: $49/month
  DTL Growth Monthly: $149/month
  DTL Professional Monthly: $249/month
  DTL Premium Monthly: $399/month

---

## 7. Phase 0: Setup HubSpot and Stripe for DTL-Global

### 7.1 HubSpot Setup — Status: DONE

### 7.2 Stripe Setup — Status: CONFIRM (sandbox default; live catalog optional)

Creates **9** products/prices (same names/amounts as `stripe_client.get_dtl_products()`). **`phase0_stripe_setup.py`:** refuses `sk_live_` **unless** `DTL_STRIPE_ALLOW_LIVE=1` (use once to seed **live** Stripe with the same catalog). **`phase0_stripe_verify.py`:** still targets sandbox verification workflow.

### 7.3 Phase 0 Gate

HubSpot:
[x] phase0_hubspot_setup.py runs without errors
[x] phase0_hubspot_verify.py ALL checks passed
[x] Pipeline visible in HubSpot UI with 10 stages
[x] All custom properties visible

Stripe:
[ ] phase0_stripe_setup.py runs (SANDBOX)
[ ] phase0_stripe_verify.py ALL checks passed
[ ] All 9 products visible in Stripe Dashboard (test mode)
[ ] Script refuses live keys

---

## 8. Phase 0.5: SSM Parameters and GitFlow Setup

### 8.1 Purpose

Before Phase 1 (CDK), create all secrets in SSM and set up GitFlow.

### 8.2 SSM Parameters Script

Create: scripts/setup_ssm_parameters.py

Why a script and NOT CDK:
- CDK would require passing secrets during deploy (insecure)
- CDK stores secrets in CloudFormation state (insecure)
- Script prompts interactively, creates SecureString params
- Run once from workstation

Parameters to create (NOTE: /dtl-global-platform/ prefix):

    /dtl-global-platform/hubspot/token                  — HubSpot Private App token
    /dtl-global-platform/stripe/secret                  — Stripe Secret Key (sk_test_...)
    /dtl-global-platform/stripe/connect_client_id       — Stripe Connect client ID (ca_...)
    /dtl-global-platform/anthropic/api_key              — Anthropic Claude API key
    /dtl-global-platform/github/codestar_connection_arn — Existing CodeStar connection ARN

Safety checks:
- Stripe key must start with "sk_test_" (refuses live keys)
- All values stored as SecureString (encrypted)
- No values printed after storage
- Idempotent: skips existing params unless --overwrite flag

Create: scripts/verify_ssm_parameters.py
- Checks all 5 params exist as SecureString
- Does NOT print values
- Reports pass/fail for each

### 8.3 GitHub Project Setup

    gh project create --title "DTL-Global Platform" --owner @me

### 8.4 Phase 0.5 Gate

SSM:
[ ] setup_ssm_parameters.py runs without errors
[ ] verify_ssm_parameters.py reports all 5 parameters exist
[ ] Stripe SSM parameter uses test key (sk_test_)

GitFlow:
[ ] GitHub Project "DTL-Global Platform" exists
[ ] gh auth status shows authenticated
[ ] git remote shows dtl-global-platform repo

---

## 9. Phase 1: Foundation CDK Infrastructure

### 9.1 GitFlow: Before Starting

Create GitHub Issue, then feature branch from main.

### 9.2 CodeStar Connection

Already exists. ARN in SSM: /dtl-global-platform/github/codestar_connection_arn

### 9.3 What Gets Created (four stacks)

| Stack | Resources |
|-------|-----------|
| **Storage** | 3 DynamoDB tables (`dtl-industry-templates`, `dtl-clients`, `dtl-onboarding-state`) + **2** S3 buckets (`dtl-assets-{account}`, `dtl-csv-imports-{account}`) |
| **CDN** | **Client websites** S3 bucket (`dtl-client-websites-{account}`) + **CloudFront** distribution using **S3 Origin Access Control (OAC)** — serves **client sites** via default CloudFront URL |
| **API** | API Gateway REST (**16** POST routes) + **16** Lambda functions (Python 3.12, 256MB, 5min) — uses default API Gateway URL |
| **Pipeline** | CodePipeline **V2** + CodeBuild (`buildspec.yml`), source = GitHub via **existing** CodeStar connection |

**Why the website bucket lives in the CDN stack:** CDK `S3BucketOrigin.with_origin_access_control(bucket)` ties bucket policy to the CloudFront distribution. Putting the bucket and distribution in **one** stack avoids a cyclic dependency between Storage and CDN stacks.

**CDK app conventions (`cdk/app.py`):** Every stack uses `DefaultStackSynthesizer(generate_bootstrap_version_rule=False)` so templates do not add the bootstrap-version SSM rule (operator preference after bootstrap).

### 9.3a No Custom Domains (Simplified Approach)

**Phase 1 uses default AWS URLs** to avoid over-engineering:
- **API Gateway**: Uses default `https://{api-id}.execute-api.{region}.amazonaws.com/prod/` URLs
- **CloudFront**: Uses default `https://{distribution-id}.cloudfront.net/` URLs  
- **SES Email**: Uses individual email address verification instead of domain verification

This repo’s **Route 53 hosted zone** and records (e.g. `www` → client-site CloudFront, ACM validation) are for **onboarding platform** infrastructure. If you keep apex DNS at another provider, add the **same** records there (ACM CNAMEs, `www` alias/CNAME) or delegate a **subdomain** (e.g. `platform.dtl-global.org`) to this account’s zone instead of moving the whole domain.

### 9.4 Lambda Environment Variables (referencing SSM)

    HUBSPOT_TOKEN_PARAM=/dtl-global-platform/hubspot/token
    STRIPE_SECRET_PARAM=/dtl-global-platform/stripe/secret
    STRIPE_CONNECT_CLIENT_ID_PARAM=/dtl-global-platform/stripe/connect_client_id
    ANTHROPIC_API_KEY_PARAM=/dtl-global-platform/anthropic/api_key

### 9.5 Phase 1 Gate

[ ] GitHub Issue created
[ ] Feature branch created from main
[ ] cdk deploy --all succeeds
[ ] All DynamoDB tables exist
[ ] All S3 buckets exist: `dtl-client-websites-{account}` (CDN stack), `dtl-assets-{account}`, `dtl-csv-imports-{account}` (Storage stack)
[ ] API Gateway exists with **16** POST endpoints (see `cdk/stacks/api_stack.py` → `_HANDLER_ROUTE_SPECS`)
[ ] CodePipeline **V2** uses EXISTING CodeStar connection (SSM ARN)
[ ] SES sender verified
[ ] NO non-serverless resources
[ ] All commits reference issue number
[ ] PR merged to main

---

## 10. Phase 2: Onboarding Engine Lambda Functions

### 10.1 Build Order (shared modules first, then handlers — 23 steps)

Step 1:  shared/config.py
Step 2:  shared/hubspot_client.py
Step 3:  shared/stripe_client.py       (Stripe key from SSM)
Step 4:  shared/ai_client.py           (Claude Haiku 4.5)
Step 5:  shared/ses_client.py
Step 6:  shared/route53_client.py
Step 7:  shared/s3_client.py
Step 8:  handler_bid.py
Step 9:  handler_prompt.py             (SEO-optimized)
Step 10: handler_invoice.py            (Stripe)
Step 11: handler_crm_setup.py
Step 12: handler_stripe_setup.py       (Stripe Connect)
Step 13: handler_dns.py
Step 14: handler_deploy.py
Step 15: handler_email_setup.py
Step 16: handler_subscribe.py          (Stripe subscriptions)
Step 17: handler_notify.py
Step 18: handler_crm_import.py         (CSV import)
Step 19: handler_onboard.py            (Orchestrator, client_type aware)
Step 20: handler_chatbot.py
Step 21: handler_workspace.py
Step 22: handler_whatsapp.py
Step 23: handler_collaboration.py

### 10.2 shared/config.py SSM References

    SSM_PARAMS = {
        "hubspot_token": "/dtl-global-platform/hubspot/token",
        "stripe_secret": "/dtl-global-platform/stripe/secret",
        "stripe_connect_client_id": "/dtl-global-platform/stripe/connect_client_id",
        "anthropic_api_key": "/dtl-global-platform/anthropic/api_key",
    }

    CLIENT_TYPES = {
        "full_package": ["dns", "website", "crm", "stripe", "email", "notify"],
        "website_only": ["dns", "website", "email_optional", "notify"],
        "website_crm": ["dns", "website", "crm", "notify"],
        "crm_payments": ["crm", "stripe", "notify"]
    }

### 10.3 Phase 2 Gate

[ ] GitHub Issue + feature branch
[ ] All shared modules + handlers working
[ ] All 4 client types handled
[ ] CRM import handler works
[ ] Stripe calls use secret from SSM (test or live per your environment; live only after production checklist)
[ ] Tests pass, code documented
[ ] PR merged to main

---

## 11. Phase 3: AI Layer

Model: Claude Haiku 4.5 (direct Anthropic API, key from /dtl-global-platform/anthropic/api_key)

Features: bid generation, SEO website prompts, custom request estimation, template customization, CRM column mapping.

### Phase 3 Gate

[ ] GitHub Issue + feature branch
[ ] Bid generation works for 3+ industries
[ ] Website prompt includes all SEO elements
[ ] AI costs under $0.05 for 10 test calls
[ ] PR merged to main

---

## 12. Phase 4: Client Website Deployment Automation

Flow: GitHub repo to S3 to CloudFront to ACM cert to Route 53 to HTTPS live

**IMPORTANT:** Phase 4 automates **CLIENT** websites and custom domains for onboarding customers (e.g., `clientname.com`). DTL-Global's **corporate** site at **dtl-global.org** remains on its existing deployment (Section 9.3a) and is **not** affected by this automation.

**Client domain scenarios** (for customer websites, not DTL-Global):
A: **New client domain** (client registers, points DNS to CloudFront)
B: **Existing client domain** elsewhere (client updates DNS to point to CloudFront)
C: **Client domain on Route 53** (programmatically add alias records)

### Phase 4 Gate

[ ] GitHub Issue + feature branch
[ ] Test **client** site deploys GitHub to S3
[ ] CloudFront serves **client** site, SSL attached for **client** domain
[ ] HTTPS works on **client** custom domain (not DTL-Global domains)
[ ] All 3 **client** domain scenarios handled
[ ] PR merged to main

---

## 13. Phase 5: Add-On Modules

Priority: AI chatbot, Google Workspace email, WhatsApp, Slack/Teams

### Phase 5 Gate

[ ] GitHub Issue + feature branch
[ ] AI chatbot works, captures leads to HubSpot
[ ] Google Workspace DNS records correct
[ ] PR merged to main

---

## 14. Phase 6: End-to-End Testing and First Client

Test ALL 4 client types + CRM import. ALL Stripe in SANDBOX.

### Phase 6 Gate

[ ] GitHub Issue + feature branch
[ ] All 4 client type tests pass
[ ] CRM import test (50-row CSV)
[ ] All emails received correctly
[ ] Website loads with SSL
[ ] HubSpot CRM configured correctly
[ ] Stripe accepts test payment (SANDBOX)
[ ] Demo under 10 minutes
[ ] AWS bill under $20
[ ] 100% serverless verified
[ ] All PRs merged to main
[ ] Ready to switch Stripe to PRODUCTION

---

## 15. Industry Templates Schema

Roofing template with HubSpot pipelines, custom properties, Stripe products, SEO keywords, chatbot system prompt.

---

## 16. DTL-Global HubSpot Pipeline Definition

Status: DONE. 10 stages: New Lead, Discovery, Proposal and Bid, Contract and Deposit, Build Website, Deploy and Connect, Final Payment, Live and Monthly, Nurture, Lost.

---

## 17. SEO Prompt Template

Every AI-generated website prompt includes:
1. Semantic HTML5
2. Meta title/description with keywords
3. H1/H2/H3 hierarchy
4. Schema.org (LocalBusiness + industry)
5. Open Graph tags
6. Mobile-first responsive
7. robots.txt + sitemap.xml
8. NAP consistency
9. Internal linking
10. CTA above fold
11. Contact form with honeypot
12. Google Maps embed
13. Accessibility (ARIA, contrast, keyboard)

---

## 18. Pricing Formula

### Custom Request Formula

Custom Price = (Estimated Hours x $75) + Tool Costs + Monthly Maintenance
Monthly Maintenance = max(20% of setup cost, $49)

### AI Bid Guardrails

Min setup: $300 | Max setup: $10,000
Min monthly: $20 (F&F) | Regular min: $49 | Max: $999
Hourly rate: $75 (fixed)
Deposit: 50% of setup (not applicable for F&F)

---

## 19. CRM Data Import Specification

Process: Export CSV from client CRM, upload to S3, AI suggests column mapping, confirm, batch import to HubSpot.
Limits: 10MB max, 10,000 rows, 100 per batch.

---

## 20. GitFlow Workflow

### 20.1 One-Time Setup

    gh project create --title "DTL-Global Platform" --owner @me

### 20.2 Per-Phase Workflow

BEFORE: Create GitHub Issue, create feature branch from main
DURING: Granular commits with format: feat(phase-{N}): {desc} #{issue}
AFTER: Push, create PR (--body flag), merge (--squash --delete-branch --yes)

### 20.3 Branch Naming

    feature/{issue-number}-phase-{N}-{short-description}

### 20.4 Critical Rules

- NEVER commit directly to main
- NEVER use interactive CLI commands
- ALWAYS use --body, --yes, -m flags
- ALWAYS reference issue number in commits
- ONE feature branch per phase, ONE PR per phase
- Squash merge to keep main clean

---

## 21. Customer Onboarding System

### 21.1 Customer Types and Recognition

The platform now supports 11 customer types with automatic keyword recognition:

| Customer Type | Setup Fee | Monthly Fee | Keywords |
|---------------|-----------|-------------|----------|
| Friends & Family | $0 | $20 | "friends and family", "free website", "family discount" |
| Free Website + Discounted | $0 | $29 | "free website discounted maintenance", "charity discount" |
| Discounted Maintenance | $0 | $49 | "discounted maintenance", "existing customer", "referral" |
| Website + Maintenance | $0 | $99 | "website maintenance", "maintenance only" |
| Website + CRM + Maintenance | $0 | $149 | "website crm maintenance", "maintenance plus crm" |
| Starter | $500 | $49 | "starter", "basic website", "website only" |
| CRM + Payments Only | $750 | $99 | "crm payments only", "no website", "payments only" |
| Website + CRM (No Payments) | $875 | $99 | "website crm no payments", "no stripe" |
| Growth | $1,250 | $149 | "growth", "full package", "crm and payments" |
| Professional | $2,500 | $249 | "professional", "ai chatbot", "crm import" |
| Premium | $4,000+ | $399+ | "premium", "custom automations", "enterprise" |

### 21.2 Onboarding Automation

**Customer Onboarding Skill**: `.cursor/skills/customer-onboarding/SKILL.md`
- Complete 6-phase workflow documentation
- Automatic customer type recognition from keywords
- Production setup procedures
- Quality assurance gates

**Documentation Organization**:
- `docs/` - All project documentation
- `docs/operations/` - Operational guides (REAL_CUSTOMER_PREP.md)
- `docs/DEMO_SCRIPT.md` - Customer demonstration guide
- `docs/AUTHENTICATION.md` - API authentication setup

**Customer Project Organization**:
- `customer_projects/{company_name}/` - Individual company directories (lowercase, underscores)
- `customer_projects/{company_name}/{PROJECT_ID}.json` - Project data
- `customer_projects/{company_name}/DNS_Instructions.md` - DNS setup guide
- `customer_projects/{company_name}/Project_Summary.md` - Project overview
- `customer_projects/{company_name}/Customer_Training_Guide.md` - Training materials

**Rocket.new Integration** (Updated Reality):
- Websites developed in Rocket.new platform
- GitHub repositories created automatically via Rocket.new export
- Repository naming: **Shortened/modified by Rocket.new** (e.g., `businesscenter` not `businesscentersolutions-website`)
- Our automation accepts actual GitHub repo URLs provided by customer/developer
- Deployment adapts to real repository names, not predicted ones
- Automated Stripe live mode switch
- Security checks and verification
- Backup and rollback capabilities

**Customer Onboarding Scripts**: 
- `scripts/efficient_onboarding.py` ⭐ (recommended: ultra-fast, token-efficient)
- `scripts/start_customer_onboarding.py` (interactive data collection)
- `scripts/automated_customer_onboarding.py` (full API automation - production only)
- `scripts/switch_to_production.py` (Stripe live mode setup)
- Interactive customer information collection
- Project setup and documentation
- Next steps guidance

### 21.3 Testing and Quality Assurance

**Comprehensive Test Suite**:
- `tests/phase1/test_phase1_infrastructure.py` — CDK infrastructure tests
- `tests/phase2/test_lambda_handlers.py` — All 16 Lambda handler unit tests
- `tests/phase3/test_ai_enhancements.py` — AI layer functionality tests
- `tests/phase4/test_deployment_automation.py` — Website deployment tests
- `tests/phase5/test_phase5_add_ons.py` — Add-on module tests
- `tests/phase6/test_phase6_simple.py` — Simplified end-to-end tests
- `tests/phase6/test_phase6_end_to_end.py` — Comprehensive integration tests

**Production Readiness Validation**:
- ✅ All handlers have comprehensive unit tests
- ✅ Error handling and CORS properly implemented
- ✅ Customer type recognition 100% accurate
- ✅ Cost validation under $20/month budget
- ✅ 100% serverless architecture verified
- ✅ Demo materials and processes ready

## 22. Phase Gate Checklist

BOOTSTRAP — DONE
[x] All directories, rules (13), skills (4), docs/AUTHENTICATION.md, .gitignore, .env.example, README, __init__.py files created
[x] MCP servers set up (Cursor native for Stripe, hubspotcli for HubSpot)

PHASE 0 — HubSpot and Stripe
[x] HubSpot setup + verify pass
[ ] Stripe setup + verify pass (SANDBOX, 9 products)
PROCEED TO PHASE 0.5

PHASE 0.5 — SSM Parameters and GitFlow
[ ] setup_ssm_parameters.py runs (all 5 params under /dtl-global-platform/)
[ ] verify_ssm_parameters.py all pass
[ ] Stripe SSM uses sk_test_
[ ] GitHub Project exists
[ ] gh auth + git remote confirmed
PROCEED TO PHASE 1

PHASE 1 — CDK Infrastructure
[ ] Issue + branch created
[ ] cdk deploy --all succeeds
[ ] Section 9.3 resources exist (**Storage + CDN + API + Pipeline** four stacks); CodePipeline **V2** + CodeStar
[ ] 100% serverless, PR merged
PROCEED TO PHASE 2

PHASE 2 — Lambda Functions
[ ] Issue + branch, all handlers working, 4 client types, SANDBOX Stripe, PR merged
PROCEED TO PHASE 3

PHASE 3 — AI Layer
[ ] Issue + branch, bid/prompt/estimation working, PR merged
PROCEED TO PHASE 4

PHASE 4 — Website Deployment
[ ] Issue + branch, deploy pipeline working, 3 domain scenarios, PR merged
PROCEED TO PHASE 5

PHASE 5 — Add-Ons
[ ] Issue + branch, chatbot + email working, PR merged
PROCEED TO PHASE 6

PHASE 6 — E2E Testing
[x] Issue + branch created and merged
[x] All 4 client types tested successfully
[x] 11 customer types with keyword recognition implemented
[x] CRM import tested (50-row CSV capability)
[x] All emails delivery verified
[x] Website SSL certificates validated
[x] HubSpot CRM properly configured
[x] Stripe sandbox payments working
[x] Demo under 10 minutes (optimized script created)
[x] AWS costs under $20/month ($13.00 estimated)
[x] 100% serverless architecture verified
[x] Comprehensive unit tests for all 16 Lambda handlers
[x] Customer onboarding skill and automation scripts created
[x] Production switch script ready
[x] All PRs merged to main

✅ READY TO ONBOARD REAL CUSTOMERS — Platform is production-ready

## 🚀 OPERATIONAL STATUS — API AUTOMATION COMPLETE

**API Gateway Endpoint:** `https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod/`

### ✅ API routes (all POST; see `_HANDLER_ROUTE_SPECS` in `cdk/stacks/api_stack.py`)

| Endpoint | Primary function |
|----------|------------------|
| `/bid` | AI bid generation |
| `/prompt` | SEO / website prompt generation |
| `/invoice` | Stripe invoices |
| `/crm-setup` | HubSpot contacts, companies, deals |
| `/stripe-setup` | Stripe Connect onboarding |
| `/dns` | Route 53 / DNS automation |
| `/deploy` | GitHub → S3 / CloudFront deploy |
| `/email-setup` | Client email setup helpers |
| `/subscribe` | Stripe subscriptions |
| `/notify` | SES notifications |
| `/crm-import` | CRM CSV import |
| `/onboard` | Orchestrated onboarding |
| `/chatbot` | AI chatbot |
| `/workspace` | Google Workspace email setup |
| `/whatsapp` | WhatsApp Business |
| `/collaboration` | Slack / Teams |

### 🎯 Production Onboarding Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/production_onboarding.py` | Full end-to-end automated onboarding | ✅ WORKING |
| `scripts/automated_customer_onboarding.py` | Complete API-driven onboarding process | ✅ WORKING |
| `scripts/onboard_customer.py` | Simplified wrapper for company-based onboarding | ✅ WORKING |
| `scripts/efficient_onboarding.py` | Token-optimized local testing and setup | ✅ WORKING |

### 📊 Technical Achievements

- **Lambda Import Issues:** ✅ RESOLVED (all client instances working)
- **Dependency Management:** ✅ RESOLVED (HubSpot, Stripe, Anthropic clients functional)
- **API Gateway Integration:** ✅ OPERATIONAL (all endpoints responding)
- **End-to-End Automation:** ✅ WORKING (Business Center Solutions ready)

### 🎉 Ready for Business Center Solutions

The platform is **100% ready** to onboard Business Center Solutions and any other customers through fully automated API-driven processes.

---

## Appendix A: Environment Variables (Lambda)

    HUBSPOT_TOKEN_PARAM=/dtl-global-platform/hubspot/token
    STRIPE_SECRET_PARAM=/dtl-global-platform/stripe/secret
    STRIPE_CONNECT_CLIENT_ID_PARAM=/dtl-global-platform/stripe/connect_client_id
    ANTHROPIC_API_KEY_PARAM=/dtl-global-platform/anthropic/api_key
    TEMPLATES_TABLE=dtl-industry-templates
    CLIENTS_TABLE=dtl-clients
    STATE_TABLE=dtl-onboarding-state
    WEBSITE_BUCKET=dtl-client-websites-{account_id}
    ASSETS_BUCKET=dtl-assets-{account_id}
    CSV_IMPORT_BUCKET=dtl-csv-imports-{account_id}
    SES_FROM_EMAIL=noreply@dtl-global.org

## Appendix B: Python Dependencies

CDK (cdk/requirements.txt):
  aws-cdk-lib>=2.180.0
  constructs>=10.4.0

Lambda runtime dependencies (declared in **`cdk/lambda_layer/requirements.txt`**; built into a **Lambda Layer** in `api_stack.py`):

  hubspot-api-client>=9.0.0
  stripe>=8.0.0
  anthropic>=0.40.0
  requests>=2.31.0

**Build:** `buildspec.yml` runs `pip install -r cdk/lambda_layer/requirements.txt -t cdk/lambda_layer/python` before `cdk deploy`. **Local:** run the same command before `cdk synth` / `cdk deploy`; CDK does not bundle the layer via Docker. **boto3** is supplied by the Lambda runtime (not listed in the layer file).

## Appendix C: SSM Parameter Paths (Complete Reference)

    /dtl-global-platform/hubspot/token                  — HubSpot Private App access token
    /dtl-global-platform/stripe/secret                  — Stripe Secret Key (sk_test_ until production)
    /dtl-global-platform/stripe/connect_client_id       — Stripe Connect client ID (ca_...)
    /dtl-global-platform/anthropic/api_key              — Anthropic Claude API key (sk-ant-...)
    /dtl-global-platform/github/codestar_connection_arn — AWS CodeStar connection ARN

All parameters are SecureString type. Created via scripts/setup_ssm_parameters.py.
Naming convention matches the repository name: dtl-global-platform.

## Appendix D: Cursor Quick Reference

1. Open dtl-global-platform/ in Cursor
2. Read DTL_MASTER_PLAN.md
3. Check phase status (Section 21)
4. BEFORE starting a phase: create GitHub Issue + feature branch (Rule 012)
5. Build ONLY current phase
6. Follow ALL 13 rules
7. Make granular commits referencing the issue
8. Run gate checklist before completing
9. Push, create PR (--body), merge (--squash --yes)
10. Clean up temp files
11. Use Sonnet 4 (not Auto)
12. Ask Gerardo if unsure

---

*End of DTL-Global Platform Master Build Plan v2.8.1*