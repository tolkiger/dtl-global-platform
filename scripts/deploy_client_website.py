"""Deploy a client website by adding it to the pipeline-factory repo.

This script automates client website provisioning by adding an entry to
the pipeline-factory's config/websites.json via the GitHub API. When the
commit lands, pipeline-factory's CodePipeline auto-triggers cdk deploy,
which provisions S3 + CloudFront + ACM + Route 53 + a client-specific
CodePipeline for future auto-deploys.

Part of Phase 4 of the DTL-Global Platform.

Usage:
    python scripts/deploy_client_website.py \
        --client-name "Smith Roofing" \
        --github-repo "dtl-client-smith-roofing" \
        --domain "smithroofing.com" \
        [--hosted-zone-id "Z0XXXXXXXXX"] \
        [--hosted-zone-name "smithroofing.com"] \
        [--dry-run]
"""

# === Standard Library Imports ===
import argparse  # Parse command-line arguments
import base64  # Decode/encode GitHub API file content
import json  # Parse and serialize JSON
import os  # Access environment variables
import re  # Regex for slug generation
import sys  # System exit codes

# === Third-Party Imports ===
import boto3  # AWS SDK for Route 53 operations
import requests  # HTTP client for GitHub API calls

# === Optional Imports ===
try:
    from dotenv import load_dotenv  # Load .env file for local development
    import pathlib  # For resolving the .env file path
    # Find the .env file relative to the project root (parent of scripts/)
    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)  # Load from the project root .env
except ImportError:
    pass  # python-dotenv not installed; rely on system env vars

# === Constants ===
PIPELINE_FACTORY_REPO = "tolkiger/pipeline-factory"  # The repo that manages website infrastructure
WEBSITES_CONFIG_PATH = "config/websites.json"  # Path to the websites config in pipeline-factory
GITHUB_API_BASE = "https://api.github.com"  # GitHub API base URL


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for client website deployment.

    Returns:
        Parsed arguments namespace with client-name, github-repo, domain, etc.
    """
    # Create the argument parser with description
    parser = argparse.ArgumentParser(
        description="Deploy a client website via pipeline-factory integration."
    )

    # Required arguments
    parser.add_argument(
        "--client-name",
        required=True,
        help="Client business name (e.g., 'Smith Roofing')"
    )
    parser.add_argument(
        "--github-repo",
        required=True,
        help="GitHub repo name for the client website (e.g., 'dtl-client-smith-roofing')"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="Client website domain (e.g., 'smithroofing.com')"
    )

    # Optional arguments
    parser.add_argument(
        "--hosted-zone-id",
        default=None,
        help="Route 53 hosted zone ID (auto-detected or created if not provided)"
    )
    parser.add_argument(
        "--hosted-zone-name",
        default=None,
        help="Route 53 hosted zone name (defaults to domain if not provided)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to pipeline-factory"
    )

    return parser.parse_args()  # Parse and return the arguments


def slugify(name: str) -> str:
    """Convert a business name to a URL-safe slug.

    Args:
        name: The business name to slugify (e.g., 'Smith Roofing Co.').

    Returns:
        A lowercase, hyphenated slug (e.g., 'smith-roofing-co').
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug  # Return the clean slug


def get_github_token() -> str:
    """Retrieve the GitHub token from environment variables.

    Returns:
        The GitHub Personal Access Token string.

    Raises:
        SystemExit: If no token is found in environment.
    """
    # Try GITHUB_TOKEN first, then GH_TOKEN (used by gh CLI)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if not token:  # No token found in environment
        print("ERROR: GITHUB_TOKEN not found in environment variables.")
        print("Set it in .env file or export GITHUB_TOKEN=ghp_xxxxx")
        sys.exit(1)  # Exit with error code

    return token  # Return the valid token


