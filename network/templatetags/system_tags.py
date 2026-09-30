from django import template
from network.models import SystemSettings

register = template.Library()

@register.simple_tag
def get_system_theme():
    try:
        settings = SystemSettings.objects.get(pk=1)
        return settings.theme
    except SystemSettings.DoesNotExist:
        return 'default'
@register.simple_tag
def get_auto_assign_enabled():
    try:
        from network.models import SystemSettings
        return SystemSettings.load().auto_assign_ips
    except Exception:
        return False
