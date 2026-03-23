#!/usr/bin/env python3
"""Create DTL-Global SSM SecureString parameters (interactive, idempotent)."""

from __future__ import annotations

import getpass  # Hide secret entry for tokens and keys
import sys  # Parse --overwrite and exit codes
from typing import Any  # Type hints for boto3 responses

import boto3  # AWS SDK for SSM Parameter Store
from botocore.exceptions import BotoCoreError  # Network and client configuration errors
from botocore.exceptions import ClientError  # AWS API error responses

# Canonical parameter names and prompt labels for operator clarity
_PARAMETER_CONFIG: list[dict[str, Any]] = [
    {
        "name": "/dtl-global-platform/hubspot/token",  # SSM path for HubSpot CRM token
        "label": "HubSpot token (/dtl-global-platform/hubspot/token)",  # Human label for prompts
        "use_getpass": True,  # Mask input because it is a secret
        "require_sk_test_prefix": False,  # Not a Stripe key
    },
    {
        "name": "/dtl-global-platform/stripe/secret",  # SSM path for Stripe secret key
        "label": "Stripe secret key (/dtl-global-platform/stripe/secret) — must be sk_test_ until production",  # Guidance
        "use_getpass": True,  # Mask Stripe secret
        "require_sk_test_prefix": True,  # Enforce sandbox keys for local/bootstrap safety
    },
    {
        "name": "/dtl-global-platform/stripe/connect_client_id",  # SSM path for Connect client id
        "label": "Stripe Connect client id (/dtl-global-platform/stripe/connect_client_id)",  # Human label
        "use_getpass": True,  # Treat as sensitive; avoid terminal history echo
        "require_sk_test_prefix": False,  # Not a Stripe secret key string
    },
    {
        "name": "/dtl-global-platform/anthropic/api_key",  # SSM path for Anthropic API key
        "label": "Anthropic API key (/dtl-global-platform/anthropic/api_key)",  # Human label
        "use_getpass": True,  # Mask API key
        "require_sk_test_prefix": False,  # Not Stripe
    },
]


def _parameter_exists(client: Any, name: str) -> bool:
    """Return True when the SSM parameter name already exists.

    Args:
        client: boto3 SSM client instance.
        name: Fully qualified parameter name.

    Returns:
        True if the parameter exists; False if AWS reports ParameterNotFound.

    Raises:
        ClientError: When the error is not ParameterNotFound.
    """
    try:
        client.get_parameter(Name=name, WithDecryption=False)  # Metadata-only existence check
    except ClientError as exc:  # AWS returned an error code
        code = exc.response.get("Error", {}).get("Code", "")  # Extract AWS error code safely
        if code == "ParameterNotFound":  # Expected when parameter is absent
            return False  # Treat as missing
        raise  # Surface unexpected API failures
    return True  # Parameter is present


def _prompt_value(cfg: dict[str, Any]) -> str:
    """Prompt for a single parameter value using getpass or input.

    Args:
        cfg: Entry from _PARAMETER_CONFIG describing prompt behavior.

    Returns:
        Stripped non-empty string from the operator.

    Raises:
        SystemExit: When input is empty after stripping.
    """
    label = cfg["label"]  # Prompt text for this parameter
    if cfg["use_getpass"]:  # Secret-style entry
        raw = getpass.getpass(f"{label}: ")  # Masked stdin read
    else:  # ARN-style entry
        raw = input(f"{label}: ")  # Visible stdin read for long ARNs
    value = raw.strip()  # Normalize whitespace
    if not value:  # Reject blank submissions
        print(f"ERROR: Value for {cfg['name']} cannot be empty.")  # Actionable message
        raise SystemExit(1)  # Abort setup
    return value  # Validated operator input


