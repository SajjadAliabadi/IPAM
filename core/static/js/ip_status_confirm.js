document.addEventListener('DOMContentLoaded', function() {
    const statusField = document.getElementById('id_status');
    const form = document.getElementById('ipaddress_form');
    
    if (!statusField || !form) return;
    
    // Remember the initial status loaded from the database
    const originalStatus = statusField.value;
    
    // Find the discovery reason. In Django admin, readonly fields are usually inside div.field-discovery_reason div.readonly
    const reasonDiv = document.querySelector('.field-discovery_reason .readonly');
    let reasonText = "";
    if (reasonDiv && reasonDiv.textContent.trim() && reasonDiv.textContent.trim() !== "-") {
        reasonText = reasonDiv.textContent.trim();
    }
    
    form.addEventListener('submit', function(e) {
        const newStatus = statusField.value;
        
        // If the admin is changing it FROM 'used' TO something else
        if (originalStatus === 'used' && newStatus !== 'used') {
            
            // Build warning message
            let msg = "WARNING: Are you sure you want to change this IP status?\n\n";
            if (reasonText) {
                msg += "This IP was actively detected as IN-USE by: " + reasonText + "\n\n";
                msg += "If you mark it as available and reassign it, you will likely cause an IP Conflict on the network!";
            } else {
                msg += "This IP is currently marked as In Use. Changing it to " + newStatus + " could lead to IP conflicts if it is still active on the network.";
            }
            
            const confirmed = confirm(msg);
            if (!confirmed) {
                // Stop the form submission
                e.preventDefault();
                // Reset the button state if Jazzmin disables it on click
                const submitBtns = form.querySelectorAll('input[type="submit"]');
                submitBtns.forEach(btn => btn.disabled = false);
            }
        }
    });
});
