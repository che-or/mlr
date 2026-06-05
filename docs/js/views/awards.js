import { state } from '../state.js';
import { loadStats } from '../data.js';
import { getSeasonSort, getMlrLogoPair, recordFranchiseKey, makeLogoImg } from '../utils.js';


export async function renderAwards() {
    // Load hitting and pitching stats for logos — lazy, cached after first load
    try {
        await Promise.all([loadStats('mlr', 'hitting'), loadStats('mlr', 'pitching')]);
    } catch (_) {}

    const container = document.getElementById('awards-view');
    const awardsData = state.awards;
    const metadata = awardsData._metadata || {};

    const seasons = Object.keys(awardsData)
        .filter(k => k.startsWith('S') && hasAwards(awardsData[k]))
        .sort((a, b) => getSeasonSort(b) - getSeasonSort(a));

    const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
    let selected = seasons.includes(urlParams.get('season')) ? urlParams.get('season') : (seasons[0] || null);

    const idx = seasons.indexOf(selected);
    const prev = idx < seasons.length - 1 ? seasons[idx + 1] : null;
    const next = idx > 0 ? seasons[idx - 1] : null;

    let html = `<div class="awards-header team-stats-header">
        <h2 class="section-title">Awards —
            <select id="awards-season-select" class="title-season-select">
                ${seasons.map(s => `<option value="${s}" ${s === selected ? 'selected' : ''}>${s.replace('S', 'Season ')}</option>`).join('')}
            </select>
        </h2>
        <div class="season-nav-buttons">
            ${prev ? `<a href="#/awards?season=${prev}" class="season-nav-button">&lt; Prev Season</a>` : ''}
            ${next ? `<a href="#/awards?season=${next}" class="season-nav-button">Next Season &gt;</a>` : ''}
        </div>
    </div>`;

    if (!selected) { container.innerHTML = html + '<p>No awards data available.</p>'; return; }

    const sa = awardsData[selected];
    if (!hasAwards(sa)) { container.innerHTML = html + '<p>No awards data for this season.</p>'; return; }

    html += `<div class="awards-container">
        <div class="league-toggle-buttons">
            <button class="league-toggle-button active" data-league="al">American League</button>
            <button class="league-toggle-button" data-league="nl">National League</button>
        </div>
        <div class="leagues-wrapper">`;

    for (const lg of ['AL', 'NL']) {
        const lgName = lg === 'AL' ? 'American League' : 'National League';
        html += `<div class="league-column league-${lg.toLowerCase()}"><h3 class="league-title">${lgName} Awards</h3>`;
        const la = sa[lg];
        if (la) {
            html += renderMajorAwards(la, metadata, selected);
            html += renderSilverSluggers(la, metadata, selected, lgName);
            html += renderAllStarTeam(la, metadata, selected, lgName);
        }
        html += '</div>';
    }

    // PCMVP and HRD are shown on player pages only, not on the awards page

    html += '</div></div>';
    container.innerHTML = html;

    // Season dropdown
    container.querySelector('#awards-season-select').addEventListener('change', e => {
        window.location.hash = `#/awards?season=${e.target.value}`;
    });

    // League toggle (mobile)
    container.querySelectorAll('.league-toggle-button').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.league-toggle-button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const lg = btn.dataset.league;
            const wrapper = container.querySelector('.leagues-wrapper');
            wrapper.classList.toggle('show-al', lg === 'al');
            wrapper.classList.toggle('show-nl', lg === 'nl');
        });
    });

    // Player links
    wirePlayerLinks(container);
}

function hasAwards(sa) {
    if (!sa) return false;
    if (sa.PCMVP?.length || sa.HRD?.length) return true;
    for (const lg of ['AL', 'NL']) {
        if (sa[lg]) {
            for (const k in sa[lg]) {
                const v = sa[lg][k];
                if (Array.isArray(v) && v.length) return true;
                if (typeof v === 'object' && v !== null && !Array.isArray(v) && Object.keys(v).length) return true;
            }
        }
    }
    return false;
}

const MAJOR_AWARD_ROWS = [['MVP', 'CYA'], ['ROTY', 'RPOTY'], ['BT', 'ERAT'], ['GMOTY']];

function renderMajorAwards(la, metadata, season) {
    // Only render if at least one award in this group has winners
    const hasAny = MAJOR_AWARD_ROWS.flat().some(key => la[key]?.length);
    if (!hasAny) return '';

    let html = '<div class="awards-sub-section"><div class="awards-major-section">';
    for (const row of MAJOR_AWARD_ROWS) {
        const rowHtml = row.filter(key => la[key]?.length).map(key => {
            const ids = la[key];
            let inner;
            if (key === 'GMOTY' && ids.length > 1) {
                const logo = logoForPlayer(ids[0], season);
                inner = `<div class="award-winner-item">${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${ids.map(id => playerLink(id)).join(' &amp; ')}</div>`;
            } else {
                inner = ids.map(id => {
                    const logo = logoForPlayer(id, season);
                    return `<div class="award-winner-item">${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}</div>`;
                }).join('');
            }
            return `<div class="award-category"><h4>${metadata[key] || key}</h4><div class="award-winners-list">${inner}</div></div>`;
        }).join('');
        if (rowHtml) html += `<div class="awards-major-row">${rowHtml}</div>`;
    }
    return html + '</div></div>';
}

