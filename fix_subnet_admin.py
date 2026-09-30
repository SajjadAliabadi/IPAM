import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace list_display
content = content.replace("list_display = ('network_address', 'name', 'gateway', 'vlan', 'department')", "list_display = ('network_address', 'name', 'gateway', 'vlan', 'department', 'auto_assign_display')")

# Add auto_assign_display method inside SubnetAdmin
method_code = '''    def auto_assign_display(self, obj):
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

    actions = ['scan_subnet']'''

content = content.replace("    actions = ['scan_subnet']", method_code)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
