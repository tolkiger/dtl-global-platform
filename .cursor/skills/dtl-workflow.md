# Skill: DTL-Global Client Onboarding Workflow

## Purpose
Understand the complete client onboarding workflow to build correct automation.

## The 8-Stage Pipeline (with Stage 5.5 Website Deployment)

Stage 1: New Lead        — Capture contact info, assign follow-up
Stage 2: Discovery       — Meeting, gather business needs, log in HubSpot
Stage 3: Proposal and Bid — AI generates bid, send proposal + contract
Stage 4: Contract and 50% — Client pays deposit, AI generates website prompt
Stage 5: Build Website   — Manual: Rocket.new then export to GitHub (no API)
Stage 5.5: Deploy Website — AUTOMATED via pipeline-factory (see below)
Stage 6: Setup CRM and Payments — HubSpot CRM + Stripe Connect
Stage 7: Final Payment   — Auto-invoice remaining 50%, create subscription
Stage 8: Live and Monthly — Client is live, monthly billing active

## Stage 5.5: Deploy Website (Pipeline-Factory Integration)

After the client website is exported from Rocket.new to a GitHub repo
(e.g., tolkiger/dtl-client-smith-roofing), run the deployment script:

```bash
python scripts/deploy_client_website.py \
  --client-name "Smith Roofing" \
  --github-repo "dtl-client-smith-roofing" \
  --domain "smithroofing.com"
```

What this does:
1. Gets or creates a Route 53 hosted zone for the domain
2. Reads config/websites.json from the pipeline-factory repo (via GitHub API)
3. Adds the client website entry to the config
4. Commits the change to pipeline-factory repo
5. Pipeline-factory's CodePipeline auto-triggers cdk deploy
6. CDK provisions: S3 + CloudFront + ACM + Route 53 + client CodePipeline
7. Updates HubSpot deal with deployment status
8. Client website goes live at https://{domain} within ~10 minutes

Optional flags:
  --hosted-zone-id Z0XXXXXXXXX    (skip Route 53 lookup)
  --dry-run                        (preview without committing)

Prerequisites:
  - GITHUB_TOKEN set in .env (with repo scope for pipeline-factory access)
  - Client website repo exists on GitHub
  - Domain registered or NS records pointed to Route 53

## Client Types (handler_onboard.py must respect these)

full_package:  DNS, Website Deploy, CRM, Stripe, Email, Notify
website_only:  DNS, Website Deploy, Email(if requested), Notify
website_crm:   DNS, Website Deploy, CRM, Notify
crm_payments:  CRM, Stripe, Notify

## Key Integration Points
- Website deployment uses pipeline-factory repo (tolkiger/pipeline-factory)
- deploy_client_website.py adds entries via GitHub API
- Pipeline-factory CodePipeline auto-deploys on commit
- Each client gets their own CodePipeline for future website updates
- HubSpot deal stage changes track onboarding progress
- Stripe payment confirmation can trigger next stage
- All state tracked in DynamoDB (dtl-onboarding-state table)
- Emails sent via SES at key milestones

## When Building Handlers
Always check: Does this handler need to behave differently based on client_type?
If yes, use the CLIENT_TYPES config from shared/config.py.