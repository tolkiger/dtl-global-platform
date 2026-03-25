# DTL-Global Platform — Master Build Plan v2.9.0

> **Owner:** Gerardo Castaneda — DTL-Global
> **Created:** 2026-03-21
> **Updated:** 2026-03-25 (v2.9.0 — Phase 4: pipeline-factory integration for automated website deployment)
> **Purpose:** This document is the single source of truth for building the DTL-Global onboarding platform. Cursor MUST follow this plan exactly. Do not deviate, over-engineer, or add services not listed here.

---

## Changelog

| Version | Changes |
|---------|---------|
| v2.9.0 | **Phase 4 pipeline-factory integration**: Client websites deployed by adding entries to existing `pipeline-factory` repo (tolkiger/pipeline-factory) via GitHub API. New script `scripts/deploy_client_website.py`. New SSM param `/dtl-global-platform/github/token`. Dry-run skips Route 53 creation. Stage 5.5 added to onboarding workflow. Updated dtl-workflow.md skill. |
| v2.8.1 | **Lambda layer**: CDK only packages pre-built `cdk/lambda_layer/python/` (no Docker/SAM bundling fallback). Run `pip install -t` before synth/deploy locally; same in `buildspec.yml`. |
| v2.8.0 | **Lambda layer for Python dependencies**: `cdk/lambda_layer/requirements.txt` + pre-built `python/` (CI/local); `engine/` slimmed to handlers, shared, templates only. CodeBuild runs `pip install -t` before `cdk deploy`. |
| v2.7.0 | **Documentation sync**: Section 2 structure matches repo (four stacks, 16 Lambda handlers, seven shared modules). Stripe Phase 0 supports optional `DTL_STRIPE_ALLOW_LIVE=1` for live catalog seeding. |
| v2.6.0 | Stripe live-mode support, Phase 0 Stripe scripts updated |
| v2.5.0 | HubSpot developer platform 2025.2 project + static auth |
| v2.4.1 | SSM parameter paths: /dtl-global-platform/{param} |
| v2.4 | GitFlow Rule 012, SSM script, pricing tiers, MCP docs, Stripe sandbox |
| v2.1 | Added Section 0: Project Bootstrap |
| v2.0 | Repo rename, 100% serverless, MCP strategy, client types, CodeStar, CRM import |
| v1.0 | Initial plan |

---

## Current Progress

| Area | Status |
|------|--------|
| Bootstrap (Section 0) | Done |
| HubSpot Phase 0 | Done — verify ALL CHECKS PASSED |
| Stripe Phase 0 | Done — 9 products created (sandbox + live support) |
| AWS SSM (Phase 0.5) | Done — 5 parameters created |
| Phase 1 (CDK) | Done — 4 stacks deployed (storage, api, pipeline, infra) |
| Phase 2 (Lambda) | Done — 16 handlers + 7 shared modules built |
| Phase 3 (AI Layer) | Not started |
| Phase 4 (Website Deploy) | In Progress — deploy script created and tested |
| Phases 5-6 | Not started |

---

## Table of Contents

