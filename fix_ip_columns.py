import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update list_display
content = content.replace("list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'discovery_reason', 'assigned_to', 'last_checked')", "list_display = ('ip_address_display', 'hostname', 'subnet', 'vlan_id_display', 'status_badge', 'discovery_reason', 'first_seen', 'last_seen')")

# Update fieldsets
old_fs = '''    fieldsets = (
        ('IP Configuration', {
            'fields': ('ip_address', 'subnet', 'vlan_display', 'hostname', 'is_unique_hostname', 'mac_address', 'status', 'discovery_reason', 'last_checked')
        }),
        ('Additional Info', {
            'fields': ('assigned_to', 'description')
        }),
    )'''

new_fs = '''    readonly_fields = ('last_checked', 'first_seen', 'last_seen', 'vlan_display')
    fieldsets = (
        ('IP Configuration', {
            'fields': ('ip_address', 'subnet', 'vlan_display', 'hostname', 'is_unique_hostname', 'mac_address', 'status', 'discovery_reason')
        }),
        ('Timeline & Tracking', {
            'fields': ('first_seen', 'last_seen', 'last_checked')
        }),
        ('Additional Info', {
            'fields': ('assigned_to', 'description')
        }),
    )'''

content = content.replace(old_fs, new_fs)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
