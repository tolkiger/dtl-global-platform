#!/usr/bin/env python3
"""Create Stripe products and prices for DTL-Global Phase 0 (test mode recommended).

This script is idempotent: existing matching products and prices are skipped.
Requires STRIPE_SECRET_KEY in the environment (see .env.example).
"""

from __future__ import annotations

import os  # Read Stripe secret key from the environment
import sys  # Exit with non-zero status on fatal errors
from typing import Any  # Type hints for Stripe objects and metadata maps

import stripe  # Official Stripe Python SDK from requirements

# Product catalog: display name, unit amount in cents, optional recurring interval
PRODUCT_SPECS: list[dict[str, Any]] = [
    {"name": "DTL Starter Setup", "amount_cents": 50000, "recurring": None},  # $500 one-time
    {"name": "DTL Growth Setup", "amount_cents": 125000, "recurring": None},  # $1,250 one-time
    {"name": "DTL Professional Setup", "amount_cents": 250000, "recurring": None},  # $2,500 one-time
    {"name": "DTL Premium Setup", "amount_cents": 400000, "recurring": None},  # $4,000 one-time
    {"name": "DTL Friends and Family Hosting", "amount_cents": 2000, "recurring": "month"},  # $20/month
    {"name": "DTL Starter Monthly", "amount_cents": 4900, "recurring": "month"},  # $49/month
    {"name": "DTL Growth Monthly", "amount_cents": 14900, "recurring": "month"},  # $149/month
    {"name": "DTL Professional Monthly", "amount_cents": 24900, "recurring": "month"},  # $249/month
    {"name": "DTL Premium Monthly", "amount_cents": 39900, "recurring": "month"},  # $399/month
]


def _load_secret_key() -> str:
    """Load the Stripe secret API key from the environment.

    Returns:
        A non-empty secret key string (must be sk_test_ for this script).

    Raises:
        SystemExit: When the key is missing, not test mode, or clearly invalid.
    """
    key = os.environ.get("STRIPE_SECRET_KEY", "").strip()  # Read Stripe key from env
    if not key:  # Guard missing configuration
        print("ERROR: STRIPE_SECRET_KEY is not set. Copy .env.example to .env and export variables.")  # Help text
        raise SystemExit(1)  # Abort early
    if key.startswith("sk_live_"):  # Explicit refusal of production keys per DTL_MASTER_PLAN.md §7.2
        print("ERROR: This script refuses Stripe live keys (sk_live_). Use SANDBOX keys (sk_test_) only.")  # Clear operator message
        raise SystemExit(1)  # Abort before any Stripe API calls
    if not key.startswith("sk_test_"):  # Refuse any non-test secret (restricted keys, typos, etc.)
        print(  # Operator-facing error for non-sandbox keys
            "ERROR: This script only runs with Stripe SANDBOX/TEST keys (sk_test_). "
            "Refusing to run with live keys."
        )  # End safety message
        raise SystemExit(1)  # Abort before any Stripe API calls
    return key  # Return validated sandbox key


def _find_product_by_name(name: str) -> stripe.Product | None:
    """Return the first active Stripe product with an exact name match.

    Args:
        name: Product name as shown in the Stripe Dashboard.

    Returns:
        A stripe.Product instance when found; otherwise None.
    """
    products = stripe.Product.list(active=True, limit=100)  # List active products page
    for product in products.auto_paging_iter():  # Iterate safely across pages
        if product.name == name:  # Exact name match for idempotency
            return product  # Return the matching product
    return None  # No matching product found


def _price_matches(spec: dict[str, Any], price: stripe.Price) -> bool:
    """Check whether a Stripe price matches the expected amount and billing mode.

    Args:
        spec: PRODUCT_SPECS entry with amount_cents and recurring keys.
        price: Stripe Price object to compare.

    Returns:
        True when unit amount and recurring settings match the spec.
    """
    if price.unit_amount != spec["amount_cents"]:  # Amount must match exactly
        return False  # Different amount means no match
    if spec["recurring"] is None:  # One-time price expected
        return price.recurring is None  # Must not be recurring
    if price.recurring is None:  # Spec wants recurring but price is one-time
        return False  # Not a match
    return price.recurring.get("interval") == spec["recurring"]  # Match billing interval (month)


def _find_matching_price(product_id: str, spec: dict[str, Any]) -> stripe.Price | None:
    """Find an active price on the product that matches the Phase 0 spec.

    Args:
        product_id: Stripe product id (prod_...).
        spec: PRODUCT_SPECS dictionary describing expected billing.

    Returns:
        A matching stripe.Price if found; otherwise None.
    """
    prices = stripe.Price.list(product=product_id, active=True, limit=100)  # List prices for the product
    for price in prices.auto_paging_iter():  # Walk all active prices
        if _price_matches(spec, price):  # Compare to expected amount and mode
            return price  # Return first matching price
    return None  # No suitable price yet


