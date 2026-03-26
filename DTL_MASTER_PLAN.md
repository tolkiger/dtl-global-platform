# DTL-Global Platform — Master Build Plan v3.0.0

> **Owner:** Gerardo Castaneda — DTL-Global
> **Created:** 2026-03-21
> **Updated:** 2026-03-26 (v3.0.0 — Phase 7: CRM Automation & Lifecycle Management)
> **Purpose:** This document is the single source of truth for building the DTL-Global onboarding platform.
> **AI Model for Implementation:** Claude Haiku 4 via Cursor.

---

## Changelog

| Version | Changes |
|---------|--------|
| v3.0.0 | Phase 7 CRM Automation: 11 HubSpot workflows, 6 email sequences, Slack notifications, cold lead + churned win-back, Churned stage. Engine refactoring: removed 5 handlers, added handler_webhook.py. 12 Lambda handlers total. |
| v2.9.0 | Phase 4 pipeline-factory integration, deploy_client_website.py |
| v2.8.1 | Lambda layer: pre-built python/ only, no Docker |
| v2.8.0 | Lambda layer for Python dependencies |
| v2.7.0 | Documentation sync, 16 handlers, DTL_STRIPE_ALLOW_LIVE |
| v2.6.0 | Stripe live-mode support |
| v2.5.3 | Rule 013: Latest Constructs Only |
| v2.5.2 | Cost optimization |
| v2.5.0 | Phase 1 CDK: OAC, CodePipeline V2 |
| v2.4.1 | SSM paths: /dtl-global-platform/ |
| v2.4 | GitFlow, SSM script, pricing, MCP docs |
| v2.0-2.3 | Bootstrap, serverless, HubSpot auth |
| v1.0 | Initial plan |

---

## Current Progress

| Area | Status |
|------|--------|
| Bootstrap | COMPLETE |
| Phase 0 (HubSpot + Stripe) | COMPLETE |
| Phase 0.5 (SSM + GitFlow) | COMPLETE |
| Phase 1 (CDK) | COMPLETE |
| Phase 2 (Lambda) | COMPLETE — needs refactoring |
| Phase 3 (AI) | COMPLETE |
| Phase 4 (Website Deploy) | COMPLETE |
| Phase 5 (Add-Ons) | COMPLETE |
| Phase 6 (E2E Testing) | COMPLETE |
| **Phase 7 (CRM Automation)** | **NOT STARTED** |

---

## 1. Cursor Rules (13 Rules)

| Rule | Name | Enforces |
|------|------|----------|
| 001 | Google Docstring | Google-style docstrings |
| 002 | Comment Every Line | Inline comments |
| 003 | No Over-Engineering | Only approved AWS services |
| 004 | Clean Up Files | Delete temp files |
| 005 | Python Only | Python 3.12+ |
| 006 | Do Not Deviate | Check plan first |
| 007 | Phase Gates | Complete phase before next |
| 008 | File Naming | snake_case |
| 009 | Error Handling | try/except on API calls |
| 010 | Secrets | SSM Parameter Store |
| 011 | Serverless | No EC2, no containers |
| 012 | GitFlow | Feature branches, PRs |
| 013 | Latest Constructs | No deprecated CDK |

---

## 2. Project Structure (v3.0.0)

```
dtl-global-platform/
+-- DTL_MASTER_PLAN.md
+-- README.md, .gitignore, .env.example, requirements.txt
+-- .cursor/rules/dtl-global.mdc
+-- .cursor/skills/ (4 files)
+-- docs/AUTHENTICATION.md
+-- config/
|   +-- hubspot_automations.yaml       # NEW: CRM workflow definitions
+-- scripts/
|   +-- phase0_hubspot_setup.py
|   +-- phase0_stripe_setup.py
|   +-- setup_ssm_parameters.py        # UPDATED: 8 params
|   +-- deploy_client_website.py
|   +-- setup_hubspot_automations.py   # NEW
+-- cdk/stacks/
|   +-- api_stack.py                   # UPDATED: 12 routes
|   +-- storage_stack.py, cdn_stack.py, pipeline_stack.py
+-- engine/
|   +-- shared/ (7 modules: config, hubspot, stripe, ai, ses, route53, s3)
|   +-- handlers/ (12 handlers — see Section 10)
|   +-- templates/ (industry JSON)
+-- tests/
```

