import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix get_readonly_fields
ro_code = '''    def get_readonly_fields(self, request, obj=None):
        base_readonly = ['requested_at', 'client_ip', 'user_agent', 'user_total_requests']
        if not (request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists()):
            if obj:
                return base_readonly + ['status', 'assigned_ip', 'admin_comment']
        return base_readonly'''

# Replace the static readonly_fields definition
content = re.sub(r"    readonly_fields = \('requested_at', 'client_ip', 'user_agent', 'user_total_requests'\)", ro_code, content)

# Fix get_fieldsets
old_fs = '''    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists():
            return (
                ('Request Details', {'fields': ('requested_at', 'client_ip', 'user_agent', 'user', 'user_total_requests')}),
                ('Admin Action', {'fields': ('subnet', 'hostname', 'reason', 'status', 'assigned_ip', 'admin_comment')}),
            )
        else:
            return (
                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
            )'''

new_fs = '''    def get_fieldsets(self, request, obj=None):
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
            )'''

content = content.replace(old_fs, new_fs)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