def _ensure_product_and_price(spec: dict[str, Any]) -> None:
    """Create the product and default price when missing, skipping when already aligned.

    Args:
        spec: PRODUCT_SPECS entry describing name, amount, and recurring interval.

    Returns:
        None: Prints created/skipped messages; exits on unrecoverable Stripe errors.
    """
    name = spec["name"]  # Human-readable product title
    product = _find_product_by_name(name)  # Try to find existing product
    if product is None:  # Product does not exist yet
        try:
            product = stripe.Product.create(name=name, metadata={"dtl_phase0": "true"})  # Create product marker
        except stripe.StripeError as exc:  # Stripe API failure
            print(f"ERROR: Failed to create product '{name}': {exc}")  # Show Stripe error
            raise SystemExit(1) from exc  # Abort setup
        print(f"OK: Created product '{name}' (id={product.id}).")  # Confirm creation
    else:  # Product already exists
        print(f"SKIP: Product '{name}' already exists (id={product.id}).")  # Idempotent skip
    existing_price = _find_matching_price(product.id, spec)  # Look for a suitable price
    if existing_price is not None:  # Matching price already configured
        print(f"SKIP: Price already exists for '{name}' (price_id={existing_price.id}).")  # Skip price creation
        return  # Nothing else required
    price_params: dict[str, Any] = {
        "product": product.id,  # Attach price to this product
        "unit_amount": spec["amount_cents"],  # Charge amount in cents
        "currency": "usd",  # USD currency per DTL-Global pricing
    }  # Base price parameters
    if spec["recurring"] is not None:  # Subscription price
        price_params["recurring"] = {"interval": spec["recurring"]}  # Monthly billing configuration
    try:
        price = stripe.Price.create(**price_params)  # Create the missing price
    except stripe.StripeError as exc:  # Stripe rejected price creation
        print(f"ERROR: Failed to create price for '{name}': {exc}")  # Show error details
        raise SystemExit(1) from exc  # Abort setup
    print(f"OK: Created price for '{name}' (price_id={price.id}).")  # Confirm new price


def _verify_connect_access() -> None:
    """Best-effort Stripe Connect readiness check using read-only Account APIs.

    Returns:
        None: Prints guidance; does not fail the script when Connect cannot be confirmed.
    """
    try:
        acct = stripe.Account.retrieve()  # Load the platform account
    except stripe.StripeError as exc:  # Network or permission failure
        print(f"WARNING: Could not retrieve Stripe account: {exc}")  # Non-fatal warning
        return  # Continue setup even if account fetch fails
    charges_enabled = getattr(acct, "charges_enabled", None)  # Whether charges can be created
    details_submitted = getattr(acct, "details_submitted", None)  # Whether onboarding submitted
    print(
        "INFO: Stripe platform account check: "
        f"charges_enabled={charges_enabled} details_submitted={details_submitted}"
    )  # Print basic platform readiness
    try:
        connected = stripe.Account.list(limit=1)  # Touch Connect Accounts API (may be empty)
        print(f"INFO: Stripe Connect Accounts API reachable (returned {len(connected.data)} sample rows).")  # API ok
    except stripe.StripeError as exc:  # Connect might be blocked or not enabled
        print(
            "WARNING: Could not list Connect accounts. "
            f"Confirm Stripe Connect is enabled in Dashboard. Details: {exc}"
        )  # Operator follow-up


def main() -> None:
    """Configure Stripe SDK and ensure all Phase 0 catalog items exist.

    Returns:
        None: Runs setup steps and prints progress.
    """
    stripe.api_key = _load_secret_key()  # Configure global Stripe authentication (sk_test_ only)
    print("Running in SANDBOX/TEST mode")  # Explicit mode banner for operators
    print("INFO: Verifying Stripe API access and Connect readiness...")  # Progress banner
    _verify_connect_access()  # Inform operator about Connect
    print("INFO: Ensuring products and prices exist (idempotent)...")  # Progress banner
    for spec in PRODUCT_SPECS:  # Process each catalog entry from the plan
        _ensure_product_and_price(spec)  # Create missing product/price pairs
    print("DONE: Stripe Phase 0 setup completed successfully.")  # Final success line


if __name__ == "__main__":  # Script entrypoint
    main()  # Execute setup routine
