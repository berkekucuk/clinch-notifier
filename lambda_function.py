import json
from notifier.config import initialize_firebase, get_supabase_config, get_webhook_secret, verify_webhook_secret
from notifier.handlers import (
    handle_fight_result, 
    handle_next_fight_starting, 
    handle_manual_notification,
    handle_event_went_live
)
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
        print("Webhook Payload:", json.dumps(body))
        
        action = body.get('action')
        table_name = body.get('table')
        record = body.get('record', {})

        # ==========================================================
        # SCENARIO 1: MANUAL NOTIFICATION (Specific Users or All)
        # ==========================================================
        if action == 'manual_notification':
            print("📣 Processing manual notification request...")
            handle_manual_notification(db_manager, body)
            return {"statusCode": 200, "body": "Manual notification processed"}

        # ==========================================================
        # SCENARIO 2: EVENT WENT LIVE (Trigger 1st Fight Alarm)
        # ==========================================================
        if table_name == 'events':
            event_id = record.get('event_id')
            status = record.get('status')
            
            if event_id and status == 'live':
                print(f"🔥 Event {event_id} went live! Triggering first fight alarm...")
                handle_event_went_live(db_manager, event_id)
                
            return {"statusCode": 200, "body": "Event update processed"}

        # ==========================================================
        # SCENARIO 3: FIGHT FINISHED (Send Result & Trigger Next Fight Alarm)
        # ==========================================================
        if table_name == 'fights':
            fight_id = record.get('fight_id')
            if not fight_id:
                return {"statusCode": 200, "body": "No fight_id found in record."}

            # A. Send the result of the finished fight silently as a standard notification
            handle_fight_result(db_manager, record)

            # B. Trigger the start alarm for the next fight (fight_order + 1)
            handle_next_fight_starting(db_manager, record)

            return {"statusCode": 200, "body": "Fight updates processed"}

        # ==========================================================
        # UNKNOWN SCENARIO
        # ==========================================================
        print(f"⚠️ Unknown payload received. Table: {table_name}, Action: {action}")
        return {"statusCode": 200, "body": "Payload ignored"}

    except Exception as e:
        print(f"💥 GLOBAL ERROR: {str(e)}")
        return {"statusCode": 500, "body": "Internal Server Error"}
