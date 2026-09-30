document.addEventListener('DOMContentLoaded', function() {
    

    const enableInput = document.getElementById('id_enable_auto_assign');
    const startInput = document.getElementById('id_auto_assign_range_start');
    const endInput = document.getElementById('id_auto_assign_range_end');
    const netInput = document.getElementById('id_network_address');

    if (!enableInput || !startInput || !endInput || !netInput) return;

            // --- UI ENHANCEMENTS ---
    const nameInput = document.getElementById('id_name');

    // Add a beautiful header banner
    if (netInput && netInput.value && nameInput && nameInput.value) {
                        const target = netInput.closest('form');
        if (target) {
            const banner = document.createElement('div');
            banner.innerHTML = '<div style="background: linear-gradient(135deg, #0f4c81, #3b82f6); color: white; padding: 20px 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 15px;">' +
                '<i class="fas fa-network-wired" style="font-size: 28px; opacity: 0.8;"></i>' +
                '<div>' +
                    '<h3 style="margin: 0; font-size: 20px; font-weight: 700; color: white;">Subnet Configuration</h3>' +
                    '<div style="font-size: 14px; opacity: 0.9; margin-top: 4px; font-family: monospace;">' + netInput.value + ' &mdash; ' + nameInput.value + '</div>' +
                '</div>' +
            '</div>';
            target.parentNode.insertBefore(banner, target);
        }
    }

    // Hide the entire "End Range" field wrapper
    const endFieldContainer = document.querySelector('.field-auto_assign_range_end');
    if (endFieldContainer) {
        endFieldContainer.style.display = 'none';
    }

        // Change the label of the Start Range to be the overarching Slider label
    const startLabel = document.querySelector('.field-auto_assign_range_start label');
    if (startLabel) {
        startLabel.innerText = 'IP Pool Range';
    }
    const startHelp = document.querySelector('.field-auto_assign_range_start .help-block');
    if (startHelp) {
        startHelp.innerText = 'Use the graphical slider below to select the start and end IP boundaries.';
    }

    // --- 1. Global Auto Assign Check ---
    if (window.GLOBAL_AUTO_ASSIGN === false) {
        enableInput.disabled = true;
        startInput.disabled = true;
        endInput.disabled = true;

        const wrapper = document.querySelector('.field-enable_auto_assign');
        if (wrapper) {
            const fieldset = wrapper.closest('fieldset');
            if (fieldset) {
                const warningMsg = document.createElement('div');
                warningMsg.innerHTML = '<div style="background: #fee2e2; color: #991b1b; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-weight: 600; border: 1px solid #f87171;"><i class="fas fa-exclamation-triangle"></i> System-wide Automatic IP Assignment is disabled. You must enable it in System Settings first before configuring subnet rules.</div>';
                fieldset.insertBefore(warningMsg, fieldset.firstChild);
            }
        }
        return; 
    }

    // --- 2. Graphical IP Range Slider ---
    
    // Hide original inputs but keep labels for structure
    startInput.style.display = 'none';
    endInput.style.display = 'none';

    const sliderWrapper = document.createElement('div');
    sliderWrapper.style.padding = '20px 10px 40px 10px';
    sliderWrapper.style.maxWidth = '600px';

    const infoDisplay = document.createElement('div');
    infoDisplay.style.marginBottom = '15px';
    infoDisplay.style.fontWeight = '600';
    infoDisplay.style.color = '#3b82f6';
    infoDisplay.style.fontSize = '15px';
    infoDisplay.innerHTML = `Auto-Assign Pool: <span id="pool-start">...</span> &nbsp;&mdash;&nbsp; <span id="pool-end">...</span>`;
    
    const sliderDiv = document.createElement('div');
    sliderDiv.id = 'ip-range-slider';
    sliderDiv.style.height = '10px';
    
    sliderWrapper.appendChild(infoDisplay);
    sliderWrapper.appendChild(sliderDiv);

    startInput.parentNode.appendChild(sliderWrapper);

    // IP Math Functions
    function ipToLong(ip) {
        return ip.split('.').reduce((int, oct) => (int << 8) + parseInt(oct, 10), 0) >>> 0;
    }
    function longToIp(int) {
        return [(int >>> 24) & 0xFF, (int >>> 16) & 0xFF, (int >>> 8) & 0xFF, int & 0xFF].join('.');
    }
    
    function parseCIDR(cidr) {
        if (!cidr || !cidr.includes('/')) return null;
        const parts = cidr.split('/');
        const ip = parts[0];
        const mask = parseInt(parts[1], 10);
        if (mask < 0 || mask > 32) return null;
        
        const ipLong = ipToLong(ip);
        const maskLong = (0xFFFFFFFF << (32 - mask)) >>> 0;
        const netLong = (ipLong & maskLong) >>> 0;
        const brdLong = (netLong | ~maskLong) >>> 0;
        
        const start = netLong + 1;
        const end = brdLong - 1;
        
        if (start > end) return null; // e.g. /32 or /31 edge cases
        
        return { start: start, end: end };
    }

    let sliderInstance = null;

    function initSlider() {
        const cidr = netInput.value;
        const range = parseCIDR(cidr);
        
        if (!range || typeof noUiSlider === 'undefined') {
            sliderWrapper.style.display = 'none';
            return;
        }
        
        let initialStart = startInput.value ? ipToLong(startInput.value) : range.start;
        let initialEnd = endInput.value ? ipToLong(endInput.value) : range.end;

        if (initialStart < range.start || initialStart > range.end) initialStart = range.start;
        if (initialEnd > range.end || initialEnd < range.start) initialEnd = range.end;
        if (initialStart > initialEnd) {
            initialStart = range.start;
            initialEnd = range.end;
        }

        if (sliderInstance) {
            sliderDiv.noUiSlider.destroy();
        }

        sliderInstance = noUiSlider.create(sliderDiv, {
            start: [initialStart, initialEnd],
            connect: true,
            step: 1,
            range: {
                'min': range.start,
                'max': range.end
            }
        });

        const connectBar = sliderDiv.querySelector('.noUi-connect');
        if (connectBar) {
            connectBar.style.background = '#3b82f6';
        }

        sliderDiv.noUiSlider.on('update', function(values, handle) {
            const startVal = longToIp(Math.round(values[0]));
            const endVal = longToIp(Math.round(values[1]));
            
            document.getElementById('pool-start').innerText = startVal;
            document.getElementById('pool-end').innerText = endVal;
            
            startInput.value = startVal;
            endInput.value = endVal;
        });
    }

    // --- 3. Toggle Visibility based on Checkbox ---
    function toggleFields() {
        const isEnabled = enableInput.checked;
        const startField = document.querySelector('.field-auto_assign_range_start');
        const endField = document.querySelector('.field-auto_assign_range_end');
        
        if (startField) startField.style.display = isEnabled ? '' : 'none';
        
        if (sliderWrapper) sliderWrapper.style.display = isEnabled ? 'block' : 'none';
        
        // If disabling, optionally clear values so they don't get saved, 
        // but it's better to keep them if user re-enables.
    }

    enableInput.addEventListener('change', toggleFields);
    toggleFields(); // Init state

    // Initialize slider if enabled
    function tryInit() {
        if (typeof noUiSlider !== 'undefined') {
            initSlider();
        } else {
            setTimeout(tryInit, 100);
        }
    }
    if (netInput.value) {
        tryInit();
    }

    netInput.addEventListener('change', function() {
        initSlider();
    });
});









