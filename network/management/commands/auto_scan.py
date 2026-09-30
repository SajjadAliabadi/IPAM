from django.core.management.base import BaseCommand
from django.utils import timezone
from network.models import Subnet, AuditLog
from network.utils import perform_discovery

class Command(BaseCommand):
    help = 'Automatically scans subnets based on their interval'

    def handle(self, *args, **kwargs):
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
