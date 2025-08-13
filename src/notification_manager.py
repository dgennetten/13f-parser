"""
Notification Manager

This module handles sending notifications about new 13F filings
via various channels like GitHub issues, email, and Slack.
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages notifications for new 13F filings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the notification manager."""
        self.email_enabled = config.get('email_enabled', False)
        self.email_recipients = config.get('email_recipients', [])
        self.github_issue_enabled = config.get('github_issue_enabled', True)
        self.slack_webhook = config.get('slack_webhook', '')
        
        # GitHub configuration (will be set via environment variables)
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.github_repo = os.environ.get('GITHUB_REPOSITORY')
        
    def send_filing_notification(self, fund_name: str, filing: Dict[str, Any], 
                               parsed_data: Dict[str, Any]):
        """Send notification about a new 13F filing."""
        try:
            logger.info(f"Sending notification for new filing from {fund_name}")
            
            # Create notification message
            message = self._create_filing_message(fund_name, filing, parsed_data)
            
            # Send notifications through different channels
            if self.github_issue_enabled:
                self._create_github_issue(fund_name, filing, parsed_data, message)
            
            if self.slack_webhook:
                self._send_slack_notification(message)
            
            if self.email_enabled:
                self._send_email_notification(message)
                
        except Exception as e:
            logger.error(f"Error sending filing notification: {e}")
    
    def send_error_notification(self, error_message: str):
        """Send notification about an error."""
        try:
            logger.info("Sending error notification")
            
            message = f"❌ **13F Parser Error**\n\n{error_message}\n\nTime: {datetime.now().isoformat()}"
            
            if self.github_issue_enabled:
                self._create_github_issue("Error", {}, {}, message, is_error=True)
            
            if self.slack_webhook:
                self._send_slack_notification(message)
                
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    def _create_filing_message(self, fund_name: str, filing: Dict[str, Any], 
                             parsed_data: Dict[str, Any]) -> str:
        """Create a formatted message about the filing."""
        try:
            total_value = parsed_data.get('total_value', 0)
            holdings_count = len(parsed_data.get('holdings', []))
            
            message = f"""📊 **New 13F Filing: {fund_name}**

**Filing Details:**
- **Date:** {filing.get('filing_date', 'Unknown')}
- **Type:** {filing.get('filing_type', 'Unknown')}
- **Accession Number:** {filing.get('accession_number', 'Unknown')}

**Portfolio Summary:**
- **Total Value:** ${total_value:,}
- **Holdings Count:** {holdings_count}

**Top Holdings:**
"""
            
            # Add top 5 holdings by value
            holdings = sorted(parsed_data.get('holdings', []), 
                            key=lambda x: x.get('value', 0), reverse=True)
            
            for i, holding in enumerate(holdings[:5]):
                security_name = holding.get('security_name', 'Unknown')
                value = holding.get('value', 0)
                shares = holding.get('shares', 0)
                
                message += f"{i+1}. **{security_name}** - ${value:,} ({shares:,} shares)\n"
            
            if holdings_count > 5:
                message += f"\n... and {holdings_count - 5} more holdings"
            
            message += f"\n\n**Processed:** {datetime.now().isoformat()}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating filing message: {e}")
            return f"Error creating message: {e}"
    
    def _create_github_issue(self, fund_name: str, filing: Dict[str, Any], 
                            parsed_data: Dict[str, Any], message: str, is_error: bool = False):
        """Create a GitHub issue for the filing notification."""
        try:
            if not self.github_token or not self.github_repo:
                logger.warning("GitHub token or repository not configured, skipping issue creation")
                return
            
            # Parse repository owner and name
            owner, repo = self.github_repo.split('/')
            
            # Create issue title
            if is_error:
                title = f"❌ 13F Parser Error - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                title = f"📊 New 13F Filing: {fund_name} - {filing.get('filing_date', 'Unknown')}"
            
            # Create issue body
            body = message
            
            if not is_error:
                # Add filing details as collapsible section
                body += f"""

<details>
<summary>📋 Filing Details</summary>

```json
{json.dumps(filing, indent=2)}
```

</details>

<details>
<summary>📊 Parsed Data Summary</summary>

```json
{json.dumps({
    'total_value': parsed_data.get('total_value'),
    'holdings_count': len(parsed_data.get('holdings', [])),
    'filing_period': parsed_data.get('filing_period'),
    'manager_info': parsed_data.get('manager_info', {})
}, indent=2)}
```

</details>
"""
            
            # Create the issue
            issue_data = {
                'title': title,
                'body': body,
                'labels': ['13f-filing', 'automated'] if not is_error else ['error', '13f-parser']
            }
            
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.post(url, headers=headers, json=issue_data)
            response.raise_for_status()
            
            issue = response.json()
            logger.info(f"Created GitHub issue: {issue['html_url']}")
            
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
    
    def _send_slack_notification(self, message: str):
        """Send notification to Slack via webhook."""
        try:
            if not self.slack_webhook:
                return
            
            # Format message for Slack
            slack_message = {
                'text': message,
                'username': '13F Parser Bot',
                'icon_emoji': ':chart_with_upwards_trend:'
            }
            
            response = requests.post(self.slack_webhook, json=slack_message)
            response.raise_for_status()
            
            logger.info("Sent Slack notification")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def _send_email_notification(self, message: str):
        """Send notification via email."""
        try:
            if not self.email_enabled or not self.email_recipients:
                return
            
            # This is a placeholder for email functionality
            # You would need to implement actual email sending logic
            # using libraries like smtplib or services like SendGrid
            
            logger.info("Email notification would be sent here")
            logger.info(f"Message: {message}")
            logger.info(f"Recipients: {self.email_recipients}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def send_daily_summary(self, summary_data: Dict[str, Any]):
        """Send a daily summary of all processed filings."""
        try:
            logger.info("Sending daily summary notification")
            
            message = self._create_daily_summary_message(summary_data)
            
            if self.github_issue_enabled:
                self._create_daily_summary_issue(summary_data, message)
            
            if self.slack_webhook:
                self._send_slack_notification(message)
                
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def _create_daily_summary_message(self, summary_data: Dict[str, Any]) -> str:
        """Create a daily summary message."""
        try:
            total_filings = summary_data.get('total_filings', 0)
            total_funds = summary_data.get('total_funds', 0)
            funds_processed = summary_data.get('funds_processed', [])
            
            message = f"""📈 **13F Parser Daily Summary - {datetime.now().strftime('%Y-%m-%d')}**

**Overview:**
- **Total Filings Processed:** {total_filings}
- **Funds Monitored:** {total_funds}

**Funds with New Filings:**
"""
            
            if funds_processed:
                for fund in funds_processed:
                    fund_name = fund.get('fund_name', 'Unknown')
                    filings_count = fund.get('filings_count', 0)
                    message += f"- **{fund_name}**: {filings_count} new filing(s)\n"
            else:
                message += "- No new filings today\n"
            
            message += f"\n**Generated:** {datetime.now().isoformat()}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating daily summary message: {e}")
            return f"Error creating daily summary: {e}"
    
    def _create_daily_summary_issue(self, summary_data: Dict[str, Any], message: str):
        """Create a GitHub issue for the daily summary."""
        try:
            if not self.github_token or not self.github_repo:
                return
            
            owner, repo = self.github_repo.split('/')
            
            title = f"📈 13F Parser Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = message + f"""

