import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "send_telegram_alert(f\"Critical IP Offline: Manually" in line:
        new_lines.append("                    send_telegram_alert(f\"Critical IP Offline: Manually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline.\")\n")
    elif "send_telegram_alert(f\"Subnet Almost Full:" in line:
        new_lines.append("                send_telegram_alert(f\"Subnet Almost Full: {subnet.network_address} is {int(used/total*100)}% full ({used}/{total} used).\")\n")
    else:
        new_lines.append(line)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done')
