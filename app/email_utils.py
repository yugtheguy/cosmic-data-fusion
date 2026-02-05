import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from pathlib import Path

# Load environment variables
load_dotenv()

# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@cosmicdatafusion.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_welcome_email(email: EmailStr, full_name: str):
    """
    Send a welcome email to a new user.
    
    Args:
        email: User's email address
        full_name: User's full name
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                color: #333;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2c3e50;
                margin: 0;
            }}
            .content {{
                line-height: 1.6;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                font-size: 12px;
                color: #888;
            }}
            .btn {{
                display: inline-block;
                background-color: #3498db;
                color: #ffffff;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to COSMIC Data Fusion!</h1>
            </div>
            <div class="content">
                <p>Hello <strong>{full_name}</strong>,</p>
                <p>We are thrilled to have you on board! Your account has been successfully created.</p>
                <p>COSMIC Data Fusion is your gateway to standardizing and querying astronomical data. We can't wait to see what you discover.</p>
                <p>If you have any questions or need assistance, feel free to reply to this email.</p>
                <br>
                <p>Clear Skies,<br>The COSMIC Data Fusion Team</p>
                <!-- <a href="#" class="btn">Get Started</a> -->
            </div>
            <div class="footer">
                <p>&copy; 2024 COSMIC Data Fusion. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Welcome to COSMIC Data Fusion!",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_verification_email(email: EmailStr, token: str):
    """
    Send a verification email with a link to activate the account.
    
    Args:
        email: User's email address
        token: Verification token
    """
    # In production, this should be an environment variable
    # Pointing to frontend URL (Vite default port 5173)
    base_url = "http://localhost:5173" 
    verification_link = f"{base_url}/verify-email?token={token}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ color: #2c3e50; margin: 0; }}
            .content {{ line-height: 1.6; text-align: center; }}
            .btn {{ display: inline-block; background-color: #27ae60; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 20px; margin-bottom: 20px; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Verify Your Email</h1>
            </div>
            <div class="content">
                <p>Welcome to COSMIC Data Fusion! Please click the button below to verify your email address and activate your account.</p>
                <a href="{verification_link}" class="btn">Verify Email</a>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p><small>{verification_link}</small></p>
            </div>
            <div class="footer">
                <p>&copy; 2024 COSMIC Data Fusion. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject="Verify your COSMIC Data Fusion account",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
