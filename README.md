# Clinch Notifier

Clinch Notifier is the push notification service for [Clinch](https://github.com/berkekucuk/clinch-app). It is a containerized AWS Lambda function that is triggered by Supabase webhooks or manual requests, finds the devices to notify, and sends the notifications through Firebase Cloud Messaging (FCM).

## How It Works

```text
Supabase webhook / manual request
        │  HTTP POST (x-webhook-secret header)
        ▼
AWS Lambda (lambda_function.py)
        │  1. Verify the secret
        │  2. Pick a scenario from the payload
        │  3. Load device tokens and fight data from Supabase
        ▼
Firebase Cloud Messaging ──► Android and iOS devices
```

## Notification Scenarios

The JSON body decides which scenario runs.

| Trigger | Who is notified |
| --- | --- |
| Manual request | All users, one platform, or specific users |
| Event goes live | Subscribers of the first fight |
| A fight finishes | Subscribers of the next fight |

## Delivery

Device tokens are loaded from Supabase, and payloads differ by platform:

| Recipient | Payload |
| --- | --- |
| Android, standard | Data only, high priority. The app builds the notification. |
| Android, alarm | Data only, high priority. The app triggers the alarm. |
| iOS | Visible notification with default sound. |
| Manual, all platforms | Visible notification with default sound. |

## Deployment

Each push to `main` builds the Docker image and deploys it to AWS Lambda through GitHub Actions.

## Tech Stack

- Python 3.12
- Firebase Cloud Messaging (FCM)
- Supabase
- AWS Lambda
- Docker
- GitHub Actions