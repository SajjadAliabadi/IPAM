import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace get_fieldsets and save_model in IPRequestAdmin
old_code_block = '''    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists():
            return (
                ('Request Details', {'fields': ('user', 'hostname', 'subnet', 'reason')}),
                ('Admin Action', {'fields': ('status', 'assigned_ip', 'admin_comment')}),
            )
        else:
            return (
                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
            )

    def save_model(self, request, obj, form, change):
        if not obj.pk and not (request.user.is_superuser or request.user.groups.filter(name='Network Operators').exists()):
            obj.user = request.user
        super().save_model(request, obj, form, change)'''

new_code_block = '''    readonly_fields = ('requested_at', 'client_ip', 'user_agent', 'user_total_requests')

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
            return (
                ('IP Request', {'fields': ('subnet', 'hostname', 'reason')}),
            )

    def save_model(self, request, obj, form, change):
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

# Using string replace, it should be exact match
content = content.replace(old_code_block, new_code_block)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
