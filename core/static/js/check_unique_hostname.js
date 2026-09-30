document.addEventListener('DOMContentLoaded', function() {
    const hostnameInput = document.getElementById('id_hostname');
    const uniqueCheckbox = document.getElementById('id_is_unique_hostname');
    
    if (!hostnameInput || !uniqueCheckbox) return;
    
    // In Django admin, we can get the ID from the URL if we are editing
    // The URL is like /admin/network/ipaddress/123/change/
    const urlParts = window.location.pathname.split('/');
    let currentId = '';
    if (urlParts[urlParts.length - 2] === 'change') {
        currentId = urlParts[urlParts.length - 3];
    }
    
    function checkHostname() {
        const hostname = hostnameInput.value.trim();
        const wantsUnique = uniqueCheckbox.checked;
        
        if (!hostname) {
            clearWarning();
            return;
        }
        
        // Call the API endpoint
        let url = `/admin/network/ipaddress/api/check-hostname/?hostname=${encodeURIComponent(hostname)}&wants_unique=${wantsUnique}`;
        if (currentId) {
            url += `&exclude_id=${currentId}`;
        }
        
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'error') {
                    showWarning(data.message);
                } else {
                    clearWarning();
                }
            })
            .catch(err => console.error("Error checking hostname:", err));
    }
    
    let warningDiv = null;
    function showWarning(message) {
        clearWarning(); // remove existing
        warningDiv = document.createElement('div');
        warningDiv.style.color = '#dc3545';
        warningDiv.style.fontWeight = 'bold';
        warningDiv.style.marginTop = '5px';
        warningDiv.className = 'hostname-warning';
        warningDiv.textContent = message;
        
        hostnameInput.parentNode.appendChild(warningDiv);
        hostnameInput.style.borderColor = '#dc3545';
        hostnameInput.style.boxShadow = '0 0 0 3px rgba(220, 53, 69, 0.2)';
    }
    
    function clearWarning() {
        if (warningDiv && warningDiv.parentNode) {
            warningDiv.parentNode.removeChild(warningDiv);
            warningDiv = null;
        }
        hostnameInput.style.borderColor = '';
        hostnameInput.style.boxShadow = '';
    }
    
    // Check when typing finishes (blur)
    hostnameInput.addEventListener('blur', checkHostname);
    // Check when user toggles the checkbox
    uniqueCheckbox.addEventListener('change', checkHostname);
});
