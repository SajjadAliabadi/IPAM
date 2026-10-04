from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Creates default permission groups for IPAM'

    def handle(self, *args, **kwargs):
        groups_data = {
            'Administrator': {
                'description': 'Full access to all system features including settings.',
                'apps': ['network', 'auth'],
                'exclude': []
            },
            'Manager': {
                'description': 'Full network access, read-only settings.',
                'apps': ['network', 'auth'],
                'exclude': ['add_systemsettings', 'change_systemsettings', 'delete_systemsettings']
            },
            'Operator': {
                'description': 'Can manage IPs, subnets, VLANs. No settings or user management.',
                'apps': ['network'],
                'exclude': ['add_systemsettings', 'change_systemsettings', 'delete_systemsettings', 'view_systemsettings']
            },
            'ReadOnly': {
                'description': 'View-only access to network models.',
                'apps': ['network'],
                'only': ['view_ipaddress', 'view_subnet', 'view_vlan', 'view_checkmethod', 'view_iprequest', 'view_systemsettings']
            },
            'Requester': {
                'description': 'Can only add and view IP requests.',
                'apps': ['network'],
                'only': ['add_iprequest', 'view_iprequest']
            }
        }

        for group_name, config in groups_data.items():
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.clear()
            
            perms_to_add = []
            
            if 'only' in config:
                for codename in config['only']:
                    try:
                        perm = Permission.objects.get(codename=codename, content_type__app_label__in=config['apps'])
                        perms_to_add.append(perm)
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Permission {codename} not found."))
            else:
                perms = Permission.objects.filter(content_type__app_label__in=config['apps'])
                for perm in perms:
                    if perm.codename not in config.get('exclude', []):
                        perms_to_add.append(perm)
            
            group.permissions.add(*perms_to_add)
            
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f'{status} group: {group_name} with {len(perms_to_add)} permissions'))

        self.stdout.write(self.style.SUCCESS('Successfully setup default groups.'))
