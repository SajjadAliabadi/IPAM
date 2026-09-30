import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace admin.ModelAdmin with ImportExportModelAdmin
content = content.replace("class SubnetAdmin(admin.ModelAdmin):", "from import_export.admin import ImportExportModelAdmin\nclass SubnetAdmin(ImportExportModelAdmin):")
content = content.replace("class IPAddressAdmin(admin.ModelAdmin):", "from import_export.admin import ImportExportModelAdmin\nclass IPAddressAdmin(ImportExportModelAdmin):")
content = content.replace("class VlanAdmin(admin.ModelAdmin):", "from import_export.admin import ImportExportModelAdmin\nclass VlanAdmin(ImportExportModelAdmin):")

# Update SystemSettingsAdmin fieldsets
old_sys_admin = '''@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):'''

new_sys_admin = '''@admin.register(SystemSettings)
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

    def save_model(self, request, obj, form, change):'''

content = content.replace(old_sys_admin, new_sys_admin)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
