import { state } from './state.js';
import { renderHome } from './views/home.js';
import { renderGlossary } from './views/glossary.js';
import { renderAwards, renderHof } from './views/awards.js';
import { renderDraftHistory } from './views/draft.js';
import { renderCompare } from './views/compare.js';
import { displayTeamList, displayTeamStatsPage } from './views/teams.js';
import { populateLeaderboardStatSelect } from './views/leaderboards.js';
import { displayPlayerPage } from './views/player.js';
import { renderSingleGameRecords } from './views/single_game_records.js';
import { renderStreaks } from './views/streaks.js';

const el = id => document.getElementById(id);

const views = {
    home:        el('home-view'),
    stats:       el('stats-view'),
    leaderboards: el('leaderboards-view'),
    glossary:    el('glossary-view'),
    awards:      el('awards-view'),
    hof:         el('hof-view'),
    compare:     el('compare-view'),
    teamStats:   el('team-stats-view'),
    draft:             el('draft-view'),
    singleGameRecords: el('single-game-records-view'),
    streaks:           el('streaks-view'),
};

const tabs = {
    home:        el('home-tab'),
    stats:       el('stats-tab'),
    teamStats:   el('team-stats-tab'),
    leaderboards: el('leaderboards-tab'),
    glossary:    el('glossary-tab'),
};

function hideAll() {
    Object.values(views).forEach(v => { v.style.display = 'none'; });
    Object.values(tabs).forEach(t => t.classList.remove('active'));
}

function show(viewKey, tabKey) {
    views[viewKey].style.display = viewKey === 'glossary' ? 'flex' : 'block';
    if (tabKey) tabs[tabKey].classList.add('active');
}

export function updateView() {
    window.scrollTo(0, 0);
    hideAll();

    const hash = window.location.hash || '#/home';

    if (hash === '#/home') {
        show('home', 'home');
        renderHome();
        return;
    }

    if (hash.startsWith('#/team-stats')) {
        show('teamStats', 'teamStats');
        const url = new URL('http://x/' + hash.slice(1));
        const season = url.searchParams.get('season');
        const team   = url.searchParams.get('team');
        const league = url.searchParams.get('league') || 'mlr';
        if (team) {
            displayTeamStatsPage(decodeURIComponent(team), season, league);
        } else {
            displayTeamList(season, league);
        }
        return;
    }

    if (hash === '#/stats') {
        show('stats', 'stats');
        if (state.currentPlayerId) {
            displayPlayerPage(state.currentPlayerId);
        } else {
            el('stats-content-display').innerHTML = '<p>Search for a player to see their stats.</p>';
        }
        return;
    }

    if (hash === '#/leaderboards') {
        show('leaderboards', 'leaderboards');
        if (el('leaderboard-stat-select').options.length <= 1) {
            populateLeaderboardStatSelect();
        }
        return;
    }

    if (hash.startsWith('#/awards')) {
        show('awards');
        renderAwards();
        return;
    }

    if (hash === '#/hof') {
        show('hof');
        renderHof();
        return;
    }

    if (hash === '#/glossary') {
        show('glossary', 'glossary');
        renderGlossary();
        return;
    }

    if (hash.startsWith('#/compare')) {
        show('compare');
        renderCompare();
        return;
    }

    if (hash.startsWith('#/draft')) {
        show('draft');
        renderDraftHistory();
        return;
    }

    if (hash === '#/single-game-records') {
        show('singleGameRecords');
        renderSingleGameRecords();
        return;
    }

    if (hash === '#/streaks') {
        show('streaks');
        renderStreaks();
        return;
    }

    // Unknown hash — redirect home
    window.location.hash = '#/home';
}
