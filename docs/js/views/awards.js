import { state } from '../state.js';
import { loadStats } from '../data.js';
import { getSeasonSort, getMlrLogoPair, getMlrTeamAbbr, getMilrLogoPair, recordFranchiseKey, makeLogoImg, getSeasonLogoOverride } from '../utils.js';
import { LEAGUE_LABELS } from '../constants.js';

// Site leagues with awards data, for the MLR/MiLR selector on this page.
const AWARDS_LEAGUES = ['mlr', 'milr'];


export async function renderAwards() {
    const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
    const league = urlParams.get('league') === 'milr' ? 'milr' : 'mlr';

    // Load hitting and pitching stats for logos — lazy, cached after first load
    try {
        await Promise.all(
            league === 'milr'
                ? [loadStats('milr', 'hitting'), loadStats('milr', 'pitching')]
                : [loadStats('mlr', 'hitting'), loadStats('mlr', 'pitching')]
        );
    } catch (_) {}

    const container = document.getElementById('awards-view');

    if (league === 'milr') {
        renderMilrAwardsPage(container, state.milrAwards, urlParams);
        return;
    }

    const awardsData = state.awards;
    const metadata = awardsData._metadata || {};

    const seasons = Object.keys(awardsData)
        .filter(k => k.startsWith('S') && hasAwards(awardsData[k]))
        .sort((a, b) => getSeasonSort(b) - getSeasonSort(a));

    let selected = seasons.includes(urlParams.get('season')) ? urlParams.get('season') : (seasons[0] || null);
    const initialConf = urlParams.get('conf') === 'nl' ? 'nl' : 'al';

    const idx = seasons.indexOf(selected);
    const prev = idx < seasons.length - 1 ? seasons[idx + 1] : null;
    const next = idx > 0 ? seasons[idx - 1] : null;

    let html = `<div class="awards-header team-stats-header">
        <h2 class="section-title">Awards —
            <select id="awards-league-select" class="title-season-select">
                ${AWARDS_LEAGUES.map(k => `<option value="${k}" ${k === league ? 'selected' : ''}>${LEAGUE_LABELS[k]}</option>`).join('')}
            </select>
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
            <button class="league-toggle-button${initialConf === 'al' ? ' active' : ''}" data-conf="al">American League</button>
            <button class="league-toggle-button${initialConf === 'nl' ? ' active' : ''}" data-conf="nl">National League</button>
        </div>
        <div class="leagues-wrapper show-${initialConf}">`;

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

    // League dropdown (MLR/MiLR)
    container.querySelector('#awards-league-select').addEventListener('change', e => {
        const newLeague = e.target.value;
        window.location.hash = newLeague === 'milr' ? `#/awards?season=${selected}&league=milr` : `#/awards?season=${selected}`;
    });

    // Season dropdown
    container.querySelector('#awards-season-select').addEventListener('change', e => {
        window.location.hash = `#/awards?season=${e.target.value}`;
    });

    // League toggle (mobile)
    container.querySelectorAll('.league-toggle-button').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.league-toggle-button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const conf = btn.dataset.conf;
            const wrapper = container.querySelector('.leagues-wrapper');
            wrapper.classList.toggle('show-al', conf === 'al');
            wrapper.classList.toggle('show-nl', conf === 'nl');
        });
    });

    // Player links
    wirePlayerLinks(container);
}

// ── MiLR All-Stars ───────────────────────────────────────────────────────────

function hasMilrAwards(entry) {
    return !!(entry?.AS && (entry.AS.GM?.length || entry.AS.R?.length));
}

