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

# Hook up login failed signal
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from django.core.cache import cache

@receiver(user_login_failed)
def login_failed_alert(sender, credentials, request, **kwargs):
    settings = SystemSettings.load()
    if not settings.alert_on_failed_login:
        return
    username = credentials.get('username', 'Unknown')
    ip = request.META.get('REMOTE_ADDR', 'Unknown')
    if request.META.get('HTTP_X_FORWARDED_FOR'):
        ip = request.META.get('HTTP_X_FORWARDED_FOR').split(',')[0]
        
    cache_key = f"failed_login_{username}_{ip}"
    count = cache.get(cache_key, 0) + 1
    cache.set(cache_key, count, 300) # Keep count for 5 minutes
    
    if count >= 3:
        send_alert(f"🚨 *Security Alert*\nMultiple failed login attempts ({count}) for user {username} from IP {ip}.")
        cache.set(cache_key, 0, 300) # Reset after alerting
