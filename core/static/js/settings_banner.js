document.addEventListener('DOMContentLoaded', function() {
    const themeInput = document.getElementById('id_theme');
    
    if (themeInput) {
        const target = themeInput.closest('form');
        if (target) {
            const banner = document.createElement('div');
            banner.innerHTML = '<div style="background: linear-gradient(135deg, #1e293b, #334155); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px;">' +
                '<i class="fas fa-cogs" style="font-size: 28px; opacity: 0.8;"></i>' +
                '<div>' +
                    '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">Global System Settings</h3>' +
                    '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">Configure IPAM behavior across all networks</div>' +
                '</div>' +
            '</div>';
            target.parentNode.insertBefore(banner, target);
        }
    }
    // --- Dynamic Time Settings ---
    const timeSyncInput = document.getElementById('id_time_sync_mode');
    const manualTimeField = document.querySelector('.field-manual_time');
    const ntpServerField = document.querySelector('.field-ntp_server');

    function toggleTimeFields() {
        if (!timeSyncInput) return;
        const mode = timeSyncInput.value;
        
        if (manualTimeField) manualTimeField.style.display = (mode === 'manual') ? '' : 'none';
        if (ntpServerField) ntpServerField.style.display = (mode === 'ntp') ? '' : 'none';
    }

    if (timeSyncInput) {
        timeSyncInput.addEventListener('change', toggleTimeFields);
        if (typeof jQuery !== 'undefined') {
            jQuery(timeSyncInput).on('change', toggleTimeFields);
        }
        toggleTimeFields(); // Init
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const timeSpan = document.getElementById('live-system-time');
    if (timeSpan) {
        let textTime = timeSpan.innerText.trim();
        
        function incrementTimeStr(timeStr) {
            let d = new Date(timeStr.replace(/-/g, '/')); 
            if (isNaN(d.getTime())) return timeStr;
            
            d.setSeconds(d.getSeconds() + 1);
            
            let yyyy = d.getFullYear();
            let mm = String(d.getMonth() + 1).padStart(2, '0');
            let dd = String(d.getDate()).padStart(2, '0');
            let hh = String(d.getHours()).padStart(2, '0');
            let min = String(d.getMinutes()).padStart(2, '0');
            let ss = String(d.getSeconds()).padStart(2, '0');
            
            return yyyy + '-' + mm + '-' + dd + ' ' + hh + ':' + min + ':' + ss;
        }

        setInterval(() => {
            textTime = incrementTimeStr(textTime);
            timeSpan.innerText = textTime;
        }, 1000);
    }
});
