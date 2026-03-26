# Phase 7 — Cursor Instructions for Haiku 4
# Drop this file in your repo root. Tell Cursor: "Read PHASE7_INSTRUCTIONS.md and execute step by step."

## IMPORTANT: Read DTL_MASTER_PLAN.md first. Follow all 13 rules. Use GitFlow (Rule 012).

## Pre-Step: GitFlow Setup

Run these commands in the terminal:
```bash
gh issue create --title "Phase 7: CRM Automation & Lifecycle Management" --body "## Phase 7\n\nImplement HubSpot CRM automation, email sequences, Slack notifications, Stripe webhooks, and engine refactoring per DTL_MASTER_PLAN.md v3.0.0 Section 15." --label "phase-7" --project "DTL-Global Platform"
```
Note the issue number. Then:
```bash
git checkout main && git pull origin main
git checkout -b feature/{ISSUE_NUMBER}-phase-7-crm-automation
```

---

## Step 1: Delete 5 Redundant Handlers

Delete these files from engine/handlers/:
- handler_deploy.py
- handler_dns.py
- handler_workspace.py
- handler_whatsapp.py
- handler_collaboration.py

```bash
rm engine/handlers/handler_deploy.py
rm engine/handlers/handler_dns.py
rm engine/handlers/handler_workspace.py
rm engine/handlers/handler_whatsapp.py
rm engine/handlers/handler_collaboration.py
git add -A
git commit -m "refactor(phase-7): remove 5 redundant handlers #{ISSUE_NUMBER}"
```

---

## Step 2: Create handler_webhook.py

Create file: engine/handlers/handler_webhook.py

This handler receives Stripe webhook events and advances HubSpot deals.

Requirements:
- Endpoint: POST /webhook/stripe
- Validate Stripe webhook signature using stripe.Webhook.construct_event()
- Get webhook secret from SSM: /dtl-global-platform/stripe/webhook_secret
- Handle event "invoice.paid":
  - Extract customer ID from event.data.object.customer
  - Query DynamoDB dtl-clients table for matching stripe_customer_id
  - Get the client's HubSpot deal_id
  - Get current deal stage from HubSpot
  - If stage is "Contract & Deposit" -> move deal to "Build Website"
  - If stage is "Final Payment" -> move deal to "Live & Monthly"
  - Send Slack notification via requests.post to SLACK_WEBHOOK_URL from SSM
- Handle event "customer.subscription.deleted":
  - Extract customer ID
  - Query DynamoDB for client
  - Move HubSpot deal to "Churned" stage
  - Send Slack notification
- Return 200 for handled events, 400 for invalid signature, 200 for unhandled events
- Use Google docstrings, comment every line, try/except on all API calls
- Import shared modules: config, hubspot_client, stripe_client

```bash
git add engine/handlers/handler_webhook.py
git commit -m "feat(phase-7): add handler_webhook.py for Stripe events #{ISSUE_NUMBER}"
```

---

## Step 3: Update handler_onboard.py

Update engine/handlers/handler_onboard.py to accept deal_id from HubSpot webhooks.

Changes:
- At the top of lambda_handler, check the request body:
  - If body contains "deal_id" (string): fetch all client info from HubSpot
    - GET /crm/v3/objects/deals/{deal_id} with properties list
    - GET associated contacts
    - GET associated companies
    - Build client_info dict from HubSpot properties
  - If body contains "client_info" (dict): use it directly (backward compatible)
- Add a new function: fetch_client_from_hubspot(deal_id) -> dict
  - Uses shared/hubspot_client.py to fetch deal, contact, company
  - Maps HubSpot properties to the client_info format the rest of the handler expects
  - Returns the same dict structure as the legacy client_info input

```bash
git add engine/handlers/handler_onboard.py
git commit -m "feat(phase-7): update handler_onboard to accept deal_id #{ISSUE_NUMBER}"
```