### 2.1 Files REMOVED in v3.0.0

| Deleted | Reason | Replacement |
|---------|--------|-------------|
| handler_deploy.py | Redundant | scripts/deploy_client_website.py |
| handler_dns.py | Redundant | deploy_client_website.py handles Route 53 |
| handler_workspace.py | Merged | handler_email_setup.py |
| handler_whatsapp.py | Premature | Future Phase 8+ |
| handler_collaboration.py | Premature | Future Phase 8+ |

### 2.2 Files ADDED in v3.0.0

| New File | Purpose |
|----------|--------|
| config/hubspot_automations.yaml | CRM workflow definitions |
| scripts/setup_hubspot_automations.py | Creates HubSpot workflows from YAML |
| engine/handlers/handler_webhook.py | Stripe webhook receiver |
| tests/test_handler_webhook.py | Webhook handler tests |

---

## 3. Approved AWS Services

100% SERVERLESS. Same as v2.9.0. Lambda, API Gateway, DynamoDB, S3, CloudFront, Route 53, ACM, SES, SSM, CodePipeline, CodeBuild, CloudWatch Logs.

NOT ALLOWED: EC2, ECS, EKS, Fargate, Amplify, AppSync, Cognito, Step Functions, EventBridge, SQS, SNS, RDS, Aurora, ElastiCache.

---

## 4. Approved External APIs

| API | Purpose | Auth |
|-----|---------|------|
| HubSpot CRM API | CRM + workflows + email | Private App Token |
| Stripe API | Payments | Secret Key |
| Stripe Connect | Client payment accounts | OAuth |
| Anthropic Claude | AI features | API Key |
| GitHub API | Pipeline-factory | PAT |
| Slack Incoming Webhooks | Notifications (NEW) | Webhook URL |
| Google Workspace Admin | Email (future) | OAuth 2.0 |

---

## 5-6. MCP Decision, Client Types, Packages

Same as v2.9.0. 4 client types, 9 Stripe products.

---

## 7-14. Phases 0 through 6

All COMPLETE. See v2.9.0 for details.

---

## 10. Phase 2: Lambda Functions (Refactored in v3.0.0)

### 10.1 Final Handler List (12 handlers)

| Handler | Endpoint | Purpose |
|---------|----------|--------|
| handler_onboard.py | POST /onboard | Main orchestrator (UPDATED: accepts deal_id) |
| handler_bid.py | POST /bid | AI bid generation |
| handler_prompt.py | POST /prompt | AI website prompt |
| handler_invoice.py | POST /invoice | Stripe invoicing |
| handler_crm_setup.py | POST /crm-setup | Client HubSpot setup |
| handler_stripe_setup.py | POST /stripe-setup | Client Stripe Connect |
| handler_email_setup.py | POST /email-setup | Custom email DNS (merged workspace) |
| handler_subscribe.py | POST /subscribe | Monthly subscriptions |
| handler_notify.py | POST /notify | Email notifications |
| handler_crm_import.py | POST /crm-import | CSV CRM import |
| handler_chatbot.py | POST /chatbot | AI chatbot |
| handler_webhook.py | POST /webhook/stripe | Stripe events (NEW) |

---

## 15. Phase 7: CRM Automation and Lifecycle Management

### 15.0 Purpose

Transform HubSpot from a passive data store into an active automation engine.

### 15.1 Prerequisites

- HubSpot Starter plan ($20/month) — CONFIRMED
- Slack workspace (free plan sufficient)
- Slack Incoming Webhook URL (see setup below)
- Lambda functions working (fix packaging first)
- API Gateway URL known

