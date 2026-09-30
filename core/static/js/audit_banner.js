document.addEventListener('DOMContentLoaded', function() {
    const actionInput = document.getElementById('id_action') || document.querySelector('.field-action .readonly');
    
    if (actionInput) {
        const target = actionInput.closest('form');
        if (target) {
            const banner = document.createElement('div');
            banner.innerHTML = '<div style="background: linear-gradient(135deg, #0f766e, #14b8a6); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px;">' +
                '<i class="fas fa-shield-alt" style="font-size: 28px; opacity: 0.8;"></i>' +
                '<div>' +
                    '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">Audit Trail Event</h3>' +
                    '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">Immutable security and access log</div>' +
                '</div>' +
            '</div>';
            target.parentNode.insertBefore(banner, target);
        }
    }
});
