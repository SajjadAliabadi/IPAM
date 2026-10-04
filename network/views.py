from django.shortcuts import render

# Create your views here.


from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if not username or not password:
            messages.error(request, "Username and Password are required.")
            return redirect('register')
            
        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')
            
        user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        user.is_staff = True # Essential for them to log into the admin panel!
        user.save()
        
        requester_group, _ = Group.objects.get_or_create(name='Requester')
        user.groups.add(requester_group)
        
        return render(request, 'admin/register_success.html')
        
    return render(request, 'admin/register.html')

import psutil
from django.http import JsonResponse

def server_stats_api(request):
    # CPU
    cpu_usage = psutil.cpu_percent(interval=None)
    
    # Memory
    mem = psutil.virtual_memory()
    def format_bytes(b):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024.0:
                return f"{b:.2f} {unit}"
            b /= 1024.0
        return f"{b:.2f} PB"
    
    mem_total_str = format_bytes(mem.total)
    mem_used_str = format_bytes(mem.used)
    mem_percent = mem.percent
    
    # Disk
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                'mountpoint': part.mountpoint,
                'percent': usage.percent,
                'total': format_bytes(usage.total),
                'used': format_bytes(usage.used)
            })
        except Exception:
            pass
            
    # Network
    net_io = psutil.net_io_counters()
    net = {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv
    }
    
    return JsonResponse({
        'cpu': cpu_usage,
        'memory': {
            'percent': mem_percent,
            'text': f"{mem_used_str} / {mem_total_str}"
        },
        'disk': disks,
        'network': net
    })
