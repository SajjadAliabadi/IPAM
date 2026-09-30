document.addEventListener('DOMContentLoaded', function() {
    // Jazzmin/Django admin uses jQuery
    if (typeof jQuery === 'undefined' && typeof django !== 'undefined' && django.jQuery) {
        window.jQuery = django.jQuery;
        window.$ = django.jQuery;
    }
    
    const protocolField = document.getElementById('id_protocol');
    if (!protocolField) return;

    // In Django admin, rows usually have the class .field-<fieldname>
    const portFieldRow = document.querySelector('.field-custom_port');
    const scriptFieldRow = document.querySelector('.field-script_content');

    function toggleFields() {
        const val = protocolField.value;
        
        // Handle Custom Port visibility
        if (portFieldRow) {
            if (val === 'tcp_port') {
                portFieldRow.style.display = ''; // Reverts to flex
            } else {
                portFieldRow.style.display = 'none';
                // Don't clear value so we don't accidentally lose user's data on a misclick
            }
        }
        
        // Handle Script Content visibility
        if (scriptFieldRow) {
            if (val === 'custom') {
                scriptFieldRow.style.display = '';
            } else {
                scriptFieldRow.style.display = 'none';
            }
        }
    }

    // Run on page load
    toggleFields();

    // Listen using jQuery if available (Select2 fires events via jQuery)
    if (typeof $ !== 'undefined') {
        $('#id_protocol').on('change', toggleFields);
    } else {
        protocolField.addEventListener('change', toggleFields);
    }
});

