#!/usr/bin/env python3
"""Create HubSpot pipeline, property groups, and custom properties for DTL-Global Phase 0.

This script is idempotent: existing resources are skipped and reported.
Reads HUBSPOT_ACCESS_TOKEN from the environment (use .env for local runs).
"""

from __future__ import annotations

import json  # Serialize request bodies for HubSpot REST calls
import os  # Read environment variables for HUBSPOT_ACCESS_TOKEN
import sys  # Exit with non-zero status on fatal errors
from typing import Any  # Type hints for HubSpot JSON payloads
from urllib.error import HTTPError, URLError  # Handle HTTP failures from urllib
from urllib.request import Request, urlopen  # Make HTTPS calls without extra deps

# HubSpot CRM API base URL for all requests in this script
HUBSPOT_API_BASE: str = "https://api.hubapi.com"
# Pipeline label exactly as specified in DTL_MASTER_PLAN.md Section 7.2
PIPELINE_LABEL: str = "DTL-Global Client Onboarding"
# Display order for the new pipeline relative to other deal pipelines
PIPELINE_DISPLAY_ORDER: int = 1
# Internal name for the deal property group that holds client onboarding fields
DEAL_GROUP_NAME: str = "dtl_client_info"
# Human-readable label for the deal property group shown in HubSpot UI
DEAL_GROUP_LABEL: str = "DTL Client Info"
# Internal name for the contact property group
CONTACT_GROUP_NAME: str = "dtl_contact_info"
# Human-readable label for the contact property group
CONTACT_GROUP_LABEL: str = "DTL Contact Info"
# Ten deal stages with labels and monotonic probabilities (deals require probability metadata)
PIPELINE_STAGES: list[dict[str, Any]] = [
    {"label": "New Lead", "displayOrder": 0, "metadata": {"probability": "0.10"}},
    {"label": "Discovery", "displayOrder": 1, "metadata": {"probability": "0.15"}},
    {"label": "Proposal & Bid", "displayOrder": 2, "metadata": {"probability": "0.25"}},
    {"label": "Contract & Deposit", "displayOrder": 3, "metadata": {"probability": "0.35"}},
    {"label": "Build Website", "displayOrder": 4, "metadata": {"probability": "0.45"}},
    {"label": "Deploy & Connect", "displayOrder": 5, "metadata": {"probability": "0.60"}},
    {"label": "Final Payment", "displayOrder": 6, "metadata": {"probability": "0.75"}},
    {"label": "Live & Monthly", "displayOrder": 7, "metadata": {"probability": "1.00"}},
    {"label": "Nurture", "displayOrder": 8, "metadata": {"probability": "0.20"}},
    {"label": "Lost", "displayOrder": 9, "metadata": {"probability": "0.00"}},
]


def _select_options(pairs: list[tuple[str, str]]) -> list[dict[str, str]]:
    """Build HubSpot enumeration option objects from (value, label) pairs.

    Args:
        pairs: Tuples of internal value and display label for each picklist option.

    Returns:
        A list of dicts with keys label and value for the HubSpot property API.
    """
    return [{"label": lbl, "value": val} for val, lbl in pairs]  # Map tuples to API shape


