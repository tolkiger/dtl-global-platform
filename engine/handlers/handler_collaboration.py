"""POST /collaboration Lambda handler for DTL-Global onboarding platform.

This handler manages Slack and Microsoft Teams integration setup.

Endpoint: POST /collaboration
Purpose: Configure Slack/Teams integrations for client communications
Dependencies: Configuration management for webhook and bot setup

Author: DTL-Global Platform
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib
import base64

# Import shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from config import config
from hubspot_client import hubspot_client


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle Slack and Teams integration setup and webhooks.
    
    Args:
        event: API Gateway event containing collaboration request
        context: Lambda context object
        
    Returns:
        Dict containing collaboration integration results
    """
    print(f"Collaboration handler started - Request ID: {context.aws_request_id}")
    
    try:
        # Parse request body from API Gateway event
        request_data = json.loads(event['body'])
        
        # Extract collaboration platform and operation
        platform = request_data.get('platform', 'slack')  # slack, teams
        operation = request_data.get('operation', 'setup')  # setup, webhook, send_message
        
        if platform == 'slack':
            return _handle_slack_integration(operation, request_data)
        elif platform == 'teams':
            return _handle_teams_integration(operation, request_data)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Unsupported collaboration platform: {platform}',
                    'success': False
                })
            }
        
    except json.JSONDecodeError as e:
        # Handle invalid JSON in request body
        print(f"JSON decode error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body',
                'success': False
            })
        }
        
    except Exception as e:
        # Handle unexpected errors
        print(f"Collaboration handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error processing collaboration request',
                'success': False
            })
        }


def _handle_slack_integration(operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Slack integration operations.
    
    Args:
        operation: Type of operation (setup, webhook, send_message)
        request_data: Request data containing operation parameters
        
    Returns:
        Dictionary with Slack integration results
    """
    try:
        if operation == 'setup':
            return _setup_slack_integration(request_data)
        elif operation == 'webhook':
            return _handle_slack_webhook(request_data)
        elif operation == 'send_message':
            return _send_slack_message(request_data)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Unsupported Slack operation: {operation}',
                    'success': False
                })
            }
            
    except Exception as e:
        print(f"Error in Slack integration: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Slack integration error: {str(e)}',
                'success': False
            })
        }


def _handle_teams_integration(operation: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft Teams integration operations.
    
    Args:
        operation: Type of operation (setup, webhook, send_message)
        request_data: Request data containing operation parameters
        
    Returns:
        Dictionary with Teams integration results
    """
    try:
        if operation == 'setup':
            return _setup_teams_integration(request_data)
        elif operation == 'webhook':
            return _handle_teams_webhook(request_data)
        elif operation == 'send_message':
            return _send_teams_message(request_data)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Unsupported Teams operation: {operation}',
                    'success': False
                })
            }
            
    except Exception as e:
        print(f"Error in Teams integration: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Teams integration error: {str(e)}',
                'success': False
            })
        }


def _setup_slack_integration(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Set up Slack integration for client workspace.
    
    Args:
        request_data: Request data containing setup parameters
        
    Returns:
        Dictionary with Slack setup results
    """
    try:
        # Extract setup parameters
        client_info = request_data.get('client_info', {})
        workspace_name = client_info.get('company', 'Client Workspace')
        admin_email = request_data.get('admin_email', '')
        webhook_url = request_data.get('webhook_url', '')
        
        print(f"Setting up Slack integration for {workspace_name}")
        
        # Generate Slack app configuration
        slack_config = _generate_slack_config(workspace_name, admin_email, webhook_url)
        
        # Generate setup instructions
        instructions = _generate_slack_instructions(slack_config)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'platform': 'slack',
                'workspace_name': workspace_name,
                'slack_config': slack_config,
                'instructions': instructions,
                'webhook_url': webhook_url or 'To be configured'
            })
        }
        
    except Exception as e:
        print(f"Error setting up Slack integration: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Slack setup error: {str(e)}',
                'success': False
            })
        }


def _setup_teams_integration(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Set up Microsoft Teams integration for client organization.
    
    Args:
        request_data: Request data containing setup parameters
        
    Returns:
        Dictionary with Teams setup results
    """
    try:
        # Extract setup parameters
        client_info = request_data.get('client_info', {})
        organization_name = client_info.get('company', 'Client Organization')
        admin_email = request_data.get('admin_email', '')
        webhook_url = request_data.get('webhook_url', '')
        
        print(f"Setting up Teams integration for {organization_name}")
        
        # Generate Teams app configuration
        teams_config = _generate_teams_config(organization_name, admin_email, webhook_url)
        
        # Generate setup instructions
        instructions = _generate_teams_instructions(teams_config)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'platform': 'teams',
                'organization_name': organization_name,
                'teams_config': teams_config,
                'instructions': instructions,
                'webhook_url': webhook_url or 'To be configured'
            })
        }
        
    except Exception as e:
        print(f"Error setting up Teams integration: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Teams setup error: {str(e)}',
                'success': False
            })
        }


