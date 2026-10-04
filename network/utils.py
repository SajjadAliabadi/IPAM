import socket
import subprocess
import ipaddress
import concurrent.futures
from django.utils import timezone
from .models import IPAddress, AuditLog, CheckMethod, SystemSettings
import platform

def check_port(ip, port, timeout=0.5):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, port))
            return True
    except:
        return False

def get_mac_address(ip_str):
    import platform, subprocess, re
    if platform.system().lower() == 'windows':
        try:
            output = subprocess.check_output(['arp', '-a', ip_str], text=True)
            match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", output)
            if match:
                mac = match.group(0).replace('-', ':').upper()
                if mac != '00:00:00:00:00:00': return mac
        except Exception: pass
    else:
        try:
            with open('/proc/net/arp', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[0] == ip_str:
                        mac = parts[3].upper()
                        if mac != '00:00:00:00:00:00': return mac
        except Exception: pass
    return None

def ping_host_ext(ip_str):
    import platform, subprocess, re
    is_online = False
    os_name = None
    try:
        if platform.system().lower() == 'windows':
            output = subprocess.run(['ping', '-n', '1', '-w', '500', ip_str], capture_output=True, text=True, timeout=2)
        else:
            output = subprocess.run(['ping', '-c', '1', '-W', '1', ip_str], capture_output=True, text=True, timeout=2)
            
        is_online = (output.returncode == 0)
        
        if is_online:
            match = re.search(r'(?i)ttl=(\d+)', output.stdout)
            if match:
                ttl = int(match.group(1))
                if ttl <= 64: os_name = "Linux / Unix / macOS"
                elif ttl <= 128: os_name = "Windows"
                elif ttl <= 255: os_name = "Cisco / Network Device"
    except Exception:
        pass
    return is_online, os_name

def ping_host(ip_str):
    is_online, _ = ping_host_ext(ip_str)
    return is_online

def run_custom_script(ip_str, script_content):
    local_env = {'ip_address': ip_str, 'result_status': 'available', 'subprocess': subprocess, 'socket': socket}
    try:
        exec(script_content, {}, local_env)
        if local_env.get('result_status') == 'used':
            return True
    except Exception:
        pass
    return False

def scan_single_host(ip_str, methods):
    final_status = 'available'
    reasons = []
    
    # Always attempt ping to gather OS Fingerprint & check ARP table for MAC
    ping_online, os_name = ping_host_ext(ip_str)
    mac_address = get_mac_address(ip_str)
    
    if not methods:
        if ping_online:
            final_status = 'used'
            reasons.append('ICMP Ping')
    else:
        for method in methods:
            is_used = False
            if method.protocol == 'icmp':
                is_used = ping_online
            elif method.protocol == 'http':
                is_used = check_port(ip_str, 80)
            elif method.protocol == 'https':
                is_used = check_port(ip_str, 443)
            elif method.protocol == 'ssh':
                is_used = check_port(ip_str, 22)
            elif method.protocol == 'ftp':
                is_used = check_port(ip_str, 21)
            elif method.protocol == 'tcp_port' and method.custom_port:
                is_used = check_port(ip_str, method.custom_port)
            elif method.protocol == 'custom' and method.script_content:
                is_used = run_custom_script(ip_str, method.script_content)

            if is_used:
                final_status = 'used'
                if method.protocol == 'tcp_port':
                    reasons.append(f"{method.name} (Port {method.custom_port})")
                elif method.protocol == 'icmp':
                    reasons.append(method.name)
                else:
                    reasons.append(f"{method.name}")
                
    reason = " | ".join(reasons) if reasons else ""
    return ip_str, final_status, reason, os_name, mac_address

def perform_discovery(subnets_queryset):
    settings = SystemSettings.load()
    
    for subnet in subnets_queryset:
        methods = list(subnet.check_methods.filter(is_active=True))
        if not methods:
            methods = list(CheckMethod.objects.filter(is_active=True))
            
        net = ipaddress.ip_network(subnet.network_address, strict=False)
        hosts = list(net.hosts())
        if len(hosts) > 65536:
            hosts = hosts[:65536]
        
        ip_strs = [str(host) for host in hosts]
        results = []
    
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = {executor.submit(scan_single_host, ip, methods): ip for ip in ip_strs}
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
            
        for ip_str, final_status, reason, os_name, mac_address in results:
            defaults = {'subnet': subnet, 'status': final_status, 'discovery_reason': reason}
            if os_name: defaults['os_name'] = os_name
            if mac_address: defaults['mac_address'] = mac_address
            ip_obj, created = IPAddress.objects.get_or_create(
                ip_address=ip_str,
                defaults=defaults
            )
            
            # Update dynamically if changed
            if os_name and ip_obj.os_name != os_name:
                ip_obj.os_name = os_name
            if mac_address and ip_obj.mac_address != mac_address:
                ip_obj.mac_address = mac_address
            
            # Double verification before marking offline
            if final_status != 'used' and ip_obj.status == 'used':
                import time
                time.sleep(1)
                _, retry_status, retry_reason, _, _ = scan_single_host(ip_str, methods)
                if retry_status == 'used':
                    final_status = 'used'
                    reason = retry_reason
        
            needs_save = False
            if final_status == 'used':
                if not ip_obj.first_seen:
                    ip_obj.first_seen = timezone.now()
                ip_obj.last_seen = timezone.now()
                ip_obj.last_offline_at = None
                ip_obj.discovery_reason = reason
                ip_obj.status = 'used'
                ip_obj.reserved_at = None
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
                    if ip_obj.reserved_at:
                        delta = timezone.now() - ip_obj.reserved_at
                        if delta.total_seconds() / 3600 >= settings.reservation_timeout_hours:
                            ip_obj.status = 'available'
                            ip_obj.reserved_at = None
                            ip_obj.assigned_to = None
                            ip_obj.hostname = ''
                            ip_obj.discovery_reason = "Reservation Expired (Auto-released)"
                            needs_save = True
                            AuditLog.objects.create(
                                action='SYSTEM',
                                model_name='IPAddress',
                                message=f"Reservation expired for {ip_obj.ip_address}. Automatically released back to pool."
                            )
                else:
                    if ip_obj.status != 'available':
                        ip_obj.status = 'available'
                        needs_save = True
        
            ip_obj.last_checked = timezone.now()
            ip_obj.save()

        subnet.last_scanned = timezone.now()
        subnet.save()
        AuditLog.objects.create(
            action='SCAN',
            model_name='Subnet',
            message=f"Discovery scan executed for subnet {subnet.name} ({subnet.network_address})"
        )
    
        if settings.alert_on_subnet_full:
            total = subnet.ips.count()
            used = subnet.ips.filter(status='used').count()
            if total > 0 and (used / total) >= 0.9:
                try:
                    from .alerts import send_telegram_alert
                    send_telegram_alert(f"Subnet Almost Full: {subnet.network_address} is {int(used/total*100)}% full.")
                except: pass

def perform_ip_discovery(ips_queryset):
    settings = SystemSettings.load()

    for ip_obj in ips_queryset:
        subnet = ip_obj.subnet
        methods = list(subnet.check_methods.filter(is_active=True))
        if not methods:
            methods = list(CheckMethod.objects.filter(is_active=True))

        ip_str = ip_obj.ip_address
        _, final_status, reason, os_name, mac_address = scan_single_host(ip_str, methods)
        if os_name: ip_obj.os_name = os_name
        if mac_address: ip_obj.mac_address = mac_address

        old_status = ip_obj.status
        
        # Double verification before marking offline
        if final_status != 'used' and old_status == 'used':
            import time
            time.sleep(1)
            _, retry_status, retry_reason, _, _ = scan_single_host(ip_str, methods)
            if retry_status == 'used':
                final_status = 'used'
                reason = retry_reason
                
        if final_status == 'used':
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
                    try:
                        from .alerts import send_telegram_alert
                        send_telegram_alert(f"Critical IP Offline: Manually assigned IP {ip_obj.ip_address} ({ip_obj.hostname}) has gone offline.")
                    except: pass
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
                        AuditLog.objects.create(
                            action='SYSTEM',
                            model_name='IPAddress',
                            message=f"Reservation expired for {ip_obj.ip_address}. Automatically released back to pool."
                        )
            else:
                ip_obj.status = 'available'

        ip_obj.last_checked = timezone.now()
        ip_obj.save()
