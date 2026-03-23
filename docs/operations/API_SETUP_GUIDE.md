# API Setup Guide - Production Deployment

## Current Status
✅ **API Gateway Deployed**: `https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod/`  
❌ **Lambda Functions Failing**: 502 Internal Server Errors  
❌ **Missing Dependencies & Configuration**  

## Required Setup Steps

### 1. Configure AWS SSM Parameters

The Lambda functions need API keys stored in AWS Systems Manager Parameter Store:

```bash
# HubSpot API Configuration
aws ssm put-parameter \
  --name "/dtl-global-platform/hubspot/access-token" \
  --value "YOUR_HUBSPOT_ACCESS_TOKEN" \
  --type "SecureString" \
  --description "HubSpot API access token"

# Stripe API Configuration  
aws ssm put-parameter \
  --name "/dtl-global-platform/stripe/secret-key" \
  --value "sk_live_YOUR_STRIPE_SECRET_KEY" \
  --type "SecureString" \
  --description "Stripe secret key (live mode)"

aws ssm put-parameter \
  --name "/dtl-global-platform/stripe/connect-client-id" \
  --value "ca_YOUR_STRIPE_CONNECT_CLIENT_ID" \
  --type "SecureString" \
  --description "Stripe Connect client ID"

# Anthropic API Configuration
aws ssm put-parameter \
  --name "/dtl-global-platform/anthropic/api-key" \
  --value "sk-ant-YOUR_ANTHROPIC_API_KEY" \
  --type "SecureString" \
  --description "Anthropic Claude API key"
```

### 2. Verify Lambda Dependencies

The CDK deployment should have included Lambda layers with required Python packages:
- `hubspot-api-client`
- `stripe`
- `anthropic`
- `boto3` (included by default)
- `requests`

### 3. Check CloudWatch Logs

View Lambda function logs to identify specific errors:

```bash
# Check logs for each Lambda function
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/DtlApi"

# View recent logs (replace with actual function name)
aws logs tail /aws/lambda/DtlApi-HandlerCrmSetup --follow
```

### 4. Test Individual Functions

Once configured, test each endpoint:

```bash
# Test HubSpot CRM Setup
curl -X POST https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod/crm-setup \
  -H "Content-Type: application/json" \
  -d '{
    "client_info": {
      "company": "Test Company",
      "email": "test@example.com",
      "contact_name": "Test User"
    },
    "crm_config": {
      "pipeline": "dtl_onboarding",
      "stage": "Build Website"
    }
  }'

# Test Website Deployment
curl -X POST https://vxdtzyxui5.execute-api.us-east-1.amazonaws.com/prod/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "test.com",
    "client_info": {"company": "Test"},
    "deployment_config": {
      "source": "github",
      "repository": "https://github.com/user/repo"
    }
  }'
```

## Business Center Solutions - Next Steps

Once the API is configured, continue the onboarding:

```bash
# Run production onboarding with working API
python scripts/production_onboarding.py \
  customer_projects/businesscentersolutions/DTL-BUSINESSCENTERSOLUTIONS-20260323.json
```

**Expected Results:**
- ✅ HubSpot contact and deal created
- ✅ S3 bucket and CloudFront distribution deployed
- ✅ SSL certificate requested and validated
- ✅ Stripe subscription created ($20/month)
- ✅ Customer notification emails sent

## Manual Fallback Process

If API setup takes time, you can manually complete the onboarding:

### 1. Manual HubSpot Setup
- Create contact: Alondra Duarte (aduarte@businesscentersolutions.net)
- Create deal: "Business Center Solutions - Free Website + Discounted"
- Set deal amount: $0 setup, $20/month recurring

### 2. Manual Infrastructure Deployment
```bash
# Deploy S3 bucket and CloudFront for businesscentersolutions.net
# Connect to GitHub repo: https://github.com/tolkiger/businesscenter
# Request SSL certificate for businesscentersolutions.net
```

### 3. Manual DNS Instructions
Provide customer with DNS records:
```
CNAME: www → [CloudFront distribution domain]
A: @ → [CloudFront IP or alias]
CNAME: _acme-challenge → [SSL validation record]
```

### 4. Manual Stripe Setup
- Create customer: Business Center Solutions
- Create subscription: $20/month for "Free Website + Discounted Maintenance"
- Send invoice for first month

## Troubleshooting Common Issues

### Lambda Import Errors
- Check that all Python dependencies are included in Lambda layers
- Verify import paths in Lambda functions
- Ensure shared modules are properly packaged

### API Key Issues
- Verify SSM parameter names match exactly
- Check IAM permissions for Lambda to read SSM parameters
- Ensure API keys are valid and have correct permissions

### Timeout Issues
- Increase Lambda timeout settings in CDK
- Optimize Lambda function code for faster execution
- Consider Lambda provisioned concurrency for frequently used functions

## Production Checklist

- [ ] All SSM parameters configured
- [ ] Lambda functions deploy successfully
- [ ] API endpoints return 200 status codes
- [ ] HubSpot integration tested
- [ ] Stripe integration tested
- [ ] Email notifications working
- [ ] DNS and SSL automation functional
- [ ] Customer onboarding end-to-end test passed