# Deal custom properties: name, label, type, fieldType, optional options list
DEAL_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "client_type",
        "label": "Client Type",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options(
            [
                ("full_package", "Full Package"),
                ("website_only", "Website Only"),
                ("website_crm", "Website + CRM"),
                ("crm_payments", "CRM + Payments"),
            ]
        ),
    },
    {
        "name": "client_industry",
        "label": "Client Industry",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options(
            [
                ("roofing", "Roofing"),
                ("accounting", "Accounting"),
                ("remodeling", "Remodeling"),
                ("auto_restoration", "Auto Restoration"),
                ("general", "General"),
                ("other", "Other"),
            ]
        ),
    },
    {"name": "client_business_name", "label": "Client Business Name", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "client_website_domain", "label": "Client Website Domain", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {
        "name": "has_existing_domain",
        "label": "Has Existing Domain",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {"name": "domain_registrar", "label": "Domain Registrar", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {
        "name": "has_existing_crm",
        "label": "Has Existing CRM",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {"name": "existing_crm_name", "label": "Existing CRM Name", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {
        "name": "crm_import_status",
        "label": "CRM Import Status",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options(
            [
                ("not_needed", "Not Needed"),
                ("pending", "Pending"),
                ("in_progress", "In Progress"),
                ("complete", "Complete"),
                ("failed", "Failed"),
            ]
        ),
    },
    {
        "name": "needs_website",
        "label": "Needs Website",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "needs_crm",
        "label": "Needs CRM",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "needs_payments",
        "label": "Needs Payments",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "needs_custom_email",
        "label": "Needs Custom Email",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "email_provider",
        "label": "Email Provider",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options(
            [
                ("google_workspace", "Google Workspace"),
                ("microsoft_365", "Microsoft 365"),
                ("none", "None"),
            ]
        ),
    },
    {
        "name": "needs_ai_chatbot",
        "label": "Needs AI Chatbot",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "needs_whatsapp_bot",
        "label": "Needs WhatsApp Bot",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "needs_slack_bot",
        "label": "Needs Slack Bot",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {
        "name": "needs_teams_bot",
        "label": "Needs Teams Bot",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options([("yes", "Yes"), ("no", "No")]),
    },
    {"name": "number_of_employees", "label": "Number of Employees", "type": "number", "fieldType": "number", "groupName": DEAL_GROUP_NAME},
    {"name": "current_tools", "label": "Current Tools", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "project_total_cost", "label": "Project Total Cost", "type": "number", "fieldType": "number", "groupName": DEAL_GROUP_NAME},
    {"name": "deposit_amount", "label": "Deposit Amount", "type": "number", "fieldType": "number", "groupName": DEAL_GROUP_NAME},
    {"name": "monthly_subscription", "label": "Monthly Subscription", "type": "number", "fieldType": "number", "groupName": DEAL_GROUP_NAME},
    {"name": "stripe_customer_id", "label": "Stripe Customer ID", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "stripe_connect_id", "label": "Stripe Connect ID", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "hubspot_portal_id", "label": "HubSpot Portal ID", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "github_repo", "label": "GitHub Repo", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "cloudfront_url", "label": "CloudFront URL", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {"name": "route53_hosted_zone_id", "label": "Route 53 Hosted Zone ID", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
    {
        "name": "onboarding_status",
        "label": "Onboarding Status",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": DEAL_GROUP_NAME,
        "options": _select_options(
            [
                ("not_started", "Not Started"),
                ("in_progress", "In Progress"),
                ("website_building", "Website Building"),
                ("deploying", "Deploying"),
                ("live", "Live"),
                ("on_hold", "On Hold"),
            ]
        ),
    },
    {"name": "custom_requests", "label": "Custom Requests", "type": "string", "fieldType": "textarea", "groupName": DEAL_GROUP_NAME},
    {"name": "ai_bid_amount", "label": "AI Bid Amount", "type": "number", "fieldType": "number", "groupName": DEAL_GROUP_NAME},
    {"name": "ai_bid_notes", "label": "AI Bid Notes", "type": "string", "fieldType": "textarea", "groupName": DEAL_GROUP_NAME},
    {"name": "rocket_prompt", "label": "Rocket Prompt", "type": "string", "fieldType": "textarea", "groupName": DEAL_GROUP_NAME},
    {"name": "seo_keywords", "label": "SEO Keywords", "type": "string", "fieldType": "text", "groupName": DEAL_GROUP_NAME},
]

# Contact custom properties for the dtl_contact_info group
CONTACT_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "contact_role",
        "label": "Contact Role",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": CONTACT_GROUP_NAME,
        "options": _select_options(
            [
                ("owner", "Owner"),
                ("manager", "Manager"),
                ("decision_maker", "Decision Maker"),
                ("technical", "Technical"),
                ("other", "Other"),
            ]
        ),
    },
    {
        "name": "preferred_contact",
        "label": "Preferred Contact",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": CONTACT_GROUP_NAME,
        "options": _select_options(
            [
                ("email", "Email"),
                ("phone", "Phone"),
                ("whatsapp", "WhatsApp"),
                ("text", "Text"),
            ]
        ),
    },
    {
        "name": "referral_source",
        "label": "Referral Source",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": CONTACT_GROUP_NAME,
        "options": _select_options(
            [
                ("referral", "Referral"),
                ("google", "Google"),
                ("social_media", "Social Media"),
                ("cold_outreach", "Cold Outreach"),
                ("networking", "Networking"),
                ("other", "Other"),
            ]
        ),
    },
]


def _auth_error_hint(payload: Any) -> str:
    """Return extra help text when HubSpot returns auth-related errors.

    Args:
        payload: Parsed JSON error body from HubSpot, if any.

    Returns:
        A multi-line string to append to error output, or empty string.
    """
    if not isinstance(payload, dict):  # Only enrich structured HubSpot errors
        return ""  # No hint to add
    category = str(payload.get("category", ""))  # HubSpot error category when present
    message = str(payload.get("message", ""))  # Human-readable API message
    if "EXPIRED" in category or "expired" in message.lower() or "OAuth" in message:  # Bad/expired token pattern
        return (
            "\n  Fix: Use a valid HubSpot developer platform static access token: "
            "upload/install the project in hubspot/dtl-global-platform-app/, then copy the token "
            "from the app component → Auth tab. Put it in .env as HUBSPOT_ACCESS_TOKEN. "
            "See docs/AUTHENTICATION.md. MCP-only credentials will not work here."
        )  # Explain MCP vs CRM API token
    return ""  # No extra hint


def load_hubspot_access_token() -> str:
    """Read and sanity-check HUBSPOT_ACCESS_TOKEN for the HubSpot CRM REST API.

    Expects a developer platform (2025.2) static access token or any valid HubSpot Bearer
    token for the same APIs; format is not limited to `pat-...`.

    Returns:
        The non-empty access token string used for Bearer authentication.

    Raises:
        SystemExit: If the token is missing or still a placeholder.
    """
    token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip()  # Pull token from env
    if not token:  # Guard against empty configuration
        print("ERROR: HUBSPOT_ACCESS_TOKEN is not set. Copy .env.example to .env and export variables.")  # Explain fix
        raise SystemExit(1)  # Abort with failure status
    lowered = token.lower()  # Lowercase for placeholder checks
    if "your_hubspot" in lowered or "replace_with" in lowered or token in ("pat-", "pat"):  # Common placeholders
        print("ERROR: HUBSPOT_ACCESS_TOKEN still looks like a placeholder. Set a real token from docs/AUTHENTICATION.md.")  # Block bad runs
        raise SystemExit(1)  # Stop before useless API calls
    if len(token) < 20:  # Unreasonably short for a HubSpot access token
        print("WARNING: HUBSPOT_ACCESS_TOKEN looks too short. Verify docs/AUTHENTICATION.md.")  # Non-fatal hint
    return token  # Return validated token


def _request(
    method: str,
    path: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | list[Any] | None]:
    """Perform an HTTPS request to the HubSpot API and parse JSON when present.

    Args:
        method: HTTP verb such as GET or POST.
        path: API path beginning with /crm/... (not the full URL).
        token: Bearer token for authorization.
        body: Optional JSON-serializable dict to send as the request body.

    Returns:
        A tuple of HTTP status code and parsed JSON (dict, list, or None for empty body).

    Raises:
        SystemExit: If the network fails before an HTTP response is received.
    """
    url = f"{HUBSPOT_API_BASE}{path}"  # Join base URL with relative API path
    data_bytes: bytes | None = None  # Default to no body for GET requests
    headers = {
        "Authorization": f"Bearer {token}",  # Authenticate with static or compatible HubSpot token
        "Content-Type": "application/json",  # Tell HubSpot we send JSON bodies
    }  # Header dict for urllib
    if body is not None:  # Only serialize when caller provided a payload
        data_bytes = json.dumps(body).encode("utf-8")  # Encode JSON as UTF-8 bytes
    req = Request(url, data=data_bytes, headers=headers, method=method)  # Build urllib Request
    try:
        with urlopen(req, timeout=60) as resp:  # Execute the HTTP call with timeout
            raw = resp.read()  # Read full response bytes
            status = getattr(resp, "status", 200)  # Capture HTTP status when available
            if not raw:  # Handle empty successful bodies
                return status, None  # Return status with no JSON
            parsed = json.loads(raw.decode("utf-8"))  # Parse JSON payloads
            return status, parsed  # Return tuple for callers
    except HTTPError as exc:  # HubSpot returned 4xx/5xx (including 404 for missing resources)
        err_body = exc.read().decode("utf-8", errors="replace")  # Read error payload safely
        if not err_body:  # Some error responses have empty bodies
            return exc.code, {"status": exc.code, "reason": exc.reason}  # Return minimal error info
        try:
            parsed_err: Any = json.loads(err_body)  # Try to parse structured HubSpot error
        except json.JSONDecodeError:
            parsed_err = err_body  # Fall back to raw text
        return exc.code, parsed_err if isinstance(parsed_err, (dict, list)) else {"message": parsed_err}  # Normalize error shape
    except URLError as exc:  # Network-level failure
        print(f"ERROR: Network failure calling HubSpot: {exc}")  # Print diagnostic for operator
        raise SystemExit(1) from exc  # Abort because we cannot reach API


def _ensure_property_group(object_type: str, internal_name: str, label: str, token: str) -> None:
    """Create a CRM property group if it does not already exist.

    Args:
        object_type: HubSpot object type such as deals or contacts.
        internal_name: Internal API name for the group (snake_case).
        label: Human-readable label shown in HubSpot UI.
        token: HubSpot Bearer token (developer platform static token or equivalent).

    Returns:
        None: Side effect only; prints created vs skipped.
    """
    path = f"/crm/v3/properties/{object_type}/groups"  # List/create groups endpoint
    status, payload = _request("GET", path, token)  # Fetch all groups for the object
    if status >= 400:  # Treat API errors as fatal for listing
        print(f"ERROR: Failed to list {object_type} property groups: {payload}{_auth_error_hint(payload)}")  # Show HubSpot error
        raise SystemExit(1)  # Stop setup because groups are required
    results = payload.get("results", []) if isinstance(payload, dict) else []  # HubSpot returns paging results
    existing = {g.get("name") for g in results}  # Build set of internal group names
    if internal_name in existing:  # Idempotent skip when already present
        print(f"SKIP: Property group '{internal_name}' ({object_type}) already exists.")  # Inform operator
        return  # Nothing else to do
    body = {"name": internal_name, "label": label, "displayOrder": 1}  # Create payload for new group
    create_status, create_payload = _request("POST", path, token, body)  # Attempt creation
    if create_status in (200, 201):  # Accept both OK and Created
        print(f"OK: Created property group '{internal_name}' ({object_type}).")  # Confirm success
        return  # Done
    print(f"ERROR: Could not create property group '{internal_name}': {create_payload}{_auth_error_hint(create_payload)}")  # Show failure details
    raise SystemExit(1)  # Abort setup on failure


def _ensure_property(object_type: str, prop: dict[str, Any], token: str) -> None:
    """Create a single custom property if it is missing.

    Args:
        object_type: deals or contacts object type segment in the API path.
        prop: Property definition dict compatible with HubSpot property create.
        token: HubSpot Bearer token (developer platform static token or equivalent).

    Returns:
        None: Prints created, skipped, or errors and may exit the process.
    """
    name = prop["name"]  # Read internal property name for lookups
    path = f"/crm/v3/properties/{object_type}/{name}"  # GET single property by name
    status, _payload = _request("GET", path, token)  # Check existence
    if status == 200:  # Property already exists
        print(f"SKIP: Property '{name}' ({object_type}) already exists.")  # Idempotent skip message
        return  # No create needed
    if status != 404:  # Unexpected error (not simply missing)
        print(f"ERROR: Unexpected response checking property '{name}': status={status}")  # Diagnostic
        raise SystemExit(1)  # Fail fast on unknown errors
    create_path = f"/crm/v3/properties/{object_type}"  # POST create endpoint
    create_status, create_payload = _request("POST", create_path, token, prop)  # Create the property
    if create_status in (200, 201):  # Successful create
        print(f"OK: Created property '{name}' ({object_type}).")  # Confirm to operator
        return  # Done
    print(f"ERROR: Failed to create property '{name}': {create_payload}{_auth_error_hint(create_payload)}")  # Show HubSpot validation errors
    raise SystemExit(1)  # Stop because property creation failed


def _ensure_pipeline(token: str) -> None:
    """Create the DTL-Global deal pipeline with ten stages if missing.

    Args:
        token: HubSpot Bearer token for HubSpot API authorization.

    Returns:
        None: Prints skip or create messages; exits on failure.
    """
    list_path = "/crm/v3/pipelines/deals"  # Endpoint listing all deal pipelines
    status, payload = _request("GET", list_path, token)  # Retrieve pipelines
    if status >= 400:  # Listing must succeed to be idempotent
        print(f"ERROR: Failed to list deal pipelines: {payload}{_auth_error_hint(payload)}")  # Show API error
        raise SystemExit(1)  # Cannot continue without pipeline list
    results = payload.get("results", []) if isinstance(payload, dict) else []  # Extract pipeline array
    for pipeline in results:  # Scan for matching label
        if pipeline.get("label") == PIPELINE_LABEL:  # Found existing pipeline by label
            print(f"SKIP: Pipeline '{PIPELINE_LABEL}' already exists (id={pipeline.get('id')}).")  # Skip create
            return  # Idempotent exit
    body = {
        "label": PIPELINE_LABEL,  # Pipeline display name
        "displayOrder": PIPELINE_DISPLAY_ORDER,  # Sort order among pipelines
        "stages": PIPELINE_STAGES,  # All ten stages with probabilities
    }  # Pipeline create payload
    create_status, create_payload = _request("POST", list_path, token, body)  # Create pipeline
    if create_status in (200, 201):  # Successful pipeline creation
        print(f"OK: Created pipeline '{PIPELINE_LABEL}'.")  # Confirm success
        return  # Done
    print(f"ERROR: Failed to create pipeline: {create_payload}{_auth_error_hint(create_payload)}")  # HubSpot may reject on plan limits
    raise SystemExit(1)  # Abort setup


def main() -> None:
    """Run property groups, properties, and pipeline setup in a safe order.

    Returns:
        None: Executes setup steps and prints progress to stdout.
    """
    token = load_hubspot_access_token()  # Read token or exit early
    print("INFO: Ensuring deal property group exists...")  # Progress line
    _ensure_property_group("deals", DEAL_GROUP_NAME, DEAL_GROUP_LABEL, token)  # Deal group first
    print("INFO: Ensuring contact property group exists...")  # Progress line
    _ensure_property_group("contacts", CONTACT_GROUP_NAME, CONTACT_GROUP_LABEL, token)  # Contact group next
    print("INFO: Creating deal properties (idempotent)...")  # Progress line
    for prop in DEAL_PROPERTIES:  # Iterate all deal fields from the plan
        _ensure_property("deals", prop, token)  # Create each if missing
    print("INFO: Creating contact properties (idempotent)...")  # Progress line
    for prop in CONTACT_PROPERTIES:  # Iterate all contact fields from the plan
        _ensure_property("contacts", prop, token)  # Create each if missing
    print("INFO: Creating deal pipeline (idempotent)...")  # Progress line
    _ensure_pipeline(token)  # Create pipeline last
    print("DONE: HubSpot Phase 0 setup completed successfully.")  # Final success message


if __name__ == "__main__":  # Script entrypoint when executed directly
    main()  # Run the setup routine
