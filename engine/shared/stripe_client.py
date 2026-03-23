"""Stripe payment client for DTL-Global onboarding platform.

This module provides a comprehensive Stripe API client for managing:
- Products and pricing (DTL service packages)
- Customers and payment methods
- Invoices and subscriptions
- Stripe Connect for client payment accounts
- Payment processing and webhooks

IMPORTANT: All operations run in SANDBOX mode (sk_test_) until production switch.
See docs/AUTHENTICATION.md for switching to live keys.

Author: DTL-Global Platform
"""

import stripe
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from datetime import datetime, timedelta

from config import config, STRIPE_CONFIG


class StripeClient:
    """Stripe payment client for DTL-Global platform operations.
    
    Handles all payment processing, subscription management, and Stripe Connect
    operations. Enforces SANDBOX mode for development and testing.
    """
    
    def __init__(self):
        """Initialize Stripe client with authentication and configuration.
        
        Loads Stripe secret key from SSM Parameter Store and validates
        that it's a sandbox key (sk_test_) for safety.
        """
        # Get Stripe secret key from SSM Parameter Store
        self._secret_key = config.get_secret("stripe_secret")
        
        # Validate that we're using sandbox keys only
        if not config.validate_stripe_key(self._secret_key):
            raise ValueError(
                "Stripe key must be sandbox (sk_test_) until production switch. "
                "See docs/AUTHENTICATION.md for switching procedure."
            )
        
        # Set Stripe API key and configuration
        stripe.api_key = self._secret_key
        stripe.api_version = STRIPE_CONFIG["api_version"]  # Use latest API version
        
        # Get Stripe Connect client ID for Connect operations
        self._connect_client_id = config.get_secret("stripe_connect_client_id")
        
        # Cache for product and price data
        self._products_cache = {}  # Cache product definitions
        self._prices_cache = {}    # Cache price definitions
    
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
            # Create customer via Stripe API
            customer = stripe.Customer.create(**customer_data)
            
            # Return customer data
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'phone': customer.phone,
                'created': customer.created,
                'metadata': customer.metadata
            }
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to create Stripe customer: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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
            # Search for customer by email
            customers = stripe.Customer.list(email=email, limit=1)
            
            # Return first result if found
            if customers.data:
                customer = customers.data[0]
                return {
                    'id': customer.id,
                    'email': customer.email,
                    'name': customer.name,
                    'phone': customer.phone,
                    'created': customer.created,
                    'metadata': customer.metadata
                }
            
            return None  # Customer not found
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to search customer by email {email}: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to create invoice for customer {customer_id}: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to create subscription for customer {customer_id}: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
    def get_dtl_products(self) -> Dict[str, Dict[str, Any]]:
        """Get DTL-Global service products and pricing.
        
        Returns the standard DTL service packages as defined in
        DTL_MASTER_PLAN.md Section 6.4.
        
        Returns:
            Dictionary mapping product names to product/price data
        """
        # DTL-Global service products (from master plan Section 6.4)
        return {
            # One-time setup products
            'dtl_starter_setup': {
                'name': 'DTL Starter Setup',
                'description': 'Website + hosting + SEO setup',
                'amount': 50000,  # $500.00 in cents
                'currency': 'usd',
                'type': 'one_time'
            },
            'dtl_growth_setup': {
                'name': 'DTL Growth Setup', 
                'description': 'Starter + HubSpot CRM + Stripe + custom email',
                'amount': 125000,  # $1,250.00 in cents
                'currency': 'usd',
                'type': 'one_time'
            },
            'dtl_professional_setup': {
                'name': 'DTL Professional Setup',
                'description': 'Growth + AI chatbot + CRM import + priority support',
                'amount': 250000,  # $2,500.00 in cents
                'currency': 'usd',
                'type': 'one_time'
            },
            'dtl_premium_setup': {
                'name': 'DTL Premium Setup',
                'description': 'Professional + bots + custom automations',
                'amount': 400000,  # $4,000.00 in cents
                'currency': 'usd',
                'type': 'one_time'
            },
            
            # Monthly subscription products
            'dtl_friends_family': {
                'name': 'DTL Friends and Family Hosting',
                'description': 'Website hosting and basic maintenance',
                'amount': 2000,  # $20.00 in cents
                'currency': 'usd',
                'type': 'recurring',
                'interval': 'month'
            },
            'dtl_starter_monthly': {
                'name': 'DTL Starter Monthly',
                'description': 'Website hosting + SEO maintenance',
                'amount': 4900,  # $49.00 in cents
                'currency': 'usd',
                'type': 'recurring',
                'interval': 'month'
            },
            'dtl_growth_monthly': {
                'name': 'DTL Growth Monthly',
                'description': 'Starter + CRM + payment processing',
                'amount': 14900,  # $149.00 in cents
                'currency': 'usd',
                'type': 'recurring',
                'interval': 'month'
            },
            'dtl_professional_monthly': {
                'name': 'DTL Professional Monthly',
                'description': 'Growth + AI chatbot + priority support',
                'amount': 24900,  # $249.00 in cents
                'currency': 'usd',
                'type': 'recurring',
                'interval': 'month'
            },
            'dtl_premium_monthly': {
                'name': 'DTL Premium Monthly',
                'description': 'Professional + custom automations',
                'amount': 39900,  # $399.00 in cents
                'currency': 'usd',
                'type': 'recurring',
                'interval': 'month'
            }
        }
    
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
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to create Connect account: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to create onboarding link for account {account_id}: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to process payment: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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
            
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            error_msg = f"Failed to cancel subscription {subscription_id}: {e}"
            raise stripe.error.StripeError(error_msg) from e
    
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


# Global Stripe client instance
stripe_client = StripeClient()