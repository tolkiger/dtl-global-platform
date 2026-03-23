# DNS Configuration Instructions for Business Center Solutions

## Domain: businesscentersolutions.net
**DNS Provider**: GoDaddy
**Website**: AWS S3 + CloudFront
**SSL**: AWS Certificate Manager

---

## Required DNS Records

### 1. Website Routing Records

Add these records in your DNS management:

```
Record Type: CNAME
Name: www
Value: [CloudFront domain will be provided]
TTL: 300

Record Type: A
Name: @
Value: [IP address will be provided]
TTL: 300
```

### 2. SSL Certificate Validation

For SSL certificate validation, add this temporary record:

```
Record Type: CNAME
Name: _acme-challenge
Value: [Validation CNAME provided by AWS]
TTL: 300
```

---

## Timeline Expectations

| Step | Expected Time |
|------|---------------|
| DNS Record Addition | Immediate |
| DNS Propagation | 2-4 hours |
| SSL Certificate Validation | 2-24 hours |
| Full Website Availability | 4-24 hours |

---

## Support Contact

**DTL-Global Support**
Email: support@dtl-global.org
Project ID: TBD