0. [Project Bootstrap](#0-project-bootstrap)
1. [Cursor Rules and Coding Standards](#1-cursor-rules-and-coding-standards)
2. [Project Structure](#2-project-structure)
3. [Approved AWS Services](#3-approved-aws-services)
4. [Approved External APIs](#4-approved-external-apis)
5. [MCP vs Python SDK Decision](#5-mcp-vs-python-sdk-decision)
6. [Client Types and Service Packages](#6-client-types-and-service-packages)
7. [Phase 0: Setup HubSpot and Stripe](#7-phase-0-setup-hubspot-and-stripe)
8. [Phase 0.5: SSM Parameters and GitFlow Setup](#8-phase-05-ssm-parameters-and-gitflow-setup)
9. [Phase 1: Foundation CDK Infrastructure](#9-phase-1-foundation-cdk-infrastructure)
10. [Phase 2: Onboarding Engine Lambda Functions](#10-phase-2-onboarding-engine-lambda-functions)
11. [Phase 3: AI Layer](#11-phase-3-ai-layer)
12. [Phase 4: Client Website Deployment Automation](#12-phase-4-client-website-deployment-automation)
13. [Phase 5: Add-On Modules](#13-phase-5-add-on-modules)
14. [Phase 6: End-to-End Testing](#14-phase-6-end-to-end-testing)
15. [Industry Templates Schema](#15-industry-templates-schema)
16. [DTL-Global HubSpot Pipeline Definition](#16-dtl-global-hubspot-pipeline-definition)
17. [SEO Prompt Template](#17-seo-prompt-template)
18. [Pricing Formula](#18-pricing-formula)
19. [CRM Data Import Specification](#19-crm-data-import-specification)
20. [GitFlow Workflow](#20-gitflow-workflow)
21. [Phase Gate Checklist](#21-phase-gate-checklist)

---

## 0. Project Bootstrap

### 0.0 Purpose

Cursor sets up the entire project structure, rules, skills, and configuration files BEFORE any development begins. Status: DONE.

### 0.1 What Was Created

- .cursor/rules/dtl-global.mdc (12 rules)
- .cursor/skills/ (phase-management, code-generation, dtl-workflow, gitflow)
- docs/AUTHENTICATION.md (HubSpot + Stripe + MCP setup guide)
- .gitignore, .env.example, README.md
- engine/__init__.py files
- All directory structure

### 0.2 MCP Setup

MCP servers are NOT configured via .cursor/mcp.json:
- Stripe MCP: Cursor native integration (Settings > MCP)
- HubSpot MCP: hubspotcli (hs mcp enable)
- See docs/AUTHENTICATION.md for setup instructions

---

## 1. Cursor Rules and Coding Standards

### 1.1 Summary of 12 Rules

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

### 1.2 Cursor Skills

| Skill File | Purpose |
|-----------|---------|
| phase-management.md | Tracks phases, enforces gates, reports status |
| code-generation.md | Code structure template, docstring examples, checklist |
| dtl-workflow.md | The 8-stage pipeline + Stage 5.5, client types, integration points |
| gitflow.md | GitFlow commands, branch naming, PR creation |

---

## 2. Project Structure

```
dtl-global-platform/
+-- DTL_MASTER_PLAN.md
+-- README.md
+-- .gitignore
+-- .env.example
+-- requirements.txt                    # Local dev/testing dependencies
+-- .cursor/
|   +-- rules/dtl-global.mdc
|   +-- skills/ (4 files)
+-- docs/
|   +-- AUTHENTICATION.md
+-- scripts/
|   +-- phase0_hubspot_setup.py
|   +-- phase0_hubspot_verify.py
|   +-- phase0_stripe_setup.py          (sandbox + live support)
|   +-- phase0_stripe_verify.py
|   +-- setup_ssm_parameters.py
|   +-- verify_ssm_parameters.py
|   +-- deploy_client_website.py        (Phase 4: pipeline-factory integration)
|   +-- seed_templates.py
+-- cdk/
|   +-- app.py
|   +-- cdk.json
|   +-- requirements.txt
|   +-- buildspec.yml
|   +-- lambda_layer/
|   |   +-- requirements.txt            # Lambda layer dependencies
|   |   +-- python/                     # Pre-built layer (pip install -t)
|   +-- stacks/
|       +-- api_stack.py                # API Gateway + 16 Lambda functions
|       +-- storage_stack.py            # DynamoDB (3 tables) + S3 (3 buckets)
|       +-- pipeline_stack.py           # CodePipeline (existing CodeStar)
|       +-- infra_stack.py              # SES, Route 53, ACM base config
+-- engine/                             # Lambda deployment asset root
|   +-- shared/
|   |   +-- __init__.py
|   |   +-- config.py
|   |   +-- hubspot_client.py
|   |   +-- stripe_client.py
|   |   +-- ai_client.py
|   |   +-- ses_client.py
|   |   +-- route53_client.py
|   |   +-- s3_client.py
|   +-- handlers/
|   |   +-- __init__.py
|   |   +-- handler_onboard.py          # Main orchestrator (client_type aware)
|   |   +-- handler_bid.py
|   |   +-- handler_prompt.py           # SEO-optimized
|   |   +-- handler_invoice.py
|   |   +-- handler_deploy.py
|   |   +-- handler_dns.py
|   |   +-- handler_crm_setup.py
|   |   +-- handler_stripe_setup.py
|   |   +-- handler_email_setup.py
|   |   +-- handler_subscribe.py
|   |   +-- handler_notify.py
|   |   +-- handler_crm_import.py
|   |   +-- handler_chatbot.py
|   |   +-- handler_workspace.py
|   |   +-- handler_whatsapp.py
|   |   +-- handler_collaboration.py
|   +-- templates/
|       +-- roofing_template.json
|       +-- accounting_template.json
|       +-- remodeling_template.json
|       +-- auto_restoration_template.json
|       +-- general_template.json
+-- tests/
|   +-- test_phase0_hubspot.py
|   +-- test_phase0_stripe.py
|   +-- test_hubspot_client.py
|   +-- test_stripe_client.py
|   +-- test_ai_client.py
|   +-- test_handler_onboard.py
|   +-- test_handler_bid.py
|   +-- test_handler_crm_import.py
|   +-- test_deploy_client_website.py   # Phase 4 tests
+-- client-sites/
    +-- .gitkeep
```

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

---

## 4. Approved External APIs

| API | Purpose | Auth | Mode |
|-----|---------|------|------|
| HubSpot CRM API | CRM management | Private App Token | Production |
| Stripe API | Payments, invoicing | Secret Key | Sandbox (live via DTL_STRIPE_ALLOW_LIVE=1) |
| Stripe Connect | Client payment accounts | OAuth + Platform | Sandbox until launch |
| Anthropic Claude (Direct) | AI features | API Key | Production |
| GitHub API | Pipeline-factory integration | Personal Access Token | Production |
| Google Workspace Admin | Email (future) | OAuth 2.0 | Future |

---

## 5. MCP vs Python SDK Decision

MCP Servers (Cursor IDE only):
- Stripe: Cursor native integration
- HubSpot: hubspotcli (hs mcp enable)
- Use for: exploring APIs, verifying data

Python SDKs (Production):
- stripe and hubspot-api-client packages
- Use for: all code, scripts, Lambda functions

---

## 6. Client Types and Service Packages

### 6.1 Client Types

TYPE A: FULL PACKAGE — DNS, Website Deploy, CRM, Stripe, Email, Notify
TYPE B: WEBSITE + EMAIL ONLY — DNS, Website Deploy, Email(if requested), Notify
TYPE C: WEBSITE + CRM — DNS, Website Deploy, CRM, Notify
TYPE D: CRM + PAYMENTS ONLY — CRM, Stripe, Notify

### 6.2 Service Packages

FRIENDS AND FAMILY: $0 setup / $20 monthly
  Website hosting and basic maintenance only.

STARTER: $500 setup / $49 monthly
  Website + hosting + SEO. Optional custom email (+$100 setup).

GROWTH: $1,250 setup / $149 monthly
  Everything in Starter + HubSpot CRM + Stripe + custom email.

PROFESSIONAL: $2,500 setup / $249 monthly
  Everything in Growth + AI chatbot + CRM import + priority support.

PREMIUM: $4,000+ setup / $399+ monthly
  Everything in Professional + bots + custom automations.

### 6.3 Stripe Products (9 total)

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

## 7. Phase 0: Setup HubSpot and Stripe

Status: DONE

HubSpot: Pipeline "DTL-Global Client Onboarding" with 10 stages. All custom deal and contact properties created. Verification passed.

Stripe: 9 products created in sandbox. Live mode supported via DTL_STRIPE_ALLOW_LIVE=1 flag.

---

## 8. Phase 0.5: SSM Parameters and GitFlow Setup

Status: DONE

### 8.1 SSM Parameters (6 total)

    /dtl-global-platform/hubspot/token                  — HubSpot Private App token
    /dtl-global-platform/stripe/secret                  — Stripe Secret Key
    /dtl-global-platform/stripe/connect_client_id       — Stripe Connect client ID
    /dtl-global-platform/anthropic/api_key              — Anthropic Claude API key
    /dtl-global-platform/github/codestar_connection_arn — Existing CodeStar connection ARN
    /dtl-global-platform/github/token                   — GitHub PAT (repo scope for pipeline-factory)

All stored as SecureString. Created via scripts/setup_ssm_parameters.py.

### 8.2 GitFlow

GitHub Project "DTL-Global Platform" created. All phases use feature branches, issues, and PRs.

---

## 9. Phase 1: Foundation CDK Infrastructure

Status: DONE

### 9.1 What Was Deployed

4 CDK stacks:
- storage_stack.py: 3 DynamoDB tables + 3 S3 buckets
- api_stack.py: API Gateway (16 endpoints) + 16 Lambda functions
- pipeline_stack.py: CodePipeline using existing CodeStar connection
- infra_stack.py: SES, Route 53, ACM base config

### 9.2 Lambda Layer

Dependencies managed via cdk/lambda_layer/:
- requirements.txt defines packages
- python/ directory contains pre-built packages
- CDK packages the python/ directory as a Lambda layer
- No Docker bundling — pip install -t before synth/deploy
- CodeBuild buildspec.yml runs pip install -t before cdk deploy

---

## 10. Phase 2: Onboarding Engine Lambda Functions

Status: DONE

### 10.1 Built (19 steps completed)

7 shared modules: config, hubspot_client, stripe_client, ai_client, ses_client, route53_client, s3_client

16 handlers: onboard, bid, prompt, invoice, deploy, dns, crm_setup, stripe_setup, email_setup, subscribe, notify, crm_import, chatbot, workspace, whatsapp, collaboration

### 10.2 Client Type Logic

```python
CLIENT_TYPES = {
    "full_package": ["dns", "website", "crm", "stripe", "email", "notify"],
    "website_only": ["dns", "website", "email_optional", "notify"],
    "website_crm": ["dns", "website", "crm", "notify"],
    "crm_payments": ["crm", "stripe", "notify"]
}
```

---

## 11. Phase 3: AI Layer

Status: NOT STARTED

Model: Claude Haiku 4.5 (direct Anthropic API, key from /dtl-global-platform/anthropic/api_key)

Features to build:
- Bid generation (pricing JSON with guardrails)
- SEO website prompts (Rocket.new prompts)
- Custom request estimation (hours, cost, complexity)
- Template customization (per client)
- CRM column mapping (CSV import assistance)

### Phase 3 Gate

```
[ ] GitHub Issue + feature branch
[ ] Bid generation works for 3+ industries
[ ] Website prompt includes all SEO elements
[ ] Custom request estimation returns structured JSON
[ ] AI costs under $0.05 for 10 test calls
[ ] PR merged to main
```

---

## 12. Phase 4: Client Website Deployment Automation

Status: IN PROGRESS — deploy script created and tested

### 12.1 Strategy: Reuse Existing Pipeline-Factory

Client websites are deployed using the EXISTING `pipeline-factory` repo
(github.com/tolkiger/pipeline-factory), NOT by rebuilding infrastructure
inside dtl-global-platform. This is the same proven pattern used for
dtl-global.org and lostuleskc.com.

The pipeline-factory is a CDK app that reads `config/websites.json` and
creates one WebsitePipelineStack per entry. Each stack provisions:
- S3 bucket (static website hosting)
- CloudFront distribution (CDN)
- ACM SSL certificate
- Route 53 DNS records
- CodePipeline (GitHub push triggers auto-deploy to S3)

When a new client entry is added to `websites.json` and committed,
pipeline-factory's own CodePipeline triggers `cdk deploy`, which
provisions all infrastructure for that client's website automatically.

### 12.2 Architecture

```
DTL-GLOBAL-PLATFORM (this repo)          PIPELINE-FACTORY (existing repo)
Cursor triggers onboarding               config/websites.json

scripts/deploy_client_website.py         Each entry creates:
    |                                      - S3 bucket
    | 1. Read client info from             - CloudFront distribution
    |    CLI args (Cursor provides)        - ACM SSL certificate
    | 2. Get or create Route 53            - Route 53 DNS records
    |    hosted zone for domain            - CodePipeline (auto-deploy)
    | 3. GitHub API: read websites.json
    |    from pipeline-factory repo
    | 4. Check for duplicates
    | 5. Add new client entry
    | 6. GitHub API: commit change
    | 7. Pipeline-factory CodePipeline
    |    auto-triggers cdk deploy
    | 8. Update HubSpot deal status
    |
    v
Client gets:                             Future pushes to client repo
  - Live website at custom domain          auto-deploy via their own
  - SSL certificate (ACM)                  CodePipeline (no manual work)
  - CDN (CloudFront)
  - Auto-deploy pipeline
```

### 12.3 The Deployment Script

File: scripts/deploy_client_website.py

Triggered by Cursor during the onboarding workflow (dtl-workflow skill).
Runs locally in Cursor's terminal.

```
Usage:
  python scripts/deploy_client_website.py \
    --client-name "Smith Roofing" \
    --github-repo "dtl-client-smith-roofing" \
    --domain "smithroofing.com" \
    [--hosted-zone-id "Z0XXXXXXXXX"] \
    [--hosted-zone-name "smithroofing.com"] \
    [--dry-run]

Flow:
  1. Parse CLI arguments and validate inputs
  2. If --dry-run and no --hosted-zone-id: skip Route 53 (use placeholder)
     If not dry-run: get or create Route 53 hosted zone
  3. GitHub API: GET config/websites.json from tolkiger/pipeline-factory
  4. Check for duplicate (by siteName or domainName)
  5. Add new entry to websites[] array
  6. If --dry-run: print entry and exit (no commit)
  7. GitHub API: PUT updated websites.json (commit to main)
  8. Update HubSpot deal (if token available)
  9. Print summary with website URL and next steps

Prerequisites:
  - Client website repo exists on GitHub
  - GITHUB_TOKEN in .env (repo scope for pipeline-factory)
  - Domain registered or NS records pointed to Route 53
```

### 12.4 Pipeline-Factory Config Reference

```json
{
  "connectionArn": "arn:aws:codestar-connections:us-east-1:485815740327:connection/8a0201d7-d2cc-4095-b1a1-80556b74c395",
  "githubOwner": "tolkiger",
  "defaultRegion": "us-east-1",
  "defaultAccount": "485815740327",
  "notificationEmail": "admin@dtl-global.org",
  "websites": [
    {
      "siteName": "example-website",
      "githubRepo": "dtl-client-example",
      "domainName": "example.com",
      "hostedZoneId": "Z0XXXXXXXXX",
      "hostedZoneName": "example.com",
      "menuPdfEnabled": false
    }
  ]
}
```

### 12.5 Onboarding Workflow Integration

The deployment script is called during Stage 5.5:

```
Stage 5:   Build Website    — Manual: Rocket.new, export to GitHub
Stage 5.5: Deploy Website   — Run deploy_client_website.py (automated)
Stage 6:   Setup CRM/Pay    — HubSpot CRM + Stripe Connect
```

### 12.6 Domain Scenarios

Scenario A: Client needs new domain
  - Register via Route 53 ($14/year)
  - deploy_client_website.py detects existing zone

Scenario B: Client has domain elsewhere
  - Script creates Route 53 hosted zone
  - Client points NS records (printed by script)

Scenario C: Client domain already on Route 53
  - Script detects existing zone automatically

### 12.7 Cost Per Client Website

| Resource | Monthly Cost |
|----------|-------------|
| S3 bucket | ~$0.50 |
| CloudFront | ~$0.00-1.00 |
| Route 53 hosted zone | $0.50 |
| CodePipeline | $1.00 |
| ACM certificate | Free |
| **Total per client** | **~$2.00/month** |

### 12.8 Phase 4 Gate Checklist

```
[ ] GitHub Issue + feature branch created
[x] scripts/deploy_client_website.py created and tested
[x] --dry-run flag works (skips Route 53 and GitHub commit)
[x] Script reads pipeline-factory config via GitHub API
[x] Script detects duplicates (by siteName and domainName)
[x] Script adds correct entry format matching pipeline-factory schema
[ ] Script commits to pipeline-factory and triggers CodePipeline
[ ] Script updates HubSpot deal after deployment
[ ] Test: add a test site, verify pipeline-factory CDK deploys
[ ] Test: website loads at custom domain with SSL
[x] tests/test_deploy_client_website.py exists
[ ] .cursor/skills/dtl-workflow.md updated with Stage 5.5
[ ] GITHUB_TOKEN added to .env.example
[ ] PR merged to main
```

---

## 13. Phase 5: Add-On Modules

Status: NOT STARTED

Priority: AI chatbot, Google Workspace email, WhatsApp, Slack/Teams

### Phase 5 Gate

```
[ ] GitHub Issue + feature branch
[ ] AI chatbot works on test site
[ ] Chatbot captures leads to HubSpot
[ ] Google Workspace DNS records correct
[ ] PR merged to main
```

---

## 14. Phase 6: End-to-End Testing and First Client

Status: NOT STARTED

Test ALL 4 client types + CRM import. Stripe in sandbox until first real client.

### Phase 6 Gate

```
[ ] GitHub Issue + feature branch
[ ] All 4 client type tests pass
[ ] CRM import test (50-row CSV)
[ ] Website deployed via pipeline-factory and loads with SSL
[ ] All emails received correctly
[ ] HubSpot CRM configured correctly
[ ] Stripe accepts test payment
[ ] Demo under 10 minutes
[ ] AWS bill under $20
[ ] 100% serverless verified
[ ] All PRs merged to main
[ ] Ready to switch Stripe to PRODUCTION
```

---

## 15. Industry Templates Schema

Roofing template with HubSpot pipelines, custom properties, Stripe products, SEO keywords, chatbot system prompt. Templates stored in engine/templates/ as JSON files.

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
8. NAP consistency (Name, Address, Phone)
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

GitHub Project "DTL-Global Platform" created (done).

### 20.2 Per-Phase Workflow

BEFORE: Create GitHub Issue, create feature branch from main
DURING: Granular commits: feat(phase-{N}): {desc} #{issue}
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

## 21. Phase Gate Checklist

```
BOOTSTRAP — DONE
[x] All setup complete

PHASE 0 — HubSpot and Stripe — DONE
[x] HubSpot setup + verify pass
[x] Stripe setup + verify pass (9 products)

PHASE 0.5 — SSM and GitFlow — DONE
[x] 6 SSM parameters created (including github/token)
[x] GitHub Project exists

PHASE 1 — CDK Infrastructure — DONE
[x] 4 stacks deployed
[x] All resources exist
[x] 100% serverless

PHASE 2 — Lambda Functions — DONE
[x] 16 handlers + 7 shared modules
[x] All 4 client types handled

PHASE 3 — AI Layer — NOT STARTED
[ ] Bid, prompt, estimation working
[ ] Haiku 4.5 confirmed
[ ] PR merged to main
PROCEED TO PHASE 4 (can be done in parallel)

PHASE 4 — Website Deployment (Pipeline-Factory) — IN PROGRESS
[x] deploy_client_website.py created and tested (dry-run works)
[x] Script reads pipeline-factory config via GitHub API
[x] Duplicate detection works
[x] tests/test_deploy_client_website.py exists
[ ] Full deployment test (commit to pipeline-factory, verify CDK deploys)
[ ] Website loads at custom domain with SSL
[ ] HubSpot deal updated after deployment
[ ] dtl-workflow.md updated with Stage 5.5
[ ] PR merged to main
PROCEED TO PHASE 5

PHASE 5 — Add-Ons — NOT STARTED
[ ] Chatbot working, leads captured
[ ] Email DNS automation working
[ ] PR merged to main
PROCEED TO PHASE 6

PHASE 6 — E2E Testing — NOT STARTED
[ ] All 4 client types tested
[ ] Website deployed via pipeline-factory
[ ] Full demo under 10 minutes
[ ] All PRs merged to main
READY TO ONBOARD REAL CLIENTS
```

---

## Appendix A: Environment Variables (Lambda + Local)

```
# Lambda Environment Variables (set via CDK)
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
SES_FROM_EMAIL=onboarding@dtl-global.org

# Local Development Only (.env)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx  # GitHub PAT (repo scope for pipeline-factory)
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

## Appendix B: Python Dependencies

```
# CDK (cdk/requirements.txt)
aws-cdk-lib>=2.100.0
constructs>=10.0.0

# Lambda Layer (cdk/lambda_layer/requirements.txt)
hubspot-api-client>=9.0.0
stripe>=8.0.0
anthropic>=0.40.0
requests>=2.31.0

# Local Development (requirements.txt — project root)
boto3>=1.34.0
hubspot-api-client>=9.0.0
stripe>=8.0.0
anthropic>=0.40.0
requests>=2.31.0
aws-cdk-lib>=2.100.0
constructs>=10.0.0
pytest>=8.0.0
pytest-cov>=5.0.0
moto>=5.0.0
python-dotenv>=1.0.0
```

Note: Lambda functions get boto3 from the Lambda runtime (not the layer).
The layer provides third-party packages only.

## Appendix C: SSM Parameter Paths

```
/dtl-global-platform/hubspot/token                  — HubSpot Private App access token
/dtl-global-platform/stripe/secret                  — Stripe Secret Key
/dtl-global-platform/stripe/connect_client_id       — Stripe Connect client ID
/dtl-global-platform/anthropic/api_key              — Anthropic Claude API key
/dtl-global-platform/github/codestar_connection_arn — AWS CodeStar connection ARN
/dtl-global-platform/github/token                   — GitHub PAT (repo scope)
```

All SecureString. Created via scripts/setup_ssm_parameters.py.

## Appendix D: Cursor Quick Reference

```
1. Open dtl-global-platform/ in Cursor
2. Read DTL_MASTER_PLAN.md
3. Check phase status (Section 21)
4. BEFORE starting a phase: create GitHub Issue + feature branch (Rule 012)
5. Build ONLY current phase
6. Follow ALL 12 rules
7. Make granular commits referencing the issue
8. Run gate checklist before completing
9. Push, create PR (--body), merge (--squash --yes)
10. Clean up temp files
11. Use Sonnet 4 (not Auto)
12. Ask Gerardo if unsure
```

---

*End of DTL-Global Platform Master Build Plan v2.9.0*