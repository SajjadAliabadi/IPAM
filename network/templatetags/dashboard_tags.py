from django import template
from network.models import IPAddress, Subnet, IPRequest, AuditLog

register = template.Library()

@register.simple_tag(takes_context=True)
def get_dashboard_stats(context):
    from django.utils import timezone
    from network.models import SystemSettings
    import datetime

    request = context.get('request')
    subnet_id = request.GET.get('subnet_id') if request else None

    if subnet_id and subnet_id != 'all':
        ips = IPAddress.objects.filter(subnet_id=subnet_id)
        selected_subnet = subnet_id
    else:
        ips = IPAddress.objects.all()
        selected_subnet = 'all'

    total_ips = ips.count()
    available_ips = ips.filter(status='available').count()
    used_ips = ips.filter(status='used').count()
    reserved_ips = ips.filter(status='reserved').count()
    offline_ips = ips.filter(status='offline').count()
    
    settings = SystemSettings.load()
    cutoff_time = timezone.now() - timezone.timedelta(hours=settings.new_ip_duration_hours)
    new_ips = ips.filter(first_seen__gte=cutoff_time, status='used').count()
    
    total_subnets = Subnet.objects.count()
    all_subnets = Subnet.objects.all()
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
        'all_subnets': all_subnets,
        'selected_subnet': selected_subnet,
        'pending_requests': pending_requests,
        'recent_logs': recent_logs,
    }
