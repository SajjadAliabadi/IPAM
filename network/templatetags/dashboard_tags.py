from django import template
from network.models import IPAddress, Subnet, IPRequest, AuditLog

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    from django.utils import timezone
    from network.models import SystemSettings
    import datetime

    total_ips = IPAddress.objects.count()
    available_ips = IPAddress.objects.filter(status='available').count()
    used_ips = IPAddress.objects.filter(status='used').count()
    reserved_ips = IPAddress.objects.filter(status='reserved').count()
    offline_ips = IPAddress.objects.filter(status='offline').count()
    
    settings = SystemSettings.load()
    cutoff_time = timezone.now() - timezone.timedelta(hours=settings.new_ip_duration_hours)
    new_ips = IPAddress.objects.filter(first_seen__gte=cutoff_time).count()
    
    total_subnets = Subnet.objects.count()
    pending_requests = IPRequest.objects.filter(status='pending').count()
    
    recent_logs = AuditLog.objects.all()[:10]
    
    return {
        'total_ips': total_ips,
        'new_ips': new_ips,
        'available_ips': available_ips,
        'used_ips': used_ips,
        'reserved_ips': reserved_ips,
        'offline_ips': offline_ips,
        'total_subnets': total_subnets,
        'pending_requests': pending_requests,
        'recent_logs': recent_logs,
    }
