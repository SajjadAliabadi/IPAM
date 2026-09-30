document.addEventListener('DOMContentLoaded', function() {
    const hostInput = document.getElementById('id_hostname');
    
    if (hostInput) {
        const target = hostInput.closest('form');
        if (target) {
            const banner = document.createElement('div');
            banner.innerHTML = '<div style="background: linear-gradient(135deg, #d97706, #f59e0b); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px;">' +
                '<i class="fas fa-paper-plane" style="font-size: 28px; opacity: 0.8;"></i>' +
                '<div>' +
                    '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">IP Request Ticket</h3>' +
                    '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">Manage user IP allocation request</div>' +
                '</div>' +
            '</div>';
            target.parentNode.insertBefore(banner, target);
        }
    }

    const subnetSelect = document.getElementById('id_subnet');
    const assignedIpSelect = document.getElementById('id_assigned_ip');

    if (subnetSelect && assignedIpSelect) {
        const mapContainer = document.createElement('div');
        mapContainer.id = 'ip-visual-map';
        mapContainer.style.marginTop = '30px';
        mapContainer.style.padding = '20px';
        mapContainer.style.background = '#f8fafc';
        mapContainer.style.border = '1px solid #e2e8f0';
        mapContainer.style.borderRadius = '8px';
        
        const targetContainer = subnetSelect.closest('.card-body') || subnetSelect.closest('form');
        if (targetContainer) {
            targetContainer.appendChild(mapContainer);
        }

        function loadMap(subnetId) {
            if (!subnetId) {
                mapContainer.innerHTML = '';
                return;
            }
            
            mapContainer.innerHTML = '<div style="text-align: center; color: #64748b;"><i class="fas fa-spinner fa-spin"></i> Loading IP map...</div>';
            
            fetch('/admin/network/iprequest/api/subnet-map/' + subnetId + '/')
                .then(r => r.json())
                .then(data => {
                    if (!data.ips || data.ips.length === 0) {
                        mapContainer.innerHTML = '<div style="color: #64748b;">No IP records found for this subnet. Please run a discovery scan first.</div>';
                        return;
                    }
                    
                    let html = '<h4 style="margin-top:0; font-size:16px; color:#334155; font-weight:600;"><i class="fas fa-th" style="margin-right:8px; opacity:0.7;"></i> Visual IP Map (Click an Available IP to select it)</h4>';
                    html += '<div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 15px;">';
                    
                    let showTwoOctets = data.ips.length > 256;
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
                            'onmouseover="this.style.transform=\'scale(1.2)\'" onmouseout="this.style.transform=\'scale(1)\'">' + label + '</div>';
                    });
                    
                    html += '</div>';
                    
                    html += '<div style="margin-top: 15px; display: flex; gap: 15px; font-size: 12px; color: #64748b;">';
                    html += '<div style="display:flex; align-items:center; gap:5px;"><div style="width:12px;height:12px;background:#10b981;border-radius:2px;"></div> Available</div>';
                    html += '<div style="display:flex; align-items:center; gap:5px;"><div style="width:12px;height:12px;background:#ef4444;border-radius:2px;"></div> In Use</div>';
                    html += '<div style="display:flex; align-items:center; gap:5px;"><div style="width:12px;height:12px;background:#6b7280;border-radius:2px;"></div> Offline</div>';
                    html += '</div>';
                    
                    mapContainer.innerHTML = html;
                    
                    mapContainer.querySelectorAll('.ip-available').forEach(block => {
                        block.addEventListener('click', function() {
                            const ipId = this.getAttribute('data-id');
                            
                            if (typeof jQuery !== 'undefined') {
                                jQuery('#id_assigned_ip').val(ipId).trigger('change');
                            } else {
                                assignedIpSelect.value = ipId;
                            }
                            
                            mapContainer.querySelectorAll('.ip-block').forEach(b => b.style.boxShadow = 'none');
                            this.style.boxShadow = '0 0 0 3px #fbbf24';
                            
                            assignedIpSelect.scrollIntoView({behavior: "smooth", block: "center"});
                            
                            const fieldWrap = assignedIpSelect.closest('.form-group');
                            if (fieldWrap) {
                                fieldWrap.style.transition = 'background 0.5s';
                                fieldWrap.style.background = '#fef3c7';
                                setTimeout(() => fieldWrap.style.background = '', 1000);
                            }
                        });
                    });
                })
                .catch(err => {
                    mapContainer.innerHTML = '<div style="color: #ef4444;">Failed to load IP map.</div>';
                });
        }

        if (subnetSelect.value) {
            loadMap(subnetSelect.value);
        }

        if (typeof jQuery !== 'undefined') {
            jQuery(subnetSelect).on('change', function() { loadMap(this.value); });
        } else {
            subnetSelect.addEventListener('change', function() { loadMap(this.value); });
        }
    }
});
