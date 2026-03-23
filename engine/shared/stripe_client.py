"""Stripe payment client for DTL-Global onboarding platform.

This module provides a comprehensive Stripe API client for managing:
- Products and pricing (DTL service packages)
- Customers and payment methods
- Invoices and subscriptions
- Stripe Connect for client payment accounts
- Payment processing and webhooks

IMPORTANT: All operations run in SANDBOX mode (sk_test_) until production switch.
See docs/AUTHENTICATION.md for switching to live keys.

Per DTL_MASTER_PLAN.md Section 4: Stripe API with SANDBOX keys only.
Per DTL_MASTER_PLAN.md Section 6.4: DTL service products and pricing.
Per Rule 001: Google-style docstrings for all functions and classes.
Per Rule 002: Inline comments on every meaningful line.
Per Rule 009: try/except blocks with specific exception types.

Author: DTL-Global Platform
"""

from __future__ import annotations

import stripe  # Stripe Python SDK for payment processing
from typing import Dict, List, Optional, Any, Union  # Type hints for function signatures
from decimal import Decimal  # Precise decimal arithmetic for currency calculations
from datetime import datetime, timedelta  # Date/time handling for subscriptions

from .config import config, STRIPE_CONFIG  # Shared configuration and Stripe settings


class StripeClient:
    """Stripe payment client for DTL-Global platform operations.
    
    Handles all payment processing, subscription management, and Stripe Connect
    operations. Enforces SANDBOX mode for development and testing.
    """
    
    def __init__(self):
        """Initialize Stripe client with authentication and configuration.
        
        Loads Stripe secret key from SSM Parameter Store and validates
        that it's a sandbox key (sk_test_) for safety.
        
        Raises:
            ValueError: If Stripe key is not a sandbox key
            RuntimeError: If SSM parameter retrieval fails
        """
        # Get Stripe secret key from SSM Parameter Store (may raise RuntimeError)
        self._secret_key = config.get_secret("stripe_secret")  # Load secret key from SSM securely
        
        # Validate that we're using sandbox keys only (per plan Section 4)
        if not config.validate_stripe_key(self._secret_key):  # Check for sk_test_ prefix
            raise ValueError(  # Enforce sandbox-only policy
                "Stripe key must be sandbox (sk_test_) until production switch. "
                "See docs/AUTHENTICATION.md for switching procedure."
            )  # End sandbox validation
        
        # Set Stripe API key and configuration globally
        stripe.api_key = self._secret_key  # Set global Stripe API key for SDK
        stripe.api_version = STRIPE_CONFIG["api_version"]  # Use latest API version from config
        
        # Get Stripe Connect client ID for Connect operations
        self._connect_client_id = config.get_secret("stripe_connect_client_id")  # Load Connect ID from SSM
        
        # Cache for product and price data (performance optimization)
        self._products_cache = {}  # Cache product definitions to avoid repeated API calls
        self._prices_cache = {}    # Cache price definitions for subscription management
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Stripe customer.
        
        Args:
            customer_data: Dictionary of customer properties
                Required: email
                Optional: name, phone, address, metadata
        
        Returns:
            Dictionary containing created customer data with Stripe ID
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
            ValueError: If required fields are missing
        """
        # Validate required fields
        if 'email' not in customer_data:
            raise ValueError("Email is required for customer creation")
        
        try:
            # Create customer via Stripe API with provided data
            customer = stripe.Customer.create(**customer_data)  # Pass all customer data to Stripe API
            
            # Return standardized customer data dictionary
            return {  # Dictionary with essential customer information
                'id': customer.id,  # Stripe customer ID for future operations
                'email': customer.email,  # Customer email address
                'name': customer.name,  # Customer full name
                'phone': customer.phone,  # Customer phone number
                'created': customer.created,  # Customer creation timestamp
                'metadata': customer.metadata  # Custom metadata attached to customer
            }  # End customer response dictionary
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with context
            error_msg = f"Failed to create Stripe customer: {e}"  # Include operation context
            raise RuntimeError(error_msg) from e  # Re-raise as application error with chaining
    
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve a customer by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Customer data dictionary if found, None if not found
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            # Search for customer by email address
            customers = stripe.Customer.list(email=email, limit=1)  # Query Stripe for customers with this email
            
            # Return first result if found, None if not found
            if customers.data:  # Check if any customers were found
                customer = customers.data[0]  # Get first matching customer
                return {  # Dictionary with standardized customer response
                    'id': customer.id,  # Stripe customer ID
                    'email': customer.email,  # Customer email address
                    'name': customer.name,  # Customer full name
                    'phone': customer.phone,  # Customer phone number
                    'created': customer.created,  # Customer creation timestamp
                    'metadata': customer.metadata  # Custom metadata
                }  # End customer response dictionary
            
            return None  # Customer not found (empty results)
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with email context
            error_msg = f"Failed to search customer by email {email}: {e}"  # Include email in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def create_invoice(self, customer_id: str, line_items: List[Dict[str, Any]], 
                      metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create and send an invoice to a customer.
        
        Args:
            customer_id: Stripe customer ID
            line_items: List of invoice line items with price_id and quantity
            metadata: Optional metadata to attach to invoice
            
        Returns:
            Dictionary containing created invoice data
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            # Create invoice
            invoice = stripe.Invoice.create(
                customer=customer_id,
                metadata=metadata or {},
                auto_advance=True,  # Automatically finalize invoice
                collection_method='send_invoice',  # Send via email
                days_until_due=30  # 30-day payment terms
            )
            
            # Add line items to invoice
            for item in line_items:
                stripe.InvoiceItem.create(
                    customer=customer_id,
                    invoice=invoice.id,
                    price=item['price_id'],
                    quantity=item.get('quantity', 1)
                )
            
            # Finalize and send the invoice
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
            invoice = stripe.Invoice.send_invoice(invoice.id)
            
            # Return invoice data
            return {
                'id': invoice.id,
                'number': invoice.number,
                'status': invoice.status,
                'amount_due': invoice.amount_due,
                'currency': invoice.currency,
                'hosted_invoice_url': invoice.hosted_invoice_url,
                'invoice_pdf': invoice.invoice_pdf,
                'created': invoice.created
            }
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with customer context
            error_msg = f"Failed to create invoice for customer {customer_id}: {e}"  # Include customer ID in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def create_subscription(self, customer_id: str, price_id: str,
                          metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the subscription
            metadata: Optional metadata to attach to subscription
            
        Returns:
            Dictionary containing created subscription data
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                metadata=metadata or {},
                payment_behavior='default_incomplete',  # Require payment method
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent']  # Include payment intent
            )
            
            # Return subscription data
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'latest_invoice': {
                    'id': subscription.latest_invoice.id,
                    'payment_intent': subscription.latest_invoice.payment_intent
                },
                'created': subscription.created
            }
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with customer context
            error_msg = f"Failed to create subscription for customer {customer_id}: {e}"  # Include customer ID in error
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def get_dtl_products(self) -> Dict[str, Dict[str, Any]]:
        """Get DTL-Global service products and pricing.
        
        Returns the standard DTL service packages as defined in
        DTL_MASTER_PLAN.md Section 6.4 (9 total products).
        
        Returns:
            Dictionary mapping product names to product/price data
        """
        # DTL-Global service products (from master plan Section 6.4 - 9 total products)
        return {  # Dictionary of all DTL service products and pricing
            # One-time setup products (4 tiers)
            'dtl_starter_setup': {  # Starter package setup
                'name': 'DTL Starter Setup',  # Product display name
                'description': 'Website + hosting + SEO setup',  # Product description
                'amount': 50000,  # $500.00 in cents (Stripe uses cents)
                'currency': 'usd',  # US Dollar currency
                'type': 'one_time'  # One-time payment type
            },  # End starter setup product
            'dtl_growth_setup': {  # Growth package setup
                'name': 'DTL Growth Setup',  # Product display name
                'description': 'Starter + HubSpot CRM + Stripe + custom email',  # Product description
                'amount': 125000,  # $1,250.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'one_time'  # One-time payment type
            },  # End growth setup product
            'dtl_professional_setup': {  # Professional package setup
                'name': 'DTL Professional Setup',  # Product display name
                'description': 'Growth + AI chatbot + CRM import + priority support',  # Product description
                'amount': 250000,  # $2,500.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'one_time'  # One-time payment type
            },  # End professional setup product
            'dtl_premium_setup': {  # Premium package setup
                'name': 'DTL Premium Setup',  # Product display name
                'description': 'Professional + bots + custom automations',  # Product description
                'amount': 400000,  # $4,000.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'one_time'  # One-time payment type
            },  # End premium setup product
            
            # Monthly subscription products (5 tiers including Friends & Family)
            'dtl_friends_family': {  # Friends and Family hosting
                'name': 'DTL Friends and Family Hosting',  # Product display name
                'description': 'Website hosting and basic maintenance',  # Product description
                'amount': 2000,  # $20.00 in cents (special pricing)
                'currency': 'usd',  # US Dollar currency
                'type': 'recurring',  # Recurring payment type
                'interval': 'month'  # Monthly billing interval
            },  # End friends family product
            'dtl_starter_monthly': {  # Starter monthly service
                'name': 'DTL Starter Monthly',  # Product display name
                'description': 'Website hosting + SEO maintenance',  # Product description
                'amount': 4900,  # $49.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'recurring',  # Recurring payment type
                'interval': 'month'  # Monthly billing interval
            },  # End starter monthly product
            'dtl_growth_monthly': {  # Growth monthly service
                'name': 'DTL Growth Monthly',  # Product display name
                'description': 'Starter + CRM + payment processing',  # Product description
                'amount': 14900,  # $149.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'recurring',  # Recurring payment type
                'interval': 'month'  # Monthly billing interval
            },  # End growth monthly product
            'dtl_professional_monthly': {  # Professional monthly service
                'name': 'DTL Professional Monthly',  # Product display name
                'description': 'Growth + AI chatbot + priority support',  # Product description
                'amount': 24900,  # $249.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'recurring',  # Recurring payment type
                'interval': 'month'  # Monthly billing interval
            },  # End professional monthly product
            'dtl_premium_monthly': {  # Premium monthly service
                'name': 'DTL Premium Monthly',  # Product display name
                'description': 'Professional + custom automations',  # Product description
                'amount': 39900,  # $399.00 in cents
                'currency': 'usd',  # US Dollar currency
                'type': 'recurring',  # Recurring payment type
                'interval': 'month'  # Monthly billing interval
            }  # End premium monthly product
        }  # End DTL products dictionary
    
    def create_connect_account(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Stripe Connect account for a client.
        
        Args:
            business_data: Dictionary of business information
                Required: email, business_type, country
                Optional: business_profile, individual, company
        
        Returns:
            Dictionary containing created Connect account data
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            # Create Express Connect account
            account = stripe.Account.create(
                type='express',  # Express account for easier onboarding
                email=business_data['email'],
                country=business_data.get('country', 'US'),
                business_type=business_data.get('business_type', 'individual'),
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True}
                },
                business_profile=business_data.get('business_profile', {}),
                metadata=business_data.get('metadata', {})
            )
            
            # Return account data
            return {
                'id': account.id,
                'email': account.email,
                'type': account.type,
                'country': account.country,
                'business_type': account.business_type,
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'created': account.created
            }
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with operation context
            error_msg = f"Failed to create Connect account: {e}"  # Describe failed operation
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def create_connect_onboarding_link(self, account_id: str, 
                                     return_url: str, refresh_url: str) -> str:
        """Create an onboarding link for a Connect account.
        
        Args:
            account_id: Stripe Connect account ID
            return_url: URL to redirect after successful onboarding
            refresh_url: URL to redirect if link expires
            
        Returns:
            Onboarding link URL
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=account_id,
                return_url=return_url,
                refresh_url=refresh_url,
                type='account_onboarding'
            )
            
            # Return the onboarding URL
            return account_link.url
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with account context
            error_msg = f"Failed to create onboarding link for account {account_id}: {e}"  # Include account id
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def process_payment(self, amount: int, currency: str, customer_id: str,
                       payment_method_id: str, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Process a one-time payment.
        
        Args:
            amount: Payment amount in cents
            currency: Currency code (e.g., 'usd')
            customer_id: Stripe customer ID
            payment_method_id: Payment method ID
            metadata: Optional metadata to attach
            
        Returns:
            Dictionary containing payment intent data
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                metadata=metadata or {}
            )
            
            # Return payment intent data
            return {
                'id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'client_secret': payment_intent.client_secret,
                'created': payment_intent.created
            }
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with operation context
            error_msg = f"Failed to process payment: {e}"  # Describe failed operation
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def cancel_subscription(self, subscription_id: str, 
                          cancel_at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            cancel_at_period_end: Whether to cancel at period end or immediately
            
        Returns:
            Dictionary containing updated subscription data
            
        Raises:
            stripe.error.StripeError: If Stripe API call fails
        """
        try:
            if cancel_at_period_end:
                # Cancel at end of current period
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Cancel immediately
                subscription = stripe.Subscription.delete(subscription_id)
            
            # Return subscription data
            return {
                'id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': subscription.canceled_at,
                'current_period_end': subscription.current_period_end
            }
            
        except stripe.error.StripeError as e:  # Handle Stripe API-specific errors
            # Handle Stripe API errors with subscription context
            error_msg = f"Failed to cancel subscription {subscription_id}: {e}"  # Include subscription id
            raise RuntimeError(error_msg) from e  # Re-raise as application error
    
    def validate_webhook_signature(self, payload: str, signature: str, 
                                 webhook_secret: str) -> bool:
        """Validate a Stripe webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            webhook_secret: Webhook endpoint secret
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Verify webhook signature
            stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return True  # Signature is valid
            
        except (stripe.error.SignatureVerificationError, ValueError):
            # Signature validation failed
            return False


# Global Stripe client instance (singleton pattern for Lambda efficiency)
stripe_client = StripeClient()  # Shared instance across all handler modules (SANDBOX mode enforced)