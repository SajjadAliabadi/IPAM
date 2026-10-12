from django.core.management.base import BaseCommand
from network.models import IPAddress, AuditLog

class Command(BaseCommand):
    help = 'Emergency reset: Clears false in-use IPs caused by firewall proxy mode (preserves static and reserved IPs)'

    def add_arguments(self, parser):
        parser.add_argument('--subnet', type=str, help='Specific subnet CIDR to reset (e.g. 212.33.204.0/24). If not provided, resets all.')

    def handle(self, *args, **options):
        subnet_cidr = options.get('subnet')
        qs = IPAddress.objects.filter(status='used')
        
        if subnet_cidr:
            qs = qs.filter(subnet__network_address=subnet_cidr)
            
        # Exclude static IPs
        qs = qs.exclude(status='static')
        
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("No 'in use' IPs found to reset."))
            return
            
        qs.update(
            status='available',
            discovery_reason='',
            os_name='',
            open_ports='',
            first_seen=None,
            last_offline_at=None
        )
        
        AuditLog.objects.create(
            action='SYSTEM',
            model_name='IPAddress',
            message=f"Emergency reset: {count} false in-use IPs were reset to available status."
        )
        
        self.stdout.write(self.style.SUCCESS(f"Successfully reset {count} IPs back to 'Available' status!"))