#### Slack Webhook Setup

1. Go to api.slack.com/apps
2. Create New App > From Scratch > Name: DTL-Global Notifications
3. Incoming Webhooks > Activate > Add New Webhook > Select #dtl-notifications
4. Copy URL, store in .env as SLACK_WEBHOOK_URL
5. Store in SSM: /dtl-global-platform/slack/webhook_url

### 15.2 Pipeline Update

Add stage 11: **Churned** (displayOrder: 10)
Purpose: Client was active but cancelled subscription.

### 15.3 Deal Stage Workflows (11 Workflows)

#### Workflow 1: New Lead

Trigger: Deal moved to "New Lead"

Actions:
- Create task: 'Initial contact with {client_name}' (due: today, HIGH)
- Slack: 'New Lead: {name} ({industry})'
- Send email: new_lead_welcome

#### Workflow 2: Discovery

Trigger: Deal moved to "Discovery"

Actions:
- Create task: 'Schedule discovery meeting' (due: +1 day)
- Send email: discovery_scheduled
- Set property: discovery_date = today

#### Workflow 3: Proposal & Bid

Trigger: Deal moved to "Proposal & Bid"

Actions:
- Webhook POST /bid with deal_id (AI bid generation)
- Create task: 'Review AI bid and send proposal' (due: +2 days, HIGH)
- Send email: proposal_preparing
- Slack: 'Proposal stage: {name}'

#### Workflow 4: Contract & Deposit

Trigger: Deal moved to "Contract & Deposit"

Actions:
- Webhook POST /invoice with deal_id + invoice_type=deposit + percentage=50
- Send email: deposit_invoice_sent
- Create task: 'Follow up on deposit' (due: +3 days, HIGH)
- Slack: 'Deposit invoice sent: {name} - ${amount}'

#### Workflow 5: Build Website

Trigger: Deal moved to "Build Website"

Actions:
- Webhook POST /prompt with deal_id (generate Rocket.new prompt)
- Create task: 'Build website in Rocket.new' (due: +5 days, HIGH)
- Send email: website_building

#### Workflow 6: Deploy & Connect

Trigger: Deal moved to "Deploy & Connect"

Actions:
- Webhook POST /onboard with deal_id (full deployment)
- Create task: 'Verify deployment' (due: +1 day, HIGH)
- Send email: systems_deploying
- Slack: 'Deploying: {name}'

#### Workflow 7: Final Payment

Trigger: Deal moved to "Final Payment"

Actions:
- Webhook POST /invoice with deal_id + invoice_type=final + percentage=50
- Send email: final_invoice_sent
- Create task: 'Follow up on final payment' (due: +3 days, HIGH)

#### Workflow 8: Live & Monthly

Trigger: Deal moved to "Live & Monthly"

Actions:
- Webhook POST /subscribe with deal_id (create subscription)
- Send email: welcome_live (all login details)
- Create task: '30-day check-in' (due: +30 days, LOW)
- Set contact lifecycle = customer
- Slack: 'CLIENT LIVE: {name} at https://{domain}'
- Enroll in sequence: post_onboarding_care

#### Workflow 9: Nurture

Trigger: Deal moved to "Nurture"

Actions:
- Enroll in sequence: cold_lead_nurture
- Create task: 'Follow up' (due: +30 days, LOW)
- Set property: nurture_start_date = today

#### Workflow 10: Lost

Trigger: Deal moved to "Lost"

Actions:
- Send email: deal_lost_feedback (delay: 1 day)
- Create task: 'Log lost reason' (due: today, MEDIUM)
- Set property: lost_date = today
- Slack: 'Deal LOST: {name}'

#### Workflow 11: Churned

Trigger: Deal moved to "Churned"

Actions:
- Enroll in sequence: churned_winback
- Send email: churned_sorry
- Create task: 'Call to understand churn reason' (due: +1 day, HIGH)
- Slack: 'CLIENT CHURNED: {name}'

