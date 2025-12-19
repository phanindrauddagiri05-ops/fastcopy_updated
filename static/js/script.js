/**
 * Fast Copy Engine - 3D Dynamic Forms & Logic
 */
let detectedPages = 0;

// Configuration for service themes and specific fields
const serviceConfig = {
    'Printing': { color: '#2563eb', icon: 'fa-print', multiplier: 1, desc: 'Standard Document Xerox' },
    'Spiral Binding': { color: '#10b981', icon: 'fa-book-open', multiplier: 1.5, desc: 'Durable Plastic Spiral' },
    'Soft Binding': { color: '#ec4899', icon: 'fa-book', multiplier: 2, desc: 'Premium Perfect Binding' },
    'Custom Printing': { color: '#8b5cf6', icon: 'fa-sliders-h', multiplier: 1.2, desc: 'Bespoke Size & Format' },
    'Thesis Binding': { color: '#f59e0b', icon: 'fa-graduation-cap', multiplier: 5, desc: 'Hardcover Gold Embossed' },
    'Photo Frames': { color: '#ef4444', icon: 'fa-image', multiplier: 10, desc: 'High-Gloss Glass Framing' }
};

function selectService(name, id) {
    const config = serviceConfig[name] || serviceConfig['Printing'];
    
    // UI Morphing
    document.getElementById('service-title-display').innerText = name;
    document.getElementById('service-desc').innerText = config.desc;
    document.getElementById('hidden_service_name').value = name;
    document.getElementById('form-header-bg').style.backgroundColor = config.color;
    document.getElementById('main-form-card').style.borderColor = config.color;
    document.getElementById('order-now-btn').style.backgroundColor = config.color;
    document.getElementById('floating-icon').className = `fas ${config.icon} text-5xl opacity-20 floating-3d`;

    // Tab Highlighting
    document.querySelectorAll('.service-tab').forEach(t => {
        t.classList.remove('active-tab');
        t.style.borderColor = 'transparent';
    });
    const activeTab = document.getElementById('tab-' + id);
    activeTab.classList.add('active-tab');
    activeTab.style.borderColor = config.color;

    updatePrice();
}

// Automatic PDF Page Counter
async function handleFileUpload(input) {
    if (!input.files[0]) return;
    const status = document.getElementById('upload-status');
    status.innerHTML = '<i class="fas fa-spinner fa-spin text-2xl"></i> Analysing Document...';

    const formData = new FormData();
    formData.append('document', input.files[0]);

    const res = await fetch('/calculate-pages/', { method: 'POST', body: formData });
    const data = await res.json();
    
    if (data.success) {
        detectedPages = data.pages;
        document.getElementById('detected-pages-label').innerText = detectedPages;
        status.innerHTML = `<i class="fas fa-check-circle text-green-500 text-3xl"></i><p class="font-bold">${input.files[0].name}</p>`;
        updatePrice();
    }
}

// Real-time Price Engine with Counter Animation
function updatePrice() {
    const currentService = document.getElementById('hidden_service_name').value;
    const config = serviceConfig[currentService];
    
    const printTypeRate = document.getElementById('print-type').value === 'color' ? 10 : 2;
    const sideMultiplier = parseFloat(document.getElementById('side-type').value);
    const copies = parseInt(document.getElementById('copy-count').value) || 1;

    const total = (detectedPages * 1 * sideMultiplier * printTypeRate * config.multiplier) * copies;
    
    animatePriceCounter(total);
    document.getElementById('total_price_hidden').value = Math.ceil(total);
}

function animatePriceCounter(target) {
    const display = document.getElementById('price-display');
    let start = parseInt(display.innerText.replace('₹', '')) || 0;
    const duration = 500;
    const startTime = performance.now();

    function step(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + progress * (target - start));
        display.innerText = `₹${current}`;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
    AOS.init({ duration: 1000, once: true });
    selectService('Printing', 1);
});