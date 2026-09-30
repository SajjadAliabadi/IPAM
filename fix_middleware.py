import re

with open('network/middleware.py', 'r', encoding='utf-8') as f:
    content = f.read()

middleware_code = '''
from django.conf import settings
from .models import SystemSettings

class DynamicThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            sys_settings = SystemSettings.load()
            
            # Update Theme
            if sys_settings.theme and sys_settings.theme != 'default':
                settings.JAZZMIN_UI_TWEAKS['theme'] = sys_settings.theme
            else:
                if 'theme' in settings.JAZZMIN_UI_TWEAKS:
                    del settings.JAZZMIN_UI_TWEAKS['theme']
                    
            # Update Logo
            if sys_settings.custom_logo:
                settings.JAZZMIN_SETTINGS['site_logo'] = sys_settings.custom_logo.url.lstrip('/')
            else:
                settings.JAZZMIN_SETTINGS['site_logo'] = None
                
        except Exception as e:
            pass
            
        response = self.get_response(request)
        return response
'''
if 'DynamicThemeMiddleware' not in content:
    content += middleware_code

with open('network/middleware.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