const SS_COL1 = ['C', '1B', '2B', '3B', 'DH'];
const SS_COL2 = ['SS', 'LF', 'CF', 'RF', 'OF', 'P'];

function renderSilverSluggers(la, metadata, season, lgName) {
    const ss = la.SS;
    if (!ss || typeof ss !== 'object' || Array.isArray(ss) || !Object.keys(ss).length) return '';

    const renderCol = (positions) => positions.map(pos => {
        if (!ss[pos]) return '';
        const ids = Array.isArray(ss[pos]) ? ss[pos] : [ss[pos]];
        if (pos === 'OF' && ids.length > 1) {
            return ids.map(id => {
                const logo = logoForPlayer(id, season);
                return `<div class="award-winner-item-pos">
                    <span class="award-position-label">${pos}</span>
                    <div class="award-player-info-pos"><div class="award-player-item-pos">
                        ${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}
                    </div></div></div>`;
            }).join('');
        }
        return `<div class="award-winner-item-pos">
            <span class="award-position-label">${pos}</span>
            <div class="award-player-info-pos">${ids.map(id => {
                const logo = logoForPlayer(id, season);
                return `<div class="award-player-item-pos">${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}</div>`;
            }).join('')}</div></div>`;
    }).join('');

    return `<h4 class="awards-sub-title">${lgName} Silver Sluggers</h4>
        <div class="awards-sub-section"><div class="award-category">
            <div class="ss-winners-list">
                <div class="ss-winners-col">${renderCol(SS_COL1)}</div>
                <div class="ss-winners-col">${renderCol(SS_COL2)}</div>
            </div>
        </div></div>`;
}

const AS_STARTER_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'];

function renderAllStarTeam(la, metadata, season, lgName) {
    const as = la.AS;
    if (!as || typeof as !== 'object' || Array.isArray(as)) return '';
    const hasContent = as.GM?.length || AS_STARTER_POSITIONS.some(pos => as[pos]) || as.P?.length || as.R?.length;
    if (!hasContent) return '';

    // ── GM section ──────────────────────────────────────────────────────────
    let gmHtml = '';
    if (as.GM?.length) {
        const infos = as.GM.map(id => ({ id, ...playerSeasonInfo(id, season) }));
        const firstLogo = infos[0]?.logo;
        const allSameLogo = infos.every(p => p.logo?.dark === firstLogo?.dark);
        let gmInner;
        if (infos.length > 1 && allSameLogo) {
            gmInner = `<div class="award-winner-item">
                ${firstLogo ? makeLogoImg(firstLogo.dark, firstLogo.light, 'award-team-logo') : ''}
                ${infos.map(p => playerLink(p.id)).join(' &amp; ')}
            </div>`;
        } else {
            gmInner = infos.map(p => `<span class="award-winner-item" style="display:inline-flex">
                ${p.logo ? makeLogoImg(p.logo.dark, p.logo.light, 'award-team-logo') : ''}${playerLink(p.id)}
            </span>`).join(' &amp; ');
        }
        gmHtml = `<div class="as-section as-gms">
            <h5>General Manager${as.GM.length > 1 ? 's' : ''}</h5>
            <div class="as-gm-list">${gmInner}</div>
        </div>`;
    }

    // ── Starting lineup ──────────────────────────────────────────────────────
    const startersHtml = AS_STARTER_POSITIONS.map(pos => {
        if (!as[pos]) return '';
        const ids = Array.isArray(as[pos]) ? as[pos] : [as[pos]];
        return ids.map(id => {
            const logo = logoForPlayer(id, season);
            return `<div class="award-winner-item">
                <span class="award-position-label">${pos}</span>
                ${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}
            </div>`;
        }).join('');
    }).join('');

    // ── Pitchers ─────────────────────────────────────────────────────────────
    let pitchersHtml = '';
    if (as.P?.length) {
        pitchersHtml = `<div class="as-section as-pitchers">
            <h5>Pitchers</h5>
            <div class="as-player-list">
                ${as.P.map(id => {
                    const logo = logoForPlayer(id, season);
                    return `<div class="award-winner-item">
                        ${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}
                    </div>`;
                }).join('')}
            </div>
        </div>`;
    }

    // ── Reserves ─────────────────────────────────────────────────────────────
    let reservesHtml = '';
    if (as.R?.length) {
        const reserves = as.R.map(id => {
            const { logo, teamAbbr } = playerSeasonInfo(id, season);
            const player = state.allPlayers.find(p => p.ID === id);
            return { id, logo, teamAbbr, name: player?.Name || `#${id}` };
        });
        reserves.sort((a, b) =>
            a.teamAbbr.localeCompare(b.teamAbbr) || a.name.localeCompare(b.name)
        );
        const mid = Math.ceil(reserves.length / 2);
        const col1 = reserves.slice(0, mid);
        const col2 = reserves.slice(mid);
        const renderReserveCol = col => col.map(r => `<div class="award-winner-item">
            ${r.logo ? makeLogoImg(r.logo.dark, r.logo.light, 'award-team-logo') : ''}${playerLink(r.id)}
        </div>`).join('');

        reservesHtml = `<div class="as-section as-reserves">
            <h5>Reserves</h5>
            <div class="as-reserves-list">
                <div class="as-reserves-col">${renderReserveCol(col1)}</div>
                ${col2.length ? `<div class="as-reserves-col">${renderReserveCol(col2)}</div>` : ''}
            </div>
        </div>`;
    }

    return `<h4 class="awards-sub-title">${lgName} All-Star Team</h4>
        <div class="awards-sub-section">
            <div class="award-category">
                <div class="all-star-team">
                    ${gmHtml}
                    <div class="as-main-roster">
                        <div class="as-section as-starters">
                            <h5>Starting Lineup</h5>
                            <div class="as-player-list">${startersHtml}</div>
                        </div>
                        ${pitchersHtml}
                    </div>
                    ${reservesHtml}
                </div>
            </div>
        </div>`;
}

