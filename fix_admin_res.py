import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace IPAddressAdmin.save_model
old_ip_save = '''    def save_model(self, request, obj, form, change):
        if change:
            from .models import IPAddress
            from django.utils import timezone
            old_obj = IPAddress.objects.get(pk=obj.pk)
            if obj.status == 'used' and old_obj.status != 'used':
                if not obj.discovery_reason or obj.discovery_reason.strip() == '':
                    obj.discovery_reason = f"Manually assigned by {request.user.username}"
        super().save_model(request, obj, form, change)'''

new_ip_save = '''    def save_model(self, request, obj, form, change):
        from .models import SystemSettings, IPAddress
        from django.utils import timezone
        settings = SystemSettings.load()
        if change:
            old_obj = IPAddress.objects.get(pk=obj.pk)
            if obj.status == 'used' and old_obj.status != 'used':
                if settings.enable_reservation:
                    obj.status = 'reserved'
                    obj.reserved_at = timezone.now()
                    obj.discovery_reason = f"Manually reserved by {request.user.username}"
                else:
                    if not obj.discovery_reason or obj.discovery_reason.strip() == '':
                        obj.discovery_reason = f"Manually assigned by {request.user.username}"
        super().save_model(request, obj, form, change)'''

content = content.replace(old_ip_save, new_ip_save)

# Replace IPRequestAdmin.save_model
old_req_save = '''    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not (request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists()):
                obj.user = request.user
            
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                obj.client_ip = x_forwarded_for.split(',')[0]
            else:
                obj.client_ip = request.META.get('REMOTE_ADDR')
            obj.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
        super().save_model(request, obj, form, change)'''

new_req_save = '''    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if not obj.pk:
            if not (request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists()):
                obj.user = request.user
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                obj.client_ip = x_forwarded_for.split(',')[0]
            else:
                obj.client_ip = request.META.get('REMOTE_ADDR')
            obj.user_agent = request.META.get('HTTP_USER_AGENT', '')
        else:
            from .models import IPRequest, SystemSettings
            old_obj = IPRequest.objects.get(pk=obj.pk)
            settings = SystemSettings.load()
            if obj.status == 'approved' and old_obj.status != 'approved' and obj.assigned_ip:
                ip = obj.assigned_ip
                if settings.enable_reservation:
                    ip.status = 'reserved'
                    ip.reserved_at = timezone.now()
                    ip.discovery_reason = f"Reserved via IP Request for {obj.user.username}"
                else:
                    ip.status = 'used'
                    ip.discovery_reason = f"Assigned via IP Request for {obj.user.username}"
                ip.assigned_to = obj.user
                ip.hostname = obj.hostname
                ip.save()
                
        super().save_model(request, obj, form, change)'''

content = content.replace(old_req_save, new_req_save)

# Add reserved_at to IPAddressAdmin fieldsets
content = content.replace("('first_seen', 'last_seen', 'last_checked')", "('first_seen', 'last_seen', 'last_checked', 'reserved_at')")
content = content.replace("('last_checked', 'first_seen', 'last_seen', 'vlan_display')", "('last_checked', 'first_seen', 'last_seen', 'vlan_display', 'reserved_at')")

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
