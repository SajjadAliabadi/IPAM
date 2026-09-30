import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from network.models import IPRequest

def create_groups():
    # IP Requesters
    ip_req_group, _ = Group.objects.get_or_create(name='IP Requesters')
    req_ct = ContentType.objects.get_for_model(IPRequest)
    perms = Permission.objects.filter(content_type=req_ct, codename__in=['add_iprequest', 'view_iprequest'])
    ip_req_group.permissions.set(perms)
    print("Created IP Requesters group.")

    # Network Operators
    net_op_group, _ = Group.objects.get_or_create(name='Network Operators')
    # Add all permissions except system settings and user management
    net_perms = Permission.objects.exclude(content_type__app_label='auth').exclude(codename__contains='systemsettings')
    net_op_group.permissions.set(net_perms)
    print("Created Network Operators group.")

create_groups()
