import re

with open('core/templates/admin/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make boxes clickable by adding an <a> tag wrapper over the content, or a footer.
# Box 1: Available IPs
b1_old = '''<div class="small-box" style="background: linear-gradient(135deg, #10b981, #34d399); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.available_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Available IPs</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-check-circle"></i>
                    </div>
                </div>'''
b1_new = '''<div class="small-box" style="background: linear-gradient(135deg, #10b981, #34d399); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                    <a href="/admin/network/ipaddress/?status__exact=available" style="color: inherit; text-decoration: none; display: block;">
                        <div class="inner" style="padding: 20px;">
                            <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.available_ips }}</h3>
                            <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Available IPs</p>
                        </div>
                        <div class="icon" style="color: rgba(255,255,255,0.2);">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div style="background: rgba(0,0,0,0.1); padding: 8px 0; text-align: center; font-size: 14px; font-weight: 600; transition: background 0.3s;">
                            View List <i class="fas fa-arrow-circle-right" style="margin-left: 5px;"></i>
                        </div>
                    </a>
                </div>'''

content = content.replace(b1_old, b1_new)

# Box 2: In Use
b2_old = '''<div class="small-box" style="background: linear-gradient(135deg, #ef4444, #f87171); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.used_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">In Use</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-network-wired"></i>
                    </div>
                </div>'''
b2_new = '''<div class="small-box" style="background: linear-gradient(135deg, #ef4444, #f87171); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                    <a href="/admin/network/ipaddress/?status__exact=used" style="color: inherit; text-decoration: none; display: block;">
                        <div class="inner" style="padding: 20px;">
                            <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.used_ips }}</h3>
                            <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">In Use</p>
                        </div>
                        <div class="icon" style="color: rgba(255,255,255,0.2);">
                            <i class="fas fa-network-wired"></i>
                        </div>
                        <div style="background: rgba(0,0,0,0.1); padding: 8px 0; text-align: center; font-size: 14px; font-weight: 600; transition: background 0.3s;">
                            View List <i class="fas fa-arrow-circle-right" style="margin-left: 5px;"></i>
                        </div>
                    </a>
                </div>'''
content = content.replace(b2_old, b2_new)

# Box 3: Reserved
b3_old = '''<div class="small-box" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.reserved_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Reserved</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-clock"></i>
                    </div>
                </div>'''
b3_new = '''<div class="small-box" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                    <a href="/admin/network/ipaddress/?status__exact=reserved" style="color: inherit; text-decoration: none; display: block;">
                        <div class="inner" style="padding: 20px;">
                            <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.reserved_ips }}</h3>
                            <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Reserved</p>
                        </div>
                        <div class="icon" style="color: rgba(255,255,255,0.2);">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div style="background: rgba(0,0,0,0.1); padding: 8px 0; text-align: center; font-size: 14px; font-weight: 600; transition: background 0.3s;">
                            View List <i class="fas fa-arrow-circle-right" style="margin-left: 5px;"></i>
                        </div>
                    </a>
                </div>'''
content = content.replace(b3_old, b3_new)

# Box 4: Offline
b4_old = '''<div class="small-box" style="background: linear-gradient(135deg, #64748b, #94a3b8); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div class="inner" style="padding: 20px;">
                        <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.offline_ips }}</h3>
                        <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Offline</p>
                    </div>
                    <div class="icon" style="color: rgba(255,255,255,0.2);">
                        <i class="fas fa-power-off"></i>
                    </div>
                </div>'''
b4_new = '''<div class="small-box" style="background: linear-gradient(135deg, #64748b, #94a3b8); color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                    <a href="/admin/network/ipaddress/?status__exact=offline" style="color: inherit; text-decoration: none; display: block;">
                        <div class="inner" style="padding: 20px;">
                            <h3 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 5px;">{{ stats.offline_ips }}</h3>
                            <p style="font-size: 1.1rem; opacity: 0.9; margin: 0;">Offline</p>
                        </div>
                        <div class="icon" style="color: rgba(255,255,255,0.2);">
                            <i class="fas fa-power-off"></i>
                        </div>
                        <div style="background: rgba(0,0,0,0.1); padding: 8px 0; text-align: center; font-size: 14px; font-weight: 600; transition: background 0.3s;">
                            View List <i class="fas fa-arrow-circle-right" style="margin-left: 5px;"></i>
                        </div>
                    </a>
                </div>'''
content = content.replace(b4_old, b4_new)

# Update Recent Actions layout
ra_old = '''    <div class="col-lg-3 col-12">
        <div id="content-related">
            <div class="module" id="recent-actions-module">
                <h4 class="mb-3">{% trans 'Recent actions' %}</h4>'''
ra_new = '''    <div class="col-lg-3 col-12">
        <div id="content-related">
            <div class="card" style="box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 8px; border: 1px solid #e2e8f0;">
                <div class="card-header" style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; border-radius: 8px 8px 0 0;">
                    <h3 class="card-title" style="font-weight: 600; color: #334155; margin: 0;"><i class="fas fa-history" style="margin-right: 8px; opacity: 0.7;"></i> {% trans 'Recent Actions' %}</h3>
                </div>
                <div class="card-body" id="recent-actions-module" style="padding: 20px;">'''
content = content.replace(ra_old, ra_new)

# Close the card divs
ca_old = '''                                </div>
                            {% endfor %}
                        </div>
                    {% endif %}
            </div>
        </div>
    </div>'''
ca_new = '''                                </div>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>'''
content = content.replace(ca_old, ca_new)

# One more thing: I want to move col-lg-3 to full width col-lg-12 if possible, but let's keep Jazzmin's grid structure, just make it beautiful.

with open('core/templates/admin/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