function renderMilrAwardsPage(container, milrAwardsData, urlParams) {
    const seasons = Object.keys(milrAwardsData)
        .filter(k => k.startsWith('S') && hasMilrAwards(milrAwardsData[k]))
        .sort((a, b) => getSeasonSort(b) - getSeasonSort(a));

    let selected = seasons.includes(urlParams.get('season')) ? urlParams.get('season') : (seasons[0] || null);
    const idx = seasons.indexOf(selected);
    const prev = idx < seasons.length - 1 ? seasons[idx + 1] : null;
    const next = idx > 0 ? seasons[idx - 1] : null;

    let html = `<div class="awards-header team-stats-header">
        <h2 class="section-title">Awards —
            <select id="awards-league-select" class="title-season-select">
                ${AWARDS_LEAGUES.map(k => `<option value="${k}" ${k === 'milr' ? 'selected' : ''}>${LEAGUE_LABELS[k]}</option>`).join('')}
            </select>
            <select id="awards-season-select" class="title-season-select">
                ${seasons.map(s => `<option value="${s}" ${s === selected ? 'selected' : ''}>${s.replace('S', 'Season ')}</option>`).join('')}
            </select>
        </h2>
        <div class="season-nav-buttons">
            ${prev ? `<a href="#/awards?season=${prev}&league=milr" class="season-nav-button">&lt; Prev Season</a>` : ''}
            ${next ? `<a href="#/awards?season=${next}&league=milr" class="season-nav-button">Next Season &gt;</a>` : ''}
        </div>
    </div>`;

    if (!selected) { container.innerHTML = html + '<p>No MiLR All-Star data available.</p>'; return; }

    html += `<div class="awards-container">${renderMilrAllStars(milrAwardsData[selected], selected)}</div>`;
    container.innerHTML = html;

    container.querySelector('#awards-league-select').addEventListener('change', e => {
        const newLeague = e.target.value;
        window.location.hash = newLeague === 'milr' ? `#/awards?season=${selected}&league=milr` : `#/awards?season=${selected}`;
    });
    container.querySelector('#awards-season-select').addEventListener('change', e => {
        window.location.hash = `#/awards?season=${e.target.value}&league=milr`;
    });

    wirePlayerLinks(container);
}

// Shared by both the GM and All-Star sections below: sorts by team abbreviation
// then name, and splits into up to 4 columns filled top-to-bottom then
// left-to-right (same approach as the Reserves section's 2-column split).
function renderMilrPlayerGrid(ids, season) {
    if (!ids.length) return '';
    const players = ids.map(id => {
        const { logo, teamAbbr } = playerSeasonInfo(id, season, 'AS', 'milr');
        const player = state.allPlayers.find(p => p.ID === id);
        return { id, logo, teamAbbr, name: player?.Name || `#${id}` };
    });
    players.sort((a, b) => a.teamAbbr.localeCompare(b.teamAbbr) || a.name.localeCompare(b.name));

    const chunkSize = Math.ceil(players.length / 4);
    const cols = [];
    for (let i = 0; i < 4; i++) {
        const chunk = players.slice(i * chunkSize, (i + 1) * chunkSize);
        if (chunk.length) cols.push(chunk);
    }
    const renderMilrCol = col => col.map(p => `<div class="award-winner-item">
        ${p.logo ? makeLogoImg(p.logo.dark, p.logo.light, 'award-team-logo') : ''}${playerLink(p.id)}
    </div>`).join('');

    return `<div class="milr-as-grid">
        ${cols.map(col => `<div class="milr-as-col">${renderMilrCol(col)}</div>`).join('')}
    </div>`;
}

