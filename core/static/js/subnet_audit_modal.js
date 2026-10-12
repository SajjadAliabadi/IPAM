document.addEventListener('DOMContentLoaded', function() {
    var auditBtn = document.getElementById('btn-open-subnet-audit');
    if (!auditBtn) return;

    // Build the modal HTML and inject into body
    var modalHtml = `
    <div class="modal fade" id="subnetAuditModal" tabindex="-1" role="dialog" aria-labelledby="subnetAuditModalLabel" aria-hidden="true" style="z-index: 10500;">
        <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
            <div class="modal-content" style="border-radius: 12px; border: none; box-shadow: 0 10px 25px rgba(0,0,0,0.15); overflow: hidden;">
                <div class="modal-header" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: white; padding: 16px 24px; border-bottom: none;">
                    <h5 class="modal-title" id="subnetAuditModalLabel" style="font-size: 17px; font-weight: 700; display: flex; align-items: center; gap: 10px;">
                        <i class="fas fa-stethoscope" style="color: #38bdf8;"></i> Subnet IP Integrity Scanner
                    </h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close" style="color: white; opacity: 0.8; text-shadow: none;">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body" id="subnetAuditBody" style="padding: 24px; min-height: 200px; background: #f8fafc;">
                    <!-- Dynamic content injected here -->
                </div>
                <div class="modal-footer" id="subnetAuditFooter" style="background: white; border-top: 1px solid #e2e8f0; padding: 12px 24px; display: flex; justify-content: space-between;">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal" style="border-radius: 6px; font-weight: 600;">Close</button>
                    <div id="subnetAuditActionButtons"></div>
                </div>
            </div>
        </div>
    </div>`;

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    var modalElem = $('#subnetAuditModal');
    var modalBody = document.getElementById('subnetAuditBody');
    var modalActions = document.getElementById('subnetAuditActionButtons');

    auditBtn.addEventListener('click', function(e) {
        e.preventDefault();
        startAuditScan();
    });

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function startAuditScan() {
        modalElem.modal('show');
        modalBody.innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <i class="fas fa-circle-notch fa-spin" style="font-size: 38px; color: #3b82f6; margin-bottom: 16px;"></i>
                <h4 style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px;">Scanning Subnet Integrity...</h4>
                <p style="color: #64748b; font-size: 13.5px; margin: 0;">Analyzing IP address bindings, CIDR boundaries, and duplicates across all subnets.</p>
            </div>
        `;
        modalActions.innerHTML = '';

        fetch('/admin/network/systemsettings/api/audit-subnets/')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.status !== 'ok') {
                    modalBody.innerHTML = `<div class="alert alert-danger">Error running scan: ${data.message || 'Unknown error'}</div>`;
                    return;
                }
                renderAuditResults(data.subnets);
            })
            .catch(function(err) {
                modalBody.innerHTML = `<div class="alert alert-danger">Network error: ${err}</div>`;
            });
    }

    function renderAuditResults(subnets) {
        var issueSubnets = subnets.filter(function(s) { return s.has_issues; });

        if (issueSubnets.length === 0) {
            modalBody.innerHTML = `
                <div style="text-align: center; padding: 40px 20px; background: white; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="width: 60px; height: 60px; background: #dcfce7; color: #16a34a; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; font-size: 28px;">
                        <i class="fas fa-check"></i>
                    </div>
                    <h4 style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">All Subnets Are Healthy!</h4>
                    <p style="color: #64748b; font-size: 14px; max-width: 480px; margin: 0 auto;">Every single subnet has exact matching CIDR boundaries. No out-of-bounds IPs, missing hosts, or duplicates were detected.</p>
                </div>
            `;
            modalActions.innerHTML = '';
            return;
        }

        var html = `
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #ef4444; padding: 14px 18px; border-radius: 8px; margin-bottom: 18px;">
                <div style="font-weight: 700; color: #991b1b; font-size: 14.5px; margin-bottom: 4px;">
                    <i class="fas fa-exclamation-triangle" style="margin-right: 6px;"></i> Found ${issueSubnets.length} Subnet(s) with IP Discrepancies
                </div>
                <div style="color: #7f1d1d; font-size: 13px;">
                    Review the problematic subnets below. Select which subnets you wish to repair and synchronize.
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-weight: 700; font-size: 13px; color: #475569; text-transform: uppercase;">Affected Subnets</span>
                <button type="button" id="btn-toggle-all-audit" class="btn btn-xs btn-light" style="font-size: 12px; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 4px;">Toggle Select All</button>
            </div>

            <div style="max-height: 340px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;">
        `;

        issueSubnets.forEach(function(s) {
            var issueBullets = s.issues.map(function(iss) {
                return `<li style="font-size: 12.5px; color: #b91c1c; margin-bottom: 2px;"><i class="fas fa-times-circle" style="margin-right: 5px;"></i>${iss}</li>`;
            }).join('');

            html += `
                <div style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; display: flex; align-items: flex-start; gap: 14px; transition: border-color 0.2s;" onmouseover="this.style.borderColor='#94a3b8'" onmouseout="this.style.borderColor='#e2e8f0'">
                    <input type="checkbox" class="audit-subnet-checkbox" value="${s.id}" checked style="margin-top: 4px; transform: scale(1.2); cursor: pointer;">
                    <div style="flex-grow: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; color: #1e293b; font-size: 15px;">
                                <i class="fas fa-network-wired" style="color: #3b82f6; margin-right: 6px;"></i> ${s.network}
                                <span style="font-weight: normal; color: #64748b; font-size: 13px; margin-left: 6px;">(${s.name})</span>
                            </span>
                            <span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">
                                ${s.total_ips} in DB (Expected: ${s.expected_ips})
                            </span>
                        </div>
                        <ul style="margin: 0; padding-left: 18px; list-style-type: none;">
                            ${issueBullets}
                        </ul>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        modalBody.innerHTML = html;

        modalActions.innerHTML = `
            <button type="button" class="btn btn-success" id="btn-execute-repair" style="border-radius: 6px; font-weight: 700; padding: 6px 18px; background: #16a34a; border-color: #16a34a; display: inline-flex; align-items: center; gap: 8px;">
                <i class="fas fa-wrench"></i> Repair Selected Subnets
            </button>
        `;

        document.getElementById('btn-toggle-all-audit').addEventListener('click', function() {
            var cbs = document.querySelectorAll('.audit-subnet-checkbox');
            var anyChecked = Array.from(cbs).some(function(cb) { return cb.checked; });
            cbs.forEach(function(cb) { cb.checked = !anyChecked; });
        });

        document.getElementById('btn-execute-repair').addEventListener('click', function() {
            var checkedCbs = document.querySelectorAll('.audit-subnet-checkbox:checked');
            var selectedIds = Array.from(checkedCbs).map(function(cb) { return parseInt(cb.value); });

            if (selectedIds.length === 0) {
                alert('Please select at least one subnet to repair.');
                return;
            }

            if (!confirm(`Are you sure you want to clean, purge stale IPs, and re-scan ${selectedIds.length} selected subnet(s)?`)) {
                return;
            }

            var repairBtn = document.getElementById('btn-execute-repair');
            repairBtn.disabled = true;
            repairBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Repairing & Scanning...';

            fetch('/admin/network/systemsettings/api/repair-subnets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ subnet_ids: selectedIds })
            })
            .then(function(r) { return r.json(); })
            .then(function(resp) {
                if (resp.status === 'ok') {
                    modalBody.innerHTML = `
                        <div style="text-align: center; padding: 30px 20px; background: white; border-radius: 8px; border: 1px solid #bbf7d0;">
                            <div style="width: 56px; height: 56px; background: #dcfce7; color: #16a34a; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto; font-size: 26px;">
                                <i class="fas fa-check-double"></i>
                            </div>
                            <h4 style="font-size: 17px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">Repair Completed Successfully!</h4>
                            <p style="color: #475569; font-size: 14px; margin-bottom: 20px;">${resp.message}</p>
                            <button type="button" class="btn btn-primary" onclick="window.location.reload();" style="border-radius: 6px; font-weight: 600;">
                                <i class="fas fa-sync-alt" style="margin-right: 6px;"></i> Refresh System Settings
                            </button>
                        </div>
                    `;
                    modalActions.innerHTML = '';
                } else {
                    alert('Error: ' + resp.message);
                    repairBtn.disabled = false;
                    repairBtn.innerHTML = '<i class="fas fa-wrench"></i> Repair Selected Subnets';
                }
            })
            .catch(function(err) {
                alert('Request failed: ' + err);
                repairBtn.disabled = false;
                repairBtn.innerHTML = '<i class="fas fa-wrench"></i> Repair Selected Subnets';
            });
        });
    }
});
