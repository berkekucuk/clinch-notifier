"""Apple Push Notification service (APNs) handling."""
import os
import time
import asyncio
import httpx
import jwt
from .utils import mask_token

def get_apns_jwt(private_key, key_id, team_id):
    """Generate a JWT token for APNs authentication."""
    # Ensure newlines are correctly formatted if they come from a single-line env var
    private_key = private_key.replace('\\n', '\n')

    headers = {
        'alg': 'ES256',
        'kid': key_id
    }
    
    payload = {
        'iss': team_id,
        'iat': int(time.time())
    }
    
    try:
        token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
        return token
    except Exception as e:
        print(f"⚠️ Failed to generate JWT token: {e}")
        return None

def build_apns_payload(title, body, data):
    """Construct the JSON payload for APNs."""
    apns_payload = {
        "aps": {
            "alert": {
                "title": title,
                "body": body
            },
            "sound": "default"
        }
    }
    
    if data:
        apns_payload.update(data)
        
    return apns_payload

def get_apns_headers(topic, jwt_token):
    """Construct the HTTP headers for APNs request."""
    return {
        "apns-topic": topic,
        "apns-push-type": "alert",
        "authorization": f"bearer {jwt_token}"
    }

def get_apns_base_url():
    """Determine the APNs base URL based on environment."""
    use_sandbox = os.getenv("APNS_USE_SANDBOX", "false").lower() == "true"
    return "https://api.sandbox.push.apple.com" if use_sandbox else "https://api.push.apple.com"

async def send_single_apns(client, token, base_url, headers, apns_payload):
    """Send a single APNs request asynchronously."""
    url = f"{base_url}/3/device/{token}"
    try:
        response = await client.post(url, headers=headers, json=apns_payload)
        if response.status_code == 200:
            return True, token, None
        else:
            masked = mask_token(token)
            # 400 BadDeviceToken or 410 Unregistered
            is_invalid = response.status_code in [400, 410]
            return False, token, {"error": f"APN Token: {masked} failed | Status: {response.status_code} | Reason: {response.text}", "is_invalid": is_invalid}
    except Exception as e:
        masked = mask_token(token)
        return False, token, {"error": f"APN Token: {masked} exception | Reason: {e}", "is_invalid": False}

async def send_apns_notification_async(tokens, title, body, data):
    """Perform parallel APNs delivery using httpx.AsyncClient."""
    # Load credentials
    private_key = os.getenv("APNS_PRIVATE_KEY")
    key_id = os.getenv("APNS_KEY_ID")
    team_id = os.getenv("APNS_TEAM_ID")
    topic = os.getenv("APNS_TOPIC")

    if not all([private_key, key_id, team_id, topic]):
        print("⚠️ APNs credentials missing in environment variables. Skipping APN delivery.")
        return []

    # Generate JWT
    jwt_token = get_apns_jwt(private_key, key_id, team_id)
    if not jwt_token:
        return []

    # Build Request parameters
    apns_payload = build_apns_payload(title, body, data)
    headers = get_apns_headers(topic, jwt_token)
    base_url = get_apns_base_url()

    try:
        invalid_tokens = []
        async with httpx.AsyncClient(http2=True) as client:
            tasks = [
                send_single_apns(client, token, base_url, headers, apns_payload)
                for token in tokens
            ]
            results = await asyncio.gather(*tasks)

        total_sent = 0
        for success, token, err_info in results:
            if success:
                total_sent += 1
            else:
                print(f"   ⚠️ {err_info['error']}")
                if err_info.get('is_invalid'):
                    invalid_tokens.append(token)

        total_failed = len(tokens) - total_sent

        print(f"🏁 Total Successful APN Deliveries: {total_sent} / {len(tokens)}")
        if total_failed > 0:
            print(f"   ❌ Failed APN Deliveries: {total_failed}")
            
        return invalid_tokens

    except Exception as e:
        print(f"❌ Critical error in APN delivery: {e}")
        return []

def send_apns_notification(tokens, title, body, data):
    """Send APNs notification to multiple iOS devices using HTTP/2 in parallel."""
    if not tokens:
        print("ℹ️ No APN tokens to send.")
        return []

    return asyncio.run(send_apns_notification_async(tokens, title, body, data))

