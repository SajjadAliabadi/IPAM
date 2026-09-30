import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any try/except block around send_telegram_alert inside save_model
content = re.sub(r'try:\s*from \.alerts import send_telegram_alert.*?except: pass', 'try:\n            from .alerts import send_telegram_alert\n            send_telegram_alert(f"New IP Request: User {obj.user.username if obj.user else \'System\'} requested an IP for hostname {obj.hostname}")\n        except: pass', content, flags=re.DOTALL)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content2 = f.read()
    
content2 = re.sub(r'from \.alerts import send_telegram_alert.*?used\)\."\)', 'from .alerts import send_telegram_alert\n                send_telegram_alert(f"Subnet Almost Full: {subnet.network_address} is {int(used/total*100)}% full.")', content2, flags=re.DOTALL)

content2 = re.sub(r'from \.alerts import send_telegram_alert.*?offline\."\)', 'from .alerts import send_telegram_alert\n                    send_telegram_alert(f"Critical IP Offline: Manually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline.")', content2, flags=re.DOTALL)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content2)

print('Done')
