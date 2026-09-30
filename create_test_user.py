import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User, Group

user, created = User.objects.get_or_create(username='ip_requester')
if created:
    user.set_password('password123')
    user.is_staff = True
    user.save()

group = Group.objects.get(name='IP Requesters')
user.groups.add(group)
print('Test user ip_requester created.')
