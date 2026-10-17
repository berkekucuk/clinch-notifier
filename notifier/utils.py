"""Utility functions for the notifier module."""

def mask_token(token):
    """Return a partially masked token for logging."""
    if not token:
        return "<empty-token>"

    if len(token) <= 10:
        return f"{token[:2]}***{token[-2:]}"

    return f"{token[:6]}***{token[-4:]}"


def is_apns_token(token):
    """Return True if the token is a raw APNs device token (hex string) rather than an FCM token."""
    if not token:
        return False

    return all(c in "0123456789abcdefABCDEF" for c in token)
