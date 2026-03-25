# Manual Onboarding: Business Center Solutions

**Customer**: Business Center Solutions  
**Contact**: Alondra Duarte (aduarte@businesscentersolutions.net)  
**Package** (customer-onboarding skill): **Friends & Family** — **$100** one-time setup + **$20/mo** hosting/maintenance  
**Note**: Skill lists Friends & Family as **$0 setup / $20 mo**; this deal adds a **$100 setup** as agreed.  
**GitHub Repo**: https://github.com/tolkiger/businesscenter  
**Domain**: businesscentersolutions.net (GoDaddy DNS)  
**Project file**: `customer_projects/businesscentersolutions/DTL-BUSINESSCENTERSOLUTIONS-20260323.json`  

## How the website gets created (onboarding flow)

The **site itself** is not generated inside Lambda. The intended flow is:

1. **Build in Rocket.new** (or another toolchain you use): design and implement the customer site in Rocket.new.
2. **Export to GitHub**: Rocket.new Code View → GitHub → push to a repo (this project uses `tolkiger/businesscenter`; the skill’s naming pattern is often `{company}-website`).
3. **Host on AWS**: CI (e.g. GitHub Actions) builds static output and syncs to **S3**; **CloudFront** serves it with **TLS (ACM)**. Your **`POST /deploy`** path (and/or manual AWS steps in this checklist) wires infra to that repo’s build output.
4. **DNS**: Customer (GoDaddy) points the domain at CloudFront (CNAME/alias + any ACM validation records).

So: **Lambdas orchestrate CRM, billing, DNS instructions, deploy API** — the **HTML/JS/assets** come from **your build (Rocket.new → GitHub → build → S3)**.

## Production gate (before real charges)

Per `.cursor/skills/customer-onboarding/SKILL.md`: confirm **Stripe live mode**, SSM live keys, and `scripts/phase0_stripe_setup.py` for live products before invoicing or subscribing this customer.

## Immediate action items

### 1. HubSpot CRM (manual)

- [ ] **Contact** (if not already present): name, email, phone, company, industry as before.  
- [ ] **Deal**:
  - Deal name: `Business Center Solutions - Friends & Family ($100 setup / $20 mo)`  
  - Pipeline: DTL Onboarding  
  - Stage: Build Website (or current)  
  - Deal amount: **$100** (setup)  
  - Monthly value: **$20**  

### 2. Infrastructure (AWS)

S3, CloudFront, ACM; GitHub Actions from `tolkiger/businesscenter`. See `Deployment_Checklist.md`.

### 3. DNS instructions for customer

Send CloudFront target and ACM validation records when ready.

### 4. Stripe billing (manual)

- [ ] **Customer**: Business Center Solutions — aduarte@businesscentersolutions.net  
- [ ] **One-time setup**: Invoice **$100.00** USD (`invoice_items[].amount` = `10000` cents).  
- [ ] **Subscription**: **$20/month** — use **DTL Friends and Family Hosting** (`dtl_friends_family` in `engine/shared/stripe_client.py`) or equivalent $20/mo recurring price.  

### 5. Customer communication

- **$100** setup + **$20/mo** Friends & Family hosting/maintenance; domain, repo, DNS, support, project ID **DTL-BUSINESSCENTERSOLUTIONS-20260323**.  

## Completion checklist

- [ ] HubSpot deal shows **$100** setup + **$20** MRR  
- [ ] Stripe: **$100** one-time + **$20/mo** subscription  
- [ ] Site pipeline: repo builds and deploys to S3/CloudFront  
- [ ] DNS live  

## Support

**Email**: aduarte@businesscentersolutions.net  
**Project ID**: DTL-BUSINESSCENTERSOLUTIONS-20260323  
