#!/usr/bin/env python3
"""Verify DTL-Global SSM parameters exist and use SecureString type (no value leak)."""

from __future__ import annotations

import sys  # Exit with non-zero status on failures
from typing import Any  # Type hints for boto3 client usage

import boto3  # AWS SDK for SSM Parameter Store
from botocore.exceptions import BotoCoreError  # Network and configuration failures
from botocore.exceptions import ClientError  # AWS API error responses

# Expected parameters: name only (values must never be printed)
_EXPECTED_PARAMETERS: list[str] = [
    "/dtl-global-platform/hubspot/token",  # HubSpot CRM token
    "/dtl-global-platform/stripe/secret",  # Stripe secret key
    "/dtl-global-platform/stripe/connect_client_id",  # Stripe Connect client id
    "/dtl-global-platform/anthropic/api_key",  # Anthropic API key
    "/dtl-global-platform/github/codestar_connection_arn",  # CodeStar Connections ARN for GitHub
]


def _check_parameter(client: Any, name: str) -> bool:
    """Verify a parameter exists and is stored as SecureString.

    Args:
        client: boto3 SSM client.
        name: Fully qualified parameter name.

    Returns:
        True when the parameter exists with type SecureString; False otherwise.
    """
    try:
        resp = client.get_parameter(Name=name, WithDecryption=False)  # Fetch metadata without decrypting value
    except ClientError as exc:  # AWS returned an error
        code = exc.response.get("Error", {}).get("Code", "")  # Normalize error code
        if code == "ParameterNotFound":  # Missing parameter is a failed check
            print(f"✗ {name} — NOT FOUND")  # Failure line without secrets
            return False  # Record failure
        print(f"✗ {name} — ERROR: {exc}")  # Unexpected API failure
        return False  # Record failure
    param = resp.get("Parameter", {})  # Parameter description dict
    ptype = param.get("Type", "")  # AWS parameter type string
    if ptype != "SecureString":  # Enforce encrypted parameter type from plan
        print(f"✗ {name} — wrong type ({ptype or 'unknown'}, expected SecureString)")  # Type mismatch
        return False  # Record failure
    print(f"✓ {name} — OK (SecureString)")  # Success without revealing value
    return True  # Record success


def main() -> None:
    """Print pass/fail lines for each expected SSM parameter.

    Returns:
        None: Exits 0 when all checks pass; 1 otherwise.

    Raises:
        SystemExit: On boto3 session failures or aggregate check failure.
    """
    client = boto3.client("ssm")  # Use default credential chain
    all_ok = True  # Aggregate success flag
    for name in _EXPECTED_PARAMETERS:  # Verify each required name
        try:
            passed = _check_parameter(client, name)  # Single-parameter check
        except BotoCoreError as exc:  # Catch boto-wide failures per iteration
            print(f"✗ {name} — boto3 error: {exc}")  # Show SDK-level problem
            passed = False  # Treat as failure
        all_ok = all_ok and passed  # Combine results
    if all_ok:  # Every parameter satisfied expectations
        print("RESULT: ALL SSM CHECKS PASSED")  # Final banner
        raise SystemExit(0)  # Success exit code
    print("RESULT: ONE OR MORE SSM CHECKS FAILED")  # Final failure banner
    raise SystemExit(1)  # Failure exit code


if __name__ == "__main__":  # Script entrypoint guard
    main()  # Run verification routine
