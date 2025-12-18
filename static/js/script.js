// Service Configuration
const serviceData = {
    'Printing': { color: '#2563eb', rate: 2 },
    'Spiral Binding': { color: '#9333ea', rate: 45 },
    'Soft Binding': { color: '#db2777', rate: 60 },
    'Custom Printing': { color: '#059669', rate: 15 },
    'Thesis Binding': { color: '#d97706', rate: 150 },
    'Photo Frames': { color: '#dc2626', rate: 200 }
};

function selectService(name, id) {
    const config = serviceData[name] || serviceData['Printing'];
    
    // Update Form Header
    const header = document.getElementById('form-header');
    const title = document.getElementById('active-service-title');
    if(header) header.style.backgroundColor = config.color;
    if(title) title.innerText = name;

    // Update Tabs
    document.querySelectorAll('.service-tab').forEach(tab => tab.classList.remove('active-tab'));
    const activeBtn = document.getElementById('btn-' + id);
    if(activeBtn) activeBtn.classList.add('active-tab');

    // Calculate initial price for new service
    updatePrice(config.rate);
}

function updatePrice(customRate = null) {
    const type = document.getElementById('pType');
    const side = document.getElementById('sType');
    const copies = document.getElementById('pCopies');
    const display = document.getElementById('final-price');

    if(!display) return;

    // Determine Base Rate
    let base = customRate;
    if(!base) {
        const activeTitle = document.getElementById('active-service-title').innerText;
        base = serviceData[activeTitle].rate;
    }

    const typeMult = (type && type.value === 'color') ? 5 : 1;
    const sideMult = side ? parseFloat(side.value) : 1;
    const count = copies ? (parseInt(copies.value) || 1) : 1;

    const total = (base * typeMult * sideMult) * count;
    display.innerText = Math.ceil(total);
}

// Global Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize AOS
    AOS.init({ duration: 1000, once: true });

    // Auto-click first tab on Services page
    const firstTab = document.querySelector('.service-tab');
    if(firstTab) firstTab.click();
});

/**
 * Cart Calculation Logic
 */
function updateCartTotal() {
    const prices = document.querySelectorAll('.cart-item-card h4');
    let total = 0;
    prices.forEach(p => {
        total += parseFloat(p.innerText.replace('₹', ''));
    });
    
    const totalDisplay = document.getElementById('cart-total-display');
    if (totalDisplay) {
        totalDisplay.innerText = total.toLocaleString('en-IN');
    }
}

// Update DOMContentLoaded to include cart init
document.addEventListener('DOMContentLoaded', () => {
    // ... existing logic
    updateCartTotal();
});