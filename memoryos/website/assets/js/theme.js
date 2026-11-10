// RJMedia Unified Ecosystem Theme & Accessibility Controller
(function () {
  function applySavedPrefs() {
    try {
      const savedTheme = localStorage.getItem('rjmedia_theme');
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
      } else if (savedTheme === 'light') {
        document.documentElement.classList.remove('dark');
      }
      const savedScale = localStorage.getItem('rjmedia_scale');
      if (savedScale) {
        document.documentElement.style.setProperty('--reader-scale', savedScale);
      }
    } catch (e) {}
    syncThemeButtons();
  }

  window.toggleArchiveTheme = function () {
    const isDark = document.documentElement.classList.toggle('dark');
    try {
      localStorage.setItem('rjmedia_theme', isDark ? 'dark' : 'light');
    } catch (e) {}
    syncThemeButtons();
  };

  window.setArchiveScale = function (scale) {
    document.documentElement.style.setProperty('--reader-scale', String(scale));
    try {
      localStorage.setItem('rjmedia_scale', String(scale));
    } catch (e) {}
    syncThemeButtons();
  };

  function syncThemeButtons() {
    const isDark = document.documentElement.classList.contains('dark');
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.innerHTML = isDark ? '☀️ Paper Mode' : '🎬 Cinema Dark';
    });
    const currentScale = getComputedStyle(document.documentElement).getPropertyValue('--reader-scale').trim() || '1';
    document.querySelectorAll('[data-scale-btn]').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-scale-btn') === currentScale);
    });
  }

  applySavedPrefs();
  document.addEventListener('DOMContentLoaded', syncThemeButtons);
})();
