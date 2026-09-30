import zoneinfo
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from network.models import SystemSettings
            settings = SystemSettings.load()
            tzname = settings.timezone
            if tzname:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            else:
                timezone.deactivate()
        except Exception as e:
            logger.error(f"TimezoneMiddleware error: {e}")
            timezone.deactivate()
            
        return self.get_response(request)

from django.conf import settings
from .models import SystemSettings

class DynamicThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            sys_settings = SystemSettings.load()
            
            # Update Theme
            dark_themes = ['darkly', 'cyborg', 'slate', 'superhero', 'solar']
            if sys_settings.theme and sys_settings.theme != 'default':
                settings.JAZZMIN_UI_TWEAKS['theme'] = sys_settings.theme
                if sys_settings.theme in dark_themes:
                    settings.JAZZMIN_UI_TWEAKS['dark_mode_theme'] = sys_settings.theme
                    settings.JAZZMIN_UI_TWEAKS['body_classes'] = 'dark-mode'
                    settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-dark'
                    settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
                    settings.JAZZMIN_UI_TWEAKS['accent'] = 'accent-primary'
                else:
                    settings.JAZZMIN_UI_TWEAKS['dark_mode_theme'] = None
                    settings.JAZZMIN_UI_TWEAKS['body_classes'] = ''
                    settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-white navbar-light'
                    settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'
                    settings.JAZZMIN_UI_TWEAKS['accent'] = 'accent-primary'
            else:
                settings.JAZZMIN_UI_TWEAKS.pop('theme', None)
                settings.JAZZMIN_UI_TWEAKS.pop('dark_mode_theme', None)
                settings.JAZZMIN_UI_TWEAKS['body_classes'] = ''
                settings.JAZZMIN_UI_TWEAKS['navbar'] = 'navbar-white navbar-light'
                settings.JAZZMIN_UI_TWEAKS['sidebar'] = 'sidebar-dark-primary'

                    
            # Update Logo
            if sys_settings.custom_logo:
                settings.JAZZMIN_SETTINGS['site_logo'] = sys_settings.custom_logo.url.lstrip('/')
            else:
                settings.JAZZMIN_SETTINGS['site_logo'] = None
                
        except Exception as e:
            pass
            
        response = self.get_response(request)
        return response