---

## Step 4: Update handler_email_setup.py

Merge the workspace logic from the deleted handler_workspace.py into handler_email_setup.py.

If handler_workspace.py had Google Workspace provisioning logic, add it to handler_email_setup.py.
If it was just a placeholder, ensure handler_email_setup.py handles both:
- Google Workspace DNS record creation (MX, TXT, CNAME for Gmail)
- Microsoft 365 DNS record creation (MX, TXT, CNAME for Outlook)

```bash
git add engine/handlers/handler_email_setup.py
git commit -m "refactor(phase-7): merge workspace logic into handler_email_setup #{ISSUE_NUMBER}"
```

---

## Step 5: Update api_stack.py

Update cdk/stacks/api_stack.py:

REMOVE these 5 Lambda functions and their API Gateway routes:
- handler_deploy / POST /deploy
- handler_dns / POST /dns
- handler_workspace / POST /workspace
- handler_whatsapp / POST /whatsapp
- handler_collaboration / POST /collaboration

ADD this 1 new Lambda function and route:
- handler_webhook / POST /webhook/stripe
  - Same runtime, memory, timeout as other handlers
  - Same Lambda layer
  - Same environment variables PLUS:
    - STRIPE_WEBHOOK_SECRET_PARAM: /dtl-global-platform/stripe/webhook_secret
    - SLACK_WEBHOOK_URL_PARAM: /dtl-global-platform/slack/webhook_url

Final route count should be 12.

```bash
git add cdk/stacks/api_stack.py
git commit -m "refactor(phase-7): update api_stack - 12 routes, add webhook #{ISSUE_NUMBER}"
```

---

## Step 6: Update shared/config.py

Add these new SSM parameter paths to engine/shared/config.py:

```python
STRIPE_WEBHOOK_SECRET_PARAM = os.environ.get(
    "STRIPE_WEBHOOK_SECRET_PARAM",
    "/dtl-global-platform/stripe/webhook_secret"
)
SLACK_WEBHOOK_URL_PARAM = os.environ.get(
    "SLACK_WEBHOOK_URL_PARAM",
    "/dtl-global-platform/slack/webhook_url"
)
```

Add a helper function:
```python
def send_slack_notification(message: str) -> None:
    # Get Slack webhook URL from SSM
    # POST to the webhook URL with {"text": message}
    # Wrap in try/except, print warning if fails (non-critical)
```

```bash
git add engine/shared/config.py
git commit -m "feat(phase-7): add Slack and webhook secret config #{ISSUE_NUMBER}"
```

---

## Step 7: Update setup_ssm_parameters.py

Add 2 new parameters to scripts/setup_ssm_parameters.py:

Parameter 7: /dtl-global-platform/stripe/webhook_secret
  - Prompt: "Stripe Webhook Signing Secret (whsec_...): "
  - Type: SecureString

Parameter 8: /dtl-global-platform/slack/webhook_url
  - Prompt: "Slack Incoming Webhook URL: "
  - Type: SecureString

Also update scripts/verify_ssm_parameters.py to check for 8 parameters.

```bash
git add scripts/setup_ssm_parameters.py scripts/verify_ssm_parameters.py
git commit -m "feat(phase-7): add Slack and Stripe webhook SSM params #{ISSUE_NUMBER}"
```

---

## Step 8: Create config/hubspot_automations.yaml

Copy the file config/hubspot_automations.yaml that Gerardo has already placed in the repo.
If it's not there yet, create the config/ directory and the file.

```bash
mkdir -p config
git add config/hubspot_automations.yaml
git commit -m "feat(phase-7): add HubSpot automations YAML config #{ISSUE_NUMBER}"
```

---

## Step 9: Create setup_hubspot_automations.py

Create file: scripts/setup_hubspot_automations.py

This script reads config/hubspot_automations.yaml and creates everything in HubSpot.

