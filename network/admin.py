from import_export.admin import ImportExportActionModelAdmin
from django import forms
from django.db import models
import ipaddress
from django.contrib import admin
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import VLAN, Subnet, IPAddress, IPRequest, CheckMethod, SystemSettings
from .utils import perform_discovery, perform_ip_discovery

class CheckMethodForm(forms.ModelForm):
    class Meta:
        model = CheckMethod
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        protocol = cleaned_data.get('protocol')
        custom_port = cleaned_data.get('custom_port')
        script_content = cleaned_data.get('script_content')

        if protocol == 'tcp_port' and not custom_port:
            self.add_error('custom_port', 'Specifying a port number is required for the Custom TCP Port method.')
            
        if protocol == 'custom' and not script_content:
            self.add_error('script_content', 'Python script content is required for the Custom Python Script method.')

        return cleaned_data

@admin.register(CheckMethod)
class CheckMethodAdmin(admin.ModelAdmin):
    form = CheckMethodForm
    list_display = ('name', 'protocol', 'is_active', 'created_at')
    list_filter = ('protocol', 'is_active')
    
    class Media:
        js = ('js/check_method_toggle.js', 'js/method_banner.js')

@admin.register(VLAN)
class VLANAdmin(admin.ModelAdmin):
    list_display = ('vlan_id', 'name', 'description')
    search_fields = ('vlan_id', 'name')

    class Media:
        js = ('js/vlan_banner.js',)

import ipaddress
from django.core.exceptions import ValidationError

class SubnetForm(forms.ModelForm):
    class Meta:
        model = Subnet
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        network_address = cleaned_data.get('network_address')
        start_ip = cleaned_data.get('auto_assign_range_start')
        end_ip = cleaned_data.get('auto_assign_range_end')

        if network_address:
            try:
                net = ipaddress.ip_network(network_address, strict=False)
                
                if start_ip:
                    if ipaddress.ip_address(start_ip) not in net:
                        self.add_error('auto_assign_range_start', f"IP {start_ip} does not belong to subnet {network_address}.")
                if end_ip:
                    if ipaddress.ip_address(end_ip) not in net:
                        self.add_error('auto_assign_range_end', f"IP {end_ip} does not belong to subnet {network_address}.")
                
                if start_ip and end_ip:
                    if ipaddress.ip_address(start_ip) > ipaddress.ip_address(end_ip):
                        self.add_error('auto_assign_range_start', "Start IP cannot be greater than End IP.")
                        
            except ValueError as e:
                pass
                
        return cleaned_data

@admin.register(Subnet)
class SubnetAdmin(ImportExportActionModelAdmin):
    form = SubnetForm
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }
    list_display = ('network_address', 'name', 'gateway', 'vlan', 'department', 'auto_assign_display')
    search_fields = ('network_address', 'name')
    list_filter = ('vlan', 'department')
    def auto_assign_display(self, obj):
        from django.utils.safestring import mark_safe
        from .models import SystemSettings
        settings = SystemSettings.load()
        
        if not settings.auto_assign_ips:
            return mark_safe('<span style="color: #ef4444; font-weight: 600; font-size: 12px; padding: 4px 8px; background: #fee2e2; border-radius: 4px; border: 1px solid #f87171;"><i class="fas fa-ban"></i> Global Disabled</span>')
            
        if not obj.enable_auto_assign:
            return mark_safe('<span style="color: #64748b; font-size: 12px; padding: 4px 8px; background: #f1f5f9; border-radius: 4px; border: 1px solid #cbd5e1;"><i class="fas fa-times-circle"></i> Disabled</span>')
            
        start = obj.auto_assign_range_start
        end = obj.auto_assign_range_end
        if not start and not end:
            range_str = "Entire Subnet"
        else:
            start_str = start if start else 'Start'
            end_str = end if end else 'End'
            range_str = f"{start_str} &rarr; {end_str}"
            
        return mark_safe(f'<div style="color: #059669; font-weight: 600; font-size: 12px; margin-bottom: 4px;"><i class="fas fa-check-circle"></i> Enabled</div><div style="font-size: 11px; color: #334155; background: #f8fafc; padding: 3px 6px; border-radius: 4px; display: inline-block; border: 1px solid #e2e8f0; font-family: monospace;">{range_str}</div>')
        
    auto_assign_display.short_description = "Auto-Assign Pool"

    actions = ['scan_subnet']
    
    fieldsets = (
        ('General Information', {
            'fields': ('network_address', 'name', 'gateway', 'vlan', 'department')
        }),
        ('Scanning & Discovery', {
            'fields': ('check_methods', 'scan_interval_minutes'),
            'description': 'Configure how and when this subnet should be scanned automatically.'
        }),
        ('Auto-IP Assignment', {
            'fields': ('enable_auto_assign', 'auto_assign_range_start', 'auto_assign_range_end'),
            'description': 'Configure automatic IP allocation specifically for this subnet.'
        }),
    )
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:subnet_id>/scan/', self.admin_site.admin_view(self.scan_single_subnet_view), name='network_subnet_scan'),
        ]
        return custom_urls + urls

    def scan_single_subnet_view(self, request, subnet_id):
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        subnet = Subnet.objects.filter(id=subnet_id)
        if subnet.exists():
            perform_discovery(subnet)
            messages.success(request, f"Discovery scan completed for {subnet.first().network_address}.")
        return HttpResponseRedirect(reverse('admin:network_ipaddress_changelist'))

    class Media:
        js = (
            'js/nouislider.min.js',
            'js/subnet_auto_assign.js',
        )
        css = {
            'all': ('css/nouislider.min.css',)
        }

    @admin.action(description='Run Discovery Scan on Selected Subnets')
    def scan_subnet(self, request, queryset):
        perform_discovery(queryset)
        messages.success(request, "Subnet scan completed successfully.")