def _generate_slack_config(workspace_name: str, admin_email: str, 
                         webhook_url: str) -> Dict[str, Any]:
    """Generate Slack app configuration.
    
    Args:
        workspace_name: Name of the Slack workspace
        admin_email: Admin email for setup
        webhook_url: Webhook URL for receiving events
        
    Returns:
        Dictionary with Slack configuration
    """
    app_name = f"DTL-Global Assistant for {workspace_name}"
    
    config = {
        'app_info': {
            'name': app_name,
            'description': f'Digital transformation assistant for {workspace_name}',
            'short_description': 'DTL-Global digital transformation bot',
            'icon': 'https://dtl-global.org/assets/slack-icon.png',
            'background_color': '#2c5aa0'
        },
        'oauth_config': {
            'redirect_urls': [webhook_url] if webhook_url else [],
            'scopes': {
                'bot': [
                    'channels:read',
                    'channels:write',
                    'chat:write',
                    'commands',
                    'im:read',
                    'im:write',
                    'users:read',
                    'users:read.email'
                ],
                'user': [
                    'channels:read',
                    'users:read'
                ]
            }
        },
        'event_subscriptions': {
            'request_url': webhook_url,
            'bot_events': [
                'message.channels',
                'message.im',
                'app_mention'
            ]
        },
        'slash_commands': [
            {
                'command': '/dtl-help',
                'url': webhook_url,
                'description': 'Get help with DTL-Global services',
                'usage_hint': '[service type]'
            },
            {
                'command': '/dtl-quote',
                'url': webhook_url,
                'description': 'Request a quote for digital transformation services',
                'usage_hint': '[project description]'
            }
        ],
        'interactive_components': {
            'request_url': webhook_url
        },
        'bot_user': {
            'display_name': 'DTL-Global Assistant',
            'default_username': 'dtl-global-bot',
            'always_online': True
        }
    }
    
    return config


def _generate_teams_config(organization_name: str, admin_email: str, 
                         webhook_url: str) -> Dict[str, Any]:
    """Generate Microsoft Teams app configuration.
    
    Args:
        organization_name: Name of the Teams organization
        admin_email: Admin email for setup
        webhook_url: Webhook URL for receiving events
        
    Returns:
        Dictionary with Teams configuration
    """
    app_name = f"DTL-Global Assistant for {organization_name}"
    
    config = {
        'manifest': {
            '$schema': 'https://developer.microsoft.com/en-us/json-schemas/teams/v1.16/MicrosoftTeams.schema.json',
            'manifestVersion': '1.16',
            'version': '1.0.0',
            'id': f'dtl-global-{hashlib.md5(organization_name.encode()).hexdigest()[:8]}',
            'packageName': f'com.dtlglobal.{organization_name.lower().replace(" ", "")}',
            'developer': {
                'name': 'DTL-Global',
                'websiteUrl': 'https://dtl-global.org',
                'privacyUrl': 'https://dtl-global.org/privacy',
                'termsOfUseUrl': 'https://dtl-global.org/terms'
            },
            'icons': {
                'color': 'https://dtl-global.org/assets/teams-icon-color.png',
                'outline': 'https://dtl-global.org/assets/teams-icon-outline.png'
            },
            'name': {
                'short': 'DTL-Global Assistant',
                'full': app_name
            },
            'description': {
                'short': 'Digital transformation assistant',
                'full': f'DTL-Global digital transformation assistant for {organization_name}'
            },
            'accentColor': '#2c5aa0'
        },
        'bots': [
            {
                'botId': f'dtl-global-bot-{hashlib.md5(organization_name.encode()).hexdigest()[:8]}',
                'needsChannelSelector': False,
                'isNotificationOnly': False,
                'scopes': ['personal', 'team', 'groupchat'],
                'commandLists': [
                    {
                        'scopes': ['personal', 'team', 'groupchat'],
                        'commands': [
                            {
                                'title': 'Help',
                                'description': 'Get help with DTL-Global services'
                            },
                            {
                                'title': 'Quote',
                                'description': 'Request a quote for digital transformation'
                            },
                            {
                                'title': 'Status',
                                'description': 'Check project status'
                            }
                        ]
                    }
                ]
            }
        ],
        'composeExtensions': [
            {
                'botId': f'dtl-global-bot-{hashlib.md5(organization_name.encode()).hexdigest()[:8]}',
                'commands': [
                    {
                        'id': 'dtl-quote',
                        'type': 'action',
                        'title': 'Request Quote',
                        'description': 'Request a digital transformation quote',
                        'initialRun': True,
                        'parameters': [
                            {
                                'name': 'project_description',
                                'title': 'Project Description',
                                'description': 'Describe your digital transformation needs'
                            }
                        ]
                    }
                ]
            }
        ],
        'permissions': [
            'identity',
            'messageTeamMembers'
        ],
        'validDomains': [
            'dtl-global.org'
        ]
    }
    
    return config


