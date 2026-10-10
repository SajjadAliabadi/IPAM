(function() {
    function renderMap() {
        if (document.getElementById('ip-visual-map-changelist')) return; // already rendered
        
        const urlParams = new URLSearchParams(window.location.search);
        const subnetId = urlParams.get('subnet__id__exact');
        
        if (!subnetId) return;
        
        const targetContainer = document.querySelector('#changelist-form') || document.getElementById('changelist') || document.querySelector('.module');
        if (!targetContainer) return;
        
        const mapContainer = document.createElement('div');
        mapContainer.id = 'ip-visual-map-changelist';
        mapContainer.style.marginBottom = '20px';
        mapContainer.style.padding = '20px';
        mapContainer.style.background = '#ffffff';
        mapContainer.style.border = '1px solid #e2e8f0';
        mapContainer.style.borderRadius = '8px';
        mapContainer.style.boxShadow = '0 4px 6px rgba(0,0,0,0.05)';
        
        targetContainer.parentNode.insertBefore(mapContainer, targetContainer.nextSibling);
        mapContainer.style.marginTop = '20px';
        
        mapContainer.innerHTML = '<div style="text-align: center; color: #64748b; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading IP map...</div>';
        
        fetch('/admin/network/iprequest/api/subnet-map/' + subnetId + '/')
            .then(r => r.json())
            .then(data => {
                if (!data.ips || data.ips.length === 0) {
                    mapContainer.innerHTML = '<div style="color: #64748b; padding: 20px;">No IP records found for this subnet.</div>';
                    return;
                }
                
                let subnetBadge = data.subnet_info ? '<span style="background: #e2e8f0; color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 12px; letter-spacing: 0.5px; font-weight:normal; margin-left: 10px;"><i class="fas fa-network-wired" style="margin-right:5px;"></i>' + data.subnet_info + '</span>' : '';
                let html = '<h4 style="margin-top:0; font-size:16px; color:#334155; font-weight:600; margin-bottom: 15px; display:flex; align-items:center; justify-content:space-between;">' + 
                    '<span><i class="fas fa-network-wired" style="margin-right:8px; opacity:0.7;"></i> Visual IP Map</span>' + 
                    subnetBadge + '</h4>';
                html += '<div style="display: flex; flex-wrap: wrap; gap: 6px;">';
                
                let showTwoOctets = data.ips.length > 256;
                data.ips.forEach(ip => {
                    let color = '#10b981'; 
                    if (ip.status === 'used') { color = '#ef4444'; } 
                    else if (ip.status === 'static') { color = '#8b5cf6'; } 
                    else if (ip.status === 'reserved') { color = '#f59e0b'; } 
                    else if (ip.status === 'offline') { color = '#64748b'; }
                    
                    let parts = ip.ip.split('.');
                    let label = showTwoOctets ? parts[2] + '.' + parts[3] : parts[3];
                    let w = showTwoOctets ? '50px' : '40px';
                    let fz = showTwoOctets ? '11px' : '13px';
                    
                    html += '<a href="/admin/network/ipaddress/' + ip.id + '/change/" title="' + ip.ip + ' (' + ip.status + ')" ' +
                        'style="width: ' + w + '; height: 36px; display: flex; align-items: center; justify-content: center; font-size: ' + fz + '; font-weight: 600; color: white; background: ' + color + '; border-radius: 4px; text-decoration: none; transition: transform 0.1s;" ' +
                        'onmouseover="this.style.transform=\'scale(1.1)\'" onmouseout="this.style.transform=\'scale(1)\'">' + label + '</a>';
                });
                html += '</div>';
                
                html += '<div style="margin-top: 20px; display: flex; gap: 15px; font-size: 13px; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 15px;">';
                html += '<div style="display:flex; align-items:center; gap:6px;"><div style="width:14px;height:14px;background:#10b981;border-radius:3px;"></div> Available</div>';
                html += '<div style="display:flex; align-items:center; gap:6px;"><div style="width:14px;height:14px;background:#ef4444;border-radius:3px;"></div> In Use</div>';
                html += '<div style="display:flex; align-items:center; gap:6px;"><div style="width:14px;height:14px;background:#8b5cf6;border-radius:3px;"></div> Static</div>';
                html += '<div style="display:flex; align-items:center; gap:6px;"><div style="width:14px;height:14px;background:#f59e0b;border-radius:3px;"></div> Reserved</div>';
                html += '<div style="display:flex; align-items:center; gap:6px;"><div style="width:14px;height:14px;background:#64748b;border-radius:3px;"></div> Offline</div>';
                html += '</div>';
                
                mapContainer.innerHTML = html;
            })
            .catch(err => {
                mapContainer.innerHTML = '<div style="color: #ef4444; padding: 20px;">Failed to load IP map. ' + err + '</div>';
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderMap);
    } else {
        renderMap();
    }
})();
