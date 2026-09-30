import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad1 = '''                from .alerts import send_telegram_alert
                send_telegram_alert(f"?? *Subnet Almost Full*

Subnet {subnet.network_address} is {int(used/total*100)}% full ({used}/{total} used).")'''

good1 = '''                from .alerts import send_telegram_alert
                msg = f"Subnet Almost Full: {subnet.network_address} is {int(used/total*100)}% full ({used}/{total} used)."
                send_telegram_alert(msg)'''
content = content.replace(bad1, good1)

bad2 = '''                    from .alerts import send_telegram_alert
                    send_telegram_alert(f"?? *Critical IP Offline*

Manually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline.")'''

good2 = '''                    from .alerts import send_telegram_alert
                    msg = f"Critical IP Offline: Manually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline."
                    send_telegram_alert(msg)'''

content = content.replace(bad2, good2)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
