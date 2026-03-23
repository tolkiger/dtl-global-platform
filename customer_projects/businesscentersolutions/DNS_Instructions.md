# DNS Configuration Instructions for Business Center Solutions

## Domain: businesscentersolutions.net
**DNS Provider**: GoDaddy  
**Website**: AWS S3 + CloudFront  
**SSL**: AWS Certificate Manager  

---

## Required DNS Records

### 1. Website Routing Records

Add these records in your GoDaddy DNS management:

```
Record Type: CNAME
Name: www
Value: d1234567890.cloudfront.net
TTL: 300

Record Type: A  
Name: @
Value: 192.0.2.1
TTL: 300
```

*Note: The actual CloudFront domain and IP addresses will be provided once deployment is complete.*

### 2. SSL Certificate Validation

For SSL certificate validation, add this temporary record:

```
Record Type: CNAME
Name: _acme-challenge
Value: [Validation CNAME provided by AWS]
TTL: 300
```

*This record can be removed after SSL certificate is validated (usually within 24 hours).*

---

## Step-by-Step GoDaddy Configuration

### Step 1: Access GoDaddy DNS Management
1. Log into your GoDaddy account
2. Go to "My Products" > "DNS" 
3. Click "Manage" next to businesscentersolutions.net

### Step 2: Add CNAME Record for www
1. Click "Add" button
2. Select "CNAME" as record type
3. Enter "www" in the Name field
4. Enter the CloudFront domain in the Value field
5. Set TTL to 300
6. Click "Save"

### Step 3: Add A Record for Root Domain
1. Click "Add" button  
2. Select "A" as record type
3. Leave Name field empty (for root domain @)
4. Enter the provided IP address in the Value field
5. Set TTL to 300
6. Click "Save"

### Step 4: Add SSL Validation Record
1. Click "Add" button
2. Select "CNAME" as record type  
3. Enter "_acme-challenge" in the Name field
4. Enter the AWS validation CNAME in the Value field
5. Set TTL to 300
6. Click "Save"

---

## Verification Steps

### 1. DNS Propagation Check
- Use online tools like whatsmydns.net to verify records are propagating
- Full propagation can take up to 48 hours but usually completes within 2-4 hours

### 2. Website Accessibility Test
- Test https://www.businesscentersolutions.net
- Test https://businesscentersolutions.net  
- Both should load the website with valid SSL certificate

### 3. SSL Certificate Validation
- Check that the SSL certificate shows as valid
- Certificate should be issued by Amazon (AWS Certificate Manager)

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

If you encounter any issues with DNS configuration:

**DTL-Global Support**  
Email: support@dtl-global.org  
Phone: [Support phone number]  
Project ID: DTL-BUSINESSCENTERSOLUTIONS-20261223

**What to include in support requests:**
- Domain name: businesscentersolutions.net
- Screenshot of GoDaddy DNS records
- Error messages (if any)
- Time when you added the records

---

## Post-Launch Checklist

After DNS records are configured and propagated:

- [ ] Website loads at https://www.businesscentersolutions.net
- [ ] Website loads at https://businesscentersolutions.net  
- [ ] SSL certificate shows as valid (green lock icon)
- [ ] All pages and links work correctly
- [ ] Contact forms submit successfully
- [ ] Website is mobile-responsive
- [ ] Page load speed is under 3 seconds

**Once all items are checked, your website is fully live and operational!**