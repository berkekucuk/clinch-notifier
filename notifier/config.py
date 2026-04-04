"""Firebase Admin SDK initialization and configuration."""
import json
import os
import firebase_admin
from firebase_admin import credentials


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    if not firebase_admin._apps:
        try:
            cred_json = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"❌ Firebase Initialization Error: {e}")


def get_supabase_config():
    """Get Supabase configuration from environment variables."""
    return {
        "url": os.environ.get('SUPABASE_URL'),
        "service_key": os.environ.get('SUPABASE_SERVICE_ROLE_KEY'),
    }


def get_supabase_headers(service_key):
    """Build HTTP headers for Supabase API requests."""
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }


def get_webhook_secret():
    """Get the webhook security token from environment variables."""
    return os.environ.get('WEBHOOK_SECRET')
