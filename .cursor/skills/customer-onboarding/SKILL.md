---
name: customer-onboarding
description: Complete DTL-Global customer onboarding process from initial consultation to production deployment. Use when onboarding new customers, switching to production mode, or when asked about the customer acquisition and implementation workflow.
---

# DTL-Global Customer Onboarding Process

This skill provides the complete workflow for onboarding new customers to the DTL-Global platform, including Stripe production setup, system deployment, and project management.

## Pre-Customer Checklist

### System Readiness Verification
Before any customer interaction:

- [ ] **AWS Infrastructure**: All CDK stacks deployed and operational
- [ ] **HubSpot Integration**: CRM pipeline and properties configured
- [ ] **Stripe Sandbox**: All products created and tested
- [ ] **AI Services**: Anthropic Claude API functional
- [ ] **Email System**: SES verification completed
- [ ] **Demo Environment**: Platform demo ready and tested

### Required Materials Ready
- [ ] `DEMO_SCRIPT.md` reviewed and practiced
- [ ] `REAL_CUSTOMER_PREP.md` accessible for reference
- [ ] Pricing sheets and service packages prepared
- [ ] Contract templates and legal documents ready

## Customer Onboarding Workflow

### Phase 1: Initial Consultation (30 minutes)

**Discovery Questions (Ask Every Customer):**
1. What's your current digital presence?
2. What are your main business goals?
3. Who are your target customers?
4. What's your biggest challenge right now?
5. What's your timeline and budget?

**Platform Demonstration:**
- Follow `DEMO_SCRIPT.md` exactly (10-minute version)
- Show relevant examples for their industry
- Demonstrate specific features they need
- Address concerns and questions immediately

**Package Recommendation:**
- Analyze their needs against our 4 client types:
  - **TYPE A**: Full Package (DNS, Website, CRM, Stripe, Email, Notify)
  - **TYPE B**: Website + Email Only (DNS, Website, Email optional, Notify)
  - **TYPE C**: Website + CRM (DNS, Website, CRM, Notify)
  - **TYPE D**: CRM + Payments Only (CRM, Stripe, Notify)

**Service Packages:**
- **Starter**: $500 setup / $49 monthly (Website + SEO + Hosting)
- **Growth**: $1,250 setup / $149 monthly (Starter + CRM + Payments + Email)
- **Professional**: $2,500 setup / $249 monthly (Growth + AI Chatbot + CRM Import)
- **Premium**: $4,000+ setup / $399+ monthly (Professional + Custom Automations)

### Phase 2: Proposal & Contract (24 hours)

**Generate Custom Proposal:**
```bash
# Use AI bid generation endpoint
curl -X POST https://your-api-gateway/prod/bid \
  -H "Content-Type: application/json" \
  -d '{
    "client_requirements": {
      "company": "Customer Company Name",
      "industry": "customer_industry",
      "services": ["website", "crm", "payments"],
      "budget": "confirmed_budget",
      "timeline": "standard"
    },
    "industry": "customer_industry"
  }'
```

**Contract Preparation:**
- Service agreement with detailed scope of work
- Payment terms: 50% deposit, 50% on completion
- Timeline with specific milestones (2-4 weeks total)
- Support and maintenance terms clearly defined

**Deposit Collection:**
```bash
# Create Stripe invoice for 50% deposit
curl -X POST https://your-api-gateway/prod/invoice \
  -H "Content-Type: application/json" \
  -d '{
    "client_info": {customer_data},
    "amount": setup_fee_50_percent,
    "description": "DTL-Global Setup Fee (50% Deposit)",
    "due_date": "7_days_from_now"
  }'
```

### Phase 3: Production Setup (Before Implementation)

**CRITICAL: Switch Stripe to Production Mode**

⚠️ **IMPORTANT**: This must be done BEFORE starting any real customer work.

