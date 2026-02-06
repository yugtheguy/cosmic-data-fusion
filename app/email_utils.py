"""
Email utilities for sending notifications and alerts.

Uses SMTP to send emails for:
- Account verification
- Password reset
- Anomaly alerts
- System notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Email configuration from environment
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_FROM = os.getenv('MAIL_FROM', MAIL_USERNAME)
MAIL_PORT = int(os.getenv('MAIL_PORT', '465'))
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')


def send_email(
    to: str | List[str],
    subject: str,
    body: str,
    html: Optional[str] = None
) -> bool:
    """
    Send an email via SMTP.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject line
        body: Plain text email body
        html: Optional HTML version of email body
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not all([MAIL_USERNAME, MAIL_PASSWORD, MAIL_SERVER]):
        logger.error("Email configuration missing")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = MAIL_FROM
        msg['To'] = to if isinstance(to, str) else ', '.join(to)
        
        # Attach text and HTML parts
        msg.attach(MIMEText(body, 'plain'))
        if html:
            msg.attach(MIMEText(html, 'html'))
        
        # Send email
        with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            recipients = [to] if isinstance(to, str) else to
            server.sendmail(MAIL_FROM, recipients, msg.as_string())
        
        logger.info(f"Email sent successfully to {to}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def send_verification_email(email: str, token: str) -> bool:
    """
    Send account verification email.
    
    Args:
        email: Recipient email address
        token: Verification token
        
    Returns:
        True if sent successfully
    """
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    verify_url = f"{frontend_url}/verify?token={token}"
    
    subject = "Verify Your COSMIC Account"
    body = f"""
Welcome to COSMIC Data Fusion!

Please verify your email address by clicking the link below:

{verify_url}

This link will expire in 24 hours.

If you didn't create an account, please ignore this email.

Best regards,
The COSMIC Team
"""
    
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #e8a87c;">Welcome to COSMIC Data Fusion!</h2>
        <p>Please verify your email address to complete your registration.</p>
        <p style="margin: 30px 0;">
            <a href="{verify_url}" 
               style="background-color: #e8a87c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Verify Email Address
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">
            This link will expire in 24 hours.
        </p>
        <p style="color: #666; font-size: 14px;">
            If you didn't create an account, please ignore this email.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            Best regards,<br>
            The COSMIC Team
        </p>
    </div>
</body>
</html>
"""
    
    return send_email(email, subject, body, html)


def send_password_reset_email(email: str, token: str) -> bool:
    """
    Send password reset email.
    
    Args:
        email: Recipient email address
        token: Password reset token
        
    Returns:
        True if sent successfully
    """
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    subject = "Reset Your COSMIC Password"
    body = f"""
A password reset was requested for your COSMIC account.

Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email and your password will remain unchanged.

Best regards,
The COSMIC Team
"""
    
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #e8a87c;">Reset Your Password</h2>
        <p>A password reset was requested for your COSMIC account.</p>
        <p style="margin: 30px 0;">
            <a href="{reset_url}" 
               style="background-color: #e8a87c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                Reset Password
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">
            This link will expire in 1 hour.
        </p>
        <p style="color: #666; font-size: 14px;">
            If you didn't request a password reset, please ignore this email and your password will remain unchanged.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            Best regards,<br>
            The COSMIC Team
        </p>
    </div>
</body>
</html>
"""
    
    return send_email(email, subject, body, html)


def send_anomaly_alert(email: str, anomaly_count: int, anomaly_details: str) -> bool:
    """
    Send anomaly detection alert email.
    
    Args:
        email: Recipient email address
        anomaly_count: Number of anomalies detected
        anomaly_details: Details about the anomalies
        
    Returns:
        True if sent successfully
    """
    subject = f"COSMIC Alert: {anomaly_count} Anomalies Detected"
    body = f"""
COSMIC has detected {anomaly_count} new anomalies in your data.

{anomaly_details}

Login to your dashboard to investigate:
{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/dashboard

Best regards,
The COSMIC Team
"""
    
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #ef4444;">🚨 Anomalies Detected</h2>
        <p>COSMIC has detected <strong>{anomaly_count}</strong> new anomalies in your data.</p>
        <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #e8a87c; margin: 20px 0;">
            <pre style="margin: 0; font-size: 14px;">{anomaly_details}</pre>
        </div>
        <p style="margin: 30px 0;">
            <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/dashboard" 
               style="background-color: #e8a87c; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                View Dashboard
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            Best regards,<br>
            The COSMIC Team
        </p>
    </div>
</body>
</html>
"""
    
    return send_email(email, subject, body, html)
