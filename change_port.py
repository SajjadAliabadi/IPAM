import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from network.models import SystemSettings
settings = SystemSettings.load()
settings.server_port = 80
settings.save()
print('Port changed to 80')