function renderLeagueWideAward(key, ids, metadata, season) {
    if (!ids?.length) return '';
    const name = metadata[key] || key;
    return `<div class="awards-sub-section" style="margin-top:20px">
        <h4 class="awards-section-title">${name}</h4>
        <div class="award-winners-list">${ids.map(id => {
            const logo = logoForPlayer(id, season);
            return `<div class="award-winner-item">${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}</div>`;
        }).join('')}</div>
    </div>`;
}

// ── HOF ──────────────────────────────────────────────────────────────────────

export async function renderHof() {
    const container = document.getElementById('hof-view');
    const hofIds = state.awards.HOF || [];
    if (!hofIds.length) { container.innerHTML = '<p>No Hall of Fame data available.</p>'; return; }

    try {
        await Promise.all([
            loadStats('mlr',  'hitting'), loadStats('mlr',  'pitching'),
            loadStats('milr', 'hitting'), loadStats('milr', 'pitching'),
            loadStats('fcb',  'hitting'), loadStats('fcb',  'pitching'),
        ]);
    } catch (_) {}

    // Determine most recent season per league and collect active player IDs
    const activeIds = new Set();
    for (const league of ['mlr', 'milr', 'fcb']) {
        const seasonKeys = Object.keys(state.divisions[league] || {});
        const recent = seasonKeys.sort((a, b) => getSeasonSort(b) - getSeasonSort(a))[0];
        if (!recent) continue;
        for (const type of ['hitting', 'pitching']) {
            (state.stats[`${league}_${type}`] || [])
                .filter(r => r['Display Season'] === recent && !r.is_sub_row)
                .forEach(r => activeIds.add(r.ID));
        }
    }

    const mlrHitting  = state.stats['mlr_hitting']  || [];
    const mlrPitching = state.stats['mlr_pitching'] || [];

    // Sort alphabetically by name
    const sortedIds = [...hofIds].sort((a, b) => {
        const na = state.allPlayers.find(p => p.ID === a)?.Name || '';
        const nb = state.allPlayers.find(p => p.ID === b)?.Name || '';
        return na.localeCompare(nb);
    });

    container.innerHTML = `
        <h2 class="section-title">Hall of Fame</h2>
        <p class="hof-note">Click a player to view their stats. * = Active player.</p>
        <div class="hof-grid">
            ${sortedIds.map(id => renderHofCard(id, mlrHitting, mlrPitching, activeIds.has(id))).join('')}
        </div>`;

    wirePlayerLinks(container);
}