def get_or_create_hosted_zone(domain: str) -> dict:
    """Get an existing Route 53 hosted zone or create a new one.

    Args:
        domain: The domain name to find or create a hosted zone for.

    Returns:
        A dict with 'id' (hosted zone ID) and 'name' (hosted zone name).
        Example: {'id': 'Z0XXXXXXXXX', 'name': 'smithroofing.com'}

    Raises:
        SystemExit: If Route 53 operations fail.
    """
    # Initialize the Route 53 client
    route53 = boto3.client("route53")

    # Search for an existing hosted zone matching the domain
    try:
        response = route53.list_hosted_zones_by_name(
            DNSName=domain,  # Search by domain name
            MaxItems="1"  # We only need the first match
        )
    except Exception as e:
        print(f"ERROR: Failed to query Route 53: {e}")
        sys.exit(1)

    # Check if a matching hosted zone was found
    zones = response.get("HostedZones", [])  # Get the list of zones
    for zone in zones:
        # Route 53 returns zone names with trailing dot
        zone_name = zone["Name"].rstrip(".")  # Remove trailing dot for comparison
        if zone_name == domain:  # Exact match found
            zone_id = zone["Id"].split("/")[-1]  # Extract ID from full path
            print(f"  Found existing hosted zone: {zone_id} ({zone_name})")
            return {"id": zone_id, "name": zone_name}

    # No existing zone found — create a new one
    print(f"  No hosted zone found for {domain}. Creating one...")
    try:
        create_response = route53.create_hosted_zone(
            Name=domain,  # The domain name for the new zone
            CallerReference=f"dtl-global-{domain}-{os.urandom(4).hex()}",  # Unique reference
            HostedZoneConfig={
                "Comment": f"Managed by DTL-Global Platform for {domain}"
            }
        )
    except Exception as e:
        print(f"ERROR: Failed to create hosted zone: {e}")
        sys.exit(1)

    # Extract the new zone details
    zone_id = create_response["HostedZone"]["Id"].split("/")[-1]  # Extract clean ID
    nameservers = create_response["DelegationSet"]["NameServers"]  # Get NS records

    # Print nameservers for DNS delegation
    print(f"  Created hosted zone: {zone_id}")
    print(f"  IMPORTANT: Update your domain's nameservers to:")
    for ns in nameservers:  # Print each nameserver
        print(f"    - {ns}")
    print(f"  (If domain is on Route 53, this is automatic.)")

    return {"id": zone_id, "name": domain}  # Return the new zone info


def read_pipeline_factory_config(token: str) -> tuple:
    """Read the current websites.json from the pipeline-factory repo.

    Args:
        token: GitHub Personal Access Token with repo scope.

    Returns:
        A tuple of (config_dict, file_sha) where config_dict is the parsed
        JSON content and file_sha is needed for the update API call.

    Raises:
        SystemExit: If the GitHub API call fails.
    """
    # Build the GitHub API URL for the config file
    url = f"{GITHUB_API_BASE}/repos/{PIPELINE_FACTORY_REPO}/contents/{WEBSITES_CONFIG_PATH}"

    # Set up authentication headers
    headers = {
        "Authorization": f"Bearer {token}",  # Auth with the GitHub token
        "Accept": "application/vnd.github.v3+json",  # Use v3 API
    }

    # Make the GET request to read the file
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to read pipeline-factory config: {e}")
        sys.exit(1)

    # Parse the response
    data = response.json()  # Get the JSON response
    file_sha = data["sha"]  # SHA is required for updating the file
    content_b64 = data["content"]  # File content is base64 encoded

    # Decode the base64 content and parse as JSON
    content_bytes = base64.b64decode(content_b64)  # Decode from base64
    config = json.loads(content_bytes.decode("utf-8"))  # Parse JSON string

    return config, file_sha  # Return the config and SHA


def check_duplicate(config: dict, site_name: str, domain: str) -> bool:
    """Check if a site already exists in the pipeline-factory config.

    Args:
        config: The parsed websites.json config dict.
        site_name: The site name to check for (e.g., 'smith-roofing-website').
        domain: The domain to check for (e.g., 'smithroofing.com').

    Returns:
        True if a duplicate is found, False otherwise.
    """
    # Iterate through existing websites to check for duplicates
    for site in config.get("websites", []):
        if site.get("siteName") == site_name:  # Check by site name
            print(f"  WARNING: Site '{site_name}' already exists in pipeline-factory.")
            return True  # Duplicate found by name
        if site.get("domainName") == domain:  # Check by domain
            print(f"  WARNING: Domain '{domain}' already exists in pipeline-factory.")
            return True  # Duplicate found by domain

    return False  # No duplicate found


