// Theme toggle
const themeToggleInput = document.getElementById('themeToggleInput');
if (themeToggleInput) {
    themeToggleInput.checked = document.documentElement.classList.contains('dark-mode');
    themeToggleInput.addEventListener('change', () => {
        document.documentElement.classList.toggle('dark-mode', themeToggleInput.checked);
        localStorage.setItem('theme', themeToggleInput.checked ? 'dark' : 'light');
    });
}

// Toast close buttons
document.querySelectorAll('.toast-close').forEach(btn => {
    btn.addEventListener('click', () => btn.parentElement.remove());
});

// Profile dropdown toggle
const trigger = document.querySelector('.profile-trigger');
const dropdown = document.getElementById('profileDropdown');
if (trigger && dropdown) {
    trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('is-open');
    });
    document.addEventListener('click', () => {
        dropdown.classList.remove('is-open');
    });
    dropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}