function renderHofCard(id, hitting, pitching, isActive) {
    const player = state.allPlayers.find(p => p.ID === id);
    const name = player ? player.Name : `Player #${id}`;

    // Check hitting then pitching for most recent MLR record
    const allRecords = [
        ...hitting.filter(s => s.ID === id && !s.is_sub_row),
        ...pitching.filter(s => s.ID === id && !s.is_sub_row),
    ].sort((a, b) => getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']));

    let logoPair = null;
    const lastStat = allRecords[0];
    if (lastStat) {
        logoPair = getMlrLogoPair(recordFranchiseKey(lastStat), lastStat['Display Season']);
    }

    return `<div class="hof-player-card player-link" data-player-id="${id}" style="cursor:pointer">
        <div class="hof-player-logo-container">
            ${logoPair
                ? makeLogoImg(logoPair.dark, logoPair.light, '')
                : '<div class="hof-placeholder-logo"></div>'}
        </div>
        <p>${name}${isActive ? '*' : ''}</p>
    </div>`;
}

// ── Shared helpers ────────────────────────────────────────────────────────────

function playerLink(id) {
    const player = state.allPlayers.find(p => p.ID === id);
    const name = player ? player.Name : `#${id}`;
    return `<a href="#/stats" class="player-link" data-player-id="${id}">${name}</a>`;
}

// Returns logo and team abbreviation for a player in a given season.
// Uses recordFranchiseKey to avoid the multi-franchise same-abbreviation bug.
function playerSeasonInfo(id, season) {
    const hitting  = state.stats['mlr_hitting']  || [];
    const pitching = state.stats['mlr_pitching'] || [];
    const all = [...hitting, ...pitching];
    const stat = all.find(s => s.ID === id && s['Display Season'] === season && !s.is_sub_row)
              || all.filter(s => s.ID === id && !s.is_sub_row)
                    .sort((a, b) => getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']))[0];
    if (!stat) return { logo: null, teamAbbr: '' };
    return {
        logo: getMlrLogoPair(recordFranchiseKey(stat), stat['Display Season']),
        teamAbbr: stat.Team !== '2TM' ? (stat.Team || '') : (stat['Last Team'] || ''),
    };
}

function logoForPlayer(id, season) {
    return playerSeasonInfo(id, season).logo;
}

function wirePlayerLinks(container) {
    container.querySelectorAll('.player-link[data-player-id]').forEach(el => {
        el.addEventListener('click', e => {
            e.preventDefault();
            const id = parseInt(el.dataset.playerId);
            // Import lazily to avoid circular dep at module parse time
            import('./player.js').then(m => {
                m.displayPlayerPage(id);
                window.location.hash = '#/stats';
            });
        });
    });
}

// Export for use by other views
export function getPlayerAwards(playerId) {
    const awardsData = state.awards;
    if (!awardsData) return [];
    const metadata = awardsData._metadata || {};
    const collected = {};

    const add = (key, season, league) => {
        if (!collected[key]) collected[key] = [];
        if (season) {
            if (!collected[key].some(a => a.season === season && a.league === league)) {
                collected[key].push({ season, league });
            }
        }
    };

    if (awardsData.HOF?.includes(playerId)) collected['HOF'] = [];
    if (awardsData.PCMVP?.includes(playerId)) add('PCMVP', null, null);
    if (awardsData.HRD?.includes(playerId)) add('HRD', null, null);

    for (const seasonKey in awardsData) {
        if (!seasonKey.startsWith('S')) continue;
        const sd = awardsData[seasonKey];
        if (sd.PCMVP?.includes(playerId)) add('PCMVP', seasonKey, null);
        if (sd.HRD?.includes(playerId)) add('HRD', seasonKey, null);
        for (const lg of ['AL', 'NL']) {
            if (!sd[lg]) continue;
            for (const awardKey in sd[lg]) {
                const av = sd[lg][awardKey];
                if (awardKey === 'SS' || awardKey === 'AS') {
                    if (typeof av === 'object' && av !== null && !Array.isArray(av)) {
                        for (const pos in av) {
                            if (pos === 'GM') continue;
                            const winners = av[pos];
                            const ids = Array.isArray(winners) ? winners : [winners];
                            if (ids.includes(playerId)) { add(awardKey, seasonKey, lg); break; }
                        }
                    }
                } else if (Array.isArray(av) && av.includes(playerId)) {
                    add(awardKey, seasonKey, lg);
                }
            }
        }
    }

    const order = ['HOF', 'MVP', 'CYA', 'ROTY', 'RPOTY', 'SS', 'AS', 'BT', 'ERAT', 'GMOTY', 'PCMVP', 'HRD'];
    const displayList = [];
    for (const awardId of order) {
        if (!collected[awardId]) continue;
        const wins = collected[awardId];
        const name = metadata[awardId] || awardId;
        if (awardId === 'HOF') {
            displayList.push({ text: name, cls: 'award-hof' });
        } else if (wins.length) {
            const count = wins.length;
            wins.sort((a, b) => getSeasonSort(a.season) - getSeasonSort(b.season));
            displayList.push({ text: count > 1 ? `${count}x ${name}` : name, cls: `award-${awardId.toLowerCase()}`, seasons: wins.map(w => w.season) });
        }
    }
    return displayList;
}
