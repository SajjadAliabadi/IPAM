import re

with open('network/utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add AuditLog for reservation expiration in perform_discovery
old_expire_1 = '''                            ip_obj.status = 'available'
                            ip_obj.reserved_at = None
                            ip_obj.assigned_to = None
                            ip_obj.hostname = ''
                            ip_obj.discovery_reason = "Reservation Expired (Auto-released)"
                            needs_save = True'''
new_expire_1 = '''                            ip_obj.status = 'available'
                            ip_obj.reserved_at = None
                            ip_obj.assigned_to = None
                            ip_obj.hostname = ''
                            ip_obj.discovery_reason = "Reservation Expired (Auto-released)"
                            needs_save = True
                            AuditLog.objects.create(
                                action='SYSTEM',
                                model_name='IPAddress',
                                message=f"Reservation expired for {ip_obj.ip_address}. Automatically released back to pool."
                            )'''
content = content.replace(old_expire_1, new_expire_1)

# Add AuditLog for reservation expiration in perform_ip_discovery
old_expire_2 = '''                        ip_obj.status = 'available'
                        ip_obj.reserved_at = None
                        ip_obj.assigned_to = None
                        ip_obj.hostname = ''
                        ip_obj.discovery_reason = "Reservation Expired (Auto-released)"'''
new_expire_2 = '''                        ip_obj.status = 'available'
                        ip_obj.reserved_at = None
                        ip_obj.assigned_to = None
                        ip_obj.hostname = ''
                        ip_obj.discovery_reason = "Reservation Expired (Auto-released)"
                        from .models import AuditLog
                        AuditLog.objects.create(
                            action='SYSTEM',
                            model_name='IPAddress',
                            message=f"Reservation expired for {ip_obj.ip_address}. Automatically released back to pool."
                        )'''
content = content.replace(old_expire_2, new_expire_2)

with open('network/utils.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
