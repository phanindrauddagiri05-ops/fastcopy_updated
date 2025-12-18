/**
 * Dynamic Logic for Fast Copy Services
 */

// Colors for each specific service as per your requirement
const themes = {
    'Printing': '#2563eb',       // Blue
    'Spiral Binding': '#9333ea', // Purple
    'Soft Binding': '#db2777',   // Pink
    'Custom Printing': '#059669',// Green
    'Thesis Binding': '#d97706', // Amber
    'Photo Frames': '#dc2626'    // Red
};

/**
 * Switch between different service forms
 */
function selectService(name, id) {
    // 1. Update the Form Header Background and Title
    const header = document.getElementById('form-header');
    const title = document.getElementById('active-service-title');
    
    if (header) header.style.backgroundColor = themes[name] || '#2563eb';
    if (title) title.innerText = name;

    // 2. Manage Active Tab Highlighting
    document.querySelectorAll('.service-tab').forEach(tab => {
        tab.classList.remove('active-tab');
    });
    
    const selectedBtn = document.getElementById('btn-' + id);
    if (selectedBtn) selectedBtn.classList.add('active-tab');

    // 3. Trigger Price Calculation
    calculatePrice();
}

/**
 * Real-time Price Calculator
 */
function calculatePrice() {
    const type = document.getElementById('pType');
    const side = document.getElementById('sType');
    const copies = document.getElementById('pCopies');
    const display = document.getElementById('final-price');

    if (!type || !side || !copies || !display) return;

    // Base rates per page
    let rate = (type.value === 'bw') ? 2 : 10;
    
    // Side multipliers (One side = 1, Two sides = 2, others as decimals)
    let sideMultiplier = parseFloat(side.value);
    
    // Total copies
    let numCopies = parseInt(copies.value) || 1;

    // Calculation Logic: (Rate * SideMultiplier) * Copies
    // Note: We assume 1 page for now until the file is analyzed server-side
    const total = (rate * sideMultiplier) * numCopies;

    // Update Display
    display.innerText = Math.ceil(total);
}

// Ensure the page initializes correctly
document.addEventListener('DOMContentLoaded', () => {
    // Auto-click the first service tab to load the default form
    const firstTab = document.querySelector('.service-tab');
    if (firstTab) firstTab.click();
    
    // Initialize AOS animations
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: true
        });
    }
});