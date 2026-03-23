# Manual Onboarding: Business Center Solutions

**Status**: API deployed but Lambda import issues detected  
**Approach**: Manual onboarding to get customer live immediately  
**Customer**: Business Center Solutions  

## Customer Details
- **Company**: Business Center Solutions
- **Contact**: Alondra Duarte (aduarte@businesscentersolutions.net)
- **Phone**: (816) 204-7169
- **Domain**: businesscentersolutions.net (GoDaddy DNS)
- **Package**: Free Website + Discounted Maintenance ($0 setup / $20 monthly)
- **GitHub**: https://github.com/tolkiger/businesscenter
- **Timeline**: ASAP (rush delivery)

## Immediate Actions Required

### 1. HubSpot CRM Setup ✅ READY
**Manual Steps:**
```
Login to HubSpot → Contacts → Create Contact
- Name: Alondra Duarte
- Email: aduarte@businesscentersolutions.net
- Phone: (816) 204-7169
- Company: Business Center Solutions
- Industry: Consulting

Create Deal:
- Deal Name: "Business Center Solutions - Free Website + Discounted"
- Pipeline: DTL Onboarding
- Stage: Build Website
- Deal Amount: $0 (setup fee)
- Monthly Value: $20
- Close Date: Today
```

### 2. AWS Infrastructure Deployment ✅ READY
**Manual Steps via AWS Console:**

**S3 Bucket:**
```
Bucket Name: businesscentersolutions-net-website
Region: us-east-1
Static Website Hosting: Enabled
Index Document: index.html
Public Read Access: Enabled
```

**CloudFront Distribution:**
```
Origin: businesscentersolutions-net-website.s3.us-east-1.amazonaws.com
Alternate Domain Names: 
- businesscentersolutions.net
- www.businesscentersolutions.net
Price Class: Use Only US, Canada and Europe
Default Root Object: index.html
```

**SSL Certificate (ACM):**
```
Domain Names:
- businesscentersolutions.net
- *.businesscentersolutions.net
Validation Method: DNS validation
```

### 3. GitHub Integration ✅ READY
**Repository**: https://github.com/tolkiger/businesscenter

**GitHub Actions Setup:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to S3
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-east-1
    - name: Deploy to S3
      run: |
        aws s3 sync . s3://businesscentersolutions-net-website --delete
        aws cloudfront create-invalidation --distribution-id EXXXXXXXXXXXXX --paths "/*"
```

### 4. DNS Instructions for Customer ✅ READY
**Email to Customer:**
```
Subject: DNS Configuration Required - Business Center Solutions Website

Hi Alondra,

Your website infrastructure is ready! Please add these DNS records in your GoDaddy account:

WEBSITE ROUTING:
Record Type: CNAME
Name: www
Value: [CloudFront distribution domain]
TTL: 300

Record Type: A
Name: @
Value: [CloudFront IP or use ALIAS to CloudFront]
TTL: 300

SSL CERTIFICATE VALIDATION:
Record Type: CNAME
Name: _acme-challenge
Value: [SSL validation record from ACM]
TTL: 300

Timeline: Please add these within 24 hours. Website will be live 2-4 hours after DNS propagation.

Best regards,
DTL-Global Team
```

### 5. Stripe Billing Setup ✅ READY
**Stripe Dashboard Steps:**
```
Create Customer:
- Name: Business Center Solutions
- Email: aduarte@businesscentersolutions.net
- Description: Free Website + Discounted Maintenance

Create Subscription:
- Product: DTL-Global Maintenance
- Price: $20/month
- Start Date: Today
- Description: Monthly maintenance for businesscentersolutions.net
```

### 6. Customer Communication ✅ READY
**Welcome Email Template:**
```
Subject: Welcome to DTL-Global - Your Website is Being Deployed!

Hi Alondra,

Welcome to DTL-Global! We're excited to work with Business Center Solutions.

PROJECT STATUS:
✅ Website code ready: https://github.com/tolkiger/businesscenter
✅ AWS infrastructure deployed
✅ SSL certificate requested
⏳ DNS configuration (your action required)

NEXT STEPS:
1. Add DNS records in GoDaddy (instructions attached)
2. Website will be live within 2-4 hours
3. We'll schedule training session once live

BILLING:
• Setup Fee: $0 (waived for Free Website package)
• Monthly Maintenance: $20/month (starts today)
• First invoice sent separately

SUPPORT:
• Email: support@dtl-global.org
• Project ID: DTL-BUSINESSCENTERSOLUTIONS-20260323

We'll keep you updated on progress!

Best regards,
DTL-Global Team
```

## Completion Checklist

- [ ] HubSpot contact and deal created
- [ ] S3 bucket created and configured
- [ ] CloudFront distribution deployed
- [ ] SSL certificate requested
- [ ] GitHub Actions workflow configured
- [ ] DNS instructions sent to customer
- [ ] Stripe subscription created
- [ ] Welcome email sent
- [ ] Project status updated to "Awaiting DNS Configuration"

## Timeline

- **Today**: Complete all infrastructure and setup
- **Within 24 hours**: Customer adds DNS records
- **2-4 hours after DNS**: Website live and functional
- **Within 48 hours**: Customer training session

## API Status Note

The API Gateway is deployed but Lambda functions have import path issues that need resolution:
- SSM parameters are correctly configured
- Python dependencies are installed
- Import paths need adjustment for Lambda environment
- Manual process ensures customer gets onboarded immediately while API is refined

## Next Steps After Manual Completion

1. Fix Lambda import paths
2. Test API endpoints
3. Migrate to automated onboarding for future customers
4. Document lessons learned for production deployment