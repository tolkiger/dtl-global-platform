---
name: streamlined-onboarding
description: Ultra-efficient DTL-Global customer onboarding with minimal token usage. Use for quick customer setup, GitHub repo integration, and deployment preparation.
---

# Streamlined Customer Onboarding

Token-efficient customer onboarding for DTL-Global platform.

## Quick Customer Recognition

| Keywords | Package | Setup/Monthly |
|----------|---------|---------------|
| "friends family", "family discount" | `friends_family` | $0/$20 |
| "free website discounted", "charity" | `free_website_discounted` | $0/$20 |
| "starter", "basic website" | `starter` | $500/$49 |
| "growth", "crm payments" | `growth` | $1500/$149 |
| "professional", "ai chatbot" | `professional` | $2500/$249 |
| "premium", "enterprise" | `premium` | $5000/$499 |

## One-Command Onboarding

```bash
# After customer consultation and Rocket.new export
python scripts/efficient_onboarding.py "Company Name" "domain.com" "package_type" "github_repo_url"
```

## Rocket.new Integration Reality

**What Actually Happens:**
- Rocket.new creates repos with shortened names (e.g., `businesscenter` not `businesscentersolutions-website`)
- Repository names are NOT controllable by us
- We must adapt to whatever Rocket.new creates

**Updated Workflow:**
1. **Customer provides GitHub repo URL** after Rocket.new export
2. **Use actual repo URL** in onboarding script
3. **Deploy using real repository name**

## Deployment Process

```bash
# 1. Quick onboarding (30 seconds)
python scripts/efficient_onboarding.py "Business Center Solutions" "businesscentersolutions.net" "free_website_discounted" "https://github.com/tolkiger/businesscenter"

# 2. Deploy infrastructure (when API is ready)
curl -X POST https://api-gateway/prod/deploy \
  -d '{"domain":"businesscentersolutions.net","github_repo":"https://github.com/tolkiger/businesscenter"}'

# 3. Provide DNS records to customer
# 4. Set up billing
```

## Files Created (Minimal)

- `{PROJECT_ID}.json` - Essential project data
- `DNS_Setup.md` - Simple DNS instructions
- `Deployment_Checklist.md` - Action items

## Token Efficiency Improvements

**Before**: 50+ API calls, verbose documentation, complex file structure  
**After**: 3 essential files, 1 command, clear next steps

**Key Changes:**
- ✅ Minimal file generation
- ✅ Single command execution  
- ✅ Real GitHub repo integration
- ✅ Clear deployment checklist
- ✅ No redundant documentation

## Production Deployment

When ready for production:
1. Ensure Stripe is in live mode
2. Deploy AWS infrastructure via CDK
3. Use actual API Gateway endpoints
4. HubSpot/Stripe records will be created automatically

## Emergency Manual Process

If automation fails:
1. Create customer directory manually
2. Add GitHub repo to deployment handler
3. Configure DNS via Route 53 or provide customer instructions
4. Set up Stripe subscription manually