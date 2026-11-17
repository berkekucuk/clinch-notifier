"""Firebase Cloud Messaging (FCM) notification handling."""
import asyncio
import logging
from collections import Counter
from firebase_admin import exceptions, messaging
from .utils import mask_token

logger = logging.getLogger(__name__)

_loop = asyncio.new_event_loop()

def send_fcm_notification(tokens, title=None, body=None, data=None, is_alarm=False):
    """Send FCM notification to multiple devices with high priority settings."""
    if not tokens:
        logger.info("ℹ️ No FCM tokens to send.")
        return []

    data = data or {}
    context = f"type={data.get('type')} fight_id={data.get('fight_id')}"

    chunk_size = 500
    total_sent = 0
    total_failed = 0
    invalid_tokens = []

    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i + chunk_size]
        chunk_no = i // chunk_size + 1

        if is_alarm or (not title and not body):
            msg = messaging.MulticastMessage(
                tokens=chunk,
                data=data,
                android=messaging.AndroidConfig(priority='high')
            )
        else:
            msg = messaging.MulticastMessage(
                tokens=chunk,
                data=data,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(sound='default')
                ),
                apns=messaging.APNSConfig(
                    headers={'apns-priority': '10'},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default')
                    )
                )
            )

        try:
            response = _loop.run_until_complete(messaging.send_each_for_multicast_async(msg))
            total_sent += response.success_count
            total_failed += response.failure_count
            logger.info(
                "📦 FCM chunk %d (%s): %d successful, %d failed.",
                chunk_no, context, response.success_count, response.failure_count
            )

            if response.failure_count > 0:
                error_counts = Counter()
                error_samples = {}

                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_token = chunk[idx]
                        err = resp.exception
                        err_code = getattr(err, 'code', 'UNKNOWN_CODE')
                        error_counts[err_code] += 1
                        error_samples.setdefault(
                            err_code,
                            f"{mask_token(failed_token)}: {getattr(err, 'message', str(err))}"
                        )

                        if err_code in ['NOT_FOUND', 'UNREGISTERED']:
                            invalid_tokens.append(failed_token)

                for err_code, count in error_counts.items():
                    logger.warning(
                        "⚠️ FCM chunk %d (%s): %s x%d | Sample %s",
                        chunk_no, context, err_code, count, error_samples[err_code]
                    )

        except (exceptions.FirebaseError, ValueError):
            total_failed += len(chunk)
            logger.exception("❌ FCM chunk %d (%s) delivery failed for %d tokens", chunk_no, context, len(chunk))

    if total_failed > 0:
        logger.warning("🏁 FCM deliveries (%s): %d / %d successful, %d failed.", context, total_sent, len(tokens), total_failed)
    else:
        logger.info("🏁 FCM deliveries (%s): %d / %d successful.", context, total_sent, len(tokens))

    return invalid_tokens
