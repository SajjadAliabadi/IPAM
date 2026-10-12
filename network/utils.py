import socket
import subprocess
import ipaddress
import concurrent.futures
import time
from django.utils import timezone
from .models import IPAddress, AuditLog, CheckMethod, SystemSettings
import platform

def check_port(ip, port, timeout=0.3):
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
    open_ports_list = []
    
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
                    if method.custom_port: open_ports_list.append(str(method.custom_port))
                elif method.protocol == 'icmp':
                    reasons.append(method.name)
                else:
                    reasons.append(f"{method.name}")
                    
                if method.protocol == 'http': open_ports_list.append('80')
                elif method.protocol == 'https': open_ports_list.append('443')
                elif method.protocol == 'ssh': open_ports_list.append('22')
                elif method.protocol == 'ftp': open_ports_list.append('21')
                
    reason = " | ".join(reasons) if reasons else ""
    open_ports_str = ",".join(sorted(list(set(open_ports_list))))
    return ip_str, final_status, reason, os_name, mac_address, open_ports_str

def _process_ip_status_update(ip_obj, final_status, reason, os_name, mac_address, open_ports_str, settings, now_time):
    if os_name: ip_obj.os_name = os_name
    if mac_address: ip_obj.mac_address = mac_address
    if open_ports_str: ip_obj.open_ports = open_ports_str

    if ip_obj.status == 'static':
        if final_status == 'used':
            ip_obj.last_seen = now_time
            ip_obj.discovery_reason = reason
        ip_obj.last_checked = now_time
        return

    if final_status == 'used':
        if not ip_obj.first_seen:
            ip_obj.first_seen = now_time
        ip_obj.last_seen = now_time
        ip_obj.last_offline_at = None
        ip_obj.discovery_reason = reason
        ip_obj.status = 'used'
        ip_obj.reserved_at = None
    else:
        if ip_obj.status == 'used':
            ip_obj.status = 'offline'
            ip_obj.last_offline_at = now_time
            prev_reason = ip_obj.discovery_reason
            method_str = prev_reason.replace('Detected via ', '') if prev_reason else 'Unknown Method'
            time_str = now_time.strftime('%Y-%m-%d %H:%M')
            ip_obj.discovery_reason = f"Last seen on {time_str} via {method_str}"
        elif ip_obj.status == 'offline':
            if ip_obj.last_offline_at:
                delta = now_time - ip_obj.last_offline_at
                if delta.total_seconds() / 3600 >= settings.offline_timeout_hours:
                    ip_obj.status = 'available'
                    ip_obj.last_offline_at = None
        elif ip_obj.status == 'reserved':
            if ip_obj.reserved_at:
                delta = now_time - ip_obj.reserved_at
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
            if ip_obj.status != 'available':
                ip_obj.status = 'available'

    ip_obj.last_checked = now_time

