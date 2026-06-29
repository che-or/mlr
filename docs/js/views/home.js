import { state } from '../state.js';
import { loadStats } from '../data.js';
import { seededRandom, getMlrLogoPair, getMlrTeamName, getSeasonSort, recordFranchiseKey, makeLogoImg } from '../utils.js';

export async function renderHome() {
    const container = document.getElementById('home-view');

    // Awards / HOF links — only shown if data exists
    const awardsSeasons = Object.keys(state.awards).filter(k => k.startsWith('S'));
    const hasAwardsData = awardsSeasons.some(k => {
        const sa = state.awards[k];
        if (!sa) return false;
        if (sa.PCMVP?.length || sa.HRD?.length) return true;
        for (const lg of ['AL', 'NL']) {
            if (!sa[lg]) continue;
            for (const k2 in sa[lg]) {
                const v = sa[lg][k2];
                if (Array.isArray(v) && v.length) return true;
                if (typeof v === 'object' && v !== null && !Array.isArray(v) && Object.keys(v).length) return true;
            }
        }
        return false;
    });
    const awardsLink = hasAwardsData
        ? `<li><a href="#/awards"><strong>Awards:</strong></a> Season-by-season award winners for MLR.</li>` : '';
    const hofLink = state.awards.HOF?.length
        ? `<li><a href="#/hof"><strong>Hall of Fame:</strong></a> View the members of the Hall of Fame.</li>` : '';

    container.innerHTML = `
        <div class="welcome-container">
            <h2 class="section-title">Welcome to MLR Reference!</h2>
            <p>MLR Reference is your guide to stats for Major League Redditball (MLR) and associated fake baseball leagues. MLR Reference also has stats for Minor League Redditball (MiLR), Fake College Baseball (FCB), the original GIB Side League (GIB), Exhibition Co-op League (ECO), Nippon Professional Redditball (NPR), and the World Baseball Classic (WBC). Postseason stats are available for MLR and MiLR.</p>
            <p>Here you can find:</p>
            <ul>
                <li><a href="#/stats"><strong>Player Stats:</strong></a> Detailed batting and pitching statistics for every player in MLR history. Players can be searched by name (including former names) or player ID.</li>
                <li><a href="#/team-stats"><strong>Team Stats:</strong></a> Season-by-season standings and team statistics.</li>
                <li><a href="#/leaderboards"><strong>Leaderboards:</strong></a> All-time and single-season leaderboards for a variety of stats.</li>
                ${awardsLink}
                ${hofLink}
                <li><a href="#/draft"><strong>Draft History:</strong></a> Season-by-season draft picks for MLR.</li>
                <li><a href="#/single-game-records"><strong>Single-Game Records:</strong></a> All-time single-game record holders for MLR batting and pitching stats.</li>
                <li><a href="#/streaks"><strong>Streaks:</strong></a> All-time and active streak records for hitting, on-base, scoreless innings, and more.</li>
                <li><a href="#/compare"><strong>Player Comparison:</strong></a> Compare up to four players side-by-side across any league and season.</li>
                <li><a href="#/glossary"><strong>Glossary:</strong></a> Definitions and equations for advanced and calculated stats.</li>
            </ul>
            <br>
            <p>Potential future features:</p>
            <ul>
                <li>Jersey numbers</li>
                <li>Player stats against each team</li>
                <li>Milestone tracking</li>
            </ul>
            <br>
            <p>Feel free to ping me (Che) if you have any suggestions or find any bugs. If you know of any names that are missing from a players former names, please let me know.</p>
            <br>

            <h3 class="section-title">Today's Features</h3>
            <div id="featured-section" class="featured-section">
                <p style="color:var(--subtle-text-color)">Loading...</p>
            </div>
            <br>

            <h3 class="section-title">Frequently Asked Questions</h3>
            <p>Why is my WAR different than it appears in the roster sheet?</p>
            <p><i>Like any good baseball statistics site, MLR Reference has its own WAR formula. MLR Reference WAR (also known as "cheWAR") is calculated using RE24. More information about WAR calculation can be found in the glossary.</i></p>
            <br>
            <p>Why do my franchise total stat lines include teams I've never played for?</p>
            <p><i>The franchise total stat lines use the abbreviations that are currently used by the franchise. For example, S2-S5 Texas Rangers has been Cleveland Guardians since S6, so even players who only played during the TEX era will have CLE in their franchise totals.</i></p>
            <br>
            <p>Why is my stolen base count different than it appears in the roster sheet?</p>
            <p><i>Differing stolen base count is likely due to being a trailing runner on a multi-steal attempt. The roster sheet does not credit trailing runners with stolen bases. MLR Reference credits all trailing runners with stolen bases, unless an unsuccessful attempts ends the inning. These trailing runner stolen bases count both for runners and against pitchers.</i></p>
            <br>
            <p>Why is my runs scored count different than it appears in the roster sheet?</p>
            <p><i>Differing runs scored count is likely due to being a ghost runner that scored. The roster sheet does not credit ghost runners with runs scored, while MLR Reference does.</i></p>
        </div>`;

    try {
        await Promise.all([
            loadStats('mlr', 'hitting'),
            loadStats('mlr', 'pitching'),
            loadStats('mlr', 'team_hitting'),
        ]);
        renderFeatured();
    } catch (_) {
        const fs = document.getElementById('featured-section');
        if (fs) fs.innerHTML = '';
    }
}

// ── Featured section ──────────────────────────────────────────────────────────