### 15.4 Email Sequences (6 Sequences, ~25 Templates)

#### Sequence 1: New Lead Welcome (4 emails)

| Timing | Template | Subject |
|--------|----------|--------|
| Day 0 | new_lead_welcome | Welcome to DTL-Global |
| Day 2 | new_lead_value | How We Help {industry} Businesses |
| Day 5 | new_lead_schedule | Ready to Chat? Schedule a Call |
| Day 10 | new_lead_last_chance | Last Chance — Special Offer |

#### Sequence 2: Proposal Follow-Up (4 emails)

| Timing | Template | Subject |
|--------|----------|--------|
| Day 0 | proposal_sent | Your Custom Proposal |
| Day 3 | proposal_questions | Any Questions? |
| Day 7 | proposal_expiring | Proposal Expires in 7 Days |
| Day 14 | proposal_final | Let's Chat |

#### Sequence 3: Onboarding Updates (5 emails)

| Timing | Template | Subject |
|--------|----------|--------|
| Day 0 | deposit_received | Payment Received — Getting Started! |
| Day 3 | website_preview_coming | Preview Coming Soon |
| Day 7 | website_ready_review | Website Ready for Review! |
| Day 10 | systems_deploying | Systems Being Deployed |
| Day 14 | everything_live | Everything is Live — Welcome Guide |

#### Sequence 4: Cold Lead Nurture (10 emails over 12 months)

| Timing | Template | Subject |
|--------|----------|--------|
| Day 0 | nurture_no_worries | No Worries — We'll Be Here |
| Day 30 | nurture_tip | Quick Tip for {industry} Businesses |
| Day 45 | nurture_case_study | How a {industry} Company Doubled Leads |
| Day 60 | nurture_new_feature | New Feature Alert |
| Day 90 | nurture_checkin | Checking In — Anything Changed? |
| Day 120 | nurture_competitor | Your Competitors Are Going Digital |
| Day 150 | nurture_seasonal | {Season} is Peak Season |
| Day 180 | nurture_6month | 6-Month Special: 15% Off |
| Day 270 | nurture_endofyear | End of Year: 20% Off |
| Day 365 | nurture_final | One Last Offer Before We Close Your File |

#### Sequence 5: Post-Onboarding Care (4 emails)

| Timing | Template | Subject |
|--------|----------|--------|
| Day 7 | care_first_week | How's Your First Week? |
| Day 30 | care_30day | First Month Check-In |
| Day 60 | care_feature_tip | Did You Know About This Feature? |
| Day 90 | care_quarterly | Quarterly Review — Let's Optimize |

#### Sequence 6: Churned Win-Back (8 emails over 6 months)

| Timing | Template | Subject |
|--------|----------|--------|
| Day 0 | churned_sorry | We're Sorry to See You Go |
| Day 7 | churned_improvements | We've Made Improvements |
| Day 14 | churned_free_trial | 30 Days Free on Us |
| Day 30 | churned_website_warning | Your Website Needs Attention |
| Day 45 | churned_success_story | See What Others Achieved |
| Day 60 | churned_discount | 50% Off First 3 Months |
| Day 120 | churned_industry | {Industry} Trends You Should Know |
| Day 180 | churned_final | Final Offer: Original Rate Locked In |

### 15.5 Slack Notifications

| Event | Message |
|-------|--------|
| New Lead | New Lead: {name} ({industry}) |
| Deposit paid | Payment: {name} - ${amount} |
| Deploy triggered | Deploying: {name} |
| Client live | CLIENT LIVE: {name} at https://{domain} |
| Deal lost | Deal LOST: {name} |
| Client churned | CLIENT CHURNED: {name} |
| Task overdue 3+ days | OVERDUE: {task} - {days} days |

### 15.6 handler_webhook.py (NEW Lambda)

Endpoint: POST /webhook/stripe

Events handled:

