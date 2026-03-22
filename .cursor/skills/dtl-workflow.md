# Skill: DTL-Global Client Onboarding Workflow

## Purpose
Understand the complete client onboarding workflow to build correct automation.

## The 8-Stage Pipeline

Stage 1: New Lead        — Capture contact info, assign follow-up
Stage 2: Discovery       — Meeting, gather business needs, log in HubSpot
Stage 3: Proposal and Bid — AI generates bid, send proposal + contract
Stage 4: Contract and 50% — Client pays deposit, AI generates website prompt
Stage 5: Build Website   — Manual: Rocket.new then GitHub (no API)
Stage 6: Deploy and Connect — AUTOMATED: website + CRM + Stripe + email + notify
Stage 7: Final Payment   — Auto-invoice remaining 50%, create subscription
Stage 8: Live and Monthly — Client is live, monthly billing active

## Client Types (handler_onboard.py must respect these)

full_package:  DNS, Website, CRM, Stripe, Email, Notify
website_only:  DNS, Website, Email(if requested), Notify
website_crm:   DNS, Website, CRM, Notify
crm_payments:  CRM, Stripe, Notify

## Key Integration Points
- HubSpot deal stage changes can trigger Lambda via webhooks
- Stripe payment confirmation can trigger next stage
- All state tracked in DynamoDB (dtl-onboarding-state table)
- Emails sent via SES at key milestones

## When Building Handlers
Always check: Does this handler need to behave differently based on client_type?
If yes, use the CLIENT_TYPES config from shared/config.py.