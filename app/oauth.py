"""
OAuth configuration and utilities for Google OAuth 2.0 authentication.
"""
import os
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

load_dotenv()

# OAuth configuration
oauth = OAuth()

# Register Google OAuth provider
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