def _generate_slack_instructions(config: Dict[str, Any]) -> List[str]:
    """Generate Slack integration setup instructions.
    
    Args:
        config: Slack configuration dictionary
        
    Returns:
        List of instruction strings
    """
    app_name = config['app_info']['name']
    
    instructions = [
        "Slack Integration Setup Instructions:",
        "",
        "1. Create Slack App:",
        "   - Go to api.slack.com/apps",
        "   - Click 'Create New App' > 'From scratch'",
        f"   - App Name: {app_name}",
        "   - Select your Slack workspace",
        "",
        "2. Configure App Settings:",
        "   - Go to 'Basic Information'",
        f"   - Description: {config['app_info']['description']}",
        f"   - Background Color: {config['app_info']['background_color']}",
        "   - Upload app icon (optional)",
        "",
        "3. OAuth & Permissions:",
        "   - Go to 'OAuth & Permissions'",
        "   - Add Bot Token Scopes:",
    ]
    
    # Add bot scopes
    for scope in config['oauth_config']['scopes']['bot']:
        instructions.append(f"     - {scope}")
    
    instructions.extend([
        "",
        "4. Event Subscriptions:",
        f"   - Request URL: {config['event_subscriptions']['request_url']}",
        "   - Subscribe to Bot Events:",
    ])
    
    # Add bot events
    for event in config['event_subscriptions']['bot_events']:
        instructions.append(f"     - {event}")
    
    instructions.extend([
        "",
        "5. Slash Commands:",
    ])
    
    # Add slash commands
    for command in config['slash_commands']:
        instructions.append(f"   - Command: {command['command']}")
        instructions.append(f"     Description: {command['description']}")
        instructions.append(f"     Request URL: {command['url']}")
        instructions.append("")
    
    instructions.extend([
        "6. Install App:",
        "   - Go to 'Install App'",
        "   - Click 'Install to Workspace'",
        "   - Authorize the app",
        "   - Save the Bot User OAuth Token",
        "",
        "7. Test Integration:",
        "   - Invite bot to a channel: @DTL-Global Assistant",
        "   - Try slash commands: /dtl-help",
        "   - Send direct message to bot",
        "",
        "For assistance with Slack setup, contact DTL-Global support."
    ])
    
    return instructions


