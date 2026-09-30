console.log('Custom Admin JS executing...');
document.addEventListener("DOMContentLoaded", function() {
    var jazzyActions = document.getElementById("jazzy-actions") || document.querySelector(".submit-row");
    var formCard = document.querySelector("form .card") || document.querySelector(".card");
    var cardBody = document.querySelector("form .card-body") || document.querySelector(".card-body");
    
    if (jazzyActions) {
        // Collect all buttons
        var allBtns = jazzyActions.querySelectorAll("input[type='submit'], a.btn, button, .deletelink, .historylink");
        while(jazzyActions.firstChild){jazzyActions.removeChild(jazzyActions.firstChild);}
        
        var deleteBtn = null;
        var historyBtn = null;
        var saveBtns = [];
        var mainSave = null;
        
        allBtns.forEach(function(btn) {
            if (btn.classList.contains("deletelink") || btn.classList.contains("btn-danger")) {
                deleteBtn = btn;
            } else if (btn.classList.contains("historylink")) {
                historyBtn = btn;
            } else if (btn.name === "_save") {
                mainSave = btn;
            } else {
                saveBtns.push(btn);
            }
            // Reset floats/margins
            btn.style.margin = "0";
            btn.style.float = "none";
        });
        
        // Create Back Button
        var backBtn = document.createElement("a");
        backBtn.href = "javascript:history.back()";
        backBtn.className = "btn btn-secondary";
        backBtn.innerHTML = "<i class=\"fas fa-arrow-left\" style=\"margin-right: 5px;\"></i> Back";
        backBtn.style.marginRight = "10px";
        
        // Add elements back in order
        var leftGroup = document.createElement("div");
        leftGroup.style.display = "flex";
        leftGroup.style.gap = "10px";
        leftGroup.style.marginRight = "auto";
        leftGroup.appendChild(backBtn);
        if (deleteBtn) leftGroup.appendChild(deleteBtn);
        
        jazzyActions.appendChild(leftGroup);
        
        saveBtns.forEach(function(btn) { jazzyActions.appendChild(btn); });
        if (historyBtn) jazzyActions.appendChild(historyBtn);
        if (mainSave) jazzyActions.appendChild(mainSave);
        
        // Style jazzyActions
        
        jazzyActions.style.padding = "15px 20px";
        
        jazzyActions.style.display = "flex";
        jazzyActions.style.alignItems = "center";
        jazzyActions.style.gap = "10px";
        
        // Move jazzyActions inside the Card
        if (formCard) {
            jazzyActions.style.borderRadius = "0 0 4px 4px";
            formCard.appendChild(jazzyActions);
            if (cardBody) {
                cardBody.style.borderBottomLeftRadius = "0";
                cardBody.style.borderBottomRightRadius = "0";
            }
        }
    }
});



document.addEventListener('DOMContentLoaded', function() {
    // IP Request Badge
    fetch('/admin/network/iprequest/api/pending-count/')
        .then(r => r.json())
        .then(data => {
            if (data.count > 0) {
                const links = document.querySelectorAll('.nav-sidebar .nav-link p');
                links.forEach(link => {
                    if (link.innerText.toLowerCase().includes('ip request')) {
                        const badge = document.createElement('span');
                        badge.className = 'right badge badge-danger';
                        badge.style.animation = 'pulse 2s infinite';
                        badge.innerText = data.count + ' New';
                        
                        // Add pulse animation CSS dynamically
                        if (!document.getElementById('pulse-anim')) {
                            const style = document.createElement('style');
                            style.id = 'pulse-anim';
                            style.innerHTML = '@keyframes pulse { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); } 70% { transform: scale(1.05); box-shadow: 0 0 0 6px rgba(220, 53, 69, 0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); } }';
                            document.head.appendChild(style);
                        }
                        
                        link.appendChild(badge);
                    }
                });
            }
        }).catch(err => console.log('Badge fetch failed:', err));
});
