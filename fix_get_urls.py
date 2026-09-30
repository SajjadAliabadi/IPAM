import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_urls = '''    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('api/check-hostname/', self.admin_site.admin_view(self.check_hostname_api), name='network_ipaddress_check_hostname'),
        ]
        return custom_urls + urls'''

new_urls = '''    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('api/check-hostname/', self.admin_site.admin_view(self.check_hostname_api), name='network_ipaddress_check_hostname'),
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
                message=f"IP {ip.ip_address} completely cleared and released manually by admin."
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

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