**Step 1: Obtain Stripe Live Keys**
1. Log into Stripe Dashboard (https://dashboard.stripe.com)
2. Switch from "Test mode" to "Live mode" (toggle in left sidebar)
3. Go to Developers > API keys
4. Copy the "Secret key" (starts with `sk_live_`)
5. Go to Connect > Settings
6. Copy the "Client ID" (starts with `ca_`)

**Step 2: Update SSM Parameters**
```bash
# Update Stripe secret key to live
aws ssm put-parameter \
  --name "/dtl-global-platform/stripe/secret" \
  --value "sk_live_YOUR_ACTUAL_LIVE_KEY" \
  --type "SecureString" \
  --overwrite

# Update Stripe Connect client ID to live
aws ssm put-parameter \
  --name "/dtl-global-platform/stripe/connect_client_id" \
  --value "ca_YOUR_ACTUAL_LIVE_CLIENT_ID" \
  --type "SecureString" \
  --overwrite
```

**Step 3: Verify Production Switch**
```bash
# Test that live keys are working
curl -X POST https://your-api-gateway/prod/stripe-setup \
  -H "Content-Type: application/json" \
  -d '{
    "client_info": {"company": "Test Company"},
    "stripe_config": {"account_type": "express", "test_mode": false}
  }'
```

**Step 4: Update Stripe Products (Live Mode)**
Run the Stripe setup script in live mode to recreate all products:
```bash
python scripts/phase0_stripe_setup.py --live-mode
```

### Phase 4: Implementation Kickoff (Week 1)

**Project Setup:**
- Create customer record in HubSpot CRM
- Set up project tracking with milestones
- Schedule regular check-ins (daily updates, weekly reviews)
- Gather all required assets and information

**Technical Implementation Start:**
```bash
# Initialize customer onboarding workflow
curl -X POST https://your-api-gateway/prod/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "client_type": "determined_from_consultation",
    "client_info": {
      "company": "Customer Company",
      "domain": "customer-domain.com",
      "industry": "customer_industry",
      "email": "contact@customer-domain.com",
      "phone": "+1-XXX-XXX-XXXX",
      "services": ["dns", "website", "crm", "stripe", "email", "notify"],
      "package": "GROWTH"
    }
  }'
```

**Progress Communication:**
- Send daily progress updates via email
- Weekly milestone review calls
- Immediate notification of any issues or delays
- Regular demos of work in progress

### Phase 5: Testing & Delivery (Week 2-3)

**System Testing Checklist:**
- [ ] Run end-to-end tests for customer's specific setup
- [ ] Verify all integrations work correctly
- [ ] Test payment processing with small live transaction
- [ ] Validate email delivery and automation
- [ ] Check website performance and SEO elements
- [ ] Verify mobile responsiveness and SSL certificates

**Customer Review Process:**
- Provide access to staging environment
- Walk through all features and functionality step-by-step
- Collect feedback and make necessary adjustments
- Get formal approval for go-live

**Go-Live Preparation:**
- Schedule specific go-live date and time
- Prepare rollback plan in case of issues
- Notify customer of any expected brief downtime
- Have support team ready for launch monitoring

### Phase 6: Launch & Support (Week 3-4)

**Production Launch:**
```bash
# Deploy customer to production environment
curl -X POST https://your-api-gateway/prod/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "customer-domain.com",
    "client_info": {customer_data},
    "go_live": true
  }'
```

**Post-Launch Verification:**
- Verify all systems operational
- Update DNS records (if managing customer's DNS)
- Monitor system performance for first 24 hours
- Confirm all integrations working correctly

**Customer Training (2 hours):**
- Complete walkthrough of all systems
- Provide comprehensive documentation and guides
- Record training session for customer reference
- Schedule follow-up training session if needed

**Final Payment & Handover:**
```bash
# Send final invoice for remaining 50%
curl -X POST https://your-api-gateway/prod/invoice \
  -H "Content-Type: application/json" \
  -d '{
    "client_info": {customer_data},
    "amount": setup_fee_remaining_50_percent,
    "description": "DTL-Global Final Payment (Project Completion)",
    "due_date": "net_30"
  }'
```

**Handover Process:**
- Provide all login credentials securely
- Transfer ownership of created accounts
- Set up ongoing support and maintenance
- Schedule first monthly check-in

## Quality Assurance Gates

### Before Customer Launch
Every customer deployment must pass:

- [ ] Website loads correctly on desktop, tablet, mobile
- [ ] SSL certificate valid and properly configured
- [ ] Contact forms submit successfully to CRM
- [ ] CRM integration captures leads properly
- [ ] Payment processing works (if applicable)
- [ ] Email notifications delivered correctly
- [ ] SEO elements properly configured
- [ ] Analytics tracking set up and functional
- [ ] Backup systems in place and tested
- [ ] Performance optimized (< 3 second load times)

### Customer Acceptance Criteria
- [ ] Customer can access all contracted systems
- [ ] All requested features are functional
- [ ] Performance meets or exceeds expectations
- [ ] Customer trained on system usage
- [ ] Complete documentation provided
- [ ] Support contact information clear
- [ ] Customer provides formal sign-off

## Ongoing Support Framework

### Included Support Services
- **Technical Support**: Email and phone during business hours
- **System Monitoring**: 24/7 uptime monitoring with alerts
- **Security Updates**: Regular patches and updates
- **Backup Management**: Daily backups with 30-day retention
- **Performance Optimization**: Monthly performance reviews

### Additional Services (Billable)
- **Content Updates**: Website changes ($100/hour)
- **Feature Additions**: New functionality (custom pricing)
- **Training Sessions**: Additional team training ($200/session)
- **Priority Support**: 24/7 support with 1-hour response (+$200/month)
- **Custom Integrations**: Third-party systems (custom pricing)

## Emergency Procedures

### System Outage Response
1. **Detection**: Automated monitoring alerts within 5 minutes
2. **Assessment**: Determine scope and impact within 10 minutes
3. **Communication**: Notify affected customers within 15 minutes
4. **Resolution**: Implement fix or rollback within 30 minutes
5. **Follow-up**: Post-incident report and prevention measures

### Customer Escalation Process
1. **Issue Documentation**: Record all details in HubSpot
2. **Management Notification**: Alert senior team immediately
3. **Customer Communication**: Provide regular updates every 2 hours
4. **Resolution Tracking**: Monitor until complete satisfaction
5. **Follow-up**: Ensure customer relationship maintained

## Success Metrics & KPIs

### Customer Success Indicators
- **Website Performance**: Page load time < 3 seconds
- **Uptime**: 99.9% availability target
- **Lead Generation**: Measurable increase in customer leads
- **Conversion Rate**: Improved sales conversion for customer
- **Customer Satisfaction**: NPS score > 8

### Business Metrics
- **Project Completion**: On-time delivery rate > 90%
- **Customer Retention**: Monthly churn rate < 5%
- **Revenue Growth**: Month-over-month growth tracking
- **Profit Margins**: Maintain target margins per package
- **Referral Rate**: Track customer referrals and testimonials

## Common Issues & Solutions

### Stripe Production Issues
**Problem**: Payment processing fails after switching to live mode
**Solution**: Verify webhook endpoints are configured for live mode, check API key permissions

**Problem**: Connected accounts can't be created
**Solution**: Ensure Stripe Connect application is approved for live mode

### DNS & Domain Issues
**Problem**: Customer domain not resolving to new website
**Solution**: Verify DNS propagation (up to 48 hours), check nameserver configuration

**Problem**: SSL certificate not working
**Solution**: Verify domain ownership, check ACM certificate validation

### Integration Issues
**Problem**: HubSpot leads not syncing
**Solution**: Check API token permissions, verify webhook endpoints

**Problem**: Email notifications not sending
**Solution**: Verify SES sender verification, check bounce/complaint rates

## Quick Reference Commands

### Check System Status
```bash
# Verify all systems operational
curl -X GET https://your-api-gateway/prod/status

# Check specific customer deployment
curl -X GET https://your-api-gateway/prod/status/{customer-id}
```

### Customer Data Lookup
```bash
# Get customer information from HubSpot
curl -X POST https://your-api-gateway/prod/crm-lookup \
  -H "Content-Type: application/json" \
  -d '{"email": "customer@domain.com"}'
```

### Emergency Rollback
```bash
# Rollback customer deployment if needed
curl -X POST https://your-api-gateway/prod/rollback \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "customer-id", "rollback_to": "previous_version"}'
```

## Process Checklist Template

Copy this checklist for each new customer:

```
Customer: _______________
Package: _______________
Start Date: _______________

PRE-CUSTOMER:
- [ ] System readiness verified
- [ ] Demo materials prepared
- [ ] Stripe production mode confirmed

CONSULTATION:
- [ ] Discovery questions completed
- [ ] Demo delivered successfully
- [ ] Package recommended and accepted
- [ ] Contract signed
- [ ] 50% deposit collected

IMPLEMENTATION:
- [ ] Customer record created in HubSpot
- [ ] Technical implementation started
- [ ] Daily progress updates sent
- [ ] Weekly milestone reviews conducted

TESTING & DELIVERY:
- [ ] End-to-end testing completed
- [ ] Customer review and approval received
- [ ] Go-live scheduled and executed
- [ ] Post-launch monitoring completed

HANDOVER:
- [ ] Customer training completed
- [ ] Documentation provided
- [ ] Final payment collected
- [ ] Ongoing support established
- [ ] Customer satisfaction confirmed
```

---

**Remember**: This process is the foundation of DTL-Global's success. Follow it exactly for every customer to ensure consistent, high-quality delivery and customer satisfaction.