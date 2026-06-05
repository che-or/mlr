import { loadCoreData } from './data.js';
import { updateView } from './router.js';
import { initTheme } from './utils.js';
import { initPlayerSearch, displayPlayerPage } from './views/player.js';
import { initLeaderboardControls } from './views/leaderboards.js';

document.addEventListener('DOMContentLoaded', async () => {
    const loader = document.getElementById('loader');
    const app    = document.getElementById('app');

    initTheme(document.getElementById('theme-switch-input'));

    try {
        await loadCoreData();
    } catch (err) {
        console.error('Failed to load core data:', err);
        loader.innerHTML = '<p>Failed to load data. Please refresh the page.</p>';
        return;
    }

    loader.style.display = 'none';
    app.style.display = 'block';

    // Expose for cross-module navigation without circular imports
    window._mlrViews = { displayPlayerPage };

    initPlayerSearch();
    initLeaderboardControls();

    window.addEventListener('hashchange', updateView);
    updateView();
});
