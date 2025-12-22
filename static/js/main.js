/**
 * FAST COPY - MASTER JAVASCRIPT ENGINE
 * Version: 12.0 (Final Integrated Build)
 * Localization: Asia/Kolkata (IST)
 * Purpose: Handles unique PDF analysis, dynamic pricing, and cart synchronization.
 */

let globalPageCount = 0; // Persistent state for the current active document

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize AOS (Animate On Scroll)
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: true,
            offset: 50,
            easing: 'ease-out-back'
        });
    }

    // 2. Pricing Engine Event Listeners
    // Re-calculates price whenever paper type, sides, or copies are modified
    const pricingInputs = document.querySelectorAll('#pType, #sType, #copies');
    pricingInputs.forEach(input => {
        input.addEventListener('change', () => {
            updateLabels();
            calculatePrice();
        });
        input.addEventListener('input', calculatePrice);
    });

    // Initial label sync for cart hidden fields
    updateLabels();
});

/**
 * 1. PRICING CALCULATION ENGINE
 * Formula: (Detected Pages * Paper Price * Side Multiplier) * Copies
 */
function calculatePrice() {
    const pPrice = parseFloat(document.getElementById('pType')?.value) || 0;
    const sMultiplier = parseFloat(document.getElementById('sType')?.value) || 1;
    const copies = parseInt(document.getElementById('copies')?.value) || 1;

    // Calculate total bill
    let total = Math.round(globalPageCount * pPrice * sMultiplier * copies);

    const priceDisplay = document.getElementById('price-display');
    const hiddenPriceInput = document.getElementById('total-price-hidden');

    // Update frontend UI and hidden form value for Django
    if (priceDisplay) priceDisplay.innerText = total;
    if (hiddenPriceInput) hiddenPriceInput.value = total;

    updateLabels();
}

/**
 * 2. PDF ANALYSIS ENGINE (AJAX)
 * Extracts page count from the server to ensure unique billing per user/file.
 */
function handleFileUpload(event, apiUrl, csrfToken) {
    const file = event.target.files[0];
    const fileStatus = document.getElementById('file-status-text');
    const pageBadge = document.getElementById('page-count-badge');

    if (!file) {
        resetPricingHub();
        return;
    }

    // UI Feedback: Loading State
    fileStatus.innerHTML = `<i class="fas fa-spinner fa-spin text-blue-500 mr-2"></i> Analyzing ${file.name}...`;

    const formData = new FormData();
    formData.append('document', file);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(apiUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest' // Ensures Django identifies the AJAX session
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            globalPageCount = parseInt(data.pages); 
            
            // UI Update: Success
            fileStatus.innerHTML = `<i class="fas fa-check-circle text-green-500 mr-2"></i> Ready: ${file.name}`;
            
            if (pageBadge) {
                pageBadge.innerText = `Pages: ${globalPageCount}`;
                pageBadge.style.display = 'inline-block';
            }
            
            calculatePrice(); // Recalculate based on new page count
            showToast(`${globalPageCount} Pages Analyzed`, "success");
        } else {
            fileStatus.innerHTML = `<span class="text-red-500"><i class="fas fa-times-circle"></i> Error Analyzing File</span>`;
            showToast(data.message || "Invalid PDF format", "error");
            resetPricingHub();
        }
    })
    .catch(err => {
        console.error("Analysis Error:", err);
        showToast("Server Connection Lost", "error");
    });
}

/**
 * 3. PRICING HUB RESET
 * Prevents previous order data from leaking into the next upload.
 */
function resetPricingHub() {
    globalPageCount = 0;
    document.getElementById('price-display').innerText = "0";
    document.getElementById('total-price-hidden').value = "0";
    document.getElementById('file-status-text').innerText = "No file selected";
}

/**
 * 4. UI UTILITIES
 */

function updateLabels() {
    const pSelect = document.getElementById('pType');
    const sSelect = document.getElementById('sType');
    
    if (pSelect && sSelect) {
        const pLabelHidden = document.getElementById('p-label-hidden');
        const sLabelHidden = document.getElementById('s-label-hidden');
        
        if (pLabelHidden) pLabelHidden.value = pSelect.options[pSelect.selectedIndex].text;
        if (sLabelHidden) sLabelHidden.value = sSelect.options[sSelect.selectedIndex].text;
    }
}

function showToast(message, type) {
    const existing = document.querySelector('.custom-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    const color = type === 'success' ? 'bg-green-600' : 'bg-red-600';
    
    toast.className = `custom-toast fixed bottom-10 right-10 ${color} text-white px-8 py-4 rounded-full shadow-2xl z-[2000] font-black uppercase tracking-widest text-[10px] animate-bounce`;
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-triangle-exclamation'} mr-2"></i> ${message}`;
    
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = '0.5s opacity';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function updateCartBadge(count) {
    const badge = document.getElementById('cart-count-badge');
    if (badge) {
        badge.innerText = count;
        badge.classList.add('animate-pulse');
        setTimeout(() => badge.classList.remove('animate-pulse'), 1000);
    }
}