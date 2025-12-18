/**
 * Global Main Logic
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("Fast Copy Main JS Initialized");
    
    // Optional: Add Navbar scroll effect
    window.addEventListener('scroll', () => {
        const nav = document.querySelector('nav');
        if (window.scrollY > 50) {
            nav.classList.add('shadow-lg');
        } else {
            nav.classList.remove('shadow-lg');
        }
    });
});