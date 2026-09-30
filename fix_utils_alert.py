import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add to perform_discovery at the end of subnet loop
old_audit_log = '''        AuditLog.objects.create(
            action='SCAN',
            model_name='Subnet',
            message=f"Discovery scan executed for subnet {subnet.name} ({subnet.network_address})"
        )'''

new_audit_log = '''        AuditLog.objects.create(
            action='SCAN',
            model_name='Subnet',
            message=f"Discovery scan executed for subnet {subnet.name} ({subnet.network_address})"
        )
        
        if settings.alert_on_subnet_full:
            total = subnet.ips.count()
            used = subnet.ips.filter(status='used').count()
            if total > 0 and (used / total) >= 0.9:
                from .alerts import send_telegram_alert
                send_telegram_alert(f"⚠️ *Subnet Almost Full*\n\nSubnet {subnet.network_address} is {int(used/total*100)}% full ({used}/{total} used).")
'''

content = content.replace(old_audit_log, new_audit_log)

# Add to offline critical alert
old_offline_update = '''                ip_obj.last_offline_at = timezone.now()
                prev_reason = ip_obj.discovery_reason'''

new_offline_update = '''                ip_obj.last_offline_at = timezone.now()
                if settings.alert_on_critical_offline and ip_obj.discovery_reason and 'Manually' in ip_obj.discovery_reason:
                    from .alerts import send_telegram_alert
                    send_telegram_alert(f"🔴 *Critical IP Offline*\n\nManually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline.")
                prev_reason = ip_obj.discovery_reason'''

content = content.replace(old_offline_update, new_offline_update)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
