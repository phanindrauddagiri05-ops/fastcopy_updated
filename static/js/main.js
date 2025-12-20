/**
 * FAST COPY - MASTER JAVASCRIPT ENGINE
 * Version: 7.0 (Final "Pin-to-Pin" Verified Build)
 */

let globalPageCount = 0; // Globally tracks the document pages

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize AOS (Animate On Scroll) for 3D effects
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: true,
            offset: 50
        });
    }

    // 2. Global Event Listeners for Pricing
    // Re-calculates price whenever a dropdown or copy count changes
    const pricingInputs = document.querySelectorAll('#pType, #sType, #copies');
    pricingInputs.forEach(input => {
        input.addEventListener('change', () => {
            updateLabels();
            calculatePrice();
        });
        input.addEventListener('input', calculatePrice);
    });
});

/**
 * 1. SERVICE THEME SWITCHER
 * Swaps service titles, 3D border colors, and hidden names dynamically
 */
function updateService(name, color, id) {
    // Reset all tabs to default state
    document.querySelectorAll('.service-tab').forEach(t => {
        t.style.borderColor = "#f1f5f9";
        t.classList.remove('active-tab', 'shadow-2xl', '-translate-y-2');
    });

    // Highlight the active tab
    const activeTab = document.getElementById('tab-' + id);
    if (activeTab) {
        activeTab.style.borderColor = color;
        activeTab.classList.add('active-tab', 'shadow-2xl', '-translate-y-2');
    }

    // Update the main card visuals
    const mainCard = document.getElementById('main-card');
    const formTitle = document.getElementById('form-title');
    const hiddenServiceName = document.getElementById('hidden-service-name');

    if (mainCard) mainCard.style.borderColor = color;
    if (formTitle) {
        formTitle.innerText = name;
        formTitle.style.color = color;
    }
    if (hiddenServiceName) hiddenServiceName.value = name;

    // Refresh pricing context for the new service
    calculatePrice();
}

/**
 * 2. PDF ANALYSIS (AJAX)
 * Extracts page count and triggers immediate price calculation
 */
function handleFileUpload(event, apiUrl, csrfToken) {
    const file = event.target.files[0];
    const fileStatus = document.getElementById('file-status-text');
    const pageBadge = document.getElementById('page-count-badge');

    if (!file) return;

    // 3D UI Feedback
    fileStatus.innerHTML = `<i class="fas fa-spinner fa-spin text-blue-500 mr-2"></i> Analyzing ${file.name}...`;

    const formData = new FormData();
    formData.append('document', file);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(apiUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update global state
            globalPageCount = data.pages; 
            
            // Sync UI
            fileStatus.innerHTML = `<i class="fas fa-check-circle text-green-500 mr-2"></i> Uploaded: ${file.name}`;
            pageBadge.innerText = `Pages: ${globalPageCount}`;
            
            // CRITICAL: Calculate price now that globalPageCount is updated
            calculatePrice(); 
            showToast("Document Analysis Complete", "success");
        } else {
            fileStatus.innerHTML = `<span class="text-red-500">Analysis Failed</span>`;
            showToast("Error reading PDF file", "error");
        }
    })
    .catch(err => {
        console.error("Upload Error:", err);
        showToast("Server connection error", "error");
    });
}

/**
 * 3. PRICING CALCULATION ENGINE
 * Formula: Pages * Base Price * Side Multiplier * Copies
 */
function calculatePrice() {
    const pPrice = parseFloat(document.getElementById('pType')?.value) || 0;
    const sMultiplier = parseFloat(document.getElementById('sType')?.value) || 1;
    const copies = parseInt(document.getElementById('copies')?.value) || 1;

    // Math Logic
    let total = Math.round(globalPageCount * pPrice * sMultiplier * copies);

    // Update Price Visuals
    const priceDisplay = document.getElementById('price-display');
    const hiddenPriceInput = document.getElementById('total-price-hidden');

    if (priceDisplay) priceDisplay.innerText = total;
    if (hiddenPriceInput) hiddenPriceInput.value = total;

    // Map labels for Django Database
    updateLabels();
}

/**
 * 4. AJAX CART SUBMISSION
 */
function addToCart(apiUrl, csrfToken) {
    if (globalPageCount === 0) {
        showToast("Please upload a document first!", "error");
        return;
    }

    const form = document.getElementById('orderForm');
    const formData = new FormData(form);

    fetch(apiUrl, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrfToken }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            showToast("Item Added to Cart!", "success");
        } else {
            showToast("Please login to add to cart", "error");
        }
    });
}

/**
 * 5. UTILITY & UI HELPERS
 */
function updateLabels() {
    const pSelect = document.getElementById('pType');
    const sSelect = document.getElementById('sType');
    if (pSelect && sSelect) {
        document.getElementById('p-label-hidden').value = pSelect.options[pSelect.selectedIndex].text;
        document.getElementById('s-label-hidden').value = sSelect.options[sSelect.selectedIndex].text;
    }
}

function updateCartBadge(count) {
    const badge = document.getElementById('cart-count-badge');
    if (badge) {
        badge.innerText = count;
        // 3D Pop animation
        badge.style.transform = 'scale(1.8)';
        setTimeout(() => badge.style.transform = 'scale(1)', 300);
    }
}

function showToast(message, type) {
    const toast = document.createElement('div');
    const color = type === 'success' ? 'bg-green-600' : 'bg-red-600';
    
    toast.className = `fixed bottom-10 right-10 ${color} text-white px-8 py-4 rounded-full shadow-2xl z-[100] font-black uppercase tracking-widest text-[10px] animate-bounce`;
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'} mr-2"></i> ${message}`;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}