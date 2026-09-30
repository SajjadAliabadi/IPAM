import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'send_telegram_alert\(f\"\?\? \*New IP Request\*\n\nUser \{obj\.user\.username if obj\.user else \'System\'\} requested an IP for hostname \{obj\.hostname\}\.\"\)', 'send_telegram_alert(f"New IP Request: User {obj.user.username if obj.user else \'System\'} requested an IP for hostname {obj.hostname}.")', content, flags=re.MULTILINE)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
