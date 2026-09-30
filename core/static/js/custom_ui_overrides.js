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


