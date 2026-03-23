# Customer Projects Directory

This directory contains organized project files for all DTL-Global customers.

## Directory Structure

```
customer_projects/
├── {company_name}/                    # Individual company directories
│   ├── {PROJECT_ID}.json            # Project data and configuration
│   ├── DNS_Instructions.md          # DNS setup guide for customer
│   ├── Project_Summary.md           # Project overview and status
│   ├── Customer_Training_Guide.md   # Training materials
│   └── additional_files/            # Any additional customer files
└── README.md                        # This file
```

## File Naming Conventions

### Company Directory Names
- Lowercase, underscores for spaces: `business_center_solutions`
- Remove special characters: `acme_corp` (not `acme-corp.`)
- Keep consistent with project IDs

### Project ID Format
- `DTL-{COMPANY_UPPER}-{YYYYMMDD}`
- Example: `DTL-BUSINESSCENTERSOLUTIONS-20261223`

### Standard Files
- **Project Data**: `{PROJECT_ID}.json` - Complete project configuration
- **DNS Guide**: `DNS_Instructions.md` - Customer DNS setup instructions  
- **Project Summary**: `Project_Summary.md` - Overview and status
- **Training**: `Customer_Training_Guide.md` - Customer training materials

## Usage

### Creating New Customer Project
```bash
# Interactive data collection
python scripts/start_customer_onboarding.py

# Automated onboarding
python scripts/onboard_customer.py {company_name}
```

### Finding Customer Files
```bash
# List all customers
ls customer_projects/

# View specific customer
ls customer_projects/{company_name}/

# View project data
cat customer_projects/{company_name}/{PROJECT_ID}.json
```

## Customer Types Supported

| Package Type | Setup Fee | Monthly Fee | Services |
|--------------|-----------|-------------|----------|
| Friends & Family | $0 | $20 | Website, DNS, Support |
| Free Website + Discounted | $0 | $20 | Website, DNS, Support |
| Starter | $500 | $49 | Website, DNS, Support |
| Growth | $1,500 | $149 | Website, CRM, Payments, Email |
| Professional | $2,500 | $249 | Full suite + AI features |
| Premium | $5,000 | $499 | Enterprise features |
| Maintenance Only | $0 | $99 | Existing website maintenance |
| CRM + Payments Only | $750 | $99 | No website, CRM/Stripe only |

## Support

For questions about customer projects or onboarding:
- **Documentation**: `docs/operations/REAL_CUSTOMER_PREP.md`
- **Onboarding Skill**: `.cursor/skills/customer-onboarding/SKILL.md`
- **Support Email**: support@dtl-global.org