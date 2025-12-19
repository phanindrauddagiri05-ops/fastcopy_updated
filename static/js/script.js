const serviceThemes = {
    'Printing': '#2563eb',
    'Spiral Binding': '#9333ea',
    'Soft Binding': '#db2777',
    'Custom Printing': '#059669',
    'Thesis Binding': '#d97706',
    'Photo Frames': '#dc2626'
};

let detectedPages = 0;

function selectService(name, id) {
    const themeColor = serviceThemes[name] || '#2563eb';
    
    // UI Updates
    document.getElementById('form-title').innerText = name;
    document.getElementById('hidden_service_name').value = name;
    document.getElementById('form-header').style.backgroundColor = themeColor;
    document.getElementById('order-btn').style.backgroundColor = themeColor;

    // Tab Highlighting
    document.querySelectorAll('.service-tab').forEach(t => t.classList.remove('active-tab'));
    document.getElementById('tab-' + id).classList.add('active-tab');
    
    updatePrice();
}

async function handleFileUpload(input) {
    if (!input.files[0]) return;
    const formData = new FormData();
    formData.append('document', input.files[0]);

    document.getElementById('upload-status').innerHTML = `<i class="fas fa-spinner fa-spin text-3xl text-blue-500"></i><p>Counting Pages...</p>`;

    const res = await fetch('/calculate-pages/', { method: 'POST', body: formData });
    const data = await res.json();
    
    if (data.success) {
        detectedPages = data.pages;
        document.getElementById('page-display').innerText = data.pages;
        document.getElementById('upload-status').innerHTML = `<i class="fas fa-check-circle text-3xl text-green-500"></i><p class="text-sm font-bold">${input.files[0].name}</p>`;
        updatePrice();
    }
}

function updatePrice() {
    const rate = document.getElementById('print-type').value === 'bw' ? 2 : 10;
    const sides = parseFloat(document.getElementById('side-type').value);
    const copies = parseInt(document.getElementById('copy-count').value) || 1;
    
    const total = (detectedPages * rate * sides) * copies;
    document.getElementById('price-display').innerText = Math.ceil(total);
    document.getElementById('total_price_hidden').value = Math.ceil(total);
}

document.addEventListener('DOMContentLoaded', () => {
    AOS.init({ duration: 1000, once: true });
    const firstTab = document.querySelector('.service-tab');
    if (firstTab) firstTab.click();
});

// ... (Keep handleFileUpload and updatePrice functions from previous step) ...

async function addToCart() {
    const formData = new FormData();
    formData.append('service_name', document.getElementById('hidden_service_name').value);
    formData.append('print_type', document.getElementById('print-type').value);
    formData.append('side_type', document.getElementById('side-type').value);
    formData.append('copies', document.getElementById('copy-count').value);
    formData.append('pages', detectedPages);
    formData.append('total_price_hidden', document.getElementById('total_price_hidden').value);

    const res = await fetch('/add-to-cart/', {
        method: 'POST',
        body: formData
    });
    const data = await res.json();

    if (data.success) {
        // Update the cart count in navbar
        const badge = document.getElementById('cart-badge');
        if(badge) badge.innerText = data.cart_count;
        
        alert("Item added to cart successfully!");
    } else {
        alert("Failed to add to cart.");
    }
}