from django.template.response import TemplateResponse
from django.urls import reverse
import ipaddress

from django import forms
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import path

class IPAddressForm(forms.ModelForm):
    class Meta:
        model = IPAddress
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        hostname = cleaned_data.get('hostname')
        is_unique = cleaned_data.get('is_unique_hostname')
        ip_obj = self.instance

        if hostname:
            # If this IP wants to be unique, check if ANY other IP has this hostname
            # OR if another IP already claimed this hostname as unique, we can't use it at all
            existing = IPAddress.objects.filter(hostname__iexact=hostname).exclude(pk=ip_obj.pk)
            
            # If another IP claimed it as unique
            conflict = existing.filter(is_unique_hostname=True).first()
            if conflict:
                raise ValidationError({'hostname': f"ÃƒËœÃ‚Â§Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â  Ãƒâ„¢Ã¢â‚¬Â¡ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â¦ ÃƒËœÃ‚Â¨Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚ÂµÃƒâ„¢Ã‹â€ ÃƒËœÃ‚Â±ÃƒËœÃ‚Âª Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã‹â€ Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™ÃƒÅ¡Ã‚Â© ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â± ÃƒËœÃ‚Â³ÃƒËœÃ‚Â±Ãƒâ„¢Ã‹â€ ÃƒËœÃ‚Â±Ãƒâ€ºÃ…â€™ ÃƒËœÃ‚Â¨ÃƒËœÃ‚Â§ ÃƒËœÃ‚Â¢ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â±ÃƒËœÃ‚Â³ {conflict.ip_address} ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚ÂªÃƒâ„¢Ã‚ÂÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â´ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª Ãƒâ„¢Ã‹â€  Ãƒâ„¢Ã¢â‚¬Â Ãƒâ„¢Ã¢â‚¬Â¦Ãƒâ€ºÃ…â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…â€™ÃƒËœÃ‚ÂªÃƒâ„¢Ã‹â€ ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™ÃƒËœÃ‚Â¯ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â² ÃƒËœÃ‚Â¢Ãƒâ„¢Ã¢â‚¬Â  ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚ÂªÃƒâ„¢Ã‚ÂÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒÅ¡Ã‚Â©Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™ÃƒËœÃ‚Â¯."})
            
            # If we want to be unique, but it's used elsewhere (even non-uniquely), it's a conflict
            if is_unique and existing.exists():
                conflict = existing.first()
                raise ValidationError({'hostname': f"ÃƒËœÃ‚Â´Ãƒâ„¢Ã¢â‚¬Â¦ÃƒËœÃ‚Â§ ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â±ÃƒËœÃ‚Â®Ãƒâ„¢Ã‹â€ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª Ãƒâ„¢Ã¢â‚¬Â¡ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â¦ Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã‹â€ Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™ÃƒÅ¡Ã‚Â© ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ÃƒÂ¢Ã¢â€šÂ¬Ã…â€™ÃƒËœÃ‚Â§Ãƒâ€ºÃ…â€™ÃƒËœÃ‚Â¯ÃƒËœÃ…â€™ ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â¦ÃƒËœÃ‚Â§ ÃƒËœÃ‚Â§Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â  Ãƒâ„¢Ã¢â‚¬Â ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â¦ ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â± ÃƒËœÃ‚Â¢ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â±ÃƒËœÃ‚Â³ {conflict.ip_address} ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â± ÃƒËœÃ‚Â­ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Å¾ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚ÂªÃƒâ„¢Ã‚ÂÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª."})
                
        return cleaned_data

