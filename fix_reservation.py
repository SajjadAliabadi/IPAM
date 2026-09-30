import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: IPRequestAdmin save_model
old_save_req = '''              if obj.status == 'approved' and old_obj.status != 'approved' and obj.assigned_ip:
                  ip = obj.assigned_ip
                  if settings.enable_reservation:
                      ip.status = 'reserved'
                      ip.reserved_at = timezone.now()
                      ip.discovery_reason = f"Reserved via IP Request for {obj.user.username}"'''

new_save_req = '''              if obj.status == 'approved' and old_obj.status != 'approved' and obj.assigned_ip:
                  ip = obj.assigned_ip
                  if settings.enable_reservation:
                      ip.status = 'reserved'
                      ip.reserved_at = timezone.now()
                      ip.discovery_reason = f"Reserved via IP Request for {obj.user.username}"
                  else:
                      ip.status = 'used'
                      ip.discovery_reason = f"Assigned via IP Request for {obj.user.username}"
                  ip.save()'''

content = content.replace(old_save_req, new_save_req)

# Fix 2: IPRequestAdmin auto_assign_api
old_auto_assign = '''          if available_ip:
              available_ip.status = 'used'
              available_ip.hostname = req.hostname
              available_ip.is_unique_hostname = True
              available_ip.assigned_to = req.user
              available_ip.save()
              
              req.status = 'approved'
              req.assigned_ip = available_ip
              req.admin_comment = "Auto-assigned by system."
              req.save()'''

new_auto_assign = '''          if available_ip:
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
              available_ip.save()
              
              req.status = 'approved'
              req.assigned_ip = available_ip
              req.admin_comment = "Auto-assigned by system."
              req.save()'''

content = content.replace(old_auto_assign, new_auto_assign)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
