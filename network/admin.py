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
    @admin.display(description='Usage')
    def usage_progress(self, obj):
        from django.utils.html import format_html
        
        total = obj.ipaddress_set.count()
        used = obj.ipaddress_set.filter(status='used').count()
        if total == 0:
            return format_html('<span style="color: #94a3b8; font-style: italic;">No IPs</span>')
            
        percent = int((used / total) * 100)
        color = '#10b981' if percent < 70 else ('#f59e0b' if percent < 90 else '#ef4444')
        
        return format_html(
            '<div style="width: 100px; background: #e2e8f0; border-radius: 999px; height: 8px; margin-top: 6px; overflow: hidden;" title="{}% Used">'
            '<div style="width: {}%; background: {}; height: 100%; border-radius: 999px;"></div>'
            '</div>'
            '<div style="font-size: 11px; color: #64748b; margin-top: 4px; font-weight: 600;">{} / {}</div>',
            percent, percent, color, used, total
        )

    @admin.display(description='Actions')
    def quick_actions(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        scan_url = reverse('admin:network_subnet_scan', args=[obj.pk])
        return format_html(
            '<a href="{}" class="btn btn-sm btn-outline-primary" style="padding: 2px 8px; font-size: 12px; font-weight: 600; border-radius: 4px; transition: all 0.2s;" onclick="this.innerHTML=\'Scanning...\'; this.style.pointerEvents=\'none\'; this.style.opacity=\'0.7\';">'
            '<i class="fas fa-sync-alt" style="margin-right: 4px;"></i> Scan'
            '</a>',
            scan_url
        )

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

        if not request.user.has_perm('network.change_subnet'):
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            messages.error(request, "Permission Denied: You do not have permission to perform this action.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:network_subnet_changelist')))
        subnet = Subnet.objects.filter(id=subnet_id)
        if subnet.exists():
            perform_discovery(subnet)
            messages.success(request, f"Discovery scan completed for {subnet.first().network_address}.")
        return HttpResponseRedirect(reverse('admin:network_ipaddress_changelist'))

    class Media:
        js = (
            'js/nouislider.min.js',
            'js/subnet_auto_assign.js',
            'js/modern_checkboxes.js',
        )
        css = {
            'all': ('css/nouislider.min.css', 'css/modern_checkboxes.css')
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

from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from network.models import SystemSettings

class IsNewIPFilter(SimpleListFilter):
    title = 'Is New'
    parameter_name = 'is_new'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Yes (New)'),
            ('false', 'No (Old)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            settings = SystemSettings.load()
            cutoff = timezone.now() - timezone.timedelta(hours=settings.new_ip_duration_hours)
            return queryset.filter(first_seen__gte=cutoff)
        if self.value() == 'false':
            settings = SystemSettings.load()
            cutoff = timezone.now() - timezone.timedelta(hours=settings.new_ip_duration_hours)
            return queryset.filter(first_seen__lt=cutoff)
        return queryset

@admin.register(IPAddress)
class IPAddressAdmin(admin.ModelAdmin):
    class Media:
        js = ('js/ip_map.js', 'js/ip_status_confirm.js', 'js/check_unique_hostname.js', 'js/ip_banner.js', 'js/ip_status_modal.js')
        


    def get_fieldsets(self, request, obj=None):
        if not request.user.has_perm('network.change_ipaddress'):
            return (
                ('IP Configuration', {
                    'fields': ('ip_address', 'subnet', 'vlan_display', 'hostname', 'is_unique_hostname', 'mac_address', 'os_name', 'status_badge_only', 'discovery_reason_display')
                }),
                ('Port Analysis', {
                    'fields': ('port_graph',),
                    'description': 'Visual representation of open ports detected during the last scan.'
                }),
                ('Timeline & Tracking', {
                    'fields': ('first_seen', 'last_seen', 'last_checked', 'reserved_at')
                }),
                ('Additional Info', {
                    'fields': ('assigned_to', 'description')
                }),
            )
        return super().get_fieldsets(request, obj)

    def get_list_display(self, request):
        default = super().get_list_display(request)
        if not (request.user.is_superuser or request.user.has_perm('network.change_ipaddress')):
            return tuple(f for f in default if f != 'clear_ip_button')
        return default

    form = IPAddressForm
    list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'mac_address', 'os_name', 'usage_reason', 'first_seen', 'last_seen', 'clear_ip_button')
    search_fields = ('ip_address', 'mac_address', 'hostname', 'os_name')
    list_display_links = ('ip_address_display',)
    list_filter = ('status', 'subnet', IsNewIPFilter)
    ordering = ('ip_address_padded',)
    
    readonly_fields = ('last_checked', 'first_seen', 'last_seen', 'vlan_display', 'reserved_at', 'os_name', 'discovery_reason_display', 'status_with_action', 'status_badge_only')
    fieldsets = (
        ('IP Configuration', {
            'fields': ('ip_address', 'subnet', 'vlan_display', 'hostname', 'is_unique_hostname', 'mac_address', 'os_name', 'status_with_action', 'discovery_reason_display')
        }),
        ('Port Analysis', {
            'fields': ('port_graph',),
            'description': 'Visual representation of open ports detected during the last scan.'
        }),
        ('Timeline & Tracking', {
            'fields': ('first_seen', 'last_seen', 'last_checked', 'reserved_at')
        }),
        ('Additional Info', {
            'fields': ('assigned_to', 'description')
        }),
    )
    

        
    actions = ['scan_ips']

    @admin.display(description='Actions')
    def clear_ip_button(self, obj):
        from django.utils.safestring import mark_safe
        buttons = []
        if obj.status == 'available':
            buttons.append('<span style="color: #cbd5e1; padding: 4px 8px;"><i class="fas fa-eraser"></i> Clear</span>')
        else:
            buttons.append(f'<a href="#" onclick="if(confirm(\'Are you sure you want to wipe {obj.ip_address}?\')) window.location.href=\'/admin/network/ipaddress/{obj.id}/clear/\'; return false;" style="color: #ef4444; font-weight: 600; padding: 4px 8px; border: 1px solid #ef4444; border-radius: 4px; display: inline-block; white-space: nowrap;"><i class="fas fa-eraser"></i> Clear Data</a>')
        if obj.status == 'offline':
            buttons.append(f'<a href="/admin/network/ipaddress/{obj.id}/quick-check/" style="color: #f59e0b; font-weight: 600; padding: 4px 8px; border: 1px solid #f59e0b; border-radius: 4px; display: inline-block; white-space: nowrap; margin-left: 5px;"><i class="fas fa-sync-alt"></i> Quick Check</a>')
        return mark_safe(f'<div style="display: flex; gap: 5px;">{" ".join(buttons)}</div>')
    @admin.display(description='Services & Ports Analysis')
    def port_graph(self, obj):
        from django.utils.safestring import mark_safe
        if not obj or not obj.discovery_reason:
            return mark_safe('<div style="padding: 20px; text-align: center; color: #64748b; font-style: italic; background: #f8fafc; border-radius: 12px; border: 1px dashed #cbd5e1;"><i class="fas fa-search" style="font-size: 24px; margin-bottom: 10px; color: #94a3b8; display: block;"></i> No scan data available. Wait for the next discovery cycle.</div>')
            
        reason = obj.discovery_reason
        
        ports = {
            'ICMP_Ping': {'name': 'Network Reachability (Ping)', 'icon': 'fa-network-wired', 'color': '#64748b', 'open': False, 'desc': 'ICMP Echo / Reply'},
            'SSH': {'name': 'Secure Shell (SSH)', 'icon': 'fa-terminal', 'color': '#64748b', 'open': False, 'desc': 'Port 22 / TCP'},
            'HTTP': {'name': 'Web Service (HTTP)', 'icon': 'fa-globe', 'color': '#64748b', 'open': False, 'desc': 'Port 80 / TCP'},
            'HTTPS': {'name': 'Secure Web (HTTPS)', 'icon': 'fa-lock', 'color': '#64748b', 'open': False, 'desc': 'Port 443 / TCP'},
            'RDP': {'name': 'Remote Desktop (RDP)', 'icon': 'fa-desktop', 'color': '#64748b', 'open': False, 'desc': 'Port 3389 / TCP'}
        }
        
        reason_parts = [r.strip() for r in reason.split('|') if r.strip()]
        has_custom = False
        
        for part in reason_parts:
            part_lower = part.lower()
            if 'ping' in part_lower or 'icmp' in part_lower:
                ports['ICMP_Ping']['open'] = True
            elif 'port 22' in part_lower or part_lower == 'ssh':
                ports['SSH']['open'] = True
            elif 'port 80' in part_lower or (part_lower == 'http' and 'https' not in part_lower):
                ports['HTTP']['open'] = True
            elif 'port 443' in part_lower or 'https' in part_lower:
                ports['HTTPS']['open'] = True
            elif 'port 3389' in part_lower or 'rdp' in part_lower:
                ports['RDP']['open'] = True
            elif 'manually' not in part_lower and 'reservation' not in part_lower and 'last seen' not in part_lower:
                # It is a custom port or service
                import re as regex
                has_custom = True
                clean_part = part.replace('Detected via ', '')
                port_match = regex.search(r'\(Port (\d+)\)', clean_part, regex.IGNORECASE)
                
                # If name already contains "(Port X)", use it as name, else append
                name_clean = regex.sub(r'\s*\(Port \d+\)', '', clean_part).strip()
                desc = f"Port {port_match.group(1)} / TCP" if port_match else "Custom Service detected"
                
                ports[f"Custom_{clean_part}"] = {
                    'name': name_clean,
                    'icon': 'fa-layer-group',
                    'color': '#64748b',
                    'open': True,
                    'desc': desc
                }
                
        if not has_custom:
            # If no custom ports were found open, show a generic closed one just to keep the grid even
            ports['Generic_Custom'] = {
                'name': 'Custom Services',
                'icon': 'fa-layer-group',
                'color': '#64748b',
                'open': False,
                'desc': 'No other ports detected'
            }

        html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; padding: 5px;">'
        
        for key, info in ports.items():
            if info['open']:
                bg_color = '#ecfdf5'
                border_color = '#a7f3d0'
                icon_color = '#10b981'
                status_text = 'AVAILABLE'
                pulse = '<span style="position: absolute; top: 12px; right: 12px; width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 0 0 rgba(16, 185, 129, 1); animation: pulse-green 2s infinite;"></span>'
            else:
                bg_color = '#f8fafc'
                border_color = '#e2e8f0'
                icon_color = '#94a3b8'
                status_text = 'CLOSED'
                pulse = '<span style="position: absolute; top: 12px; right: 12px; width: 8px; height: 8px; background: #cbd5e1; border-radius: 50%;"></span>'
                
            html += f"""
            <div style="position: relative; background: {bg_color}; border: 1px solid {border_color}; border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 12px; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                {pulse}
                <div style="width: 42px; height: 42px; border-radius: 10px; background: white; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); color: {icon_color}; font-size: 18px;">
                    <i class="fas {info['icon']}"></i>
                </div>
                <div>
                    <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 2px;">{info['name']}</div>
                    <div style="font-size: 11px; color: #64748b; font-weight: 500; letter-spacing: 0.3px;">{info['desc']} &bull; <span style="color: {icon_color}; font-weight: 700;">{status_text}</span></div>
                </div>
            </div>
            """
            
        html += '</div>'
        html += "\n<style>\n@keyframes pulse-green {\n    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }\n    70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }\n    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }\n}\n</style>\n"
        
        return mark_safe(html)

    clear_ip_button.short_description = "Actions"

    @admin.display(description='Discovery Reason')
    def discovery_reason_display(self, obj):
        from django.utils.safestring import mark_safe
        dr = obj.discovery_reason or ""
        
        if not dr:
            return mark_safe('<span style="color: #94a3b8; font-style: italic;">No discovery data</span>')
            
        if dr.startswith('Manually') or 'Reservation Expired' in dr or dr.startswith('Last seen'):
            return mark_safe(f'<div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 15px; border-radius: 8px; color: #475569; font-weight: 500; display: inline-block;"><i class="fas fa-info-circle" style="color: #64748b; margin-right: 8px;"></i> {dr}</div>')
            
        methods = [m.strip() for m in dr.split('|') if m.strip()]
        badges = []
        for m in methods:
            m = m.replace('Detected via ', '')
            badges.append(f'<div style="display: inline-flex; align-items: center; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); color: #334155; border: 1px solid #cbd5e1; padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; margin-right: 8px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);"><i class="fas fa-satellite-dish" style="margin-right: 8px; color: #3b82f6;"></i>{m}</div>')
            
        return mark_safe('<div style="display: flex; flex-wrap: wrap; align-items: center;">' + ''.join(badges) + '</div>')

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
            
            if dr:
                # Handle multiple methods separated by |
                methods = [m.strip() for m in dr.split('|') if m.strip()]
                if not methods:
                    return dr
                
                badges = []
                for m in methods:
                    # Clean up 'Detected via' if it exists from legacy data
                    m = m.replace('Detected via ', '')
                    badges.append(f'<span style="display: inline-block; background: #e2e8f0; color: #475569; border: 1px solid #cbd5e1; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; margin-right: 4px; margin-bottom: 2px; white-space: nowrap;"><i class="fas fa-satellite-dish" style="margin-right: 3px; opacity: 0.7;"></i>{m}</span>')
                return mark_safe('<div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">' + ''.join(badges) + '</div>')
                
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

    @admin.display(description='Status', ordering='status')
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
        from django.utils.safestring import mark_safe
        from django.utils import timezone
        import datetime
        from network.models import SystemSettings
        
        # Avoid N+1 queries by caching settings briefly for the request/view, or just loading it
        # Since SystemSettings is heavily used, let's just get it. 
        # In SQLite, getting pk=1 254 times is fast, but we can do it faster.
        if not hasattr(self, '_cached_settings'):
            self._cached_settings = SystemSettings.load()
            
        badge = ""
        if obj.first_seen:
            duration_hours = self._cached_settings.new_ip_duration_hours
            if (timezone.now() - obj.first_seen).total_seconds() < duration_hours * 3600:
                badge = ' <span style="background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 8px; vertical-align: text-top; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3); animation: pulse 2s infinite;">NEW</span>'
                
        return format_html('<span style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-weight: 700; font-size: 14px; letter-spacing: 0.5px;">{}</span>{}', obj.ip_address, mark_safe(badge))

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
        if not request.user.has_perm('network.change_ipaddress'):
            base_ro = ('subnet', 'vlan_display', 'discovery_reason_display', 'last_checked', 'status_badge_only', 'first_seen', 'last_seen', 'reserved_at', 'port_graph')
        else:
            base_ro = ('subnet', 'vlan_display', 'discovery_reason_display', 'last_checked', 'status_with_action', 'first_seen', 'last_seen', 'reserved_at', 'port_graph')
        if obj:
            return ('ip_address',) + base_ro
        return base_ro
        
    def change_status_modal_view(self, request, object_id):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.contrib import messages
        from django.utils import timezone

        if not request.user.has_perm('network.change_ipaddress'):
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            messages.error(request, "Permission Denied: You do not have permission to perform this action.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:network_ipaddress_changelist')))
        
        obj = get_object_or_404(self.model, pk=object_id)
        
        if request.method == 'POST':
            new_status = request.POST.get('status')
            hostname = request.POST.get('hostname')
            mac_address = request.POST.get('mac_address')
            os_name = request.POST.get('os_name')
            reason = request.POST.get('discovery_reason')
            
            obj.status = new_status
            obj.hostname = hostname
            obj.mac_address = mac_address
            obj.os_name = os_name
            obj.discovery_reason = reason
            
            if new_status == 'reserved':
                obj.reserved_at = timezone.now()
            elif new_status == 'used':
                if not obj.discovery_reason or obj.discovery_reason.strip() == '':
                    obj.discovery_reason = f"Manually assigned by {request.user.username}"
            
            obj.save()
            messages.success(request, f"Successfully updated IP {obj.ip_address} details.")
            
        return HttpResponseRedirect(reverse('admin:network_ipaddress_change', args=[object_id]))


    @admin.display(description='Status')
    def status_badge_only(self, obj):
        from django.utils.safestring import mark_safe
        status_colors = {
            'available': ('#10b981', '#d1fae5'),
            'used': ('#ef4444', '#fee2e2'),
            'reserved': ('#f59e0b', '#fef3c7'),
            'offline': ('#64748b', '#f1f5f9'),
        }
        color, bg = status_colors.get(obj.status, ('#64748b', '#f1f5f9'))
        label = dict(obj.STATUS_CHOICES).get(obj.status, obj.status)
        return mark_safe(f'<span style="background: {bg}; color: {color}; border: 1px solid {color}40; padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 13px;">{label}</span>')

    @admin.display(description='Status & Actions')

    def status_with_action(self, obj):
        from django.utils.safestring import mark_safe
        status_colors = {
            'available': ('#10b981', '#d1fae5'),
            'used': ('#ef4444', '#fee2e2'),
            'reserved': ('#f59e0b', '#fef3c7'),
            'offline': ('#64748b', '#f1f5f9'),
        }
        color, bg = status_colors.get(obj.status, ('#64748b', '#f1f5f9'))
        label = dict(obj.STATUS_CHOICES).get(obj.status, obj.status)
        
        def esc(s):
            if not s:
                return ""
            return str(s).replace("'", "\\'").replace('"', '&quot;').replace("\n", " ").replace("\r", " ")
            
        html = f'''
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="background: {bg}; color: {color}; border: 1px solid {color}40; padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 13px;">{label}</span>
            <button type="button" onclick="openStatusModal({obj.id}, \'{obj.ip_address}\', \'{obj.status}\', \'{esc(obj.hostname)}\', \'{esc(obj.mac_address)}\', \'{esc(obj.os_name)}\', \'{esc(obj.discovery_reason)}\')" class="btn btn-sm btn-outline-primary" style="border-radius: 8px; font-weight: 600; padding: 6px 14px; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);"><i class="fas fa-edit" style="margin-right: 6px;"></i> Change Details</button>
        </div>
        '''
        return mark_safe(html)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('api/check-hostname/', self.admin_site.admin_view(self.check_hostname_api), name='network_ipaddress_check_hostname'),
            path('<int:ip_id>/clear/', self.admin_site.admin_view(self.clear_ip_view), name='clear-ip'),
            path('<int:ip_id>/quick-check/', self.admin_site.admin_view(self.quick_check_view), name='quick-check-ip'),
            path('<int:object_id>/change-status-modal/', self.admin_site.admin_view(self.change_status_modal_view), name='ipaddress_change_status_modal'),
        ]
        return custom_urls + urls

    def quick_check_view(self, request, ip_id):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponseRedirect
        from django.contrib import messages
        from django.urls import reverse
        from .models import IPAddress
        from .utils import perform_ip_discovery

        if not request.user.has_perm('network.change_ipaddress'):
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            messages.error(request, "Permission Denied: You do not have permission to perform this action.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:network_ipaddress_changelist')))
        
        ip = get_object_or_404(IPAddress, id=ip_id)
        if ip.status == 'offline':
            perform_ip_discovery(IPAddress.objects.filter(id=ip_id))
            ip.refresh_from_db()
            if ip.status == 'used':
                messages.success(request, f"{ip.ip_address} is now ONLINE!")
            else:
                messages.warning(request, f"{ip.ip_address} is still offline.")
                
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return HttpResponseRedirect(referer)
        return HttpResponseRedirect(reverse('admin:network_ipaddress_changelist'))
        
    def clear_ip_view(self, request, ip_id):
        from django.shortcuts import get_object_or_404
        from django.http import HttpResponseRedirect
        from django.contrib import messages
        from .models import IPAddress, AuditLog

        if not request.user.has_perm('network.change_ipaddress'):
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            messages.error(request, "Permission Denied: You do not have permission to perform this action.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:network_ipaddress_changelist')))
        
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
        allowed_keys = {'p', 'o', 'e'}
        request_keys = set(request.GET.keys())
        
        if not request_keys - allowed_keys:
            # If no subnet or other filters are selected, render the subnet selector page
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
            from .models import SystemSettings
            settings = SystemSettings.load()
            if settings.auto_assign_ips:
                self.fields['subnet'].label_from_instance = lambda obj: f'{obj.network_address} ({obj.name})' if obj.enable_auto_assign else f'❌ {obj.network_address} ({obj.name}) - AUTO-ASSIGN DISABLED'
            else:
                self.fields['subnet'].label_from_instance = lambda obj: f"{obj.network_address} ({obj.name})"

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


    @admin.display(description='Network Information')
    def network_details(self, obj):
        from django.utils.safestring import mark_safe
        if obj.status == 'approved' and obj.subnet and obj.assigned_ip:
            gw = obj.subnet.gateway or 'Not Configured'
            net = obj.subnet.network_address
            return mark_safe(f'''
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 15px; border-radius: 8px; margin-top: 5px;">
                <h4 style="margin-top: 0; color: #166534; font-size: 14px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;"><i class="fas fa-network-wired"></i> Assigned Network Details</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #dcfce7;"><strong style="color: #15803d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">Assigned IP Address</strong><span style="color: #166534; font-weight: 700; font-size: 15px;">{obj.assigned_ip.ip_address}</span></div>
                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #dcfce7;"><strong style="color: #15803d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">Gateway</strong><span style="color: #166534; font-weight: 700; font-size: 15px;">{gw}</span></div>
                    <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #dcfce7; grid-column: 1 / -1;"><strong style="color: #15803d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">Subnet Network</strong><span style="color: #166534; font-weight: 700; font-size: 15px;">{net}</span></div>
                </div>
            </div>
            ''')
        return "Network details will be provided here once the request is approved."

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name__in=['Administrator', 'Manager', 'Operator', 'ReadOnly']).exists() or request.user.has_perm('network.change_iprequest'):
            return qs
        return qs.filter(user=request.user)

    def get_readonly_fields(self, request, obj=None):
        base_readonly = ['user', 'requested_at', 'client_ip', 'user_agent', 'user_total_requests', 'network_details']
        if not (request.user.is_superuser or request.user.groups.filter(name__in=['Administrator', 'Manager', 'Operator']).exists() or request.user.has_perm('network.change_iprequest')):
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
                ('Admin Action', {'fields': ('subnet', 'hostname', 'reason', 'status', 'assigned_ip', 'admin_comment', 'network_details')}),
            )
        else:
            if obj:
                return (
                    ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
                    ('Admin Response', {'fields': ('status', 'assigned_ip', 'admin_comment', 'network_details')}),
                )
            return (
                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
            )

    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if not obj.pk:
            if not getattr(obj, 'user', None):
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
            path('api/pending-count/', self.admin_site.admin_view(self.pending_count_api), name='network_iprequest_pending_count'),
            path('api/subnet-map/<int:subnet_id>/', self.admin_site.admin_view(self.subnet_map_api), name='network_iprequest_subnet_map'),
        ]
        return custom_urls + urls

    def subnet_map_api(self, request, subnet_id):
        from django.http import JsonResponse
        from .models import IPAddress
        ips = IPAddress.objects.filter(subnet_id=subnet_id).order_by('ip_address_padded')
        data = [{'id': ip.id, 'ip': ip.ip_address, 'status': ip.status} for ip in ips]
        return JsonResponse({'ips': data})

    
    def pending_count_api(self, request):
        from django.http import JsonResponse
        from .models import IPRequest
        count = IPRequest.objects.filter(status='pending').count()
        return JsonResponse({'count': count})

    def process_request_view(self, request, request_id):
        req = IPRequest.objects.get(id=request_id)
        return TemplateResponse(request, 'admin/network/iprequest/process.html', {'req': req})

    def auto_assign_api(self, request, request_id):
        import time, ipaddress
        from .models import IPAddress, AuditLog
        from .utils import perform_discovery
        
        req = IPRequest.objects.get(id=request_id)
        
        # Perform fresh scan of the subnet to prevent assigning stale IPs
        if req.subnet:
            try:
                perform_discovery(req.subnet)
            except Exception as e:
                pass # Continue even if scan fails for some reason
        
        time.sleep(1) # Tiny pause for UX
        
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
            
            return JsonResponse({
                'status': 'success', 
                'ip': available_ip.ip_address,
                'gateway': available_ip.subnet.gateway or 'Not Configured',
                'network': available_ip.subnet.network_address
            })
        else:
            req.admin_comment = "Auto-assignment failed: No available IPs in subnet or range."
            req.save()
            return JsonResponse({'status': 'error', 'message': 'No available IPs in the auto-assign range. Your request is pending admin approval.'})

from .models import AuditLog
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    change_list_template = "admin/network/auditlog/change_list.html"
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
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('clear-badges/', self.admin_site.admin_view(self.clear_badges_view), name='systemsettings_clear_badges'),
            path('clear-logs/', self.admin_site.admin_view(self.clear_logs_view), name='systemsettings_clear_logs'),
        ]
        return custom_urls + urls

    def clear_badges_view(self, request):
        from network.models import IPAddress

        if not request.user.has_perm('network.change_systemsettings'):
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            messages.error(request, "Permission Denied: You do not have permission to perform this action.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:network_systemsettings_changelist')))
        import datetime
        from django.utils import timezone
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        IPAddress.objects.filter(first_seen__isnull=False).update(first_seen=timezone.now() - datetime.timedelta(days=365))
        messages.success(request, "All 'New' badges have been cleared successfully.")
        return HttpResponseRedirect(reverse('admin:network_systemsettings_change', args=[1]))

    def clear_logs_view(self, request):
        from network.models import AuditLog
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        if not request.user.has_perm('network.change_systemsettings'):
            from django.contrib import messages
            from django.http import HttpResponseRedirect
            from django.urls import reverse
            messages.error(request, "Permission Denied: You do not have permission to perform this action.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:network_systemsettings_changelist')))
        count, _ = AuditLog.objects.all().delete()
        messages.success(request, f"Successfully cleared {count} monitoring logs.")
        return HttpResponseRedirect(reverse('admin:network_systemsettings_change', args=[1]))

    @admin.display(description="Clear All 'New' Badges")
    def action_clear_badges(self, obj):
        from django.utils.safestring import mark_safe
        from django.urls import reverse
        url = reverse('admin:systemsettings_clear_badges')
        return mark_safe(f'<a href="{url}" class="btn btn-outline-danger" style="border-radius: 8px; font-weight: 600; padding: 6px 12px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;" onclick="return confirm(\'Are you sure you want to clear all New badges?\');"><i class="fas fa-eraser"></i> Clear Badges</a>')

    @admin.display(description="Clear All Monitoring Logs")
    def action_clear_logs(self, obj):
        from django.utils.safestring import mark_safe
        from django.urls import reverse
        url = reverse('admin:systemsettings_clear_logs')
        return mark_safe(f'<a href="{url}" class="btn btn-outline-danger" style="border-radius: 8px; font-weight: 600; padding: 6px 12px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;" onclick="return confirm(\'Are you sure you want to delete ALL monitoring logs?\');"><i class="fas fa-trash-alt"></i> Delete Logs</a>')

    fieldsets = (
        ('UI & Theming', {
            'fields': ('theme', 'custom_logo')
        }),
        ('Automation & Provisioning', {
            'fields': ('auto_assign_ips', 'enable_reservation', 'reservation_timeout_hours', 'offline_timeout_hours', 'new_ip_duration_hours', 'clear_all_new_ips', 'monitoring_retention_days', 'clear_monitoring_logs'),
            'description': 'Manage background automation, timeouts, and IP status behaviors.'
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
    readonly_fields = ('action_clear_badges', 'action_clear_logs')
    def get_fieldsets(self, request, obj=None):
        from django.utils import timezone
        current_time = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
        from django.utils.safestring import mark_safe
        return (
            ('Server Configuration', {
                'fields': (
                    'server_port', 'enable_ssl', 'ssl_cert_path', 'ssl_key_path'
                ),
                'description': mark_safe('<div style="background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%); border: 1px solid #fecdd3; border-left: 4px solid #e11d48; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(225, 29, 72, 0.05); display: flex; align-items: flex-start; gap: 18px;"><div style="background: white; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); flex-shrink: 0;"><i class="fas fa-server" style="color: #e11d48; font-size: 24px;"></i></div><div><h4 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px; letter-spacing: -0.01em;">Core Server & SSL Setup</h4><p style="margin: 0; font-size: 13.5px; color: #64748b; font-weight: 500; line-height: 1.5;">Manage the core port and SSL certificates for the background service. <strong style="color:#e11d48;">Note:</strong> Changes here require a manual restart of the backend service to take effect.</p></div></div>')
            }),
            ('UI & Theming', {
                'fields': ('theme', 'custom_logo'),
                'description': mark_safe('<div style="background: linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%); border: 1px solid #fbcfe8; border-left: 4px solid #c026d3; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(192, 38, 211, 0.05); display: flex; align-items: flex-start; gap: 18px;"><div style="background: white; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); flex-shrink: 0;"><i class="fas fa-paint-roller" style="color: #c026d3; font-size: 22px;"></i></div><div><h4 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px; letter-spacing: -0.01em;">Interface & Branding</h4><p style="margin: 0; font-size: 13.5px; color: #64748b; font-weight: 500; line-height: 1.5;">Customize the visual appearance of the IPAM dashboard. Select from multiple built-in dark and light themes, and upload your own corporate logo. Changes apply instantly.</p></div></div>')
            }),
            ('Alert Policies & Events', {
                'fields': (
                    'alert_on_subnet_full', 'alert_on_critical_offline',
                    'alert_on_any_offline', 'alert_on_new_ip_request', 
                    'alert_on_ip_in_use',
                    'alert_on_new_ip_discovered', 'alert_on_disk_full',
                    'alert_on_cpu_high', 'alert_on_memory_high',
                    'alert_on_failed_login'
                ),
                'description': mark_safe('<div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 1px solid #fecaca; border-left: 4px solid #ef4444; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(239, 68, 68, 0.05); display: flex; align-items: flex-start; gap: 18px;"><div style="background: white; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); flex-shrink: 0;"><i class="fas fa-bell" style="color: #ef4444; font-size: 24px;"></i></div><div><h4 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px; letter-spacing: -0.01em;">Alert Policies & Triggers</h4><p style="margin: 0; font-size: 13.5px; color: #64748b; font-weight: 500; line-height: 1.5;">Select which system events and thresholds should trigger an alert. Notifications will be sent via all enabled channels (Telegram, Mattermost, SMS).</p></div></div>')
            }),
            ('Alerting (Telegram)', {
                'fields': (
                    'alert_telegram',
                    'telegram_bot_token', 'telegram_chat_id'
                ),
                'description': mark_safe('<div style="background: #eff6ff; border: 1px solid #bfdbfe; border-left: 4px solid #3b82f6; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.05); display: flex; align-items: center; gap: 15px;"><div style="background: white; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><i class="fab fa-telegram-plane" style="color: #3b82f6; font-size: 24px;"></i></div><div><h4 style="margin: 0; font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 3px;">Telegram Bot API</h4><p style="margin: 0; font-size: 13px; color: #64748b; font-weight: 500;">Configure a bot to receive real-time IPAM alerts directly to your phone.</p></div></div>')
            }),
            ('Alerting (Mattermost)', {
                'fields': ('alert_mattermost', 'mattermost_webhook_url'),
                'description': mark_safe('<div style="background: #fdf4ff; border: 1px solid #fbcfe8; border-left: 4px solid #d946ef; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(217, 70, 239, 0.05); display: flex; align-items: center; gap: 15px;"><div style="background: white; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><i class="fas fa-hashtag" style="color: #d946ef; font-size: 24px;"></i></div><div><h4 style="margin: 0; font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 3px;">Mattermost Webhooks</h4><p style="margin: 0; font-size: 13px; color: #64748b; font-weight: 500;">Send automated notifications to your Mattermost team channels.</p></div></div>')
            }),
            ('Alerting (SMS Gateway)', {
                'fields': ('alert_sms', 'sms_webhook_url', 'sms_payload_template'),
                'description': mark_safe('<div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #22c55e; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(34, 197, 94, 0.05); display: flex; align-items: center; gap: 15px;"><div style="background: white; width: 45px; height: 45px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><i class="fas fa-sms" style="color: #22c55e; font-size: 22px;"></i></div><div><h4 style="margin: 0; font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 3px;">SMS Provider (Webhook)</h4><p style="margin: 0; font-size: 13px; color: #64748b; font-weight: 500;">Connect to Kavenegar, FarazSMS, or any generic HTTP SMS gateway. Use <code>{message}</code> in your JSON payload.</p></div></div>')
            }),
            ('Automation & Provisioning', {
                'fields': (
                    'auto_assign_ips', 'enable_reservation', 
                    'reservation_timeout_hours', 'offline_timeout_hours', 
                    'new_ip_duration_hours', 'monitoring_retention_days', 
                    'action_clear_badges', 'action_clear_logs'
                ),
                'description': mark_safe('<div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 1px solid #e2e8f0; border-left: 4px solid #6366f1; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(99, 102, 241, 0.05); display: flex; align-items: flex-start; gap: 18px;"><div style="background: white; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); flex-shrink: 0;"><i class="fas fa-robot" style="color: #6366f1; font-size: 24px;"></i></div><div><h4 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px; letter-spacing: -0.01em;">Automation Engine & Lifecycle Rules</h4><p style="margin: 0; font-size: 13.5px; color: #64748b; font-weight: 500; line-height: 1.5;">Configure how the system automatically provisions new IPs, recycles offline servers, and manages data retention. These rules run continuously in the background to keep your network state perfectly accurate.</p></div></div>')
            }),
            ('System Time', {
                'fields': (
                    'timezone', 'time_sync_mode', 'manual_time', 'ntp_server'
                ),
                'description': mark_safe(f'<div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 1px solid #fde68a; border-left: 4px solid #d97706; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(217, 119, 6, 0.05); display: flex; align-items: flex-start; gap: 18px;"><div style="background: white; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); flex-shrink: 0;"><i class="fas fa-clock" style="color: #d97706; font-size: 24px;"></i></div><div style="flex-grow: 1;"><h4 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px; letter-spacing: -0.01em;">Time Synchronization</h4><p style="margin: 0; font-size: 13.5px; color: #64748b; font-weight: 500; line-height: 1.5; margin-bottom: 12px;">Ensure all your IP discovery logs and audit trails have the correct timestamps. You can sync with the host OS, specify an NTP server, or enter time manually.</p><div style="background: white; border: 1px dashed #fcd34d; padding: 8px 15px; border-radius: 8px; display: inline-block;"><span style="color: #92400e; font-weight: 600; font-size: 13px;"><i class="fas fa-stopwatch" style="margin-right: 6px;"></i>Live System Time:</span> <span id="live-system-time" style="font-family: monospace; font-size: 14px; font-weight: 700; color: #1e293b; margin-left: 8px;">{current_time}</span></div></div></div>')
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





































from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    class Media:
        css = {
            'all': ('css/hide_password_text.css',)
        }
    
    readonly_fields = ('last_login', 'date_joined')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return (
            (None, {'fields': ('username', 'password')}),
            ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
            ('Permissions', {
                'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            }),
            ('Important dates', {'fields': ('last_login', 'date_joined')}),
        )

    # In Django, 'password' field in fieldsets automatically shows the reset password link
    # But to hide the raw hash text, we can use a custom form or just rely on Django's default 
    # UserAdmin behavior which ONLY shows the 'Raw passwords are not stored...' string.
    # To truly hide the raw hash and only show the link, we can modify the password field's readonly display.

from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(BaseGroupAdmin):
    class Media:
        css = {
            'all': ('css/modern_filter_horizontal.css',)
        }