<details>
<summary>📊 Detailed Summary Data</summary>

```json
{json.dumps(summary_data, indent=2)}
```

</details>
"""
            
            issue_data = {
                'title': title,
                'body': body,
                'labels': ['daily-summary', '13f-parser', 'automated']
            }
            
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.post(url, headers=headers, json=issue_data)
            response.raise_for_status()
            
            issue = response.json()
            logger.info(f"Created daily summary issue: {issue['html_url']}")
            
        except Exception as e:
            logger.error(f"Error creating daily summary issue: {e}")
    
    def test_notifications(self):
        """Test all notification channels."""
        try:
            logger.info("Testing notification channels")
            
            test_message = f"""🧪 **13F Parser Notification Test**

This is a test message to verify that all notification channels are working correctly.

**Test Time:** {datetime.now().isoformat()}
**Status:** ✅ All systems operational

If you receive this message, your notification setup is working properly!
"""
            
            if self.github_issue_enabled:
                self._create_github_issue("Test", {}, {}, test_message, is_error=False)
            
            if self.slack_webhook:
                self._send_slack_notification(test_message)
            
            if self.email_enabled:
                self._send_email_notification(test_message)
            
            logger.info("Notification test completed")
            
        except Exception as e:
            logger.error(f"Error testing notifications: {e}")