@admin.register(IPAddress)
class IPAddressAdmin(ImportExportActionModelAdmin):
    class Media:
        js = ('js/ip_map.js', 'js/ip_status_confirm.js', 'js/check_unique_hostname.js', 'js/ip_banner.js')
        
    form = IPAddressForm
    list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'usage_reason', 'first_seen', 'last_seen', 'clear_ip_button')
    search_fields = ('ip_address', 'mac_address', 'hostname')
    list_display_links = ('ip_address_display',)
    list_filter = ('status', 'subnet')
    ordering = ('ip_address_padded',)
    
    readonly_fields = ('last_checked', 'first_seen', 'last_seen', 'vlan_display', 'reserved_at')
    fieldsets = (
        ('IP Configuration', {
            'fields': ('ip_address', 'subnet', 'vlan_display', 'hostname', 'is_unique_hostname', 'mac_address', 'status', 'discovery_reason')
        }),
        ('Timeline & Tracking', {
            'fields': ('first_seen', 'last_seen', 'last_checked', 'reserved_at')
        }),
        ('Additional Info', {
            'fields': ('assigned_to', 'description')
        }),
    )
    

        
    actions = ['scan_ips']

    def clear_ip_button(self, obj):
        from django.utils.safestring import mark_safe
        if obj.status == 'available':
            return mark_safe('<span style="color: #cbd5e1;"><i class="fas fa-eraser"></i> Clear</span>')
        return mark_safe(f'<a href="#" onclick="if(confirm(\'Are you sure you want to completely wipe all data for {obj.ip_address} and mark it as Available?\')) window.location.href=\'/admin/network/ipaddress/{obj.id}/clear/\'; return false;" style="color: #ef4444; font-weight: 600; padding: 4px 8px; border: 1px solid #ef4444; border-radius: 4px; display: inline-block; white-space: nowrap;"><i class="fas fa-eraser"></i> Clear Data</a>')
    clear_ip_button.short_description = "Actions"

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
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False

    @admin.action(description='Run Live Discovery Scan on Selected IPs')
    def scan_ips(self, request, queryset):
        perform_ip_discovery(queryset)
        self.message_user(request, "Scan completed for selected IPs.", level='SUCCESS')

    @admin.display(description='status_badge', ordering='status_badge')
    def status_badge(self, obj):
        from django.utils.safestring import mark_safe
        if obj.status == 'available':
            return mark_safe('<span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 12px; display: inline-flex; align-items: center; gap: 6px;"><i class="fas fa-check-circle" style="font-size: 11px;"></i> Available</span>')
        elif obj.status == 'used':
            return mark_safe('<span style="background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 12px; display: inline-flex; align-items: center; gap: 6px;"><i class="fas fa-server" style="font-size: 11px;"></i> In Use</span>')
        elif obj.status == 'offline':
            return mark_safe('<span style="background: #f1f5f9; color: #475569; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 12px; display: inline-flex; align-items: center; gap: 6px;"><i class="fas fa-power-off" style="font-size: 11px;"></i> Offline</span>')
        elif obj.status == 'reserved':
            return mark_safe('<span style="background: #fef9c3; color: #854d0e; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 12px; display: inline-flex; align-items: center; gap: 6px;"><i class="fas fa-lock" style="font-size: 11px;"></i> Reserved</span>')
        return obj.get_status_display()

    @admin.display(ordering='ip_address_padded', description='IP Address')
    def ip_address_display(self, obj):
        from django.utils.html import format_html
        return format_html('<span style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight: 700; font-size: 14px; letter-spacing: 0.5px;">{}</span>', obj.ip_address)

    def vlan_id_display(self, obj):
        if obj.subnet and obj.subnet.vlan:
            return obj.subnet.vlan.vlan_id
        return '-'
    vlan_id_display.short_description = 'VLAN ID'
    vlan_id_display.admin_order_field = 'subnet__vlan__vlan_id'
    
    def vlan_display(self, obj):
        if obj and obj.subnet and obj.subnet.vlan:
            return f"VLAN {obj.subnet.vlan.vlan_id} ({obj.subnet.vlan.name})"
        return '-'
    vlan_display.short_description = 'VLAN'
        
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('ip_address', 'subnet', 'vlan_display', 'discovery_reason', 'last_checked')
        return ('subnet', 'vlan_display', 'discovery_reason', 'last_checked')
        
    def get_urls(self):
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
        return HttpResponseRedirect(referer)
        
    def check_hostname_api(self, request):
        hostname = request.GET.get('hostname', '').strip()
        current_ip_id = request.GET.get('exclude_id', '')
        
        if not hostname:
            return JsonResponse({'status_badge': 'ok'})
            
        qs = IPAddress.objects.filter(hostname__iexact=hostname)
        if current_ip_id:
            qs = qs.exclude(id=current_ip_id)
            
        conflict = qs.filter(is_unique_hostname=True).first()
        if conflict:
            return JsonResponse({
                'status_badge': 'error', 
                'message': f"Ãƒâ„¢Ã¢â‚¬Â¡ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â¦ ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â ÃƒËœÃ‚ÂªÃƒËœÃ‚Â®ÃƒËœÃ‚Â§ÃƒËœÃ‚Â¨Ãƒâ€ºÃ…â€™ ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â± Ãƒâ€ºÃ…â€™ÃƒÅ¡Ã‚Â© ÃƒËœÃ‚Â³ÃƒËœÃ‚Â±Ãƒâ„¢Ã‹â€ ÃƒËœÃ‚Â± ÃƒËœÃ‚Â¯Ãƒâ€ºÃ…â€™ÃƒÅ¡Ã‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â¨ÃƒËœÃ‚Â§ ÃƒËœÃ‚Â¢ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â±ÃƒËœÃ‚Â³ {conflict.ip_address} ÃƒËœÃ‚Â¨Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚ÂµÃƒâ„¢Ã‹â€ ÃƒËœÃ‚Â±ÃƒËœÃ‚Âª Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã‹â€ Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™ÃƒÅ¡Ã‚Â© ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚ÂªÃƒâ„¢Ã‚ÂÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â´ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ Ãƒâ„¢Ã‹â€  Ãƒâ„¢Ã¢â‚¬Â Ãƒâ„¢Ã¢â‚¬Â¦Ãƒâ€ºÃ…â€™ ÃƒËœÃ‚Â´Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â² ÃƒËœÃ‚Â§Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â  Ãƒâ„¢Ã¢â‚¬Â¡ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚Âª Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â¦ ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚ÂªÃƒâ„¢Ã‚ÂÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒÅ¡Ã‚Â©ÃƒËœÃ‚Â±ÃƒËœÃ‚Â¯."
            })
            
        # Also warn if the user is checking 'unique' but the name is used elsewhere
        if request.GET.get('wants_unique') == 'true' and qs.exists():
            conflict = qs.first()
            return JsonResponse({
                'status_badge': 'error',
                'message': f"ÃƒËœÃ‚Â§Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã¢â‚¬Â  Ãƒâ„¢Ã¢â‚¬Â ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â¦ ÃƒËœÃ‚Â¯ÃƒËœÃ‚Â± ÃƒËœÃ‚Â­ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Å¾ ÃƒËœÃ‚Â­ÃƒËœÃ‚Â§ÃƒËœÃ‚Â¶ÃƒËœÃ‚Â± ÃƒËœÃ‚ÂªÃƒâ„¢Ã‹â€ ÃƒËœÃ‚Â³ÃƒËœÃ‚Â· {conflict.ip_address} ÃƒËœÃ‚Â§ÃƒËœÃ‚Â³ÃƒËœÃ‚ÂªÃƒâ„¢Ã‚ÂÃƒËœÃ‚Â§ÃƒËœÃ‚Â¯Ãƒâ„¢Ã¢â‚¬Â¡ Ãƒâ„¢Ã¢â‚¬Â¦Ãƒâ€ºÃ…â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…â€™ÃƒËœÃ‚Â´Ãƒâ„¢Ã‹â€ ÃƒËœÃ‚Â¯ Ãƒâ„¢Ã‹â€  Ãƒâ„¢Ã¢â‚¬Â Ãƒâ„¢Ã¢â‚¬Â¦Ãƒâ€ºÃ…â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…â€™ÃƒËœÃ‚ÂªÃƒâ„¢Ã‹â€ ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â ÃƒËœÃ‚Â¯ ÃƒËœÃ‚Â¨Ãƒâ„¢Ã¢â‚¬Â¡ ÃƒËœÃ‚Â¹Ãƒâ„¢Ã¢â‚¬Â Ãƒâ„¢Ã‹â€ ÃƒËœÃ‚Â§Ãƒâ„¢Ã¢â‚¬Â  Ãƒâ€ºÃ…â€™Ãƒâ„¢Ã‹â€ Ãƒâ„¢Ã¢â‚¬Â Ãƒâ€ºÃ…â€™ÃƒÅ¡Ã‚Â© ÃƒËœÃ‚Â«ÃƒËœÃ‚Â¨ÃƒËœÃ‚Âª ÃƒËœÃ‚Â´Ãƒâ„¢Ã‹â€ ÃƒËœÃ‚Â¯."
            })
            
        return JsonResponse({'status_badge': 'ok'})

    def response_change(self, request, obj):
        res = super().response_change(request, obj)
        if isinstance(res, HttpResponseRedirect) and res.url == reverse('admin:network_ipaddress_changelist'):
            return HttpResponseRedirect(f"{res.url}?subnet__id__exact={obj.subnet.id}")
        return res

    def response_add(self, request, obj, post_url_continue=None):
        res = super().response_add(request, obj, post_url_continue)
        if isinstance(res, HttpResponseRedirect) and res.url == reverse('admin:network_ipaddress_changelist'):
            return HttpResponseRedirect(f"{res.url}?subnet__id__exact={obj.subnet.id}")
        return res
        
    def changelist_view(self, request, extra_context=None):
        # If no subnet filter is applied and not searching, show the subnet selector page
        if 'subnet__id__exact' not in request.GET and 'q' not in request.GET and 'status__exact' not in request.GET:
            from .models import Subnet
            subnets = Subnet.objects.all()
            
            # Pre-calculate stats for each subnet for the UI
            subnet_stats = []
            for sub in subnets:
                total = sub.ips.count()
                used = sub.ips.filter(status='used').count()
                available = sub.ips.filter(status='available').count()
                subnet_stats.append({
                    'obj': sub,
                    'total': total,
                    'used': used,
                    'available': available,
                    'percent': int((used / total * 100)) if total > 0 else 0
                })
                
            context = dict(
                self.admin_site.each_context(request),
                subnet_stats=subnet_stats,
                title="Select a Subnet to manage its IP Addresses",
                app_label="network",
            )
            return TemplateResponse(request, "admin/network/ipaddress/subnet_selector.html", context)
            
        # If subnet is applied, we want to inject the IP grid for that subnet into the changelist
        subnet_id = request.GET.get('subnet__id__exact')
        print(f'IP GRID HIT, subnet={subnet_id}')
        if subnet_id:
            try:
                from .models import Subnet
                subnet = Subnet.objects.get(id=subnet_id)
                
                # Generate the HTML grid
                ips = subnet.ips.all()
                sorted_ips = sorted(ips, key=lambda x: ipaddress.IPv4Address(x.ip_address))
                html = '<div class="ip-grid-wrapper" style="margin-top: 30px; padding: 20px; background: white; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">'
                html += f'<h4 style="margin-top:0; margin-bottom: 20px; color: #334155;">IP Map: {subnet.network_address}</h4>'
                html += '<div class="ip-grid-container" style="display: flex; flex-wrap: wrap; gap: 6px;">'
                for ip in sorted_ips:
                    url = reverse('admin:network_ipaddress_change', args=[ip.pk])
                    color = '#28a745' if ip.status == 'available' else '#dc3545'
                    if ip.status == 'reserved': color = '#ffc107'
                    if ip.status == 'offline': color = '#6c757d'
                    last_octet = str(ip.ip_address).split('.')[-1]
                    html += f'<a href="{url}" class="ip-box" title="{ip.ip_address} ({ip.status})" style="background-color: {color};">{last_octet}</a>'
                html += '</div></div>'
                
                extra_context = extra_context or {}
                extra_context['ip_grid_html'] = html
                extra_context['title'] = f"IP Addresses in {subnet.network_address}"
            except Exception as e:
                extra_context['ip_grid_html'] = f"<div style='color:red;'>Error generating IP Map: {str(e)}</div>"
                
        return super().changelist_view(request, extra_context=extra_context)

