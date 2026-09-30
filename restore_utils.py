import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We know the destruction happened right after:
# if total > 0 and (used / total) >= 0.9:
#     from .alerts import send_telegram_alert

prefix = content.split("if total > 0 and (used / total) >= 0.9:")[0]

suffix = '''if total > 0 and (used / total) >= 0.9:
                from .alerts import send_telegram_alert
                send_telegram_alert(f"Subnet Almost Full: {subnet.network_address} is {int(used/total*100)}% full.")

def perform_ip_discovery(ips_queryset):
    from django.utils import timezone
    from .models import SystemSettings, IPAddress, CheckMethod
    settings = SystemSettings.load()

    for ip_obj in ips_queryset:
        subnet = ip_obj.subnet
        methods = list(subnet.check_methods.filter(is_active=True))
        if not methods:
            methods = list(CheckMethod.objects.filter(is_active=True))

        ip_str = ip_obj.ip_address
        is_used = False
        reason = ''
        
        for method in methods:
            if method.protocol == 'icmp':
                is_used = ping_host(ip_str)
            elif method.protocol == 'tcp_port':
                is_used = check_tcp_port(ip_str, method.custom_port)
            elif method.protocol == 'custom' and method.script_content:
                is_used = run_custom_script(ip_str, method.script_content)

            if is_used:
                reason = f"Detected via {method.name} ({method.get_protocol_display()})"
                if method.protocol == 'tcp_port':
                    reason += f" Port {method.custom_port}"
                break 

        old_status = ip_obj.status
        if is_used:
            if not ip_obj.first_seen:
                ip_obj.first_seen = timezone.now()
            ip_obj.last_seen = timezone.now()
            ip_obj.last_offline_at = None
            ip_obj.discovery_reason = reason
            ip_obj.status = 'used'
            ip_obj.reserved_at = None
        else:
            if old_status == 'used':
                ip_obj.status = 'offline'
                ip_obj.last_offline_at = timezone.now()
                if settings.alert_on_critical_offline and ip_obj.discovery_reason and 'Manually' in ip_obj.discovery_reason:
                    from .alerts import send_telegram_alert
                    send_telegram_alert(f"Critical IP Offline: Manually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline.")
                prev_reason = ip_obj.discovery_reason
                method_str = prev_reason.replace('Detected via ', '') if prev_reason else 'Unknown Method'
                time_str = timezone.now().strftime('%Y-%m-%d %H:%M')
                ip_obj.discovery_reason = f"Last seen on {time_str} via {method_str}"
            elif old_status == 'offline':
                if ip_obj.last_offline_at:
                    delta = timezone.now() - ip_obj.last_offline_at
                    if delta.total_seconds() / 3600 >= settings.offline_timeout_hours:
                        ip_obj.status = 'available'
                        ip_obj.last_offline_at = None
            elif old_status == 'reserved':
                if ip_obj.reserved_at:
                    delta = timezone.now() - ip_obj.reserved_at
                    if delta.total_seconds() / 3600 >= settings.reservation_timeout_hours:
                        ip_obj.status = 'available'
                        ip_obj.reserved_at = None
                        ip_obj.assigned_to = None
                        ip_obj.hostname = ''
                        ip_obj.discovery_reason = "Reservation Expired (Auto-released)"
                        from .models import AuditLog
                        AuditLog.objects.create(
                            action='SYSTEM',
                            model_name='IPAddress',
                            message=f"Reservation expired for {ip_obj.ip_address}. Automatically released back to pool."
                        )
            else:
                ip_obj.status = 'available'

        ip_obj.last_checked = timezone.now()
        ip_obj.save()
'''

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(prefix + suffix)

print('Done')