def perform_discovery(subnets_queryset):
    settings = SystemSettings.load()
    now_time = timezone.now()

    for subnet in subnets_queryset:
        methods = list(subnet.check_methods.filter(is_active=True))
        if not methods:
            methods = list(CheckMethod.objects.filter(is_active=True))

        net = ipaddress.ip_network(subnet.network_address, strict=False)
        hosts = list(net.hosts())
        if len(hosts) > 65536:
            hosts = hosts[:65536]

        ip_strs = [str(host) for host in hosts]
        results_map = {}

        # 1. Parallel live discovery of all subnet hosts
        with concurrent.futures.ThreadPoolExecutor(max_workers=150) as executor:
            futures = {executor.submit(scan_single_host, ip, methods): ip for ip in ip_strs}
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                results_map[res[0]] = res

        # 2. Fast pre-fetch existing IPs from DB in 1 single query
        existing_ips = {ip.ip_address: ip for ip in IPAddress.objects.filter(subnet=subnet)}

        # 3. Fast Parallel Double-Verification for hosts transitioning from 'used' to offline
        retry_ips = [
            ip_str for ip_str in ip_strs
            if results_map.get(ip_str) and results_map[ip_str][1] != 'used'
            and existing_ips.get(ip_str) and existing_ips[ip_str].status == 'used'
            and existing_ips[ip_str].status != 'static'
        ]

        if retry_ips:
            time.sleep(1)
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(100, len(retry_ips))) as retry_exec:
                retry_futures = {retry_exec.submit(scan_single_host, ip, methods): ip for ip in retry_ips}
                for f in concurrent.futures.as_completed(retry_futures):
                    retry_res = f.result()
                    if retry_res[1] == 'used':
                        results_map[retry_res[0]] = retry_res

        # 4. Batch updates in memory
        to_create = []
        to_update = []

        for ip_str in ip_strs:
            res = results_map.get(ip_str)
            if not res: continue
            _, final_status, reason, os_name, mac_address, open_ports_str = res

            ip_obj = existing_ips.get(ip_str)
            if not ip_obj:
                new_ip = IPAddress(
                    ip_address=ip_str,
                    subnet=subnet,
                    status=final_status,
                    discovery_reason=reason,
                    open_ports=open_ports_str,
                    os_name=os_name or '',
                    mac_address=mac_address or '',
                    first_seen=now_time if final_status == 'used' else None,
                    last_seen=now_time if final_status == 'used' else None,
                    last_checked=now_time,
                )
                to_create.append(new_ip)
            else:
                _process_ip_status_update(ip_obj, final_status, reason, os_name, mac_address, open_ports_str, settings, now_time)
                to_update.append(ip_obj)

        # 5. Bulk database write (100x faster than individual saves)
        if to_create:
            IPAddress.objects.bulk_create(to_create, batch_size=500, ignore_conflicts=True)
        if to_update:
            IPAddress.objects.bulk_update(to_update, [
                'status', 'discovery_reason', 'os_name', 'mac_address',
                'open_ports', 'last_seen', 'first_seen', 'last_offline_at',
                'reserved_at', 'assigned_to', 'hostname', 'last_checked'
            ], batch_size=500)

        Subnet.objects.filter(id=subnet.id).update(last_scanned=now_time)
        subnet.last_scanned = now_time
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
    now_time = timezone.now()

    ips_list = list(ips_queryset.select_related('subnet'))
    if not ips_list:
        return

    # Cache methods per subnet
    subnet_methods = {}
    for ip_obj in ips_list:
        if ip_obj.subnet_id not in subnet_methods:
            methods = list(ip_obj.subnet.check_methods.filter(is_active=True)) if ip_obj.subnet else []
            if not methods:
                methods = list(CheckMethod.objects.filter(is_active=True))
            subnet_methods[ip_obj.subnet_id] = methods

    # 1. Concurrent scan across all selected IPs
    results_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(100, len(ips_list))) as executor:
        futures = {
            executor.submit(scan_single_host, ip_obj.ip_address, subnet_methods.get(ip_obj.subnet_id, [])): ip_obj
            for ip_obj in ips_list
        }
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results_map[res[0]] = res

    # 2. Parallel retry for any IP transitioning from used to offline
    retry_ips = [
        ip_obj.ip_address for ip_obj in ips_list
        if results_map.get(ip_obj.ip_address) and results_map[ip_obj.ip_address][1] != 'used'
        and ip_obj.status == 'used' and ip_obj.status != 'static'
    ]

    if retry_ips:
        time.sleep(1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(100, len(retry_ips))) as retry_exec:
            retry_futures = {
                retry_exec.submit(scan_single_host, ip_str, subnet_methods.get(next((ip.subnet_id for ip in ips_list if ip.ip_address == ip_str), None), [])): ip_str
                for ip_str in retry_ips
            }
            for f in concurrent.futures.as_completed(retry_futures):
                retry_res = f.result()
                if retry_res[1] == 'used':
                    results_map[retry_res[0]] = retry_res

    # 3. Update objects in memory and bulk update
    to_update = []
    for ip_obj in ips_list:
        res = results_map.get(ip_obj.ip_address)
        if not res: continue
        _, final_status, reason, os_name, mac_address, open_ports_str = res
        _process_ip_status_update(ip_obj, final_status, reason, os_name, mac_address, open_ports_str, settings, now_time)
        to_update.append(ip_obj)

    if to_update:
        IPAddress.objects.bulk_update(to_update, [
            'status', 'discovery_reason', 'os_name', 'mac_address',
            'open_ports', 'last_seen', 'first_seen', 'last_offline_at',
            'reserved_at', 'assigned_to', 'hostname', 'last_checked'
        ], batch_size=500)

