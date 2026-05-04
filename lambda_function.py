import json
from notifier.config import initialize_firebase, get_supabase_config, get_webhook_secret, verify_webhook_secret
from notifier.handlers import handle_fight_result, handle_next_fight_starting
from notifier.supabase_manager import SupabaseManager

# Firebase Admin SDK initialization (performed once globally)
initialize_firebase()

# Environment variables & Supabase manager initialization (performed once globally)
config = get_supabase_config()
db_manager = SupabaseManager(config['url'], config['service_key'])

def lambda_handler(event, context):
    print(">>> MMA NOTIFICATION ENGINE AWOKE <<<")

    # --- 1. SECURITY CHECK (Webhook Secret) ---
    headers = event.get('headers', {})
    expected_token = get_webhook_secret()

    if not verify_webhook_secret(headers, expected_token):
        return {"statusCode": 403, "body": "Unauthorized"}

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
        handle_fight_result(db_manager, new_fight)

        # ==========================================================
        # SCENARIO 2: THE NEXT FIGHT IS STARTING (With fighter names!)
        # ==========================================================
        handle_next_fight_starting(db_manager, new_fight)

        return {"statusCode": 200, "body": "Success"}

    except Exception as e:
        print(f"💥 GLOBAL ERROR: {str(e)}")
        return {"statusCode": 500, "body": "Internal Server Error"}
