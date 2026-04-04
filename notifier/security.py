"""Security utilities for webhook authentication and validation."""


def verify_webhook_secret(headers, expected_token):
    """Verify webhook authenticity using secret token."""
    incoming_token = headers.get('x-webhook-secret') or headers.get('X-Webhook-Secret')

    if not expected_token or incoming_token != expected_token:
        print("🚨 SECURITY ALERT: Unauthorized Access Attempt!")
        return False

    return True
