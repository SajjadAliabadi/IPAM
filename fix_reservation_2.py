import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix IPRequestAdmin auto_assign_api
pattern = r"if available_ip:\s*available_ip\.status = 'used'\s*available_ip\.hostname = req\.hostname\s*available_ip\.is_unique_hostname = True\s*available_ip\.assigned_to = req\.user\s*available_ip\.save\(\)"

replacement = '''if available_ip:
            from django.utils import timezone
            from .models import SystemSettings
            settings = SystemSettings.load()
            if settings.enable_reservation:
                available_ip.status = 'reserved'
                available_ip.reserved_at = timezone.now()
                available_ip.discovery_reason = f"Reserved via Auto-Assign for {req.user.username if req.user else 'System'}"
            else:
                available_ip.status = 'used'
                available_ip.discovery_reason = f"Auto-assigned for {req.user.username if req.user else 'System'}"
            available_ip.hostname = req.hostname
            available_ip.is_unique_hostname = True
            available_ip.assigned_to = req.user
            available_ip.save()'''

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