def _generate_teams_instructions(config: Dict[str, Any]) -> List[str]:
    """Generate Microsoft Teams integration setup instructions.
    
    Args:
        config: Teams configuration dictionary
        
    Returns:
        List of instruction strings
    """
    app_name = config['manifest']['name']['full']
    
    instructions = [
        "Microsoft Teams Integration Setup Instructions:",
        "",
        "1. Azure AD App Registration:",
        "   - Go to portal.azure.com",
        "   - Navigate to Azure Active Directory > App registrations",
        "   - Click 'New registration'",
        f"   - Name: {app_name}",
        "   - Supported account types: Single tenant",
        "",
        "2. Bot Framework Registration:",
        "   - Go to dev.botframework.com",
        "   - Create new bot registration",
        "   - Use App ID from Azure AD registration",
        "   - Generate and save App Password",
        f"   - Messaging endpoint: {config.get('webhook_url', 'YOUR_WEBHOOK_URL')}",
        "",
        "3. Teams App Manifest:",
        "   - Create manifest.json with the following configuration:",
        f"   - App ID: {config['manifest']['id']}",
        f"   - Version: {config['manifest']['version']}",
        f"   - Package Name: {config['manifest']['packageName']}",
        "",
        "4. App Package Creation:",
        "   - Create a ZIP file containing:",
        "     - manifest.json",
        "     - color.png (192x192 icon)",
        "     - outline.png (32x32 icon)",
        "",
        "5. Upload to Teams:",
        "   - Go to Teams Admin Center",
        "   - Navigate to Teams apps > Manage apps",
        "   - Click 'Upload' and select your app package",
        "   - Review and approve the app",
        "",
        "6. App Permissions:",
        "   - Configure the following permissions in Azure AD:",
        "     - User.Read (delegated)",
        "     - ChatMessage.Send (application)",
        "     - Team.ReadBasic.All (application)",
        "",
        "7. Bot Configuration:",
        f"   - Bot ID: {config['bots'][0]['botId']}",
        "   - Supported scopes: personal, team, groupchat",
        "   - Commands available:",
    ]
    
    # Add bot commands
    for command in config['bots'][0]['commandLists'][0]['commands']:
        instructions.append(f"     - {command['title']}: {command['description']}")
    
    instructions.extend([
        "",
        "8. Test Integration:",
        "   - Install app in Teams",
        "   - Start conversation with bot",
        "   - Try available commands",
        "   - Test in team channels",
        "",
        "Note: Teams app requires admin approval in your organization.",
        "Contact your IT administrator for deployment assistance.",
        "",
        "For assistance with Teams setup, contact DTL-Global support."
    ])
    
    return instructions


def _handle_slack_webhook(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Slack webhook events and commands.
    
    Args:
        request_data: Slack webhook data
        
    Returns:
        Dictionary with webhook handling results
    """
    try:
        # Handle URL verification challenge
        if 'challenge' in request_data:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/plain'
                },
                'body': request_data['challenge']
            }
        
        # Handle Slack events
        if 'event' in request_data:
            event = request_data['event']
            event_type = event.get('type')
            
            if event_type == 'message':
                return _process_slack_message(event)
            elif event_type == 'app_mention':
                return _process_slack_mention(event)
        
        # Handle slash commands
        if 'command' in request_data:
            return _process_slack_command(request_data)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'success': True})
        }
        
    except Exception as e:
        print(f"Error handling Slack webhook: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Webhook processing error: {str(e)}',
                'success': False
            })
        }


def _handle_teams_webhook(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Microsoft Teams webhook events and commands.
    
    Args:
        request_data: Teams webhook data
        
    Returns:
        Dictionary with webhook handling results
    """
    try:
        # Handle Teams activity
        if 'type' in request_data:
            activity_type = request_data['type']
            
            if activity_type == 'message':
                return _process_teams_message(request_data)
            elif activity_type == 'invoke':
                return _process_teams_invoke(request_data)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'success': True})
        }
        
    except Exception as e:
        print(f"Error handling Teams webhook: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Webhook processing error: {str(e)}',
                'success': False
            })
        }


def _process_slack_message(event: Dict[str, Any]) -> Dict[str, Any]:
    """Process Slack message and sync to HubSpot if needed.
    
    Args:
        event: Slack message event data
        
    Returns:
        Dictionary with processing results
    """
    try:
        user_id = event.get('user', '')
        text = event.get('text', '')
        channel = event.get('channel', '')
        
        print(f"Processing Slack message from {user_id}: {text[:50]}...")
        
        # Check if message indicates a lead opportunity
        if _is_lead_message(text):
            # Create lead in HubSpot
            try:
                contact_result = hubspot_client.create_contact(
                    lead_source='Slack',
                    notes=f'Slack message: {text}',
                    slack_user_id=user_id
                )
                
                print(f"Slack lead synced to HubSpot: {contact_result.get('contact_id')}")
                
            except Exception as e:
                print(f"Error syncing Slack lead to HubSpot: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'success': True})
        }
        
    except Exception as e:
        print(f"Error processing Slack message: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Message processing error: {str(e)}',
                'success': False
            })
        }


