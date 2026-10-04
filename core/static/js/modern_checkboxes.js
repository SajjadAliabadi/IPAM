document.addEventListener("DOMContentLoaded", function() {
    const checkboxes = document.querySelectorAll('.field-check_methods input[type="checkbox"]');
    if (checkboxes.length === 0) return;
    
    checkboxes.forEach(cb => {
        // Hide the checkbox visually but keep it accessible
        cb.style.position = 'absolute';
        cb.style.opacity = '0';
        cb.style.pointerEvents = 'none';
        
        // Setup initial state
        const label = cb.closest('label');
        if (!label) return;
        
        label.classList.add('modern-pill-label');
        
        // Add check icon placeholder
        const icon = document.createElement('i');
        icon.className = 'fas fa-check check-icon';
        label.prepend(icon);
        
        if (cb.checked) {
            label.classList.add('is-checked');
        }
        
        // Change event
        cb.addEventListener('change', function() {
            if (this.checked) {
                label.classList.add('is-checked');
            } else {
                label.classList.remove('is-checked');
            }
        });
    });
});
