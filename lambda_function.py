import json
from notifier.config import initialize_firebase, get_supabase_config, get_supabase_headers, get_webhook_secret
from notifier.security import verify_webhook_secret
from notifier.handlers import handle_fight_result, handle_next_fight_starting

# Firebase Admin SDK initialization (performed once globally)
initialize_firebase()

def lambda_handler(event, context):
    print(">>> MMA NOTIFICATION ENGINE AWOKE <<<")

    # --- 1. SECURITY CHECK (Webhook Secret) ---
    headers = event.get('headers', {})
    expected_token = get_webhook_secret()

    if not verify_webhook_secret(headers, expected_token):
        return {"statusCode": 403, "body": "Unauthorized"}

    # Environment variables
    config = get_supabase_config()
    SUPABASE_URL = config['url']
    SERVICE_KEY = config['service_key']
    HEADERS = get_supabase_headers(SERVICE_KEY)

    try:
        # Process the payload coming from Supabase
        body = json.loads(event.get('body', '{}'))
        new_fight = body.get('record', {})

        fight_id = new_fight.get('fight_id')

        if not fight_id:
            return {"statusCode": 200, "body": "No fight_id found in record."}

        # ==========================================================
        # SCENARIO 1: SEND THE RESULT OF THE FINISHED FIGHT
        # ==========================================================
        handle_fight_result(SUPABASE_URL, HEADERS, new_fight)

        # ==========================================================
        # SCENARIO 2: THE NEXT FIGHT IS STARTING (With fighter names!)
        # ==========================================================
        handle_next_fight_starting(SUPABASE_URL, HEADERS, new_fight)

        return {"statusCode": 200, "body": "Success"}

    except Exception as e:
        print(f"💥 GLOBAL ERROR: {str(e)}")
        return {"statusCode": 500, "body": "Internal Server Error"}
