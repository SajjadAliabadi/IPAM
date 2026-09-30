import re

with open('core/templates/admin/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

widget = '''{% load dashboard_tags %}
{% get_dashboard_stats as stats %}
    <div class="col-12 mb-4">
        <h4 class="mb-3" style="color: #334155; font-weight: 600;"><i class="fas fa-tachometer-alt" style="margin-right: 8px;"></i> IPAM Overview</h4>
        <div class="row">
            <div class="col-lg-3 col-6">
                <div class="small-box" style="background: linear-gradient(135deg, #10b981, #34d399); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.available_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Available IPs</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-check-circle"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="small-box" style="background: linear-gradient(135deg, #ef4444, #f87171); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.used_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">In Use</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-network-wired"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="small-box" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.reserved_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Reserved</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-clock"></i>
                    </div>
                </div>
            </div>
            
            <div class="col-lg-3 col-6">
                <div class="small-box" style="background: linear-gradient(135deg, #64748b, #94a3b8); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.offline_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Offline</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-power-off"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
'''

content = content.replace("{% block content %}", "{% block content %}\n" + widget)

with open('core/templates/admin/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
