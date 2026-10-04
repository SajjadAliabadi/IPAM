import ipaddress
import threading
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class VLAN(models.Model):
    vlan_id = models.IntegerField(unique=True, verbose_name="VLAN ID")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)



    def __str__(self):
        return f"VLAN {self.vlan_id} - {self.name}"

class Subnet(models.Model):
    vlan = models.ForeignKey(VLAN, on_delete=models.SET_NULL, null=True, blank=True)
    network_address = models.CharField(max_length=45, help_text="e.g. 192.168.1.0/24")
    gateway = models.GenericIPAddressField(null=True, blank=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    check_methods = models.ManyToManyField('CheckMethod', help_text="Select one or more discovery methods for this subnet. If multiple are selected, IP is marked 'In Use' if ANY method succeeds.")
    scan_interval_minutes = models.IntegerField(default=60, help_text="Scan interval in minutes")
    last_scanned = models.DateTimeField(null=True, blank=True)
    enable_auto_assign = models.BooleanField(default=True, verbose_name='Enable Auto-Assignment', help_text='Allow the system to automatically hand out IPs from this subnet.')
    auto_assign_range_start = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP Pool Range', help_text='Use the graphical slider below to select the auto-assign IP boundaries.')
    auto_assign_range_end = models.GenericIPAddressField(null=True, blank=True, help_text='End IP of the auto-assign pool. Leave blank to use entire subnet.')



    def __str__(self):
        return f"{self.network_address} ({self.name})"

class SystemSettings(models.Model):
    THEME_CHOICES = (
        ('default', 'Default SaaS (Light)'),
        ('darkly', 'Darkly (Sleek Dark Mode)'),
        ('cyborg', 'Cyborg (Black/Blue Dark)'),
        ('slate', 'Slate (Gray Dark Mode)'),
        ('cerulean', 'Cerulean (Corporate Blue)'),
        ('cosmo', 'Cosmo (Modern Blue)'),
        ('lumen', 'Lumen (Clean Light)'),
        ('sandstone', 'Sandstone (Warm Light)'),
        ('yeti', 'Yeti (Blue/Gray)'),
        ('flatly', 'Flatly (Flat Design)'),
        ('pulse', 'Pulse (Purple/Primary)'),
        ('simplex', 'Simplex (Minimalist)'),
        ('solar', 'Solar (Yellow/Dark)'),
        ('spacelab', 'Spacelab (Silver/Blue)'),
        ('superhero', 'Superhero (Blue/Gray Dark)'),
        ('united', 'United (Ubuntu Orange)'),
    )
    theme = models.CharField(max_length=50, choices=THEME_CHOICES, default='default', verbose_name="UI Theme")
    offline_timeout_hours = models.IntegerField(default=24, verbose_name="Offline Timeout (Hours)", help_text="How many hours an IP remains 'Offline' (Gray) before automatically becoming 'Available' (Green).")
    auto_assign_ips = models.BooleanField(default=False, verbose_name="Automatic IP Assignment", help_text="If enabled, users requesting IPs will immediately receive an available IP without requiring admin approval.")
    enable_reservation = models.BooleanField(default=False, verbose_name="Enable IP Reservation System", help_text="Place assigned IPs in 'Reserved' status until they are detected online.")
    reservation_timeout_hours = models.IntegerField(default=72, verbose_name="Reservation Timeout (Hours)", help_text="If a reserved IP is not detected online within this time, it becomes Available again.")
    timezone = models.CharField(max_length=50, default='UTC', verbose_name='System Timezone')
    TIME_SYNC_CHOICES = (
        ('host', 'Sync with Host/OS (Default)'),
        ('manual', 'Manual Time Entry'),
        ('ntp', 'Network Time Protocol (NTP)'),
    )
    time_sync_mode = models.CharField(max_length=20, choices=TIME_SYNC_CHOICES, default='host', verbose_name='Time Synchronization Mode')
    manual_time = models.DateTimeField(null=True, blank=True, verbose_name='Manual Date & Time')
    ntp_server = models.CharField(max_length=100, default='pool.ntp.org', verbose_name='NTP Server Address')
    custom_logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Custom Site Logo")
    server_port = models.IntegerField(default=8000, verbose_name="Server Port")
    enable_ssl = models.BooleanField(default=False, verbose_name="Enable HTTPS (SSL)")
    ssl_cert_path = models.CharField(max_length=255, null=True, blank=True, verbose_name="SSL Certificate Path (.crt/.pem)")
    ssl_key_path = models.CharField(max_length=255, null=True, blank=True, verbose_name="SSL Private Key Path (.key)")
    new_ip_duration_hours = models.IntegerField(default=24, verbose_name="New IP Badge Duration (Hours)", help_text="How long an IP retains the 'New' badge after discovery.")
    clear_all_new_ips = models.BooleanField(default=False, verbose_name="Clear All 'New' Badges", help_text="Check this box and save to instantly clear the 'New' status from all current IPs.")
    
    monitoring_retention_days = models.IntegerField(default=30, verbose_name="Monitoring Logs Retention (Days)", help_text="Number of days to keep audit logs before they are auto-deleted.")
    clear_monitoring_logs = models.BooleanField(default=False, verbose_name="Clear All Monitoring Logs", help_text="Check this box and save to instantly delete ALL monitoring (audit) logs.")
    
    telegram_bot_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="Telegram Bot Token", help_text="Get this from @BotFather")
    telegram_chat_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Telegram Chat/Group ID")
    alert_on_subnet_full = models.BooleanField(default=True, verbose_name="Alert when subnet is >90% full")
    alert_on_critical_offline = models.BooleanField(default=True, verbose_name="Alert when manually assigned IP goes offline")

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class IPAddress(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('used', 'In Use'),
        ('offline', 'Offline (Was In Use)'),
    )
    subnet = models.ForeignKey(Subnet, on_delete=models.CASCADE, related_name='ips')
    ip_address = models.GenericIPAddressField(unique=True)
    ip_address_padded = models.CharField(max_length=15, editable=False, db_index=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    discovery_reason = models.CharField(max_length=255, blank=True, null=True, help_text="Method that detected this IP as in-use")
    hostname = models.CharField(max_length=255, blank=True, null=True, help_text="Hostname or Server Name associated with this IP")
    is_unique_hostname = models.BooleanField(default=False, verbose_name="Unique Hostname", help_text="Check this to prevent any other IP from using this hostname.")
    mac_address = models.CharField(max_length=17, blank=True, null=True, verbose_name="MAC Address")
    os_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Operating System")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)
    last_offline_at = models.DateTimeField(null=True, blank=True)
    first_seen = models.DateTimeField(null=True, blank=True, verbose_name="First Seen Online")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Last Seen Online")
    reserved_at = models.DateTimeField(null=True, blank=True, verbose_name="Reserved At")
    description = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.ip_address:
            try:
                parts = str(self.ip_address).split('.')
                if len(parts) == 4:
                    self.ip_address_padded = f"{int(parts[0]):03d}.{int(parts[1]):03d}.{int(parts[2]):03d}.{int(parts[3]):03d}"
            except Exception:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ip_address} - {self.status}"

class IPRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subnet = models.ForeignKey(Subnet, on_delete=models.SET_NULL, null=True, blank=True)
    hostname = models.CharField(max_length=255, blank=True, null=True, help_text="Desired Hostname")
    requested_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_ip = models.ForeignKey(IPAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')
    admin_comment = models.TextField(blank=True, null=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Client IP Address")
    user_agent = models.TextField(null=True, blank=True, verbose_name="Client Browser (User-Agent)")



    def __str__(self):
        return f"Request by {self.user.username} - {self.status}"

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('SYSTEM', 'System Process'),
        ('SCAN', 'Network Scan'),
        ('ASSIGN', 'IP Assignment'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.action} - {self.message}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Audit Log"
        verbose_name_plural = "Monitoring"

class CheckMethod(models.Model):
    PROTOCOL_CHOICES = (
        ('icmp', 'ICMP Ping'),
        ('http', 'HTTP (Port 80)'),
        ('https', 'HTTPS (Port 443)'),
        ('ssh', 'SSH (Port 22)'),
        ('ftp', 'FTP (Port 21)'),
        ('tcp_port', 'Custom TCP Port'),
        ('custom', 'Custom Python Script'),
    )
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Default Ping Checker")
    protocol = models.CharField(max_length=20, choices=PROTOCOL_CHOICES, default='icmp')
    custom_port = models.IntegerField(null=True, blank=True, help_text="Specify port number if 'Custom TCP Port' is selected.")
    script_content = models.TextField(blank=True, null=True, help_text="Only used if 'Custom Python Script' is selected. Variables available: ip_address. Must set result_status to 'available' or 'used'.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return self.name

# Signal to auto-discover IPs when a Subnet is created
@receiver(post_save, sender=Subnet)
def subnet_post_save(sender, instance, created, **kwargs):
    if created:
        def scan_new_subnet(subnet):
            from .utils import perform_discovery
            net = ipaddress.ip_network(subnet.network_address, strict=False)
            hosts = list(net.hosts())
            # For local demo, limit large subnets
            if len(hosts) > 256:
                hosts = hosts[:256]
                
            for host in hosts:
                ip_str = str(host)
                IPAddress.objects.get_or_create(
                    ip_address=ip_str,
                    defaults={'subnet': subnet, 'status': 'available'}
                )
            # Run the discovery logic on this subnet
            perform_discovery([subnet])
            
        thread = threading.Thread(target=scan_new_subnet, args=(instance,))
        thread.start()

















class ServerMetric(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    cpu_percent = models.FloatField()
    memory_percent = models.FloatField()
    disk_percent = models.FloatField()
    net_bytes_sent = models.BigIntegerField(default=0)
    net_bytes_recv = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Server Metric"
        verbose_name_plural = "Server Metrics"
