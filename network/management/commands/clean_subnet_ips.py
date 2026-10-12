from django.core.management.base import BaseCommand
from network.models import Subnet, IPAddress, AuditLog
import ipaddress

class Command(BaseCommand):
    help = 'Validates and cleans Subnet IP integrity: removes duplicates, purges IPs outside subnet CIDR, and populates missing IPs.'

    def add_arguments(self, parser):
        parser.add_argument('--subnet', type=str, help='Specific subnet CIDR to clean (e.g. 172.16.152.0/24). If omitted, cleans all.')

    def handle(self, *args, **options):
        subnet_filter = options.get('subnet')
        subnets = Subnet.objects.all()
        if subnet_filter:
            subnets = subnets.filter(network_address=subnet_filter)

        total_cleaned = 0
        total_created = 0
        total_duplicates = 0

        for subnet in subnets:
            try:
                net = ipaddress.ip_network(subnet.network_address, strict=False)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Invalid network address for subnet {subnet}: {e}"))
                continue

            hosts = list(net.hosts())
            if len(hosts) > 65536:
                hosts = hosts[:65536]
            valid_ip_strs = set(str(h) for h in hosts)

            # Step 1: Find all current IPs attached to this subnet
            current_ips = list(subnet.ips.all().order_by('id'))

            seen = {}
            duplicates_to_delete = []
            outside_to_delete = []

            for ip_obj in current_ips:
                # Is it outside CIDR?
                if ip_obj.ip_address not in valid_ip_strs:
                    # Check if another subnet owns it
                    other_subnets = Subnet.objects.exclude(id=subnet.id)
                    reassigned = False
                    for other in other_subnets:
                        try:
                            other_net = ipaddress.ip_network(other.network_address, strict=False)
                            if ipaddress.ip_address(ip_obj.ip_address) in other_net:
                                ip_obj.subnet = other
                                ip_obj.save(update_fields=['subnet'])
                                reassigned = True
                                break
                        except Exception:
                            pass
                    if not reassigned:
                        outside_to_delete.append(ip_obj.id)
                    continue

                # Is it duplicate within this subnet?
                if ip_obj.ip_address in seen:
                    prev_obj = seen[ip_obj.ip_address]
                    # Keep the one with better data (used, static, reserved, mac, etc.)
                    if prev_obj.status in ['used', 'static', 'reserved'] or prev_obj.mac_address:
                        duplicates_to_delete.append(ip_obj.id)
                    else:
                        duplicates_to_delete.append(prev_obj.id)
                        seen[ip_obj.ip_address] = ip_obj
                else:
                    seen[ip_obj.ip_address] = ip_obj

            # Delete duplicates and outside IPs
            if duplicates_to_delete:
                IPAddress.objects.filter(id__in=duplicates_to_delete).delete()
                total_duplicates += len(duplicates_to_delete)

            if outside_to_delete:
                IPAddress.objects.filter(id__in=outside_to_delete).delete()
                total_cleaned += len(outside_to_delete)

            # Step 2: Ensure all valid hosts exist
            existing_ip_strs = set(IPAddress.objects.filter(subnet=subnet).values_list('ip_address', flat=True))
            missing_hosts = [h for h in valid_ip_strs if h not in existing_ip_strs]

            new_ips = []
            for ip_str in missing_hosts:
                if not IPAddress.objects.filter(ip_address=ip_str).exists():
                    parts = ip_str.split('.')
                    padded = f"{int(parts[0]):03d}.{int(parts[1]):03d}.{int(parts[2]):03d}.{int(parts[3]):03d}" if len(parts) == 4 else None
                    new_ips.append(IPAddress(
                        ip_address=ip_str,
                        ip_address_padded=padded,
                        subnet=subnet,
                        status='available'
                    ))

            if new_ips:
                IPAddress.objects.bulk_create(new_ips, batch_size=500)
                total_created += len(new_ips)

            final_count = IPAddress.objects.filter(subnet=subnet).count()
            self.stdout.write(self.style.SUCCESS(
                f"Subnet {subnet.network_address} ({subnet.name}): "
                f"Fixed! Total {final_count} IPs "
                f"(Purged {len(outside_to_delete)} out-of-bounds, {len(duplicates_to_delete)} duplicates, created {len(new_ips)} missing)."
            ))

        AuditLog.objects.create(
            action='SYSTEM',
            model_name='Subnet',
            message=f"Subnet IP Integrity Check: Purged {total_cleaned} out-of-bounds IPs, {total_duplicates} duplicates, created {total_created} missing IPs."
        )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Purged {total_cleaned} out-of-bounds IPs, {total_duplicates} duplicates, created {total_created} missing IPs."
        ))
