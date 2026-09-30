import re

with open('core/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

urls_config = '''
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'''

content = re.sub(r'urlpatterns = \[\s*path\(\'admin/\', admin\.site\.urls\),\s*\]', urls_config.strip(), content)

with open('core/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
