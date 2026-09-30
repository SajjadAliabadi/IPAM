import re

with open('network/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the THEME_CHOICES in SystemSettings to include proper bootswatch themes supported by Jazzmin
old_theme = '''    THEME_CHOICES = (
        ('default', 'Default SaaS (Light)'),
        ('dark', 'Dark Mode'),
        ('dracula', 'Dracula (Purple/Dark)'),
        ('corporate', 'Corporate (Navy/Blue)'),
    )'''

new_theme = '''    THEME_CHOICES = (
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
    )'''

content = content.replace(old_theme, new_theme)

new_fields = '''    custom_logo = models.ImageField(upload_to='logos/', null=True, blank=True, verbose_name="Custom Site Logo")
    server_port = models.IntegerField(default=8000, verbose_name="Server Port")
    enable_ssl = models.BooleanField(default=False, verbose_name="Enable HTTPS (SSL)")
    ssl_cert_path = models.CharField(max_length=255, null=True, blank=True, verbose_name="SSL Certificate Path (.crt/.pem)")
    ssl_key_path = models.CharField(max_length=255, null=True, blank=True, verbose_name="SSL Private Key Path (.key)")
    
    telegram_bot_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="Telegram Bot Token", help_text="Get this from @BotFather")
    telegram_chat_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Telegram Chat/Group ID")
    alert_on_subnet_full = models.BooleanField(default=True, verbose_name="Alert when subnet is >90% full")
    alert_on_critical_offline = models.BooleanField(default=True, verbose_name="Alert when manually assigned IP goes offline")'''

content = content.replace("    ntp_server = models.CharField(max_length=100, default='pool.ntp.org', verbose_name='NTP Server Address')", "    ntp_server = models.CharField(max_length=100, default='pool.ntp.org', verbose_name='NTP Server Address')\n" + new_fields)

with open('network/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