def _process_teams_message(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Process Teams message and sync to HubSpot if needed.
    
    Args:
        activity: Teams message activity data
        
    Returns:
        Dictionary with processing results
    """
    try:
        from_user = activity.get('from', {})
        text = activity.get('text', '')
        
        print(f"Processing Teams message from {from_user.get('name', 'Unknown')}: {text[:50]}...")
        
        # Check if message indicates a lead opportunity
        if _is_lead_message(text):
            # Create lead in HubSpot
            try:
                contact_result = hubspot_client.create_contact(
                    lead_source='Microsoft Teams',
                    notes=f'Teams message: {text}',
                    teams_user_id=from_user.get('id', '')
                )
                
                print(f"Teams lead synced to HubSpot: {contact_result.get('contact_id')}")
                
            except Exception as e:
                print(f"Error syncing Teams lead to HubSpot: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'success': True})
        }
        
    except Exception as e:
        print(f"Error processing Teams message: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Message processing error: {str(e)}',
                'success': False
            })
        }


def _is_lead_message(text: str) -> bool:
    """Check if message indicates a potential lead.
    
    Args:
        text: Message text to analyze
        
    Returns:
        True if message appears to be from a potential lead
    """
    lead_keywords = [
        'quote', 'price', 'cost', 'website', 'help', 'service',
        'consultation', 'digital transformation', 'crm', 'automation'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in lead_keywords)


def _send_slack_message(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send message to Slack channel or user.
    
    Args:
        request_data: Request data with message parameters
        
    Returns:
        Dictionary with message sending results
    """
    # Placeholder for actual Slack API integration
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': True,
            'message': 'Slack message sending simulated - actual API integration required'
        })
    }


def _send_teams_message(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send message to Teams channel or user.
    
    Args:
        request_data: Request data with message parameters
        
    Returns:
        Dictionary with message sending results
    """
    # Placeholder for actual Teams API integration
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': True,
            'message': 'Teams message sending simulated - actual API integration required'
        })
    }


def _process_slack_command(command_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Slack slash command.
    
    Args:
        command_data: Slack command data
        
    Returns:
        Dictionary with command response
    """
    command = command_data.get('command', '')
    text = command_data.get('text', '')
    
    if command == '/dtl-help':
        response_text = ("DTL-Global Services:\n"
                        "• Website Development & SEO\n"
                        "• CRM Setup & Automation\n" 
                        "• Payment Processing Integration\n"
                        "• Email Marketing Setup\n"
                        "Use /dtl-quote to request a quote!")
    elif command == '/dtl-quote':
        response_text = ("Thanks for your interest! Please provide:\n"
                        "• Your business name\n"
                        "• Services needed\n"
                        "• Contact information\n"
                        "We'll get back to you within 24 hours!")
    else:
        response_text = "Unknown command. Try /dtl-help for available options."
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'response_type': 'ephemeral',
            'text': response_text
        })
    }


def _process_teams_invoke(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Process Teams invoke activity (commands/actions).
    
    Args:
        activity: Teams invoke activity data
        
    Returns:
        Dictionary with invoke response
    """
    name = activity.get('name', '')
    value = activity.get('value', {})
    
    if name == 'composeExtension/query':
        # Handle compose extension query
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'composeExtension': {
                    'type': 'result',
                    'attachmentLayout': 'list',
                    'attachments': [
                        {
                            'contentType': 'application/vnd.microsoft.card.adaptive',
                            'content': {
                                'type': 'AdaptiveCard',
                                'body': [
                                    {
                                        'type': 'TextBlock',
                                        'text': 'DTL-Global Services',
                                        'weight': 'Bolder',
                                        'size': 'Medium'
                                    },
                                    {
                                        'type': 'TextBlock',
                                        'text': 'Digital transformation services for your business'
                                    }
                                ]
                            }
                        }
                    ]
                }
            })
        }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({'success': True})
    }