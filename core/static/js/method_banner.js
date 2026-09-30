document.addEventListener('DOMContentLoaded', function() {
    const nameInput = document.getElementById('id_name');
    
    if (nameInput) {
        const target = nameInput.closest('form');
        if (target) {
            const banner = document.createElement('div');
            banner.innerHTML = '<div style="background: linear-gradient(135deg, #be185d, #ec4899); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px;">' +
                '<i class="fas fa-stethoscope" style="font-size: 28px; opacity: 0.8;"></i>' +
                '<div>' +
                    '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">Health Check Method</h3>' +
                    '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">Define scanning behavior for discovery</div>' +
                '</div>' +
            '</div>';
            target.parentNode.insertBefore(banner, target);
        }
    }
});