**invoice.paid:**
1. Extract customer_id from Stripe event
2. Look up client in DynamoDB by stripe_customer_id
3. Get current HubSpot deal stage
4. If 'Contract & Deposit' -> move to 'Build Website'
5. If 'Final Payment' -> move to 'Live & Monthly'
6. Slack notification: 'Payment received: {name}'

**customer.subscription.deleted:**
1. Extract customer_id
2. Look up client in DynamoDB
3. Move HubSpot deal to 'Churned'
4. Slack: 'CLIENT CHURNED: {name}'

**Security:** Validate Stripe webhook signature using STRIPE_WEBHOOK_SECRET from SSM.

**New SSM parameter:** /dtl-global-platform/stripe/webhook_secret

### 15.7 Updated handler_onboard.py

CURRENT: Input requires full client JSON
UPDATED: Accepts deal_id, fetches all info from HubSpot

```python
# New flow:
# 1. Receive { 'deal_id': '12345' } from HubSpot webhook
# 2. GET /crm/v3/objects/deals/{deal_id} with all properties
# 3. Fetch associated contact (email, name, phone)
# 4. Fetch associated company (business name)
# 5. Build client_info dict from HubSpot data
# 6. Proceed with existing onboarding logic
#
# Backward compatible:
#   if 'deal_id' in body: fetch from HubSpot
#   elif 'client_info' in body: use provided data (legacy)
```

### 15.8 Updated api_stack.py

REMOVE 5 routes: /deploy, /dns, /workspace, /whatsapp, /collaboration
ADD 1 route: POST /webhook/stripe -> handler_webhook
FINAL: 12 routes

### 15.9 Recurring Tasks (After Client is Live)

| Task | Frequency | Due |
|------|-----------|-----|
| Monthly check-in | 30 days | +30 days from Live |
| Quarterly review | 90 days | +90 days from Live |
| Annual renewal | Yearly | +11 months from start |
| Content review | 60 days | +60 days from Live |

### 15.10 Phase 7 Build Order (Cursor follows this EXACTLY)

Step 1: Add 'Churned' stage to HubSpot pipeline (scripts/setup_hubspot_automations.py)
Step 2: Create config/hubspot_automations.yaml with all workflow definitions
Step 3: Delete 5 redundant handlers: handler_deploy.py, handler_dns.py, handler_workspace.py, handler_whatsapp.py, handler_collaboration.py
Step 4: Update cdk/stacks/api_stack.py: remove 5 routes, add POST /webhook/stripe
Step 5: Create engine/handlers/handler_webhook.py (Stripe events)
Step 6: Update engine/handlers/handler_onboard.py (accept deal_id from webhook)
Step 7: Update engine/handlers/handler_email_setup.py (merge workspace logic)
Step 8: Update engine/shared/config.py (add SLACK_WEBHOOK_URL, STRIPE_WEBHOOK_SECRET)
Step 9: Update scripts/setup_ssm_parameters.py (add 2 new params: slack/webhook_url, stripe/webhook_secret)
Step 10: Create scripts/setup_hubspot_automations.py (reads YAML, creates workflows)
Step 11: Create 25 email templates in HubSpot via setup script
Step 12: Create 11 workflows in HubSpot via setup script
Step 13: Set up Stripe webhook in Dashboard: URL = {api-gw}/prod/webhook/stripe, events: invoice.paid, customer.subscription.deleted
Step 14: Set up HubSpot Slack integration
Step 15: Create tests: test_handler_webhook.py, test_hubspot_automations.py
Step 16: Deploy: cdk deploy --all
Step 17: Test full lifecycle: create deal -> move through all stages -> verify automations

### 15.11 Phase 7 Gate Checklist

