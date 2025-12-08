"""
Email Service - Send OTP verification emails

Supports multiple email providers:
- SMTP (Gmail, Outlook, etc.)
- SendGrid (future)
- AWS SES (future)
"""

import os
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional

from celery import shared_task
from app.core.logger import logger


class EmailService:
    """
    Email service for sending OTP verification emails
    """
    
    def __init__(self):
        # Load email config from environment variables
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")  # Your email
        self.smtp_password = os.getenv("SMTP_PASSWORD")  # App password
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "NLPForge")
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def send_verification_email(self, to_email: str, otp: str, username: str = "User") -> bool:
        """
        Send OTP verification email
        
        Args:
            to_email: Recipient email address
            otp: 6-digit OTP
            username: User's name (for personalization)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("⚠️ Email service not configured (SMTP_USER/SMTP_PASSWORD missing)")
                logger.info(f"📧 [DEV MODE] OTP for {to_email}: {otp}")
                return True  # Return True in dev mode for testing
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Verify your NLPForge account - OTP: {otp}"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Create HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f4f4f5;">
                <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f4f4f5;">
                    <tr>
                        <td align="center" style="padding: 40px 20px;">
                            <table role="presentation" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                <!-- Header -->
                                <tr>
                                    <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px 12px 0 0;">
                                        <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                                            ✨ NLPForge
                                        </h1>
                                        <p style="margin: 10px 0 0; color: #e0e0ff; font-size: 14px;">
                                            AI-Powered API Testing Platform
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- Content -->
                                <tr>
                                    <td style="padding: 40px;">
                                        <h2 style="margin: 0 0 20px; color: #18181b; font-size: 24px; font-weight: 600;">
                                            Verify Your Email Address
                                        </h2>
                                        
                                        <p style="margin: 0 0 20px; color: #3f3f46; font-size: 16px; line-height: 1.6;">
                                            Hi <strong>{username}</strong>,
                                        </p>
                                        
                                        <p style="margin: 0 0 30px; color: #3f3f46; font-size: 16px; line-height: 1.6;">
                                            Welcome to NLPForge! To complete your registration and start using our platform, please verify your email address by entering the following One-Time Password (OTP):
                                        </p>
                                        
                                        <!-- OTP Box -->
                                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 30px; text-align: center; margin: 0 0 30px;">
                                            <p style="margin: 0 0 10px; color: #e0e0ff; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 1px;">
                                                Your OTP Code
                                            </p>
                                            <p style="margin: 0; color: #ffffff; font-size: 48px; font-weight: 700; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                                {otp}
                                            </p>
                                        </div>
                                        
                                        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 8px; margin: 0 0 30px;">
                                            <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                                                ⚠️ <strong>Important:</strong> This OTP will expire in <strong>10 minutes</strong>. Do not share this code with anyone.
                                            </p>
                                        </div>
                                        
                                        <p style="margin: 0 0 20px; color: #3f3f46; font-size: 16px; line-height: 1.6;">
                                            If you didn't create an account with NLPForge, please ignore this email or contact our support team.
                                        </p>
                                        
                                        <div style="border-top: 1px solid #e4e4e7; padding-top: 20px; margin-top: 30px;">
                                            <p style="margin: 0 0 10px; color: #71717a; font-size: 14px;">
                                                Best regards,<br>
                                                <strong>The NLPForge Team</strong>
                                            </p>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 12px 12px; text-align: center;">
                                        <p style="margin: 0 0 10px; color: #71717a; font-size: 12px;">
                                            This is an automated message from NLPForge. Please do not reply to this email.
                                        </p>
                                        <p style="margin: 0; color: #a1a1aa; font-size: 12px;">
                                            © 2025 NLPForge. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            # Plain text fallback
            text_content = f"""
            NLPForge - Verify Your Email Address
            
            Hi {username},
            
            Welcome to NLPForge! To complete your registration, please use the following OTP:
            
            OTP: {otp}
            
            This code will expire in 10 minutes. Do not share it with anyone.
            
            If you didn't create an account, please ignore this email.
            
            Best regards,
            The NLPForge Team
            """
            
            # Attach both HTML and plain text versions
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"✅ Verification email sent to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send verification email to {to_email}: {e}")
            # In development, log OTP for testing
            logger.info(f"📧 [DEV MODE] OTP for {to_email}: {otp}")
            return False
    
    def send_resend_otp_email(self, to_email: str, otp: str, username: str = "User") -> bool:
        """
        Send resend OTP email
        
        Similar to verification email but with different subject/text
        """
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("⚠️ Email service not configured")
                logger.info(f"📧 [DEV MODE] Resend OTP for {to_email}: {otp}")
                return True
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Your new NLPForge verification code: {otp}"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Simplified HTML for resend
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #667eea;">NLPForge - New Verification Code</h2>
                    <p>Hi {username},</p>
                    <p>You requested a new verification code. Here it is:</p>
                    <div style="background: #667eea; color: white; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; border-radius: 8px; margin: 20px 0;">
                        {otp}
                    </div>
                    <p style="color: #f59e0b;"><strong>⚠️ This code expires in 10 minutes.</strong></p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>Best regards,<br>The NLPForge Team</p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"Your new NLPForge verification code: {otp}\n\nThis code expires in 10 minutes."
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"✅ Resend OTP email sent to {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send resend OTP email: {e}")
            logger.info(f"📧 [DEV MODE] Resend OTP for {to_email}: {otp}")
            return False


# Singleton instance
_email_service = None


def get_email_service() -> EmailService:
    """Get or create singleton instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


@shared_task(name="app.services.email_service.send_email_async")
def send_email_async(to_email: str, otp: str, username: str = "User", email_type: str = "verification"):
    """
    Async task to send email
    
    Args:
        to_email: Recipient email
        otp: One-time password
        username: User's name
        email_type: Type of email ('verification' or 'resend')
    
    Returns:
        dict: Email send result
    """
    try:
        logger.info(f"Sending {email_type} email to {to_email}")
        
        email_service = get_email_service()
        
        if email_type == "resend":
            success = email_service.send_resend_otp_email(to_email, otp, username)
        else:
            success = email_service.send_verification_email(to_email, otp, username)
        
        if success:
            logger.info(f"✅ Email sent successfully to {to_email}")
            return {"status": "sent", "email": to_email}
        else:
            logger.warning(f"⚠️ Email send returned false for {to_email}")
            return {"status": "warning", "email": to_email, "message": "Email service returned false"}
            
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}", exc_info=True)
        return {"status": "failed", "email": to_email, "error": str(e)}