from django.template.response import TemplateResponse
import zoneinfo


class SystemSettingsForm(forms.ModelForm):
    timezone = forms.ChoiceField(choices=[(tz, tz) for tz in sorted(zoneinfo.available_timezones())])
    class Meta:
        model = SystemSettings
        fields = '__all__'

class IPRequestForm(forms.ModelForm):
    class Meta:
        model = IPRequest
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'subnet' in self.fields:
            self.fields['subnet'].label_from_instance = lambda obj: f"{obj.network_address} ({obj.name})" if obj.enable_auto_assign else f"❌ {obj.network_address} ({obj.name}) - AUTO-ASSIGN DISABLED"

    def clean(self):
        cleaned_data = super().clean()
        hostname = cleaned_data.get('hostname')
        
        if hostname:
            conflict = IPAddress.objects.filter(hostname__iexact=hostname, is_unique_hostname=True).first()
            if conflict:
                raise ValidationError({'hostname': f"This hostname is already uniquely reserved on the network by IP: {conflict.ip_address}"})
        return cleaned_data

@admin.register(IPRequest)
class IPRequestAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/req_banner.js',)
    form = IPRequestForm
    list_display = ('user', 'hostname', 'subnet', 'status', 'requested_at', 'assigned_ip')
    list_filter = ('status', 'subnet', 'requested_at')
    search_fields = ('user__username', 'hostname', 'reason')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists():
            return qs
        return qs.filter(user=request.user)

    def get_readonly_fields(self, request, obj=None):
        base_readonly = ['requested_at', 'client_ip', 'user_agent', 'user_total_requests']
        if not (request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists()):
            if obj:
                return base_readonly + ['status', 'assigned_ip', 'admin_comment']
        return base_readonly

    def user_total_requests(self, obj):
        if obj and obj.user:
            from .models import IPRequest
            return IPRequest.objects.filter(user=obj.user).count()
        return 0
    user_total_requests.short_description = "Total Requests by User"

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists():
            return (
                ('Request Details', {'fields': ('requested_at', 'client_ip', 'user_agent', 'user', 'user_total_requests')}),
                ('Admin Action', {'fields': ('subnet', 'hostname', 'reason', 'status', 'assigned_ip', 'admin_comment')}),
            )
        else:
            if obj:
                return (
                    ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
                    ('Admin Response', {'fields': ('status', 'assigned_ip', 'admin_comment')}),
                )
            return (
                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
            )

    def save_model(self, request, obj, form, change):
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
                
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        from .models import SystemSettings, AuditLog
        settings = SystemSettings.load()
        
        AuditLog.objects.create(user=request.user, action='CREATE', model_name='IPRequest', message=f"IP requested for {obj.hostname}")
        
        try:
            from .alerts import send_telegram_alert
            send_telegram_alert(f"New IP Request: User {obj.user.username if obj.user else 'System'} requested an IP for hostname {obj.hostname}")
        except: pass

        if settings.auto_assign_ips and obj.subnet.enable_auto_assign and obj.status == 'pending':
            return HttpResponseRedirect(reverse('admin:network_iprequest_process', args=[obj.id]))
            
        return super().response_add(request, obj, post_url_continue)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:request_id>/process/', self.admin_site.admin_view(self.process_request_view), name='network_iprequest_process'),
                        path('<int:request_id>/auto-assign/', self.admin_site.admin_view(self.auto_assign_api), name='network_iprequest_auto_assign'),
            path('api/subnet-map/<int:subnet_id>/', self.admin_site.admin_view(self.subnet_map_api), name='network_iprequest_subnet_map'),
        ]
        return custom_urls + urls

    def subnet_map_api(self, request, subnet_id):
        from django.http import JsonResponse
        from .models import IPAddress
        ips = IPAddress.objects.filter(subnet_id=subnet_id).order_by('ip_address_padded')
        data = [{'id': ip.id, 'ip': ip.ip_address, 'status': ip.status} for ip in ips]
        return JsonResponse({'ips': data})

    def process_request_view(self, request, request_id):
        req = IPRequest.objects.get(id=request_id)
        return TemplateResponse(request, 'admin/network/iprequest/process.html', {'req': req})

    def auto_assign_api(self, request, request_id):
        import time, ipaddress
        from .models import IPAddress, AuditLog
        time.sleep(3) 
        req = IPRequest.objects.get(id=request_id)
        
        if not req.subnet.enable_auto_assign:
            from django.http import JsonResponse
            return JsonResponse({'status': 'error', 'message': 'Auto-assignment is disabled for this subnet.'})
            
        qs = IPAddress.objects.filter(subnet=req.subnet, status='available').order_by('ip_address_padded')
        
        # Filter by range if specified
        start_ip = req.subnet.auto_assign_range_start
        end_ip = req.subnet.auto_assign_range_end
        
        available_ip = None
        for ip in qs:
            ip_obj = ipaddress.ip_address(ip.ip_address)
            valid = True
            if start_ip:
                try:
                    if ip_obj < ipaddress.ip_address(start_ip): valid = False
                except: pass
            if end_ip:
                try:
                    if ip_obj > ipaddress.ip_address(end_ip): valid = False
                except: pass
            if valid:
                available_ip = ip
                break

        if available_ip:
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
            req.save()
            
            AuditLog.objects.create(user=request.user, action='ASSIGN', model_name='IPAddress', message=f"Auto-assigned {available_ip.ip_address} to {req.hostname}")
            
            return JsonResponse({'status': 'success', 'ip': available_ip.ip_address})
        else:
            req.admin_comment = "Auto-assignment failed: No available IPs in subnet or range."
            req.save()
            return JsonResponse({'status': 'error', 'message': 'No available IPs in the auto-assign range. Your request is pending admin approval.'})

