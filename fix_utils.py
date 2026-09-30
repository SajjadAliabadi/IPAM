import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_discovery = '''        for ip_str, final_status, reason in results:
            ip_obj, created = IPAddress.objects.get_or_create(
                ip_address=ip_str,
                defaults={'subnet': subnet, 'status': final_status, 'discovery_reason': reason}
            )
            
            if final_status == 'used':
                ip_obj.last_offline_at = None
                ip_obj.discovery_reason = reason
                if ip_obj.status != 'used':
                    ip_obj.status = 'used'
                    ip_obj.save()
            else:
                if ip_obj.status == 'used':
                    ip_obj.status = 'offline'
                    ip_obj.last_offline_at = timezone.now()
                    prev_reason = ip_obj.discovery_reason
                    method_str = prev_reason.replace('Detected via ', '') if prev_reason else 'Unknown Method'
                    time_str = timezone.now().strftime('%Y-%m-%d %H:%M')
                    ip_obj.discovery_reason = f"Last seen on {time_str} via {method_str}"
                    ip_obj.save()
                elif ip_obj.status == 'offline':
                    if ip_obj.last_offline_at:
                        delta = timezone.now() - ip_obj.last_offline_at
                        if delta.total_seconds() / 3600 >= settings.offline_timeout_hours:
                            ip_obj.status = 'available'
                            ip_obj.last_offline_at = None
                            ip_obj.save()
                elif ip_obj.status == 'reserved':
                    pass
                else:
                    if ip_obj.status != 'available':
                        ip_obj.status = 'available'
                        ip_obj.save()'''

new_discovery = '''        for ip_str, final_status, reason in results:
            ip_obj, created = IPAddress.objects.get_or_create(
                ip_address=ip_str,
                defaults={'subnet': subnet, 'status': final_status, 'discovery_reason': reason}
            )
            
            # Update first_seen/last_seen if it's currently online
            needs_save = False
            if final_status == 'used':
                if not ip_obj.first_seen:
                    ip_obj.first_seen = timezone.now()
                ip_obj.last_seen = timezone.now()
                ip_obj.last_offline_at = None
                ip_obj.discovery_reason = reason
                ip_obj.status = 'used'
                needs_save = True
            else:
                if ip_obj.status == 'used':
                    ip_obj.status = 'offline'
                    ip_obj.last_offline_at = timezone.now()
                    prev_reason = ip_obj.discovery_reason
                    method_str = prev_reason.replace('Detected via ', '') if prev_reason else 'Unknown Method'
                    time_str = timezone.now().strftime('%Y-%m-%d %H:%M')
                    ip_obj.discovery_reason = f"Last seen on {time_str} via {method_str}"
                    needs_save = True
                elif ip_obj.status == 'offline':
                    if ip_obj.last_offline_at:
                        delta = timezone.now() - ip_obj.last_offline_at
                        if delta.total_seconds() / 3600 >= settings.offline_timeout_hours:
                            ip_obj.status = 'available'
                            ip_obj.last_offline_at = None
                            needs_save = True
                elif ip_obj.status == 'reserved':
                    pass
                else:
                    if ip_obj.status != 'available':
                        ip_obj.status = 'available'
                        needs_save = True
            
            # Force last_checked to update by saving if there's any change
            # Actually, to update last_checked even if no status change, we can just save it.
            ip_obj.save()'''

content = content.replace(old_discovery, new_discovery)

old_ip_disc = '''        old_status = ip_obj.status
        if is_used:
            ip_obj.last_offline_at = None
            ip_obj.discovery_reason = reason
            ip_obj.status = 'used'
        else:
            if old_status == 'used':
                ip_obj.status = 'offline'
                ip_obj.last_offline_at = timezone.now()
                ip_obj.discovery_reason = ''
            elif old_status == 'offline':
                if ip_obj.last_offline_at:
                    delta = timezone.now() - ip_obj.last_offline_at
                    if delta.total_seconds() / 3600 >= settings.offline_timeout_hours:
                        ip_obj.status = 'available'
                        ip_obj.last_offline_at = None
            elif old_status == 'reserved':
                pass
            else:
                ip_obj.status = 'available'
                ip_obj.discovery_reason = ''

        # Force update last_checked
        ip_obj.last_checked = timezone.now()
        ip_obj.save()'''

new_ip_disc = '''        old_status = ip_obj.status
        if is_used:
            if not ip_obj.first_seen:
                ip_obj.first_seen = timezone.now()
            ip_obj.last_seen = timezone.now()
            ip_obj.last_offline_at = None
            ip_obj.discovery_reason = reason
            ip_obj.status = 'used'
        else:
            if old_status == 'used':
                ip_obj.status = 'offline'
                ip_obj.last_offline_at = timezone.now()
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
                pass
            else:
                ip_obj.status = 'available'

        # Force update last_checked
        ip_obj.last_checked = timezone.now()
        ip_obj.save()'''

content = content.replace(old_ip_disc, new_ip_disc)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
