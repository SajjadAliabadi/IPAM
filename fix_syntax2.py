import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = '''        try:
            from .alerts import send_telegram_alert
            send_telegram_alert(f"?? *New IP Request*

User {obj.user.username if obj.user else 'System'} requested an IP for hostname {obj.hostname}.")
        except: pass'''

good_block = '''        try:
            from .alerts import send_telegram_alert
            msg = f"New IP Request: User {obj.user.username if obj.user else 'System'} requested an IP for hostname {obj.hostname}."
            send_telegram_alert(msg)
        except: pass'''

content = content.replace(bad_block, good_block)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