from .models import AuditLog
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/audit_banner.js',)
    list_display = ('timestamp', 'action_badge', 'model_name', 'user_display', 'message')

    def action_badge(self, obj):
        from django.utils.safestring import mark_safe
        color = '#64748b'
        icon = 'fa-info-circle'
        if obj.action == 'CREATE': color, icon = '#10b981', 'fa-plus-circle'
        elif obj.action == 'UPDATE': color, icon = '#3b82f6', 'fa-edit'
        elif obj.action == 'DELETE': color, icon = '#ef4444', 'fa-trash'
        elif obj.action == 'SCAN': color, icon = '#8b5cf6', 'fa-satellite-dish'
        elif obj.action == 'ASSIGN': color, icon = '#f59e0b', 'fa-user-tag'
        elif obj.action == 'SYSTEM': color, icon = '#475569', 'fa-cogs'
        
        return mark_safe(f'<span style="background: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;"><i class="fas {icon}" style="margin-right: 4px;"></i> {obj.get_action_display()}</span>')
    action_badge.short_description = "Event Type"
    
    def user_display(self, obj):
        from django.utils.safestring import mark_safe
        if obj.user:
            return mark_safe(f'<div style="display:flex; align-items:center; gap:8px;"><div style="width:24px; height:24px; border-radius:50%; background:#e2e8f0; display:flex; align-items:center; justify-content:center; color:#475569;"><i class="fas fa-user" style="font-size:10px;"></i></div><span style="font-weight:600; color:#334155;">{obj.user.username}</span></div>')
        return mark_safe('<div style="display:flex; align-items:center; gap:8px;"><div style="width:24px; height:24px; border-radius:50%; background:#f1f5f9; display:flex; align-items:center; justify-content:center; color:#94a3b8;"><i class="fas fa-robot" style="font-size:10px;"></i></div><span style="font-style:italic; color:#64748b;">System Process</span></div>')
    user_display.short_description = "Initiator"
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('message', 'user__username')
    readonly_fields = ('timestamp', 'action', 'model_name', 'user', 'message')

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def has_change_permission(self, request, obj=None):
        return False








