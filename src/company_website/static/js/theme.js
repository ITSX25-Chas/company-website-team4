// Körs i <head>, så att mörkt läge slås på innan sidan ritas.
(function() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark') {
        document.documentElement.classList.add('dark-mode');
    }
})();
