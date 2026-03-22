#!/usr/bin/env python3
"""Verify HubSpot Phase 0 resources: pipeline stages, property groups, and properties."""

from __future__ import annotations

import json  # Parse JSON responses from HubSpot
import sys  # Insert scripts dir for importing the setup module
from pathlib import Path  # Locate sibling module path reliably
from typing import Any  # Type JSON payloads from HubSpot

# Allow `python scripts/phase0_hubspot_verify.py` from repo root to import setup constants
_SCRIPTS_DIR = Path(__file__).resolve().parent  # Directory containing Phase 0 scripts
if str(_SCRIPTS_DIR) not in sys.path:  # Avoid duplicate entries when re-run
    sys.path.insert(0, str(_SCRIPTS_DIR))  # Ensure sibling imports resolve

import phase0_hubspot_setup as hub  # noqa: E402  # Shared labels and property definitions

from urllib.error import HTTPError, URLError  # Match setup script networking errors
from urllib.request import Request, urlopen  # Minimal HTTP client for verification


def _request(
    method: str,
    path: str,
    token: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | list[Any] | None]:
    """Perform a HubSpot API request and return status plus parsed JSON.

    Args:
        method: HTTP method such as GET.
        path: Relative API path beginning with /crm/.
        token: HubSpot CRM API Bearer token.
        body: Optional JSON body for non-GET calls.

    Returns:
        Tuple of HTTP status and parsed JSON payload when present.

    Raises:
        SystemExit: When the network is unreachable.
    """
    url = f"{hub.HUBSPOT_API_BASE}{path}"  # Reuse the same API base as setup
    data_bytes: bytes | None = None  # Default to no request body
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}  # Auth headers
    if body is not None:  # Serialize JSON only when needed
        data_bytes = json.dumps(body).encode("utf-8")  # UTF-8 JSON bytes
    req = Request(url, data=data_bytes, headers=headers, method=method)  # Build request object
    try:
        with urlopen(req, timeout=60) as resp:  # Execute network call
            raw = resp.read()  # Read response body
            status = getattr(resp, "status", 200)  # Capture HTTP status code
            if not raw:  # Handle empty 204-style bodies
                return status, None  # No JSON to parse
            parsed = json.loads(raw.decode("utf-8"))  # Parse JSON documents
            return status, parsed  # Return to caller
    except HTTPError as exc:  # HTTP error responses including 404
        err_body = exc.read().decode("utf-8", errors="replace")  # Read error JSON or text
        if not err_body:  # Empty error body edge case
            return exc.code, {"status": exc.code, "reason": exc.reason}  # Minimal error dict
        try:
            parsed_err: Any = json.loads(err_body)  # Parse HubSpot error JSON
        except json.JSONDecodeError:
            parsed_err = err_body  # Use raw string on parse failure
        return exc.code, parsed_err if isinstance(parsed_err, (dict, list)) else {"message": parsed_err}  # Normalize
    except URLError as exc:  # DNS/TLS/connectivity failures
        print(f"ERROR: Network failure calling HubSpot: {exc}")  # Print root cause
        raise SystemExit(1) from exc  # Abort verification


def _fail(message: str) -> None:
    """Print a failure line and rely on caller to track overall success.

    Args:
        message: Human-readable failure description.

    Returns:
        None: Prints only.
    """
    print(f"FAIL: {message}")  # Consistent failure prefix for scanning output


def _ok(message: str) -> None:
    """Print a passing check line.

    Args:
        message: Human-readable success description.

    Returns:
        None: Prints only.
    """
    print(f"OK: {message}")  # Consistent success prefix for scanning output


def _verify_property_groups(token: str) -> bool:
    """Verify deal and contact property groups exist.

    Args:
        token: HubSpot CRM API access token.

    Returns:
        True if both groups exist; False if any check failed.
    """
    all_passed = True  # Assume success until a check fails
    for object_type, internal, _label in (
        ("deals", hub.DEAL_GROUP_NAME, hub.DEAL_GROUP_LABEL),
        ("contacts", hub.CONTACT_GROUP_NAME, hub.CONTACT_GROUP_LABEL),
    ):  # Check each required group
        path = f"/crm/v3/properties/{object_type}/groups"  # List groups endpoint
        status, payload = _request("GET", path, token)  # Fetch group catalog
        if status != 200:  # Listing must succeed
            _fail(f"Could not list {object_type} property groups (HTTP {status}).")  # Report HTTP issue
            all_passed = False  # Mark failure
            continue  # Continue checking other objects for full diagnostics
        results = payload.get("results", []) if isinstance(payload, dict) else []  # Extract results safely
        names = {g.get("name") for g in results}  # Build name set for membership tests
        if internal in names:  # Group exists
            _ok(f"Property group '{internal}' exists on {object_type}.")  # Confirm presence
        else:  # Missing group
            _fail(f"Missing property group '{internal}' on {object_type}.")  # Report missing group
            all_passed = False  # Mark failure
    return all_passed  # Return aggregate result


