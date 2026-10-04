document.addEventListener('DOMContentLoaded', function() {
    const ipInput = document.getElementById('id_ip_address') || document.querySelector('.field-ip_address .readonly');
    const statusSelect = document.getElementById('id_status');

    if (ipInput) {
        const ipText = ipInput.tagName === 'INPUT' ? ipInput.value : ipInput.innerText;
        
        let statusVal = 'available';
        if (statusSelect) {
            statusVal = statusSelect.value;
        } else {
            const statusRo = document.querySelector('.field-status .readonly');
            if (statusRo) statusVal = statusRo.innerText.toLowerCase();
        }

        if (ipText) {
            const target = ipInput.closest('form');
            if (target) {
                const banner = document.createElement('div');
                banner.id = 'dynamic-ip-banner';
                
                function updateBanner(status) {
                    let bg = 'linear-gradient(135deg, #059669, #10b981)'; 
                    let icon = 'fa-check-circle';
                    let statusText = 'Available';
                    
                    if (status.includes('used') || status.includes('in use')) {
                        bg = 'linear-gradient(135deg, #dc2626, #ef4444)'; 
                        icon = 'fa-server';
                        statusText = 'In Use';
                    } else if (status.includes('offline')) {
                        bg = 'linear-gradient(135deg, #4b5563, #6b7280)'; 
                        icon = 'fa-power-off';
                        statusText = 'Offline';
                    } else if (status.includes('reserved')) {
                        bg = 'linear-gradient(135deg, #ca8a04, #eab308)'; 
                        icon = 'fa-lock';
                        statusText = 'Reserved';
                    }

                    banner.innerHTML = '<div style="background: ' + bg + '; color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px; transition: all 0.3s ease;">' +
                        '<i class="fas ' + icon + '" style="font-size: 28px; opacity: 0.8;"></i>' +
                        '<div>' +
                            '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">IP Address Details</h3>' +
                            '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">' + ipText + ' &mdash; Status: ' + statusText + '</div>' +
                        '</div>' +
                    '</div>';
                }

                updateBanner(statusVal);
                target.parentNode.insertBefore(banner, target);

                if (statusSelect) {
                    // Update dynamically when admin changes the dropdown!
                    // Jazzmin uses select2, so we listen to change on the jQuery object too
                    statusSelect.addEventListener('change', function() { updateBanner(this.value); });
                    if (typeof jQuery !== 'undefined') {
                        jQuery(statusSelect).on('change', function() { updateBanner(this.value); });
                    }
                }
            }
        }
    }
});
