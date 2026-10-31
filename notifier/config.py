"""Firebase Admin SDK initialization and configuration."""
import json
import logging
import os
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)


def initialize_firebase():
    """Initialize Firebase Admin SDK, failing fast if its configuration is unusable."""
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    raw_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '').strip()
    if not raw_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT environment variable is empty")

    try:
        cred_json = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT is not valid JSON") from e

    logger.debug("Lambda Project ID: %s", cred_json.get('project_id'))

    firebase_admin.initialize_app(credentials.Certificate(cred_json))
    logger.info("✅ Firebase Admin SDK successfully initialized.")


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
        logger.warning("Unauthorized Access!")
        return False

    return True