def add_site_to_config(config: dict, client_name: str, github_repo: str,
                       domain: str, hosted_zone_id: str,
                       hosted_zone_name: str) -> dict:
    """Add a new client website entry to the pipeline-factory config.

    Args:
        config: The current websites.json config dict.
        client_name: The client business name.
        github_repo: The GitHub repo name for the client website.
        domain: The client website domain.
        hosted_zone_id: The Route 53 hosted zone ID.
        hosted_zone_name: The Route 53 hosted zone name.

    Returns:
        The updated config dict with the new site entry added.
    """
    # Create the new site entry matching pipeline-factory's expected format
    new_site = {
        "siteName": f"{slugify(client_name)}-website",  # Slugified name + '-website'
        "githubRepo": github_repo,  # The client's website repo
        "domainName": domain,  # The client's domain
        "hostedZoneId": hosted_zone_id,  # Route 53 hosted zone ID
        "hostedZoneName": hosted_zone_name,  # Route 53 hosted zone name
        "menuPdfEnabled": False  # Default: no menu PDF feature
    }

    # Add the new entry to the websites array
    config["websites"].append(new_site)

    return config  # Return the updated config


def commit_config(token: str, config: dict, file_sha: str,
                  client_name: str) -> None:
    """Commit the updated websites.json back to the pipeline-factory repo.

    Args:
        token: GitHub Personal Access Token.
        config: The updated config dict to commit.
        file_sha: The current file SHA (required by GitHub API for updates).
        client_name: The client name (used in commit message).

    Raises:
        SystemExit: If the GitHub API call fails.
    """
    # Build the GitHub API URL for updating the file
    url = f"{GITHUB_API_BASE}/repos/{PIPELINE_FACTORY_REPO}/contents/{WEBSITES_CONFIG_PATH}"

    # Set up authentication headers
    headers = {
        "Authorization": f"Bearer {token}",  # Auth with the GitHub token
        "Accept": "application/vnd.github.v3+json",  # Use v3 API
    }

    # Serialize the config to JSON with pretty formatting
    updated_content = json.dumps(config, indent=2) + "\n"  # Add trailing newline

    # Encode the content to base64 (required by GitHub API)
    content_b64 = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")

    # Build the request payload
    payload = {
        "message": f"feat: add {client_name} website pipeline",  # Commit message
        "content": content_b64,  # Base64 encoded file content
        "sha": file_sha,  # Current file SHA for conflict detection
        "branch": "main"  # Commit to main branch
    }

    # Make the PUT request to update the file
    try:
        response = requests.put(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to commit to pipeline-factory: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"  Response: {e.response.text}")  # Print error details
        sys.exit(1)

    print(f"  Committed to pipeline-factory repo successfully.")


def update_hubspot_deal(client_name: str, domain: str,
                        github_repo: str) -> None:
    """Update the HubSpot deal with deployment information.

    Args:
        client_name: The client business name (used to find the deal).
        domain: The client website domain.
        github_repo: The GitHub repo name.
    """
    # Get HubSpot token from environment
    hubspot_token = os.environ.get("HUBSPOT_ACCESS_TOKEN")

    if not hubspot_token:  # No token available
        print("  SKIP: HUBSPOT_ACCESS_TOKEN not set. Skipping HubSpot update.")
        return  # Skip HubSpot update gracefully

    # Search for the deal by client business name
    search_url = "https://api.hubapi.com/crm/v3/objects/deals/search"
    headers = {
        "Authorization": f"Bearer {hubspot_token}",
        "Content-Type": "application/json"
    }
    search_payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "client_business_name",
                "operator": "EQ",
                "value": client_name
            }]
        }],
        "properties": ["dealname", "client_business_name", "onboarding_status"]
    }

    try:
        # Search for the deal
        resp = requests.post(search_url, headers=headers, json=search_payload, timeout=30)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        if not results:  # No deal found
            print(f"  SKIP: No HubSpot deal found for '{client_name}'.")
            return

        deal_id = results[0]["id"]  # Get the first matching deal ID

        # Update the deal properties
        update_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
        update_payload = {
            "properties": {
                "onboarding_status": "deploying",  # Mark as deploying
                "github_repo": github_repo,  # Set the repo name
                "client_website_domain": domain,  # Set the domain
                "cloudfront_url": f"https://{domain}"  # Set the website URL
            }
        }
        resp = requests.patch(update_url, headers=headers, json=update_payload, timeout=30)
        resp.raise_for_status()
        print(f"  Updated HubSpot deal {deal_id} for '{client_name}'.")

    except requests.exceptions.RequestException as e:
        # Don't fail the whole deployment if HubSpot update fails
        print(f"  WARNING: Failed to update HubSpot: {e}")


