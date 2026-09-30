from django import template
from network.models import IPAddress, Subnet, IPRequest, AuditLog

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    total_ips = IPAddress.objects.count()
    available_ips = IPAddress.objects.filter(status='available').count()
    used_ips = IPAddress.objects.filter(status='used').count()
    reserved_ips = IPAddress.objects.filter(status='reserved').count()
    offline_ips = IPAddress.objects.filter(status='offline').count()
    
    total_subnets = Subnet.objects.count()
    pending_requests = IPRequest.objects.filter(status='pending').count()
    
    recent_logs = AuditLog.objects.all()[:10]
    
    return {
        'total_ips': total_ips,
        'available_ips': available_ips,
        'used_ips': used_ips,
        'reserved_ips': reserved_ips,
        'offline_ips': offline_ips,
        'total_subnets': total_subnets,
        'pending_requests': pending_requests,
        'recent_logs': recent_logs,
    }