function renderFeatured() {
    const today = new Date();
    const seed  = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate();
    const random = seededRandom(seed);

    const hitting  = state.stats['mlr_hitting']  || [];
    const pitching = state.stats['mlr_pitching'] || [];

    // Pool: all unique player IDs with at least one real non-sub-row season record
    const idSet = new Set();
    hitting.filter(r => !r.is_sub_row && r['Display Season']?.startsWith('S')).forEach(r => idSet.add(r.ID));
    pitching.filter(r => !r.is_sub_row && r['Display Season']?.startsWith('S')).forEach(r => idSet.add(r.ID));
    const ids = [...idSet];

    let i1 = Math.floor(random() * ids.length);
    let i2 = Math.floor(random() * ids.length);
    while (i2 === i1) i2 = Math.floor(random() * ids.length);

    const p1 = buildFeaturedPlayer(ids[i1], hitting, pitching);
    const p2 = buildFeaturedPlayer(ids[i2], hitting, pitching);
    const team = buildFeaturedTeam(random);

    const fs = document.getElementById('featured-section');
    if (!fs) return;

    fs.innerHTML = `
        ${renderPlayerCard(p1)}
        ${renderPlayerCard(p2)}
        ${team ? renderTeamCard(team) : ''}
        <div class="featured-item action-item">
            <h4>Discover More!</h4>
            <button id="random-player-button" class="action-button">Random Player</button>
        </div>`;

    // Wire featured player links
    fs.querySelectorAll('.player-link[data-player-id]').forEach(el => {
        el.addEventListener('click', e => {
            e.preventDefault();
            const id = parseInt(el.dataset.playerId);
            import('./player.js').then(m => {
                m.displayPlayerPage(id);
                window.location.hash = '#/stats';
            });
        });
    });

    // Random player button
    document.getElementById('random-player-button')?.addEventListener('click', () => {
        const allIds = state.allPlayers.map(p => p.ID);
        const id = allIds[Math.floor(Math.random() * allIds.length)];
        import('./player.js').then(m => {
            m.displayPlayerPage(id);
            window.location.hash = '#/stats';
        });
    });
}

// ── Data builders ─────────────────────────────────────────────────────────────

function buildFeaturedPlayer(id, hitting, pitching) {
    const allStats = [
        ...hitting.filter(r => r.ID === id && !r.is_sub_row && r['Display Season']?.startsWith('S')),
        ...pitching.filter(r => r.ID === id && !r.is_sub_row && r['Display Season']?.startsWith('S')),
    ];
    if (!allStats.length) return null;

    allStats.sort((a, b) =>
        getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']) ||
        (b['Last Session'] || 0) - (a['Last Session'] || 0)
    );
    const latest = allStats[0];
    const seasons = allStats.map(r => getSeasonSort(r['Display Season'])).filter(n => n > 0);
    const first = Math.min(...seasons), last = Math.max(...seasons);
    const range = first === last ? `S${first}` : `S${first}-S${last}`;

    const ds   = latest['Display Season'];
    const fk   = recordFranchiseKey(latest);
    const logo = fk ? getMlrLogoPair(fk, ds) : null;
    const name = latest.Name || `#${id}`;

    return { id, name, logo, range };
}

function buildFeaturedTeam(random) {
    const teamHitting = state.stats['mlr_team_hitting'] || [];
    const teamKeys    = Object.keys(state.teamHistory.mlr);
    if (!teamKeys.length) return null;

    const maxSeason = Math.max(
        ...teamHitting.filter(r => r['Display Season']?.startsWith('S'))
                      .map(r => getSeasonSort(r['Display Season']))
    );

    const key = teamKeys[Math.floor(random() * teamKeys.length)];
    const entries = state.teamHistory.mlr[key] || [];

    const validSeasons = [];
    for (const e of entries) {
        for (let s = e.start; s <= Math.min(e.end === 9999 ? maxSeason : e.end, maxSeason); s++) {
            validSeasons.push(`S${s}`);
        }
    }
    if (!validSeasons.length) return null;

    const ds    = validSeasons[Math.floor(random() * validSeasons.length)];
    const entry = entries.find(e => {
        const n = parseInt(ds.slice(1));
        return n >= e.start && (e.end === 9999 || n <= e.end);
    });
    if (!entry) return null;

    const logo = getMlrLogoPair(key, ds);
    const name = entry.name;

    const th = teamHitting.find(r => r['Display Season'] === ds && r.Franchise === key);

    return { key, name, ds, logo, hitting: th || null };
}

// ── Card renderers ────────────────────────────────────────────────────────────

function renderPlayerCard(p) {
    if (!p) return '';
    return `
        <div class="featured-item">
            <h4>Featured Player</h4>
            <a href="#/stats" class="player-link" data-player-id="${p.id}">
                ${p.logo ? makeLogoImg(p.logo.dark, p.logo.light, 'team-list-logo', `${p.name} team logo`) : ''}
                <p>${p.name}</p>
                <p class="featured-player-season-range">${p.range}</p>
            </a>
        </div>`;
}

function renderTeamCard(t) {
    const h = t.hitting;
    const seasonLabel = `${t.ds} ${t.name}`;
    return `
        <div class="featured-item">
            <h4>Featured Team</h4>
            <a href="#/team-stats?season=${t.ds}&team=${encodeURIComponent(t.key)}">
                ${t.logo ? makeLogoImg(t.logo.dark, t.logo.light, 'team-list-logo', `${t.name} logo`) : ''}
                <p>${seasonLabel}</p>
            </a>
        </div>`;
}
