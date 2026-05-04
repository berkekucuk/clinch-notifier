"""Firebase Cloud Messaging (FCM) notification handling."""
from firebase_admin import messaging


def mask_token(token):
    """Return a partially masked token for logging."""
    if not token:
        return "<empty-token>"

    if len(token) <= 10:
        return f"{token[:2]}***{token[-2:]}"

    return f"{token[:6]}***{token[-4:]}"


def send_fcm_notification(tokens, title, body, image_url, data):
    """Send FCM notification to multiple devices with high priority settings."""
    if not tokens:
        print("ℹ️ No tokens to send.")
        return

    chunk_size = 500
    total_sent = 0

    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i + chunk_size]

        msg = messaging.MulticastMessage(
            tokens=chunk,
            data=data,
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image_url
            ),
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(sound='default')
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(aps=messaging.Aps(content_available=True, sound='default')),
                headers={'apns-priority': '10'}
            )
        )

        try:
            response = messaging.send_each_for_multicast(msg)
            total_sent += response.success_count
            print(f"📦 Chunk {i//chunk_size + 1}: {response.success_count} successful, {response.failure_count} failed.")

        except Exception as e:
            print(f"❌ Critical error in chunk delivery: {e}")

    print(f"🏁 Total Successful Deliveries: {total_sent} / {len(tokens)}")

