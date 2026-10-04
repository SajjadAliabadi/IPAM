from django.core.management.base import BaseCommand
from django.utils import timezone
from network.models import Subnet, AuditLog
from network.utils import perform_discovery

class Command(BaseCommand):
    help = 'Automatically scans subnets based on their interval'

    def handle(self, *args, **kwargs):
                import psutil
        from network.models import ServerMetric
        try:
            # Gather metrics
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            
            # Find primary disk
            disk_percent = 0
            for part in psutil.disk_partitions(all=False):
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                if part.mountpoint == '/' or part.mountpoint == 'C:\\':
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_percent = usage.percent
                    break
                    
            net_io = psutil.net_io_counters()
            
            ServerMetric.objects.create(
                cpu_percent=cpu,
                memory_percent=mem,
                disk_percent=disk_percent,
                net_bytes_sent=net_io.bytes_sent,
                net_bytes_recv=net_io.bytes_recv
            )
            
            # Prune old metrics (older than 7 days)
            from datetime import timedelta
            ServerMetric.objects.filter(timestamp__lt=timezone.now() - timedelta(days=7)).delete()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not collect server metrics: {e}"))

        now = timezone.now()
        subnets_to_scan = []
        
        for subnet in Subnet.objects.all():
            if not subnet.last_scanned:
                subnets_to_scan.append(subnet)
            else:
                elapsed_minutes = (now - subnet.last_scanned).total_seconds() / 60
                if elapsed_minutes >= subnet.scan_interval_minutes:
                    subnets_to_scan.append(subnet)

        if subnets_to_scan:
            self.stdout.write(f"Found {len(subnets_to_scan)} subnets to scan.")
            # We can't pass the raw list to perform_discovery, it expects a queryset.
            qs = Subnet.objects.filter(id__in=[s.id for s in subnets_to_scan])
            perform_discovery(qs)
            
            # Update last_scanned
            for s in subnets_to_scan:
                s.last_scanned = timezone.now()
                s.save()
                AuditLog.objects.create(
                    action='SCAN',
                    model_name='Subnet',
                    message=f"Auto-scanned subnet {s.name} ({s.network_address})"
                )
            
            self.stdout.write(self.style.SUCCESS('Auto-scan completed.'))
        else:
            self.stdout.write("No subnets due for scanning right now.")