function renderMilrAllStars(entry, season) {
    if (!entry?.AS) return '';
    const gmIds = entry.AS.GM || [];
    const asIds = entry.AS.R || [];
    if (!gmIds.length && !asIds.length) return '';

    let gmHtml = '';
    if (gmIds.length) {
        gmHtml = `<div class="as-section as-gms">
            <h5>General Manager${gmIds.length > 1 ? 's' : ''}</h5>
            ${renderMilrPlayerGrid(gmIds, season)}
        </div>`;
    }

    let gridHtml = '';
    if (asIds.length) {
        gridHtml = `<div class="as-section as-milr-list">
            <h5>All-Stars</h5>
            ${renderMilrPlayerGrid(asIds, season)}
        </div>`;
    }

    return `<h4 class="awards-sub-title">MiLR All-Star Team</h4>
        <div class="awards-sub-section">
            <div class="award-category">
                <div class="all-star-team">
                    ${gmHtml}
                    ${gridHtml}
                </div>
            </div>
        </div>`;
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

// GMOTY was renamed in honor of Hannibal Bligh starting S12.
function getAwardName(key, season, metadata) {
    if (key === 'GMOTY' && getSeasonSort(season) >= 12) return 'Hannibal Bligh GM of the Year';
    return metadata[key] || key;
}

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
                const logo = logoForPlayer(ids[0], season, key);
                inner = `<div class="award-winner-item">${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${ids.map(id => playerLink(id)).join(' &amp; ')}</div>`;
            } else {
                inner = ids.map(id => {
                    const logo = logoForPlayer(id, season, key);
                    return `<div class="award-winner-item">${logo ? makeLogoImg(logo.dark, logo.light, 'award-team-logo') : ''}${playerLink(id)}</div>`;
                }).join('');
            }
            return `<div class="award-category"><h4>${getAwardName(key, season, metadata)}</h4><div class="award-winners-list">${inner}</div></div>`;
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
                const logo = logoForPlayer(id, season, 'SS');
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
                const logo = logoForPlayer(id, season, 'SS');
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
        const infos = as.GM.map(id => ({ id, ...playerSeasonInfo(id, season, 'AS') }));
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
            const logo = logoForPlayer(id, season, 'AS');
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
                    const logo = logoForPlayer(id, season, 'AS');
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
            const { logo, teamAbbr } = playerSeasonInfo(id, season, 'AS');
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
            const logo = logoForPlayer(id, season, key);
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
    return `<a href="#/stats?id=${id}" class="player-link" data-player-id="${id}">${name}</a>`;
}

// Returns logo and team abbreviation for a player in a given season.
// Uses recordFranchiseKey to avoid the multi-franchise same-abbreviation bug.
// `awardKey` (e.g. "AS", "SS", "MVP") lets docs/data/logo_overrides.json
// override the represented team per-award, for players who changed teams
// mid-season (e.g. an All-Star picked while on their first team).
// `league` ('mlr' or 'milr') selects which league's stats/team helpers to use.
// MiLR has no franchise-key indirection (a stat row's own team IS the display
// abbreviation) and no logo-override support (docs/data/logo_overrides.json
// is MLR-only), so the milr branch skips both of those MLR-specific steps.
function playerSeasonInfo(id, season, awardKey, league = 'mlr') {
    if (league === 'milr') {
        const hitting  = state.stats['milr_hitting']  || [];
        const pitching = state.stats['milr_pitching'] || [];
        const all = [...hitting, ...pitching];
        const stat = all.filter(s => s.ID === id && s['Display Season'] === season && !s.is_sub_row)
                        .sort((a, b) => (b['Last Session'] || 0) - (a['Last Session'] || 0))[0]
                  || all.filter(s => s.ID === id && !s.is_sub_row)
                        .sort((a, b) =>
                            getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']) ||
                            (b['Last Session'] || 0) - (a['Last Session'] || 0))[0];
        if (!stat) return { logo: null, teamAbbr: '' };
        const teamAbbr = recordFranchiseKey(stat);
        return { logo: getMilrLogoPair(teamAbbr, stat['Display Season']), teamAbbr };
    }

    // Checked first and independent of stat rows: some award winners (e.g. a
    // GM who never played) have no MLR stat history at all to fall back on.
    const override = getSeasonLogoOverride(id, season, awardKey);
    if (override) {
        return {
            logo: getMlrLogoPair(override, season),
            teamAbbr: getMlrTeamAbbr(override, season),
        };
    }

    const hitting  = state.stats['mlr_hitting']  || [];
    const pitching = state.stats['mlr_pitching'] || [];
    const all = [...hitting, ...pitching];
    // A two-way player has separate hitting and pitching rows for the same
    // season; when they differ (e.g. traded mid-season during their pitching
    // stint but not their hitting one), prefer whichever stint ran later.
    const stat = all.filter(s => s.ID === id && s['Display Season'] === season && !s.is_sub_row)
                    .sort((a, b) => (b['Last Session'] || 0) - (a['Last Session'] || 0))[0]
              || all.filter(s => s.ID === id && !s.is_sub_row)
                    .sort((a, b) =>
                        getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']) ||
                        (b['Last Session'] || 0) - (a['Last Session'] || 0))[0];
    if (!stat) return { logo: null, teamAbbr: '' };

    // Derive teamAbbr from the same resolved franchise as the logo (rather than
    // a separate check on stat.Team) so sorting always matches what's displayed —
    // stat.Team can be "3TM", "4TM", etc. for players with more than two stops.
    const franchiseKey = recordFranchiseKey(stat);
    return {
        logo: getMlrLogoPair(franchiseKey, stat['Display Season']),
        teamAbbr: getMlrTeamAbbr(franchiseKey, stat['Display Season']),
    };
}

