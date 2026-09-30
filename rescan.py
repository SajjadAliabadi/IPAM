import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from network.models import Subnet
from network.utils import perform_discovery

subs = Subnet.objects.filter(network_address='31.7.56.0/23')
if subs.exists():
    print(f"Rescanning {subs.first().network_address}...")
    perform_discovery(subs)
    print("Done scanning.")
else:
    print("Subnet not found.")