def main() -> None:
    """Main entry point for the client website deployment script.

    Orchestrates the full deployment flow:
    1. Parse arguments and validate inputs
    2. Get or create Route 53 hosted zone
    3. Read pipeline-factory config from GitHub
    4. Add new client entry (if not duplicate)
    5. Commit updated config to pipeline-factory
    6. Update HubSpot deal
    7. Print summary
    """
    # Parse command-line arguments
    args = parse_args()

    # Print header
    print("=" * 60)
    print("  DTL-Global Platform — Client Website Deployment")
    print("=" * 60)
    print()
    print(f"  Client:      {args.client_name}")
    print(f"  GitHub Repo: {args.github_repo}")
    print(f"  Domain:      {args.domain}")
    print(f"  Dry Run:     {args.dry_run}")
    print()

    # Step 1: Get GitHub token
    print("[1/6] Authenticating with GitHub...")
    token = get_github_token()  # Get token from environment
    print("  GitHub token found.")

    # Step 2: Get or create Route 53 hosted zone
    print(f"[2/6] Setting up DNS for {args.domain}...")
    if args.hosted_zone_id:  # User provided the zone ID
        zone_info = {
            "id": args.hosted_zone_id,
            "name": args.hosted_zone_name or args.domain
        }
        print(f"  Using provided hosted zone: {zone_info['id']}")
    else:  # Auto-detect or create
        zone_info = get_or_create_hosted_zone(args.domain)

    # Step 3: Read current pipeline-factory config
    print("[3/6] Reading pipeline-factory config...")
    config, file_sha = read_pipeline_factory_config(token)
    print(f"  Found {len(config.get('websites', []))} existing sites.")

    # Step 4: Check for duplicates
    print("[4/6] Checking for duplicates...")
    site_name = f"{slugify(args.client_name)}-website"  # Generate the site name
    if check_duplicate(config, site_name, args.domain):
        print("  Site already exists. No changes needed.")
        print()
        print("RESULT: No changes made (duplicate detected).")
        sys.exit(0)  # Exit cleanly — not an error
    print("  No duplicates found. Proceeding.")

    # Step 5: Add new site and commit
    print("[5/6] Adding client to pipeline-factory...")
    updated_config = add_site_to_config(
        config=config,
        client_name=args.client_name,
        github_repo=args.github_repo,
        domain=args.domain,
        hosted_zone_id=zone_info["id"],
        hosted_zone_name=zone_info["name"]
    )

    if args.dry_run:  # Preview mode — don't commit
        print("  DRY RUN — would add this entry:")
        new_entry = updated_config["websites"][-1]  # Get the last entry (the new one)
        print(f"    {json.dumps(new_entry, indent=4)}")
        print()
        print("RESULT: Dry run complete. No changes committed.")
        sys.exit(0)

    # Commit the updated config to pipeline-factory
    commit_config(token, updated_config, file_sha, args.client_name)

    # Step 6: Update HubSpot deal
    print("[6/6] Updating HubSpot deal...")
    update_hubspot_deal(args.client_name, args.domain, args.github_repo)

    # Print summary
    print()
    print("=" * 60)
    print("  DEPLOYMENT TRIGGERED SUCCESSFULLY")
    print("=" * 60)
    print()
    print(f"  Website URL:    https://{args.domain}")
    print(f"  GitHub Repo:    tolkiger/{args.github_repo}")
    print(f"  Hosted Zone:    {zone_info['id']}")
    print(f"  Pipeline:       pipeline-factory will auto-deploy via CodePipeline")
    print()
    print("  NEXT STEPS:")
    print("  1. Pipeline-factory CodePipeline will trigger within ~1 minute")
    print("  2. CDK will deploy: S3 + CloudFront + ACM + Route 53 + client CodePipeline")
    print("  3. Website will be live at https://{} within ~10 minutes".format(args.domain))
    print("  4. Client gets their own CodePipeline for future auto-deploys")
    print()
    print("  If domain was just registered or NS records need updating,")
    print("  DNS propagation may take up to 48 hours.")
    print("=" * 60)


if __name__ == "__main__":
    main()