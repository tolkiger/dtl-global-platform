"""AWS SES email client for DTL-Global onboarding platform.

This module provides email functionality for the DTL-Global platform including:
- Transactional emails (invoices, notifications, onboarding)
- Email template management
- Bounce and complaint handling
- Email verification and domain setup
- Multi-part HTML/text email support

Uses AWS SES with individual email verification (no custom domains required).

Author: DTL-Global Platform
"""

import boto3
import json
from typing import Dict, List, Optional, Any, Union
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from botocore.exceptions import ClientError

from config import config, SES_CONFIG


class SESClient:
    """AWS SES email client for DTL-Global platform operations.
    
    Handles all email communications including transactional emails,
    notifications, and onboarding communications. Supports both HTML
    and plain text formats with attachment capabilities.
    """
    
    def __init__(self):
        """Initialize SES client with AWS configuration.
        
        Sets up SES client in the appropriate region and loads
        configuration from the platform config.
        """
        # Initialize SES client in the configured region
        self._ses_client = boto3.client('ses', region_name=SES_CONFIG['region'])
        
        # Get default sender email from configuration
        self._default_sender = SES_CONFIG['from_email']
        
        # Email template cache
        self._templates_cache = {}  # Cache for email templates
    
    def send_email(self, to_addresses: Union[str, List[str]], subject: str,
                  body_text: str, body_html: Optional[str] = None,
                  from_address: Optional[str] = None,
                  reply_to: Optional[str] = None,
                  attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send an email via AWS SES.
        
        Args:
            to_addresses: Recipient email address(es)
            subject: Email subject line
            body_text: Plain text email body
            body_html: Optional HTML email body
            from_address: Optional sender address (defaults to platform default)
            reply_to: Optional reply-to address
            attachments: Optional list of attachment dictionaries
            
        Returns:
            Dictionary containing SES response with MessageId
            
        Raises:
            ClientError: If SES API call fails
            ValueError: If required parameters are missing
        """
        # Validate required parameters
        if not to_addresses:
            raise ValueError("At least one recipient address is required")
        if not subject or not body_text:
            raise ValueError("Subject and body text are required")
        
        # Normalize to_addresses to list
        if isinstance(to_addresses, str):
            to_addresses = [to_addresses]
        
        # Use default sender if not specified
        sender_address = from_address or self._default_sender
        
        try:
            if attachments:
                # Send email with attachments using raw message
                return self._send_raw_email(
                    to_addresses, subject, body_text, body_html,
                    sender_address, reply_to, attachments
                )
            else:
                # Send simple email without attachments
                destination = {'ToAddresses': to_addresses}
                
                # Build message content
                message = {
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'}
                    }
                }
                
                # Add HTML body if provided
                if body_html:
                    message['Body']['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}
                
                # Add reply-to if specified
                reply_to_addresses = [reply_to] if reply_to else []
                
                # Send email via SES
                response = self._ses_client.send_email(
                    Source=sender_address,
                    Destination=destination,
                    Message=message,
                    ReplyToAddresses=reply_to_addresses
                )
                
                # Return response with message ID
                return {
                    'MessageId': response['MessageId'],
                    'ResponseMetadata': response['ResponseMetadata']
                }
                
        except ClientError as e:
            # Handle SES API errors
            error_code = e.response['Error']['Code']
            error_msg = f"Failed to send email: {error_code} - {e.response['Error']['Message']}"
            raise ClientError(error_msg) from e
    
    def send_onboarding_welcome(self, client_email: str, client_name: str,
                              project_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send welcome email to new client starting onboarding.
        
        Args:
            client_email: Client's email address
            client_name: Client's name
            project_details: Dictionary containing project information
            
        Returns:
            Dictionary containing SES response
        """
        # Create welcome email content
        subject = f"Welcome to DTL-Global - {project_details.get('project_name', 'Your Project')}"
        
        # Build plain text body
        text_body = f"""
Dear {client_name},

Welcome to DTL-Global! We're excited to help transform your business with our digital solutions.

PROJECT DETAILS:
- Project: {project_details.get('project_name', 'Not specified')}
- Services: {', '.join(project_details.get('services', []))}
- Timeline: {project_details.get('timeline', 'To be determined')}

NEXT STEPS:
1. We'll schedule a discovery call within 24 hours
2. Our team will begin initial setup and planning
3. You'll receive regular updates throughout the process

If you have any questions, please don't hesitate to reach out.

Best regards,
The DTL-Global Team

---
DTL-Global Digital Transformation
Email: {self._default_sender}
"""
        
        # Build HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to DTL-Global</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c5aa0;">Welcome to DTL-Global!</h1>
        
        <p>Dear {client_name},</p>
        
        <p>Welcome to DTL-Global! We're excited to help transform your business with our digital solutions.</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2c5aa0;">Project Details</h3>
            <ul>
                <li><strong>Project:</strong> {project_details.get('project_name', 'Not specified')}</li>
                <li><strong>Services:</strong> {', '.join(project_details.get('services', []))}</li>
                <li><strong>Timeline:</strong> {project_details.get('timeline', 'To be determined')}</li>
            </ul>
        </div>
        
        <h3 style="color: #2c5aa0;">Next Steps</h3>
        <ol>
            <li>We'll schedule a discovery call within 24 hours</li>
            <li>Our team will begin initial setup and planning</li>
            <li>You'll receive regular updates throughout the process</li>
        </ol>
        
        <p>If you have any questions, please don't hesitate to reach out.</p>
        
        <p>Best regards,<br>
        <strong>The DTL-Global Team</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #666;">
            DTL-Global Digital Transformation<br>
            Email: {self._default_sender}
        </p>
    </div>
</body>
</html>
"""
        
        # Send welcome email
        return self.send_email(
            to_addresses=client_email,
            subject=subject,
            body_text=text_body.strip(),
            body_html=html_body.strip()
        )
    
    def send_invoice_notification(self, client_email: str, client_name: str,
                                invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send invoice notification email to client.
        
        Args:
            client_email: Client's email address
            client_name: Client's name
            invoice_data: Dictionary containing invoice information
            
        Returns:
            Dictionary containing SES response
        """
        # Create invoice notification content
        subject = f"Invoice #{invoice_data.get('number', 'N/A')} from DTL-Global"
        
        # Format invoice amount
        amount = invoice_data.get('amount_due', 0) / 100  # Convert from cents
        currency = invoice_data.get('currency', 'USD').upper()
        
        # Build plain text body
        text_body = f"""
Dear {client_name},

Your invoice from DTL-Global is ready for payment.

INVOICE DETAILS:
- Invoice Number: {invoice_data.get('number', 'N/A')}
- Amount Due: {currency} ${amount:.2f}
- Due Date: {invoice_data.get('due_date', 'Upon receipt')}

You can view and pay your invoice online at:
{invoice_data.get('hosted_invoice_url', 'Contact us for payment link')}

If you have any questions about this invoice, please contact us.

Thank you for your business!

Best regards,
The DTL-Global Team

---
DTL-Global Digital Transformation
Email: {self._default_sender}
"""
        
        # Build HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Invoice from DTL-Global</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c5aa0;">Invoice from DTL-Global</h1>
        
        <p>Dear {client_name},</p>
        
        <p>Your invoice from DTL-Global is ready for payment.</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2c5aa0;">Invoice Details</h3>
            <ul>
                <li><strong>Invoice Number:</strong> {invoice_data.get('number', 'N/A')}</li>
                <li><strong>Amount Due:</strong> {currency} ${amount:.2f}</li>
                <li><strong>Due Date:</strong> {invoice_data.get('due_date', 'Upon receipt')}</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{invoice_data.get('hosted_invoice_url', '#')}" 
               style="background: #2c5aa0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                View & Pay Invoice
            </a>
        </div>
        
        <p>If you have any questions about this invoice, please contact us.</p>
        
        <p>Thank you for your business!</p>
        
        <p>Best regards,<br>
        <strong>The DTL-Global Team</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #666;">
            DTL-Global Digital Transformation<br>
            Email: {self._default_sender}
        </p>
    </div>
</body>
</html>
"""
        
        # Send invoice notification
        return self.send_email(
            to_addresses=client_email,
            subject=subject,
            body_text=text_body.strip(),
            body_html=html_body.strip()
        )
    
    def send_status_update(self, client_email: str, client_name: str,
                          status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send project status update email to client.
        
        Args:
            client_email: Client's email address
            client_name: Client's name
            status_data: Dictionary containing status information
            
        Returns:
            Dictionary containing SES response
        """
        # Create status update content
        subject = f"Project Update: {status_data.get('project_name', 'Your Project')}"
        
        # Build plain text body
        text_body = f"""
Dear {client_name},

Here's an update on your project progress with DTL-Global.

PROJECT: {status_data.get('project_name', 'Not specified')}
CURRENT STAGE: {status_data.get('current_stage', 'In progress')}
COMPLETION: {status_data.get('completion_percentage', 0)}%

RECENT ACTIVITIES:
{self._format_activities_text(status_data.get('activities', []))}

NEXT STEPS:
{self._format_next_steps_text(status_data.get('next_steps', []))}

If you have any questions or concerns, please don't hesitate to reach out.

Best regards,
The DTL-Global Team

---
DTL-Global Digital Transformation
Email: {self._default_sender}
"""
        
        # Build HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Project Update</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #2c5aa0;">Project Update</h1>
        
        <p>Dear {client_name},</p>
        
        <p>Here's an update on your project progress with DTL-Global.</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2c5aa0;">Project Status</h3>
            <ul>
                <li><strong>Project:</strong> {status_data.get('project_name', 'Not specified')}</li>
                <li><strong>Current Stage:</strong> {status_data.get('current_stage', 'In progress')}</li>
                <li><strong>Completion:</strong> {status_data.get('completion_percentage', 0)}%</li>
            </ul>
        </div>
        
        <h3 style="color: #2c5aa0;">Recent Activities</h3>
        {self._format_activities_html(status_data.get('activities', []))}
        
        <h3 style="color: #2c5aa0;">Next Steps</h3>
        {self._format_next_steps_html(status_data.get('next_steps', []))}
        
        <p>If you have any questions or concerns, please don't hesitate to reach out.</p>
        
        <p>Best regards,<br>
        <strong>The DTL-Global Team</strong></p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="font-size: 12px; color: #666;">
            DTL-Global Digital Transformation<br>
            Email: {self._default_sender}
        </p>
    </div>
</body>
</html>
"""
        
        # Send status update
        return self.send_email(
            to_addresses=client_email,
            subject=subject,
            body_text=text_body.strip(),
            body_html=html_body.strip()
        )
    
    def verify_email_address(self, email_address: str) -> Dict[str, Any]:
        """Verify an email address for sending.
        
        Args:
            email_address: Email address to verify
            
        Returns:
            Dictionary containing verification response
            
        Raises:
            ClientError: If SES API call fails
        """
        try:
            # Send verification email via SES
            response = self._ses_client.verify_email_identity(
                EmailAddress=email_address
            )
            
            # Return verification response
            return {
                'email_address': email_address,
                'verification_sent': True,
                'response_metadata': response['ResponseMetadata']
            }
            
        except ClientError as e:
            # Handle SES API errors
            error_msg = f"Failed to verify email {email_address}: {e}"
            raise ClientError(error_msg) from e
    
    def get_send_statistics(self) -> Dict[str, Any]:
        """Get SES sending statistics.
        
        Returns:
            Dictionary containing send statistics
            
        Raises:
            ClientError: If SES API call fails
        """
        try:
            # Get send statistics from SES
            response = self._ses_client.get_send_statistics()
            
            # Return statistics data
            return {
                'send_data_points': response['SendDataPoints'],
                'response_metadata': response['ResponseMetadata']
            }
            
        except ClientError as e:
            # Handle SES API errors
            error_msg = f"Failed to get send statistics: {e}"
            raise ClientError(error_msg) from e
    
    def _send_raw_email(self, to_addresses: List[str], subject: str,
                       body_text: str, body_html: Optional[str],
                       from_address: str, reply_to: Optional[str],
                       attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send raw email with attachments.
        
        Args:
            to_addresses: List of recipient addresses
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            from_address: Sender address
            reply_to: Optional reply-to address
            attachments: List of attachment dictionaries
            
        Returns:
            Dictionary containing SES response
        """
        # Create multipart message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = from_address
        msg['To'] = ', '.join(to_addresses)
        
        # Add reply-to if specified
        if reply_to:
            msg['Reply-To'] = reply_to
        
        # Create message body
        body = MIMEMultipart('alternative')
        
        # Add text part
        text_part = MIMEText(body_text, 'plain', 'utf-8')
        body.attach(text_part)
        
        # Add HTML part if provided
        if body_html:
            html_part = MIMEText(body_html, 'html', 'utf-8')
            body.attach(html_part)
        
        # Attach body to main message
        msg.attach(body)
        
        # Add attachments
        for attachment in attachments:
            att = MIMEApplication(
                attachment['content'],
                attachment.get('subtype', 'octet-stream')
            )
            att.add_header(
                'Content-Disposition',
                'attachment',
                filename=attachment['filename']
            )
            msg.attach(att)
        
        # Send raw email
        response = self._ses_client.send_raw_email(
            Source=from_address,
            Destinations=to_addresses,
            RawMessage={'Data': msg.as_string()}
        )
        
        return {
            'MessageId': response['MessageId'],
            'ResponseMetadata': response['ResponseMetadata']
        }
    
    def _format_activities_text(self, activities: List[str]) -> str:
        """Format activities list for plain text email.
        
        Args:
            activities: List of activity strings
            
        Returns:
            Formatted activities text
        """
        if not activities:
            return "- No recent activities"
        
        return '\n'.join(f"- {activity}" for activity in activities)
    
    def _format_activities_html(self, activities: List[str]) -> str:
        """Format activities list for HTML email.
        
        Args:
            activities: List of activity strings
            
        Returns:
            Formatted activities HTML
        """
        if not activities:
            return "<p>No recent activities</p>"
        
        items = ''.join(f"<li>{activity}</li>" for activity in activities)
        return f"<ul>{items}</ul>"
    
    def _format_next_steps_text(self, next_steps: List[str]) -> str:
        """Format next steps list for plain text email.
        
        Args:
            next_steps: List of next step strings
            
        Returns:
            Formatted next steps text
        """
        if not next_steps:
            return "- To be determined"
        
        return '\n'.join(f"- {step}" for step in next_steps)
    
    def _format_next_steps_html(self, next_steps: List[str]) -> str:
        """Format next steps list for HTML email.
        
        Args:
            next_steps: List of next step strings
            
        Returns:
            Formatted next steps HTML
        """
        if not next_steps:
            return "<p>To be determined</p>"
        
        items = ''.join(f"<li>{step}</li>" for step in next_steps)
        return f"<ol>{items}</ol>"


# Global SES client instance
ses_client = SESClient()