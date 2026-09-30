import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add get_urls and clear_ip_view
old_urls = '''    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('api/subnet-map/<int:subnet_id>/', self.admin_site.admin_view(self.subnet_map_api), name='subnet-map-api'),
        ]
        return custom_urls + urls'''

new_urls = '''    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('api/subnet-map/<int:subnet_id>/', self.admin_site.admin_view(self.subnet_map_api), name='subnet-map-api'),
            path('<int:ip_id>/clear/', self.admin_site.admin_view(self.clear_ip_view), name='clear-ip'),
        ]
        return custom_urls + urls

    def clear_ip_view(self, request, ip_id):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponseRedirect
        from django.contrib import messages
        from .models import IPAddress, AuditLog
        
        ip = get_object_or_404(IPAddress, id=ip_id)
        if ip.status != 'available':
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='IPAddress',
                message=f"IP {ip.ip_address} data completely cleared and released manually."
            )
            ip.status = 'available'
            ip.hostname = ''
            ip.is_unique_hostname = False
            ip.mac_address = ''
            ip.assigned_to = None
            ip.discovery_reason = ''
            ip.reserved_at = None
            ip.description = ''
            ip.save()
            messages.success(request, f"Successfully cleared IP {ip.ip_address} and released it to the Available pool.")
        
        referer = request.META.get('HTTP_REFERER', '/admin/network/ipaddress/')
        return HttpResponseRedirect(referer)'''

content = content.replace(old_urls, new_urls)

# Add clear_ip_button to list_display
old_list_display = "list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'usage_reason', 'first_seen', 'last_seen')"
new_list_display = "list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'usage_reason', 'first_seen', 'last_seen', 'clear_ip_button')"

content = content.replace(old_list_display, new_list_display)

# Add the method
method_code = '''    def clear_ip_button(self, obj):
        from django.utils.safestring import mark_safe
        if obj.status == 'available':
            return mark_safe('<span style="color: #cbd5e1;"><i class="fas fa-eraser"></i> Clear</span>')
        return mark_safe(f'<a href="#" onclick="if(confirm(\\'Are you sure you want to completely wipe all data for {obj.ip_address} and mark it as Available?\\')) window.location.href=\\'/admin/network/ipaddress/{obj.id}/clear/\\'; return false;" style="color: #ef4444; font-weight: 600; padding: 4px 8px; border: 1px solid #ef4444; border-radius: 4px; display: inline-block; white-space: nowrap;"><i class="fas fa-eraser"></i> Clear Data</a>')
    clear_ip_button.short_description = "Actions"

    def usage_reason(self, obj):'''

content = content.replace("    def usage_reason(self, obj):", method_code)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