[ ] GitHub Issue + feature branch created
[ ] Churned stage added to HubSpot pipeline
[ ] 5 redundant handlers deleted
[ ] handler_webhook.py created and tested
[ ] handler_onboard.py updated (accepts deal_id)
[ ] handler_email_setup.py updated (workspace merged)
[ ] api_stack.py updated (12 routes)
[ ] config/hubspot_automations.yaml created
[ ] scripts/setup_hubspot_automations.py created
[ ] 25 email templates created in HubSpot
[ ] 11 workflows created in HubSpot
[ ] 6 email sequences created in HubSpot
[ ] Stripe webhook configured in Dashboard
[ ] Slack incoming webhook configured
[ ] HubSpot-Slack integration active
[ ] SSM params added (slack/webhook_url, stripe/webhook_secret)
[ ] All tests pass
[ ] cdk deploy --all succeeds
[ ] Full lifecycle test passes
[ ] PR merged to main

---

## 16-20. Remaining Sections

Same as v2.9.0: Industry Templates, HubSpot Pipeline (now 11 stages with Churned), SEO Prompt, Pricing, CRM Import, GitFlow.

---

## 22. Phase Gate Checklist (Complete)

BOOTSTRAP through PHASE 6 — ALL COMPLETE

PHASE 7 — CRM Automation — NOT STARTED
[ ] GitHub Issue + feature branch created
[ ] Churned stage added to HubSpot pipeline
[ ] 5 redundant handlers deleted
[ ] handler_webhook.py created and tested
[ ] handler_onboard.py updated (accepts deal_id)
[ ] handler_email_setup.py updated (workspace merged)
[ ] api_stack.py updated (12 routes)
[ ] config/hubspot_automations.yaml created
[ ] scripts/setup_hubspot_automations.py created
[ ] 25 email templates created in HubSpot
[ ] 11 workflows created in HubSpot
[ ] 6 email sequences created in HubSpot
[ ] Stripe webhook configured in Dashboard
[ ] Slack incoming webhook configured
[ ] HubSpot-Slack integration active
[ ] SSM params added (slack/webhook_url, stripe/webhook_secret)
[ ] All tests pass
[ ] cdk deploy --all succeeds
[ ] Full lifecycle test passes
[ ] PR merged to main

FUTURE PHASES:
  Phase 8: Automated client reports
  Phase 9: Client self-service portal
  Phase 10: Social media automation
  Phase 11: Google SEO monitoring

---

## Appendix A: Environment Variables

```
# Lambda
HUBSPOT_TOKEN_PARAM=/dtl-global-platform/hubspot/token
STRIPE_SECRET_PARAM=/dtl-global-platform/stripe/secret
STRIPE_CONNECT_CLIENT_ID_PARAM=/dtl-global-platform/stripe/connect_client_id
STRIPE_WEBHOOK_SECRET_PARAM=/dtl-global-platform/stripe/webhook_secret
ANTHROPIC_API_KEY_PARAM=/dtl-global-platform/anthropic/api_key
SLACK_WEBHOOK_URL_PARAM=/dtl-global-platform/slack/webhook_url
TEMPLATES_TABLE=dtl-industry-templates
CLIENTS_TABLE=dtl-clients
STATE_TABLE=dtl-onboarding-state
SES_FROM_EMAIL=onboarding@dtl-global.org

# Local (.env)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Appendix B: Python Dependencies

Same as v2.9.0.

## Appendix C: SSM Parameter Paths (8 total)

```
/dtl-global-platform/hubspot/token
/dtl-global-platform/stripe/secret
/dtl-global-platform/stripe/connect_client_id
/dtl-global-platform/stripe/webhook_secret          (NEW)
/dtl-global-platform/anthropic/api_key
/dtl-global-platform/github/codestar_connection_arn
/dtl-global-platform/github/token
/dtl-global-platform/slack/webhook_url               (NEW)
```

## Appendix D: Cursor Quick Reference

1. Read DTL_MASTER_PLAN.md
2. Use Haiku 4 (not Auto)
3. Follow Phase 7 build order (Section 15.10) step by step
4. Follow all 13 rules
5. GitFlow: issue + branch + commits + PR
6. Read config/hubspot_automations.yaml for workflow definitions

## Appendix E: Pipeline-Factory Integration

Same as v2.9.0.

---

*End of DTL-Global Platform Master Build Plan v3.0.0*