function logoForPlayer(id, season, awardKey) {
    return playerSeasonInfo(id, season, awardKey).logo;
}

function wirePlayerLinks(container) {
    container.querySelectorAll('.player-link[data-player-id]').forEach(el => {
        el.addEventListener('click', e => {
            e.preventDefault();
            const id = parseInt(el.dataset.playerId);
            // Import lazily to avoid circular dep at module parse time
            import('./player.js').then(m => {
                m.displayPlayerPage(id);
                window.location.hash = `#/stats?id=${id}`;
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

    // `conf` is AL/NL (MLR-only); `siteLeague` is which site league ('mlr'/'milr')
    // the award is from, so a player's badge link can carry both independently.
    const add = (key, season, conf, siteLeague = 'mlr') => {
        if (!collected[key]) collected[key] = [];
        if (season) {
            if (!collected[key].some(a => a.season === season && a.conf === conf)) {
                collected[key].push({ season, conf, siteLeague });
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

    // MiLR All-Stars live in their own file/state slot, shaped like MLR's own
    // AS object (GM + a flat roster, here under "R" since there are no
    // positions to label). GM picks are intentionally not badged, matching
    // how MLR's own AS.GM is skipped above.
    const milrAwardsData = state.milrAwards || {};
    for (const seasonKey in milrAwardsData) {
        if (milrAwardsData[seasonKey].AS?.R?.includes(playerId)) add('MILRAS', seasonKey, null, 'milr');
    }

    const order = ['HOF', 'MVP', 'CYA', 'ROTY', 'RPOTY', 'SS', 'AS', 'BT', 'ERAT', 'GMOTY', 'PCMVP', 'HRD', 'MILRAS'];
    const displayList = [];
    for (const awardId of order) {
        if (!collected[awardId]) continue;
        const wins = collected[awardId];
        if (awardId === 'HOF') {
            const name = metadata[awardId] || awardId;
            displayList.push({ text: name, cls: 'award-hof' });
        } else if (wins.length) {
            const count = wins.length;
            wins.sort((a, b) => getSeasonSort(a.season) - getSeasonSort(b.season));
            const name = getAwardName(awardId, wins[wins.length - 1]?.season, metadata);
            const lastConf = wins[wins.length - 1]?.conf?.toLowerCase() || null;
            const lastSiteLeague = wins[wins.length - 1]?.siteLeague || 'mlr';
            displayList.push({ text: count > 1 ? `${count}x ${name}` : name, cls: `award-${awardId.toLowerCase()}`, seasons: wins.map(w => w.season), conf: lastConf, siteLeague: lastSiteLeague });
        }
    }
    return displayList;
}