def _verify_properties(object_type: str, props: list[dict[str, Any]], token: str) -> bool:
    """Verify each configured property exists on the given object type.

    Args:
        object_type: HubSpot object type segment (deals or contacts).
        props: Property definition dicts whose name keys must exist server-side.
        token: HubSpot CRM API access token.

    Returns:
        True when every property exists; False if any property is missing or errors occur.
    """
    all_passed = True  # Track overall success for this object type
    for prop in props:  # Check each expected property from the plan
        name = prop["name"]  # Internal API name to verify
        path = f"/crm/v3/properties/{object_type}/{name}"  # Single-property GET endpoint
        status, _payload = _request("GET", path, token)  # Attempt to load the property
        if status == 200:  # Property exists
            _ok(f"Property '{name}' exists on {object_type}.")  # Confirm existence
        else:  # Missing or error
            _fail(f"Property '{name}' missing or error on {object_type} (HTTP {status}).")  # Report problem
            all_passed = False  # Record failure
    return all_passed  # Return whether this object type passed


def _verify_pipeline(token: str) -> bool:
    """Verify the deal pipeline exists and contains the ten expected stages in order.

    Args:
        token: HubSpot CRM API access token.

    Returns:
        True when pipeline and stages match; False otherwise.
    """
    list_path = "/crm/v3/pipelines/deals"  # Pipeline list endpoint
    status, payload = _request("GET", list_path, token)  # Load all deal pipelines
    if status != 200:  # Must list pipelines successfully
        _fail(f"Could not list deal pipelines (HTTP {status}).")  # Report HTTP failure
        return False  # Pipeline checks cannot proceed
    results = payload.get("results", []) if isinstance(payload, dict) else []  # Extract pipelines array
    pipeline_id = None  # Will hold matching pipeline id when found
    for pipeline in results:  # Scan pipelines for the DTL label
        if pipeline.get("label") == hub.PIPELINE_LABEL:  # Found target pipeline
            pipeline_id = pipeline.get("id")  # Capture pipeline id for detailed GET
            break  # Stop scanning once found
    if pipeline_id is None:  # No matching pipeline
        _fail(f"Pipeline '{hub.PIPELINE_LABEL}' not found.")  # Report missing pipeline
        return False  # Fail verification
    detail_path = f"/crm/v3/pipelines/deals/{pipeline_id}"  # Single pipeline GET for stages
    detail_status, detail_payload = _request("GET", detail_path, token)  # Fetch full pipeline
    if detail_status != 200:  # Detail fetch must succeed
        _fail(f"Could not load pipeline id={pipeline_id} (HTTP {detail_status}).")  # Report error
        return False  # Cannot verify stages without detail
    stages = detail_payload.get("stages", []) if isinstance(detail_payload, dict) else []  # Read stages array
    if len(stages) != len(hub.PIPELINE_STAGES):  # Stage count must match plan
        _fail(f"Pipeline stage count {len(stages)} != expected {len(hub.PIPELINE_STAGES)}.")  # Report mismatch
        return False  # Fail when counts differ
    sorted_stages = sorted(stages, key=lambda s: s.get("displayOrder", 0))  # Order stages by displayOrder
    expected_labels = [s["label"] for s in hub.PIPELINE_STAGES]  # Expected ordered labels from setup
    actual_labels = [s.get("label") for s in sorted_stages]  # Actual ordered labels from HubSpot
    if actual_labels != expected_labels:  # Compare label sequences exactly
        _fail(f"Pipeline stage labels mismatch.\n Expected: {expected_labels}\n Actual:   {actual_labels}")  # Show diff
        return False  # Fail when labels differ
    _ok(f"Pipeline '{hub.PIPELINE_LABEL}' has {len(expected_labels)} expected stages.")  # Confirm pipeline
    return True  # Pipeline verification passed


def main() -> None:
    """Run all HubSpot verification checks and exit non-zero on any failure.

    Returns:
        None: Prints results and sets process exit code via SystemExit.
    """
    token = hub.load_hubspot_access_token()  # Load credentials (same validation as setup script)
    print("INFO: Verifying HubSpot Phase 0 configuration...")  # Start banner
    checks_passed = True  # Aggregate success flag
    checks_passed = _verify_property_groups(token) and checks_passed  # Verify groups first
    checks_passed = _verify_properties("deals", hub.DEAL_PROPERTIES, token) and checks_passed  # Verify deal props
    checks_passed = _verify_properties("contacts", hub.CONTACT_PROPERTIES, token) and checks_passed  # Verify contacts
    checks_passed = _verify_pipeline(token) and checks_passed  # Verify pipeline + stages
    if checks_passed:  # All checks succeeded
        print("RESULT: ALL CHECKS PASSED")  # Final success banner
        raise SystemExit(0)  # Success exit code
    print("RESULT: ONE OR MORE CHECKS FAILED")  # Final failure banner
    raise SystemExit(1)  # Failure exit code


if __name__ == "__main__":  # Script entrypoint
    main()  # Execute verification
