"""Event handlers for fight notifications."""
import time
from .firebase_service import send_fcm_notification
from .apns_service import send_apns_notification


def handle_fight_result(db_manager, fight_data):
    """
    Scenario 1: Send notification for the result of the finished fight.
    (Disabled for Android, sending to iOS only)
    """
    fight_id = fight_data.get('fight_id')
    current_tokens = db_manager.get_tokens_for_fight(fight_id)

    if current_tokens.get('ios'):
        f1_name, f2_name, result = db_manager.get_fight_result_details(fight_id)

        # RETRY LOGIC: If result_type is not found, it might be due to a race condition with the scraper.
        # We wait for 2 seconds and try one more time.
        if not result:
            print(f"⚠️ Result data not ready for fight {fight_id}. Retrying in 2 seconds...")
            time.sleep(2)
            f1_name, f2_name, result = db_manager.get_fight_result_details(fight_id)

        method_type = fight_data.get('method_type', '')
        method_detail = fight_data.get('method_detail', '')
        method_str = f"{method_type} - {method_detail}" if method_detail else method_type

        # Customize title/body based on result type
        if result == "DRAW":
            title = f"Draw: {f1_name} vs {f2_name}"
            message = f"Result: {method_str}"
        elif result == "NC":
            title = f"No Contest: {f1_name} vs {f2_name}"
            message = f"Result: {method_str}"
        elif result == "WIN":
            title = f"{f1_name} defeated {f2_name}"
            message = f"by {method_str}"
        else:
            title = "Fight Concluded!"
            message = f"Method: {method_str}"
            
        send_apns_notification(
            tokens=current_tokens['ios'],
            title=title,
            body=message,
            data={"fight_id": fight_id, "type": "RESULT"}
        )


def handle_next_fight_starting(db_manager, fight_data):
    """
    Scenario 2: Send notification when the next fight is starting with fighter names.
    """
    event_id = fight_data.get('event_id')
    current_order = fight_data.get('fight_order')

    if current_order is not None and event_id:
        next_fight_id = db_manager.get_fight_id_by_order(event_id, current_order + 1)

        if next_fight_id:
            next_tokens = db_manager.get_tokens_for_fight(next_fight_id)
            if next_tokens.get('android_standard') or next_tokens.get('android_alarm') or next_tokens.get('ios'):
                matchup = db_manager.get_fight_matchup_names(next_fight_id)

                if next_tokens.get('android_standard'):
                    send_fcm_notification(
                        tokens=next_tokens['android_standard'],
                        title="Next Fight Starting! 🔥",
                        body=f"{matchup}",
                        data={"fight_id": next_fight_id, "type": "START"}
                    )
                    
                if next_tokens.get('android_alarm'):
                    send_fcm_notification(
                        tokens=next_tokens['android_alarm'],
                        data={"fight_id": next_fight_id, "type": "ALARM", "matchup": matchup},
                        is_alarm=True
                    )
                    
                if next_tokens.get('ios'):
                    send_apns_notification(
                        tokens=next_tokens['ios'],
                        title="Next Fight Starting! 🔥",
                        body=f"{matchup}",
                        data={"fight_id": next_fight_id, "type": "START"}
                    )


def handle_manual_notification(db_manager, payload):
    """
    Scenario 3: Send manual notification to all users or specific users.
    """
    title = payload.get('title')
    body = payload.get('body')
    data = payload.get('data', {})

    if not title or not body:
        print("⚠️ Title or body missing in manual notification request. Skipping.")
        return

    target = payload.get('target', 'all')
    
    if target == 'users':
        user_ids = payload.get('user_ids', [])
        tokens = db_manager.get_device_tokens_for_users(user_ids)
    else:
        tokens = db_manager.get_all_device_tokens()

    android_tokens = tokens.get('android', [])
    ios_tokens = tokens.get('ios', [])

    if not android_tokens and not ios_tokens:
        print("ℹ️ No target tokens found for manual notification.")
        return

    # Set dynamic notification type in payload data if not present
    if 'type' not in data:
        data['type'] = 'MANUAL'

    invalid_tokens = []
    
    if android_tokens:
        fcm_invalid = send_fcm_notification(
            tokens=android_tokens,
            title=title,
            body=body,
            data=data
        )
        if fcm_invalid:
            invalid_tokens.extend(fcm_invalid)

    if ios_tokens:
        apns_invalid = send_apns_notification(
            tokens=ios_tokens,
            title=title,
            body=body,
            data=data
        )
        if apns_invalid:
            invalid_tokens.extend(apns_invalid)

    if invalid_tokens:
        db_manager.remove_invalid_tokens(invalid_tokens)

def handle_event_went_live(db_manager, event_id):
    """
    Scenario 4: Send notification when the event goes live for the first fight.
    """
    first_fight_id = db_manager.get_fight_id_by_order(event_id, 1)

    if first_fight_id:
        first_tokens = db_manager.get_tokens_for_fight(first_fight_id)
        if first_tokens.get('android_standard') or first_tokens.get('android_alarm') or first_tokens.get('ios'):
            matchup = db_manager.get_fight_matchup_names(first_fight_id)

            if first_tokens.get('android_standard'):
                send_fcm_notification(
                    tokens=first_tokens['android_standard'],
                    title="Fight starting 🔥",
                    body=f"{matchup}",
                    data={"fight_id": first_fight_id, "type": "START"}
                )
                
            if first_tokens.get('android_alarm'):
                send_fcm_notification(
                    tokens=first_tokens['android_alarm'],
                    data={"fight_id": first_fight_id, "type": "ALARM", "matchup": matchup},
                    is_alarm=True
                )
                
            if first_tokens.get('ios'):
                send_apns_notification(
                    tokens=first_tokens['ios'],
                    title="Fight starting 🔥",
                    body=f"{matchup}",
                    data={"fight_id": first_fight_id, "type": "START"}
                )