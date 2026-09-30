import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_auto_assign = '''        if available_ip:
            available_ip.status = 'used'
            available_ip.hostname = req.hostname
            available_ip.assigned_to = req.user
            available_ip.save()
            
            req.assigned_ip = available_ip
            req.status = 'approved'
            req.admin_comment = "Auto-assigned by system."
            req.save()'''

new_auto_assign = '''        if available_ip:
            from .models import SystemSettings
            from django.utils import timezone
            settings = SystemSettings.load()
            if settings.enable_reservation:
                available_ip.status = 'reserved'
                available_ip.reserved_at = timezone.now()
                available_ip.discovery_reason = f"Auto-reserved via IP Request for {req.user.username}"
            else:
                available_ip.status = 'used'
                available_ip.discovery_reason = f"Auto-assigned via IP Request for {req.user.username}"
            available_ip.hostname = req.hostname
            available_ip.assigned_to = req.user
            available_ip.save()
            
            req.assigned_ip = available_ip
            req.status = 'approved'
            req.admin_comment = "Auto-assigned by system."
            req.save()'''

content = content.replace(old_auto_assign, new_auto_assign)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