@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('UI & Theming', {
            'fields': ('theme', 'custom_logo')
        }),
        ('Automation & Provisioning', {
            'fields': ('auto_assign_ips', 'enable_reservation', 'reservation_timeout_hours', 'offline_timeout_hours'),
        }),
        ('Time Synchronization', {
            'fields': ('timezone', 'time_sync_mode', 'manual_time', 'ntp_server')
        }),
        ('Alerting (Telegram)', {
            'fields': ('telegram_bot_token', 'telegram_chat_id', 'alert_on_subnet_full', 'alert_on_critical_offline'),
            'description': 'Configure Telegram Bot API to receive real-time IPAM alerts.'
        }),
        ('Server Configuration', {
            'fields': ('server_port', 'enable_ssl', 'ssl_cert_path', 'ssl_key_path'),
            'description': 'WARNING: Changing these settings requires manually restarting the background server runner, or using the customized wait_server.py script.'
        })
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        import subprocess
        try:
            if obj.time_sync_mode == 'manual' and obj.manual_time:
                date_str = obj.manual_time.strftime('%Y-%m-%d %H:%M:%S')
                result = subprocess.run(['powershell', '-Command', f'Set-Date -Date "{date_str}"'], check=False, capture_output=True, text=True)
                if result.returncode == 0:
                    messages.success(request, f"System time successfully set to {date_str}.")
                else:
                    messages.error(request, f"Failed to set manual time: {result.stderr}")
            elif obj.time_sync_mode == 'ntp' and obj.ntp_server:
                ps_script = f'w32tm /config /syncfromflags:manual /manualpeerlist:"{obj.ntp_server}" /update; Restart-Service w32time; w32tm /resync'
                result = subprocess.run(['powershell', '-Command', ps_script], check=False, capture_output=True, text=True)
                if result.returncode == 0:
                    messages.success(request, f"NTP Server configured to {obj.ntp_server} and resynchronized.")
                else:
                    messages.error(request, f"Failed to configure NTP: {result.stderr}")
        except Exception as e:
            messages.error(request, f"Failed to apply time settings: {e}")
    class Media:
        js = ('js/settings_banner.js',)
    list_display = ('__str__', 'theme', 'offline_timeout_hours', 'auto_assign_ips')
    
    form = SystemSettingsForm
    def get_fieldsets(self, request, obj=None):
        from django.utils import timezone
        current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        from django.utils.safestring import mark_safe
        return (
            ('Server Configuration', {
                'fields': ('server_port', 'enable_ssl', 'ssl_cert_path', 'ssl_key_path'),
                'description': 'WARNING: Changing these settings takes effect on the next server restart.'
            }),
            ('UI & Theming', {
                'fields': ('theme', 'custom_logo'),
                'description': 'Choose a responsive UI theme and set a custom logo. Changes apply immediately.'
            }),
            ('Alerting (Telegram)', {
                'fields': ('telegram_bot_token', 'telegram_chat_id', 'alert_on_subnet_full', 'alert_on_critical_offline'),
                'description': 'Configure Telegram Bot API to receive real-time IPAM alerts.'
            }),
            ('Automation & Provisioning', {
                'fields': ('auto_assign_ips', 'enable_reservation', 'reservation_timeout_hours', 'offline_timeout_hours'),
                'description': 'Configure automatic IP allocation, recycling, and reservation settings.'
            }),
            ('System Time', {
                'fields': ('timezone', 'time_sync_mode', 'manual_time', 'ntp_server'),
                'description': mark_safe(f'Configure time synchronization and timezone.<br><br><b>Current System Time:</b> {current_time}')
            }),
        )

    def has_add_permission(self, request):
        return False if self.model.objects.exists() else super().has_add_permission(request)
        
    def has_delete_permission(self, request, obj=None):
        return False
        
    def changelist_view(self, request, extra_context=None):
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        obj = self.model.load()
        return HttpResponseRedirect(reverse('admin:network_systemsettings_change', args=[obj.id]))




































