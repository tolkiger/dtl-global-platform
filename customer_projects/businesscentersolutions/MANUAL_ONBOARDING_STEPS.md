# Manual Onboarding: Business Center Solutions

**Customer**: Business Center Solutions  
**Contact**: Alondra Duarte (aduarte@businesscentersolutions.net)  
**Package**: Free Website + Discounted Maintenance ($0 setup / $20 monthly)  
**GitHub Repo**: https://github.com/tolkiger/businesscenter  
**Domain**: businesscentersolutions.net (GoDaddy DNS)  

## Immediate Action Items

### 1. HubSpot CRM Setup (Manual)
- [ ] **Create Contact**:
  - Name: Alondra Duarte
  - Email: aduarte@businesscentersolutions.net
  - Phone: (816) 204-7169
  - Company: Business Center Solutions
  - Industry: Consulting

- [ ] **Create Deal**:
  - Deal Name: "Business Center Solutions - Free Website + Discounted"
  - Pipeline: DTL Onboarding
  - Stage: Build Website
  - Deal Amount: $0 (setup fee)
  - Monthly Value: $20
  - Close Date: Today

### 2. Infrastructure Deployment (AWS Console)

**S3 Bucket Setup:**
- [ ] Create S3 bucket: `businesscentersolutions-net-website`
- [ ] Enable static website hosting
- [ ] Configure bucket policy for public read access
- [ ] Set up GitHub Actions deployment (connect to `tolkiger/businesscenter` repo)

**CloudFront Distribution:**
- [ ] Create CloudFront distribution
- [ ] Origin: S3 bucket (businesscentersolutions-net-website)
- [ ] Alternate domain names: `businesscentersolutions.net`, `www.businesscentersolutions.net`
- [ ] SSL Certificate: Request new ACM certificate

**SSL Certificate (ACM):**
- [ ] Request certificate for `businesscentersolutions.net` and `*.businesscentersolutions.net`
- [ ] Note DNS validation records for customer

### 3. DNS Instructions for Customer

**Send to Alondra Duarte:**

```
Subject: DNS Configuration Required - Business Center Solutions Website

Hi Alondra,

Your website infrastructure is being deployed. Please add these DNS records in your GoDaddy account:

WEBSITE ROUTING:
Record Type: CNAME
Name: www
Value: [CloudFront distribution domain - will be provided]
TTL: 300

Record Type: A
Name: @  
Value: [CloudFront IP - will be provided]
TTL: 300

SSL CERTIFICATE VALIDATION:
Record Type: CNAME
Name: _acme-challenge
Value: [SSL validation record - will be provided]
TTL: 300

Timeline: Please add these records within 24 hours. Your website will be live 2-4 hours after DNS propagation.

Best regards,
DTL-Global Team
```

### 4. Stripe Billing Setup (Manual)

**Stripe Dashboard:**
- [ ] Create customer: "Business Center Solutions"
- [ ] Email: aduarte@businesscentersolutions.net
- [ ] Create subscription:
  - Product: "DTL-Global Free Website + Discounted Maintenance"
  - Price: $20/month
  - Start date: Today
  - Description: "Monthly maintenance for businesscentersolutions.net"

### 5. Customer Communication

**Welcome Email Template:**

```
Subject: Welcome to DTL-Global - Your Website is Being Built!

Hi Alondra,

Welcome to DTL-Global! We're excited to build your website for Business Center Solutions.

PROJECT DETAILS:
• Domain: businesscentersolutions.net
• Package: Free Website + Discounted Maintenance
• Monthly Fee: $20/month
• GitHub Repository: https://github.com/tolkiger/businesscenter

NEXT STEPS:
1. We're deploying your website infrastructure on AWS
2. You'll receive DNS configuration instructions within 24 hours
3. Your website will be live 2-4 hours after DNS setup
4. We'll schedule a training session once everything is ready

BILLING:
• Setup Fee: $0 (waived)
• Monthly Maintenance: $20/month (starts today)
• First invoice will be sent shortly

SUPPORT:
• Email: support@dtl-global.org
• Project ID: DTL-BUSINESSCENTERSOLUTIONS-20260323

We'll keep you updated on progress!

Best regards,
DTL-Global Team
```

## Completion Checklist

- [ ] HubSpot contact and deal created
- [ ] AWS infrastructure deployed (S3, CloudFront, SSL)
- [ ] DNS instructions sent to customer
- [ ] Stripe subscription created and activated
- [ ] Welcome email sent to customer
- [ ] Project status updated to "In Progress - Awaiting DNS"
- [ ] Follow-up scheduled for DNS configuration verification

## Timeline

- **Today**: Infrastructure deployment, HubSpot/Stripe setup, customer communication
- **Within 24 hours**: DNS records provided to customer
- **2-4 hours after DNS**: Website live and functional
- **Within 48 hours**: Customer training session scheduled

## Support Information

**Customer Contact**: aduarte@businesscentersolutions.net  
**Project ID**: DTL-BUSINESSCENTERSOLUTIONS-20260323  
**GitHub Repo**: https://github.com/tolkiger/businesscenter  
**Monthly Billing**: $20 (starts immediately)  