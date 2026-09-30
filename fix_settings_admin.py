import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace get_fieldsets in SystemSettingsAdmin
old_fs = '''            ('Automation & Provisioning', {
                'fields': ('auto_assign_ips',),
                'description': 'Enable or disable automatic IP assignment for the whole system.'
            }),'''

new_fs = '''            ('Automation & Provisioning', {
                'fields': ('auto_assign_ips', 'enable_reservation', 'reservation_timeout_hours'),
                'description': 'Configure automatic IP allocation and reservation settings.'
            }),'''

content = content.replace(old_fs, new_fs)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
