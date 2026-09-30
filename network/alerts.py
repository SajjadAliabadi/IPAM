import requests
from .models import SystemSettings

def send_telegram_alert(message):
    settings = SystemSettings.load()
    if settings.telegram_bot_token and settings.telegram_chat_id:
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
