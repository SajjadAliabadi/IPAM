import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace in perform_discovery
old_reserved_1 = "                elif ip_obj.status == 'reserved':\n                    pass"
new_reserved_1 = '''                elif ip_obj.status == 'reserved':
                    if ip_obj.reserved_at:
                        delta = timezone.now() - ip_obj.reserved_at
                        if delta.total_seconds() / 3600 >= settings.reservation_timeout_hours:
                            ip_obj.status = 'available'
                            ip_obj.reserved_at = None
                            ip_obj.assigned_to = None
                            ip_obj.hostname = ''
                            ip_obj.discovery_reason = "Reservation Expired (Auto-released)"
                            needs_save = True'''
content = content.replace(old_reserved_1, new_reserved_1)

# Replace in perform_ip_discovery
old_reserved_2 = "            elif old_status == 'reserved':\n                pass"
new_reserved_2 = '''            elif old_status == 'reserved':
                if ip_obj.reserved_at:
                    delta = timezone.now() - ip_obj.reserved_at
                    if delta.total_seconds() / 3600 >= settings.reservation_timeout_hours:
                        ip_obj.status = 'available'
                        ip_obj.reserved_at = None
                        ip_obj.assigned_to = None
                        ip_obj.hostname = ''
                        ip_obj.discovery_reason = "Reservation Expired (Auto-released)"'''
content = content.replace(old_reserved_2, new_reserved_2)

# Ensure reserved_at is cleared when going to 'used' in perform_discovery
content = content.replace("ip_obj.last_offline_at = None\n                ip_obj.discovery_reason = reason\n                ip_obj.status = 'used'\n                needs_save = True", "ip_obj.last_offline_at = None\n                ip_obj.discovery_reason = reason\n                ip_obj.status = 'used'\n                ip_obj.reserved_at = None\n                needs_save = True")

# Ensure reserved_at is cleared when going to 'used' in perform_ip_discovery
content = content.replace("ip_obj.last_offline_at = None\n            ip_obj.discovery_reason = reason\n            ip_obj.status = 'used'\n        else:", "ip_obj.last_offline_at = None\n            ip_obj.discovery_reason = reason\n            ip_obj.status = 'used'\n            ip_obj.reserved_at = None\n        else:")


with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
