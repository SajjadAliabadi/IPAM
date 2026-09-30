document.addEventListener('DOMContentLoaded', function() {
    const vlanIdInput = document.getElementById('id_vlan_id');
    const nameInput = document.getElementById('id_name');

    if (vlanIdInput && vlanIdInput.value && nameInput && nameInput.value) {
        // Only run if we're on the VLAN change form (we assume id_vlan_id means it's the VLAN form)
        // Wait, Subnet also has a VLAN dropdown, but its ID is `id_vlan`. 
        // VLAN model has `vlan_id` field, so its input is `id_vlan_id`.
        
        const target = vlanIdInput.closest('form');
        if (target) {
            const banner = document.createElement('div');
            banner.innerHTML = '<div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px;">' +
                '<i class="fas fa-layer-group" style="font-size: 28px; opacity: 0.8;"></i>' +
                '<div>' +
                    '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">VLAN Configuration</h3>' +
                    '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">VLAN ' + vlanIdInput.value + ' &mdash; ' + nameInput.value + '</div>' +
                '</div>' +
            '</div>';
            target.parentNode.insertBefore(banner, target);
        }
    }
});
