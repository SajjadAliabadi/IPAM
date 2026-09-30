import re

with open('core/static/js/req_banner.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_loop = '''                    data.ips.forEach(ip => {
                        let color = '#10b981'; 
                        let cursor = 'pointer';
                        if (ip.status === 'used') {
                            color = '#ef4444';
                            cursor = 'not-allowed';
                        } else if (ip.status === 'offline') {
                            color = '#6b7280';
                            cursor = 'not-allowed'; 
                        }
                        
                        let lastOctet = ip.ip.split('.').pop();
                        
                        html += '<div class="ip-block ' + (ip.status === 'available' ? 'ip-available' : '') + '" ' +
                            'data-id="' + ip.id + '" data-ip="' + ip.ip + '" data-status="' + ip.status + '" ' +
                            'title="' + ip.ip + ' (' + ip.status + ')" ' +
                            'style="width: 38px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: white; background: ' + color + '; border-radius: 4px; cursor: ' + cursor + '; transition: transform 0.1s;" ' +
                            'onmouseover="this.style.transform=\\'scale(1.2)\\'" onmouseout="this.style.transform=\\'scale(1)\\'">' + lastOctet + '</div>';
                    });'''

new_loop = '''                    let showTwoOctets = data.ips.length > 256;
                    data.ips.forEach(ip => {
                        let color = '#10b981'; 
                        let cursor = 'pointer';
                        if (ip.status === 'used') {
                            color = '#ef4444';
                            cursor = 'not-allowed';
                        } else if (ip.status === 'reserved') {
                            color = '#f59e0b';
                            cursor = 'not-allowed';
                        } else if (ip.status === 'offline') {
                            color = '#64748b';
                            cursor = 'not-allowed'; 
                        }
                        
                        let parts = ip.ip.split('.');
                        let label = showTwoOctets ? parts[2] + '.' + parts[3] : parts[3];
                        let w = showTwoOctets ? '50px' : '38px';
                        let fz = showTwoOctets ? '11px' : '13px';
                        
                        html += '<div class="ip-block ' + (ip.status === 'available' ? 'ip-available' : '') + '" ' +
                            'data-id="' + ip.id + '" data-ip="' + ip.ip + '" data-status="' + ip.status + '" ' +
                            'title="' + ip.ip + ' (' + ip.status + ')" ' +
                            'style="width: ' + w + '; height: 32px; display: flex; align-items: center; justify-content: center; font-size: ' + fz + '; font-weight: 600; color: white; background: ' + color + '; border-radius: 4px; cursor: ' + cursor + '; transition: transform 0.1s;" ' +
                            'onmouseover="this.style.transform=\\'scale(1.2)\\'" onmouseout="this.style.transform=\\'scale(1)\\'">' + label + '</div>';
                    });'''

content = content.replace(old_loop, new_loop)

with open('core/static/js/req_banner.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
