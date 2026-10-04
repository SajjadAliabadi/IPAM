import requests
from .models import SystemSettings
import json

def send_alert(message):
    settings = SystemSettings.load()
    
    # 1. Telegram
    if settings.alert_telegram and settings.telegram_bot_token and settings.telegram_chat_id:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            'chat_id': settings.telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except:
            pass
            
    # 2. Mattermost
    if settings.alert_mattermost and settings.mattermost_webhook_url:
        try:
            payload = {'text': message}
            requests.post(settings.mattermost_webhook_url, json=payload, timeout=5)
        except:
            pass
            
    # 3. SMS Webhook
    if settings.alert_sms and settings.sms_webhook_url and settings.sms_payload_template:
        try:
            # Replace {message} with actual message in the JSON string
            payload_str = settings.sms_payload_template.replace('{message}', message.replace('"', '\\"'))
            payload = json.loads(payload_str)
            requests.post(settings.sms_webhook_url, json=payload, timeout=5)
        except:
            pass

def send_telegram_alert(message):
    # Keep backward compatibility if it's imported elsewhere
    send_alert(message)
