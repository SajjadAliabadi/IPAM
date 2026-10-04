function openStatusModal(ipId, ipAddress, currentStatus, hostname, mac, os, reason) {
    // Remove existing modal if any
    const existing = document.getElementById('ipStatusModal');
    if (existing) {
        existing.remove();
    }
    
    // Format nulls
    hostname = (hostname === 'None' || !hostname) ? '' : hostname;
    mac = (mac === 'None' || !mac) ? '' : mac;
    os = (os === 'None' || !os) ? '' : os;
    reason = (reason === 'None' || !reason) ? '' : reason;

    const modalHtml = `
    <div class="modal fade" id="ipStatusModal" tabindex="-1" role="dialog" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content" style="border-radius: 16px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
          <div class="modal-header" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-bottom: 1px solid #e2e8f0; border-radius: 16px 16px 0 0; padding: 20px 25px; display: flex; justify-content: space-between; align-items: center;">
            <h5 class="modal-title" style="margin: 0; font-weight: 700; color: #1e293b;"><i class="fas fa-edit" style="color: #3b82f6; margin-right: 8px;"></i> Change Details for ${ipAddress}</h5>
            <button type="button" onclick="jQuery('#ipStatusModal').modal('hide');" style="background: transparent; border: none; font-size: 22px; color: #94a3b8; cursor: pointer; outline: none; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 8px; transition: all 0.2s;" onmouseover="this.style.background='#e2e8f0'; this.style.color='#ef4444';" onmouseout="this.style.background='transparent'; this.style.color='#94a3b8';">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <form method="POST" action="/admin/network/ipaddress/${ipId}/change-status-modal/">
            <div class="modal-body" style="padding: 25px;">
              <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
              
              <div class="form-group mb-4">
                <label style="font-weight: 600; color: #475569; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">New Status</label>
                <select name="status" class="form-control" style="border-radius: 8px; border-color: #cbd5e1; box-shadow: none;">
                  <option value="available" ${currentStatus === 'available' ? 'selected' : ''}>Available</option>
                  <option value="reserved" ${currentStatus === 'reserved' ? 'selected' : ''}>Reserved</option>
                  <option value="used" ${currentStatus === 'used' ? 'selected' : ''}>In Use</option>
                </select>
              </div>

              <div class="form-group mb-3">
                <label style="font-weight: 600; color: #475569; font-size: 13px;">Hostname</label>
                <input type="text" name="hostname" class="form-control" value="${hostname}" placeholder="e.g. SRV-WEB-01" style="border-radius: 8px; border-color: #cbd5e1;">
              </div>

              <div class="row">
                <div class="col-md-6 form-group mb-3">
                  <label style="font-weight: 600; color: #475569; font-size: 13px;">MAC Address</label>
                  <input type="text" name="mac_address" class="form-control" value="${mac}" placeholder="AA:BB:CC:DD:EE:FF" style="border-radius: 8px; border-color: #cbd5e1;">
                </div>
                <div class="col-md-6 form-group mb-3">
                  <label style="font-weight: 600; color: #475569; font-size: 13px;">Operating System</label>
                  <input type="text" name="os_name" class="form-control" value="${os}" placeholder="e.g. Windows Server" style="border-radius: 8px; border-color: #cbd5e1;">
                </div>
              </div>

              <div class="form-group mb-0">
                <label style="font-weight: 600; color: #475569; font-size: 13px;">Discovery Reason / Description</label>
                <input type="text" name="discovery_reason" class="form-control" value="${reason}" placeholder="Why is this IP reserved/used?" style="border-radius: 8px; border-color: #cbd5e1;">
              </div>

            </div>
            <div class="modal-footer" style="border-top: 1px solid #e2e8f0; padding: 15px 25px; border-radius: 0 0 16px 16px; background: #f8fafc;">
              <button type="button" onclick="jQuery('#ipStatusModal').modal('hide');" class="btn btn-light" style="border-radius: 8px; font-weight: 600; color: #475569; border: 1px solid #e2e8f0;">Cancel</button>
              <button type="submit" class="btn btn-primary" style="border-radius: 8px; font-weight: 600; padding: 8px 20px; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);">Save Changes</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Check if jQuery/Bootstrap is loaded for modals
    if (typeof jQuery !== 'undefined' && typeof jQuery.fn.modal !== 'undefined') {
        jQuery('#ipStatusModal').modal('show');
    } else {
        alert("Bootstrap JS is not loaded properly!");
    }
}