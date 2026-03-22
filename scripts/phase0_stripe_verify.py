#!/usr/bin/env python3
"""Verify Stripe Phase 0 products, prices, and basic Connect/API readiness."""

from __future__ import annotations

import os  # Load STRIPE_SECRET_KEY from the environment
import sys  # Exit with failure codes when checks fail
from pathlib import Path  # Resolve sibling module paths for imports
from typing import Any  # Type hints for Stripe objects and spec dicts

import stripe  # Official Stripe Python SDK

# Import expected catalog from setup to avoid drift between setup and verify
_SCRIPTS_DIR = Path(__file__).resolve().parent  # Scripts directory path
if str(_SCRIPTS_DIR) not in sys.path:  # Ensure sibling imports work from repo root
    sys.path.insert(0, str(_SCRIPTS_DIR))  # Add scripts directory to import path

import phase0_stripe_setup as st0  # noqa: E402  # Reuse PRODUCT_SPECS single source of truth


def _load_secret_key() -> str:
    """Load Stripe secret key or exit when missing.

    Returns:
        Non-empty Stripe API secret key string.

    Raises:
        SystemExit: When STRIPE_SECRET_KEY is not configured.
    """
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()  # Read key from environment
    if not key:  # Missing configuration
        print("ERROR: STRIPE_SECRET_KEY is not set.")  # Explain failure
        raise SystemExit(1)  # Abort verification
    if not key.startswith("sk_test_"):  # Phase 0 verify requires test keys only
        print(  # Match setup script safety messaging
            "FAIL: Stripe key must be a test key (sk_test_) for Phase 0 verification."
        )  # End failure line
        raise SystemExit(1)  # Abort before catalog checks
    return key  # Return validated test key


def _fail(message: str) -> None:
    """Print a failed verification line.

    Args:
        message: Description of what failed.

    Returns:
        None: Prints only.
    """
    print(f"FAIL: {message}")  # Standard failure prefix


def _ok(message: str) -> None:
    """Print a successful verification line.

    Args:
        message: Description of what passed.

    Returns:
        None: Prints only.
    """
    print(f"OK: {message}")  # Standard success prefix


def _price_matches(spec: dict[str, Any], price: stripe.Price) -> bool:
    """Return True when a Stripe price matches expected amount and recurring settings.

    Args:
        spec: PRODUCT_SPECS entry from phase0_stripe_setup.
        price: Stripe Price object to evaluate.

    Returns:
        True if the price matches the spec; False otherwise.
    """
    if price.unit_amount != spec["amount_cents"]:  # Compare amounts in cents
        return False  # Mismatch
    if spec["recurring"] is None:  # Expect one-time price
        return price.recurring is None  # Must not recur
    if price.recurring is None:  # Missing recurring config
        return False  # Not a match
    return price.recurring.get("interval") == spec["recurring"]  # Compare interval


def _find_product_by_name(name: str) -> stripe.Product | None:
    """Locate an active Stripe product by exact name.

    Args:
        name: Product name to locate.

    Returns:
        stripe.Product when found; otherwise None.
    """
    products = stripe.Product.list(active=True, limit=100)  # Query active products
    for product in products.auto_paging_iter():  # Iterate pages safely
        if product.name == name:  # Exact match for deterministic verification
            return product  # Found product
    return None  # Not found


def _verify_catalog() -> bool:
    """Verify each PRODUCT_SPEC has a product and at least one matching active price.

    Returns:
        True when all catalog entries pass; False if any entry fails.
    """
    all_passed = True  # Assume success until a failure is recorded
    for spec in st0.PRODUCT_SPECS:  # Walk expected catalog
        name = spec["name"]  # Expected product title
        product = _find_product_by_name(name)  # Locate product by name
        if product is None:  # Missing product entirely
            _fail(f"Missing product '{name}'.")  # Report missing product
            all_passed = False  # Record failure
            continue  # Continue checking remaining items
        _ok(f"Product exists: '{name}' (id={product.id}).")  # Confirm product presence
        prices = stripe.Price.list(product=product.id, active=True, limit=100)  # Load active prices
        match_found = False  # Track whether a suitable price exists
        for price in prices.auto_paging_iter():  # Inspect each active price
            if _price_matches(spec, price):  # Compare against expected billing
                match_found = True  # Mark match
                _ok(f"Matching active price for '{name}' (price_id={price.id}).")  # Confirm price
                break  # Stop after first match
        if not match_found:  # No suitable price
            _fail(f"No matching active price for '{name}' (amount/recurring).")  # Report missing price
            all_passed = False  # Record failure
    return all_passed  # Return aggregate catalog result


def _verify_stripe_api() -> bool:
    """Verify Stripe API connectivity by retrieving the platform account.

    Returns:
        True on success; False when the API call fails.
    """
    try:
        acct = stripe.Account.retrieve()  # Simple authenticated request
    except stripe.StripeError as exc:  # Auth or network failure
        _fail(f"Could not retrieve Stripe account: {exc}")  # Report failure
        return False  # API not usable
    _ok(f"Stripe API reachable (account_id={acct.get('id')}).")  # Confirm connectivity
    return True  # API check passed


def _verify_connect_hint() -> bool:
    """Best-effort verification that Connect-related APIs are accessible.

    Returns:
        True when listing connected accounts succeeds; False on error (non-fatal messaging).
    """
    try:
        connected = stripe.Account.list(limit=1)  # Exercises Connect Accounts API surface
    except stripe.StripeError as exc:  # May fail if Connect not enabled
        _fail(
            "Could not call Stripe Connect Accounts list. "
            f"Confirm Connect is enabled in Stripe Dashboard. Details: {exc}"
        )  # Actionable guidance
        return False  # Treat as verification failure for Phase 0 gate
    _ok(f"Stripe Connect Accounts API call succeeded (sample size={len(connected.data)}).")  # Confirm API works
    return True  # Pass Connect probe


def main() -> None:
    """Run Stripe verification checks and exit non-zero on any failure.

    Returns:
        None: Prints results and exits with appropriate status code.
    """
    stripe.api_key = _load_secret_key()  # Configure Stripe SDK authentication (sk_test_ only)
    print("Running in SANDBOX/TEST mode")  # Match setup script mode banner
    print("INFO: Verifying Stripe Phase 0 configuration...")  # Start banner
    checks_passed = True  # Aggregate success flag
    checks_passed = _verify_stripe_api() and checks_passed  # Must authenticate
    checks_passed = _verify_connect_hint() and checks_passed  # Connect probe from plan
    checks_passed = _verify_catalog() and checks_passed  # Must match full catalog
    if checks_passed:  # All checks succeeded
        print("RESULT: ALL CHECKS PASSED")  # Final success banner
        raise SystemExit(0)  # Success exit code
    print("RESULT: ONE OR MORE CHECKS FAILED")  # Final failure banner
    raise SystemExit(1)  # Failure exit code


if __name__ == "__main__":  # Script entrypoint
    main()  # Execute verification
