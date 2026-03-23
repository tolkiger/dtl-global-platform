# DNS Setup: Business Center Solutions

Domain: businesscentersolutions.net
Provider: Customer Managed

## Required Records
```
CNAME: www → [CloudFront-URL-from-deployment]
A: @ → [IP-from-deployment]
```

## SSL Validation
```
CNAME: _acme-challenge → [AWS-validation-record]
```

Timeline: 2-24 hours after deployment