def _validate_stripe_ssm_secret(value: str) -> None:
    """Refuse Stripe live keys and require sk_test_ for SSM bootstrap (DTL_MASTER_PLAN.md §8.2).

    Args:
        value: Raw Stripe secret key string for `/dtl-global-platform/stripe/secret`.

    Raises:
        SystemExit: When the key is sk_live_ or not sk_test_.
    """
    if value.startswith("sk_live_"):  # Never store production keys via this interactive script
        print("ERROR: Refusing to store Stripe live keys (sk_live_) in SSM via this script. Use sk_test_ until go-live.")  # Plan §8.2
        raise SystemExit(1)  # Stop before writing SSM
    if not value.startswith("sk_test_"):  # Block non-test keys (restricted keys, typos, etc.)
        print(  # Enforce sandbox-only bootstrap path
            "ERROR: Stripe key must start with sk_test_. Refusing to store non-test keys via this script."
        )  # End error line
        raise SystemExit(1)  # Stop before writing SSM


def _put_secure_string(client: Any, name: str, value: str, overwrite: bool) -> None:
    """Create or overwrite a SecureString parameter in SSM.

    Args:
        client: boto3 SSM client.
        name: Parameter name path.
        value: Secret value to store.
        overwrite: When True, replace an existing parameter.

    Raises:
        SystemExit: On unrecoverable AWS API errors.
    """
    try:
        client.put_parameter(  # Persist encrypted secret in Parameter Store
            Name=name,  # Full parameter path
            Value=value,  # Secret payload
            Type="SecureString",  # Encrypted at rest
            Overwrite=overwrite,  # Allow replacement when requested or first create
        )  # End put_parameter call
    except ClientError as exc:  # AWS rejected the request
        print(f"ERROR: Failed to write SSM parameter {name}: {exc}")  # Include AWS context
        raise SystemExit(1) from exc  # Abort with failure code
    except BotoCoreError as exc:  # Lower-level SDK/network failure
        print(f"ERROR: boto3 error writing {name}: {exc}")  # Show connectivity issues
        raise SystemExit(1) from exc  # Abort with failure code


def main() -> None:
    """Prompt for four SSM values and create missing SecureString parameters.

    Returns:
        None: Prints created/skipped summary or exits on validation failure.

    Raises:
        SystemExit: On missing values, invalid Stripe key, or AWS failures.
    """
    overwrite = "--overwrite" in sys.argv  # Detect optional overwrite mode from argv
    client = boto3.client("ssm")  # Default session uses env/profile credentials
    created: list[str] = []  # Track newly written names
    skipped: list[str] = []  # Track skipped existing names
    for cfg in _PARAMETER_CONFIG:  # Walk each configured parameter
        name = cfg["name"]  # Target SSM name
        exists = _parameter_exists(client, name)  # Check idempotency precondition
        if exists and not overwrite:  # Skip when already present and not forcing overwrite
            skipped.append(name)  # Record skip for summary
            print(f"SKIP: {name} already exists (pass --overwrite to replace).")  # Operator feedback
            continue  # Move to next parameter
        value = _prompt_value(cfg)  # Collect operator input with correct prompt style
        if cfg["require_sk_test_prefix"]:  # Stripe secret validation gate
            _validate_stripe_ssm_secret(value)  # Refuse sk_live_ and require sk_test_
        _put_secure_string(client, name, value, overwrite=exists)  # Create (exists=False) or replace (--overwrite path)
        created.append(name)  # Record successful write
        print(f"OK: Wrote {name} as SecureString.")  # Confirm without echoing value
    print("")  # Blank line before summary
    print("SUMMARY")  # Summary header
    print(f"  Created/updated: {len(created)}")  # Count writes
    for item in created:  # List written parameters only by name
        print(f"    - {item}")  # One line per created parameter
    print(f"  Skipped (already existed): {len(skipped)}")  # Count skips
    for item in skipped:  # List skipped parameters
        print(f"    - {item}")  # One line per skipped parameter


if __name__ == "__main__":  # Script entrypoint guard
    main()  # Run interactive SSM bootstrap
