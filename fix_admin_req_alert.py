import re

with open('network/admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_req_add = '''        AuditLog.objects.create(user=request.user, action='CREATE', model_name='IPRequest', message=f"IP requested for {obj.hostname}")

        if settings.auto_assign_ips and obj.status == 'pending':'''

new_req_add = '''        AuditLog.objects.create(user=request.user, action='CREATE', model_name='IPRequest', message=f"IP requested for {obj.hostname}")
        
        try:
            from .alerts import send_telegram_alert
            send_telegram_alert(f"📨 *New IP Request*\n\nUser {obj.user.username if obj.user else 'System'} requested an IP for hostname {obj.hostname}.")
        except: pass

        if settings.auto_assign_ips and obj.status == 'pending':'''

content = content.replace(old_req_add, new_req_add)

with open('network/admin.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