Requirements:
- Load YAML config using PyYAML (add pyyaml to requirements.txt if needed)
- Load HubSpot token from .env (HUBSPOT_ACCESS_TOKEN)
- Functions to create:
  - add_pipeline_stage(stage_name, display_order): Add "Churned" stage
  - create_email_template(name, subject, body): Create marketing email in HubSpot
  - create_workflow(name, trigger, actions): Create automation workflow
    NOTE: HubSpot Starter plan has LIMITED workflow capabilities.
    If the API doesn't support full workflow creation, print instructions
    for manual setup in HubSpot UI and create a checklist.
  - create_sequence(name, emails): Create email sequence
- Idempotent: skip if already exists
- Print summary of created vs skipped items

```bash
git add scripts/setup_hubspot_automations.py
git commit -m "feat(phase-7): add HubSpot automation setup script #{ISSUE_NUMBER}"
```

---

## Step 10: Create Tests

Create file: tests/test_handler_webhook.py
- Test invoice.paid event handling (mock Stripe, DynamoDB, HubSpot)
- Test subscription.deleted event handling
- Test invalid signature rejection
- Test unknown event type (should return 200)

Create file: tests/test_hubspot_automations.py
- Test YAML loading
- Test pipeline stage creation (mock HubSpot API)
- Test email template creation
- Test idempotency (skip existing)

```bash
git add tests/test_handler_webhook.py tests/test_hubspot_automations.py
git commit -m "test(phase-7): add webhook and automation tests #{ISSUE_NUMBER}"
```

---

## Step 11: Update .env.example

Add these lines to .env.example:

```
# Slack Incoming Webhook (for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Stripe Webhook Secret (for signature validation)
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

```bash
git add .env.example
git commit -m "chore(phase-7): add Slack and Stripe webhook to .env.example #{ISSUE_NUMBER}"
```

---

## Step 12: Deploy and Test

```bash
# Rebuild Lambda layer (if needed)
cd cdk/lambda_layer
pip install --platform manylinux2014_x86_64 --target python/ --implementation cp --python-version 3.12 --only-binary=:all: -r requirements.txt
cd ../..

# Deploy
cd cdk
cdk deploy --all
cd ..

# Run tests
python -m pytest tests/ -v
```

```bash
git add -A
git commit -m "chore(phase-7): deploy and verify #{ISSUE_NUMBER}"
```

---

## Step 13: Push and Create PR

```bash
git push origin feature/{ISSUE_NUMBER}-phase-7-crm-automation

gh pr create --title "Phase 7: CRM Automation & Lifecycle Management" --body "## Summary\n\n- Added handler_webhook.py for Stripe events\n- Updated handler_onboard.py to accept deal_id\n- Removed 5 redundant handlers\n- Updated api_stack.py (12 routes)\n- Added HubSpot automations YAML config\n- Added setup_hubspot_automations.py\n- Added Slack notification support\n- Added 2 new SSM parameters\n- All tests passing\n\nCloses #{ISSUE_NUMBER}" --base main --head feature/{ISSUE_NUMBER}-phase-7-crm-automation

gh pr merge --squash --delete-branch --yes
```

---

## Step 14: Manual Steps (Gerardo does these after Cursor finishes)

1. Run: python scripts/setup_ssm_parameters.py (add 2 new params)
2. Run: python scripts/setup_hubspot_automations.py (create HubSpot workflows)
3. Set up Stripe webhook in Dashboard:
   - URL: https://{api-gateway-url}/prod/webhook/stripe
   - Events: invoice.paid, customer.subscription.deleted
   - Copy the webhook signing secret (whsec_...)
   - Store in SSM: /dtl-global-platform/stripe/webhook_secret
4. Set up Slack Incoming Webhook (see Section 15.1.1 in plan)
5. Test: create a test deal in HubSpot, move through stages, verify automations

---

## DONE! Phase 7 is complete when all gate checklist items pass.