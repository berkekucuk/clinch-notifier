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


def get_webhook_secret():
    """Get the webhook security token from environment variables."""
    return os.environ.get('WEBHOOK_SECRET')


def verify_webhook_secret(headers, expected_token):
    """Verify webhook authenticity using secret token."""
    incoming_token = headers.get('x-webhook-secret') or headers.get('X-Webhook-Secret')

    if not expected_token or incoming_token != expected_token:
        print("Unauthorized Access!")
        return False

    return True