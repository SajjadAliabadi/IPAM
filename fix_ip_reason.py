import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace list_display
content = content.replace("list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'discovery_reason', 'first_seen', 'last_seen')", "list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'usage_reason', 'first_seen', 'last_seen')")

# Inject usage_reason and save_model
old_actions = "    actions = ['scan_ips']\n\n    def has_add_permission(self, request):"
new_methods = '''    actions = ['scan_ips']

    def usage_reason(self, obj):
        from django.utils.safestring import mark_safe
        from django.urls import reverse
        if obj.status == 'used':
            req = obj.requests.filter(status='approved').first()
            if req:
                url = reverse('admin:network_iprequest_change', args=[req.id])
                return mark_safe(f'<a href="{url}" style="color: #3b82f6; text-decoration: none; font-weight: 500;"><i class="fas fa-ticket-alt" style="margin-right:4px;"></i> User Request ({req.user.username})</a>')
            
            dr = obj.discovery_reason or ""
            if dr.startswith('Manually'):
                return mark_safe(f'<span style="color: #8b5cf6; font-weight: 500;"><i class="fas fa-user-shield" style="margin-right:4px;"></i> {dr}</span>')
            elif dr.startswith('Detected'):
                return mark_safe(f'<span style="color: #64748b;"><i class="fas fa-satellite-dish" style="margin-right:4px;"></i> {dr}</span>')
            elif dr:
                return dr
            return "Unknown"
        elif obj.status == 'offline':
            return mark_safe(f'<span style="color: #94a3b8; font-style: italic;">{obj.discovery_reason or "Offline"}</span>')
        return "-"
    usage_reason.short_description = "Usage Reason"

    def save_model(self, request, obj, form, change):
        if change:
            from .models import IPAddress
            from django.utils import timezone
            old_obj = IPAddress.objects.get(pk=obj.pk)
            if obj.status == 'used' and old_obj.status != 'used':
                if not obj.discovery_reason or obj.discovery_reason.strip() == '':
                    obj.discovery_reason = f"Manually assigned by {request.user.username}"
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):'''

content = content.replace(old_actions, new_methods)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
