import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the get_fieldsets for SystemSettingsAdmin completely
old_get_fieldsets = '''    def get_fieldsets(self, request, obj=None):
        from django.utils import timezone
        current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        from django.utils.safestring import mark_safe
        return (
            ('Display Settings', {
                'fields': ('theme',),
                'description': 'Choose a responsive UI theme. Changes apply immediately upon save.'
            }),
            ('Offline Timeout (IP Recycling)', {
                'fields': ('offline_timeout_hours',),
                'description': 'When a server goes offline, its IP turns Gray. It will not be assigned to new requests until this timeout expires.'
            }),
            ('Automation & Provisioning', {
                'fields': ('auto_assign_ips', 'enable_reservation', 'reservation_timeout_hours'),
                'description': 'Configure automatic IP allocation and reservation settings.'
            }),
            ('System Time', {
                'fields': ('timezone', 'time_sync_mode', 'manual_time', 'ntp_server'),
                'description': mark_safe(f'Configure time synchronization and timezone.<br><br><b>Current System Time:</b> {current_time}')
            }),
        )'''

new_get_fieldsets = '''    def get_fieldsets(self, request, obj=None):
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
        )'''

content = content.replace(old_get_fieldsets, new_get_fieldsets)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
