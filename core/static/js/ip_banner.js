document.addEventListener('DOMContentLoaded', function() {
    const ipInput = document.getElementById('id_ip_address') || document.querySelector('.field-ip_address .readonly') || document.querySelector('.field-ip_address');
    const statusSelect = document.getElementById('id_status');

    if (ipInput) {
        const ipText = ipInput.tagName === 'INPUT' ? ipInput.value : ipInput.innerText;
        
        let statusVal = 'available';
        if (statusSelect) {
            statusVal = statusSelect.value.toLowerCase();
        } else {
            const labels = document.querySelectorAll('label');
            for (let i = 0; i < labels.length; i++) {
                if (labels[i].textContent.includes('Status')) {
                    const parent = labels[i].parentElement;
                    if (parent) {
                        statusVal = parent.textContent.toLowerCase();
                    }
                    break;
                }
            }
        }

        if (ipText && ipText.trim() !== '') {
            const target = ipInput.closest('form');
            if (target) {
                const banner = document.createElement('div');
                banner.id = 'dynamic-ip-banner';
                
                function updateBanner(status) {
                    let bg = 'linear-gradient(135deg, #059669, #10b981)'; 
                    let icon = 'fa-check-circle';
                    let statusText = 'Available';
                    
                    if (status.includes('static')) {
                        bg = 'linear-gradient(135deg, #7c3aed, #8b5cf6)'; 
                        icon = 'fa-thumbtack';
                        statusText = 'Static (Always In-Use)';
                    } else if (status.includes('offline')) {
                        bg = 'linear-gradient(135deg, #4b5563, #6b7280)'; 
                        icon = 'fa-power-off';
                        statusText = 'Offline';
                    } else if (status.includes('reserved')) {
                        bg = 'linear-gradient(135deg, #ca8a04, #eab308)'; 
                        icon = 'fa-lock';
                        statusText = 'Reserved';
                    } else if (status.includes('used') || status.includes('in use')) {
                        bg = 'linear-gradient(135deg, #dc2626, #ef4444)'; 
                        icon = 'fa-server';
                        statusText = 'In Use';
                    }

                    // Extract actual IP address from ipText (it might have "Ip address:\n192.168.1.1")
                    let cleanIp = ipText.replace('Ip address', '').replace(':', '').trim();

                    banner.innerHTML = '<div style="background: ' + bg + '; color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px; transition: all 0.3s ease;">' +
                        '<i class="fas ' + icon + '" style="font-size: 28px; opacity: 0.8;"></i>' +
                        '<div>' +
                            '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">IP Address Details</h3>' +
                            '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">' + cleanIp + ' &mdash; Status: ' + statusText + '</div>' +
                        '</div>' +
                    '</div>';
                }

                updateBanner(statusVal);
                target.parentNode.insertBefore(banner, target);

                if (statusSelect) {
                    statusSelect.addEventListener('change', function() { updateBanner(this.value); });
                    if (typeof jQuery !== 'undefined') {
                        jQuery(statusSelect).on('change', function() { updateBanner(this.value); });
                    }
                }
            }
        }
    }
});
