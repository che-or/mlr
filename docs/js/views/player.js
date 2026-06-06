import { state } from '../state.js';
import { loadStats, searchPlayers, getPlayerById } from '../data.js';
import { formatStat, getSeasonSort, getFranchiseKey, getMlrLogo, getMlrLogoPair, getMilrTeamName, getMilrLogoPair, getFcbTeamName, getHistoricalLogoPair, setStickyColumnOffsets, recordFranchiseKey, makeLogoImg } from '../utils.js';
import { STAT_DEFINITIONS, STAT_DESCRIPTIONS, LEAGUES_WITH_CAREER } from '../constants.js';
import { getPlayerAwards } from './awards.js';

const LOWER_BETTER_PITCH = new Set(['ERA', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'RE24', 'HR%', 'BB%', 'ERA-', 'FB%']);
const LOWER_BETTER_BAT = new Set(['K%', 'GB%', 'GB/FB', 'Avg Diff']);

const POSITION_NAMES = {
    'C':   'Catcher',
    '1B':  'First Baseman',
    '2B':  'Second Baseman',
    '3B':  'Third Baseman',
    'SS':  'Shortstop',
    'LF':  'Left Fielder',
    'CF':  'Center Fielder',
    'RF':  'Right Fielder',
    'OF':  'Outfielder',
    'P':   'Pitcher',
    'DH':  'Designated Hitter',
    'PH':  'Pinch Hitter',
    'SP':  'Starting Pitcher',
    'RP':  'Relief Pitcher',
};

// Leagues shown as collapsible toggles after MLR, in display order.
// playoffKey: the corresponding playoff league key, if one exists.
const TOGGLE_LEAGUES = [
    { key: 'milr',  label: 'MiLR', storageKey: 'milrStatsVisible', playoffKey: 'milr_playoff' },
    { key: 'fcb',   label: 'FCB',  storageKey: 'fcbStatsVisible'  },
    { key: 'gib',   label: 'GIB',  storageKey: 'gibStatsVisible'  },
    { key: 'eco',   label: 'ECO',  storageKey: 'ecoStatsVisible'  },
    { key: 'npr',   label: 'NPR',  storageKey: 'nprStatsVisible'  },
    { key: 'wbc',   label: 'WBC',  storageKey: 'wbcStatsVisible'  },
];

// ── Search ────────────────────────────────────────────────────────────────────

export function initPlayerSearch() {
    const input       = document.getElementById('player-search');
    const suggestions = document.getElementById('player-suggestions');

    input.addEventListener('input', () => {
        const q = input.value.trim();
        if (/^\d+$/.test(q)) {
            const p = getPlayerById(parseInt(q));
            if (p) { showSuggestions([p], suggestions); return; }
        }
        if (q.length < 2) { suggestions.style.display = 'none'; return; }
        showSuggestions(searchPlayers(q).slice(0, 10), suggestions);
    });

    suggestions.addEventListener('click', e => {
        const item = e.target.closest('.suggestion-item');
        if (!item) return;
        input.value = item.dataset.name;
        suggestions.style.display = 'none';
        state.currentPlayerId = parseInt(item.dataset.id);
        displayPlayerPage(state.currentPlayerId);
    });

    document.addEventListener('click', e => {
        if (!e.target.closest('#stats-controls')) suggestions.style.display = 'none';
    });
}

function showSuggestions(players, container) {
    if (!players.length) { container.style.display = 'none'; return; }
    const nameCounts = {};
    players.forEach(p => { nameCounts[p.Name] = (nameCounts[p.Name] || 0) + 1; });
    container.innerHTML = players.map(p => {
        const label = nameCounts[p.Name] > 1 ? `${p.Name} (#${p.ID})` : p.Name;
        return `<div class="suggestion-item" data-id="${p.ID}" data-name="${p.Name}">${label}</div>`;
    }).join('');
    container.style.display = 'block';
}

// ── Player page ───────────────────────────────────────────────────────────────

export async function displayPlayerPage(playerId) {
    const display = document.getElementById('stats-content-display');
    state.currentPlayerId = playerId;
    display.innerHTML = '<p>Loading...</p>';

    try {
        // Build full fetch list: MLR core + franchise breakdowns + all toggle leagues
        const fetches = [
            loadStats('mlr',         'hitting'),          loadStats('mlr',         'pitching'),
            loadStats('mlr',         'career_hitting'),   loadStats('mlr',         'career_pitching'),
            loadStats('mlr',         'hitting_by_team'),  loadStats('mlr',         'pitching_by_team'),
            loadStats('mlr_playoff', 'hitting'),          loadStats('mlr_playoff', 'pitching'),
            loadStats('mlr_playoff', 'career_hitting'),   loadStats('mlr_playoff', 'career_pitching'),
            loadStats('mlr_playoff', 'hitting_by_team'),  loadStats('mlr_playoff', 'pitching_by_team'),
        ];
        for (const { key, playoffKey } of TOGGLE_LEAGUES) {
            fetches.push(loadStats(key, 'hitting'), loadStats(key, 'pitching'));
            if (LEAGUES_WITH_CAREER.includes(key)) {
                fetches.push(loadStats(key, 'career_hitting'), loadStats(key, 'career_pitching'));
            }
            if (playoffKey) {
                fetches.push(loadStats(playoffKey, 'hitting'), loadStats(playoffKey, 'pitching'));
                if (LEAGUES_WITH_CAREER.includes(playoffKey)) {
                    fetches.push(loadStats(playoffKey, 'career_hitting'), loadStats(playoffKey, 'career_pitching'));
                }
            }
        }
        await Promise.all(fetches);

        const player = getPlayerById(playerId);
        if (!player) { display.innerHTML = '<p>Player not found.</p>'; return; }

        // MLR season stats
        const mlrH = filterPlayer(state.stats['mlr_hitting']  || [], playerId);
        const mlrP = filterPlayer(state.stats['mlr_pitching'] || [], playerId);
        attachCareerRow(mlrH, 'mlr_career_hitting',  playerId);
        attachCareerRow(mlrP, 'mlr_career_pitching', playerId);
        attachFranchiseRows(mlrH, 'mlr_hitting_by_team',  playerId);
        attachFranchiseRows(mlrP, 'mlr_pitching_by_team', playerId);

        const mlrPoH = filterPlayer(state.stats['mlr_playoff_hitting']  || [], playerId);
        const mlrPoP = filterPlayer(state.stats['mlr_playoff_pitching'] || [], playerId);
        attachCareerRow(mlrPoH, 'mlr_playoff_career_hitting',  playerId);
        attachCareerRow(mlrPoP, 'mlr_playoff_career_pitching', playerId);
        attachFranchiseRows(mlrPoH, 'mlr_playoff_hitting_by_team',  playerId);
        attachFranchiseRows(mlrPoP, 'mlr_playoff_pitching_by_team', playerId);

        const hasMLR = mlrH.length || mlrP.length;
        const primaryRole = determinePrimaryRole(mlrH, mlrP);

        // Build header
        display.innerHTML = buildHeader(player, playerId, mlrH, mlrP,
            [...filterPlayer(state.stats['fcb_hitting']  || [], playerId),
             ...filterPlayer(state.stats['fcb_pitching'] || [], playerId)],
            [...filterPlayer(state.stats['npr_hitting']  || [], playerId),
             ...filterPlayer(state.stats['npr_pitching'] || [], playerId)],
            [...filterPlayer(state.stats['wbc_hitting']  || [], playerId),
             ...filterPlayer(state.stats['wbc_pitching'] || [], playerId)],
            [...filterPlayer(state.stats['milr_hitting']  || [], playerId),
             ...filterPlayer(state.stats['milr_pitching'] || [], playerId)]);

        // League tabs: MLR first, then other leagues in order
        const leagues = [];
        if (hasMLR || mlrPoH.length || mlrPoP.length) {
            leagues.push({ key: 'mlr', label: 'MLR', regH: mlrH, regP: mlrP, poH: mlrPoH, poP: mlrPoP, regLeague: 'mlr', poLeague: 'mlr_playoff' });
        }

        for (const { key, label, playoffKey } of TOGGLE_LEAGUES) {
            const lgH = filterPlayer(state.stats[`${key}_hitting`]  || [], playerId);
            const lgP = filterPlayer(state.stats[`${key}_pitching`] || [], playerId);
            if (!lgH.length && !lgP.length) continue;

            if (LEAGUES_WITH_CAREER.includes(key)) {
                attachCareerRow(lgH, `${key}_career_hitting`,  playerId);
                attachCareerRow(lgP, `${key}_career_pitching`, playerId);
            }

            let poH = [], poP = [];
            if (playoffKey) {
                poH = filterPlayer(state.stats[`${playoffKey}_hitting`]  || [], playerId);
                poP = filterPlayer(state.stats[`${playoffKey}_pitching`] || [], playerId);
                if (LEAGUES_WITH_CAREER.includes(playoffKey)) {
                    attachCareerRow(poH, `${playoffKey}_career_hitting`,  playerId);
                    attachCareerRow(poP, `${playoffKey}_career_pitching`, playerId);
                }
            }

            leagues.push({ key, label, regH: lgH, regP: lgP, poH, poP, regLeague: key, poLeague: playoffKey || null });
        }

        if (leagues.length > 0) {
            buildLeagueTabGrid(display, leagues, primaryRole);
        }

        wireTeamLinks(display);
        display.querySelectorAll('.stats-table').forEach(makeTableSortable);
        setStickyColumnOffsets();
    } catch (err) {
        console.error(err);
        display.innerHTML = '<p>Failed to load player stats.</p>';
    }
}

// ── Header ────────────────────────────────────────────────────────────────────

function buildHeader(player, playerId, mlrH, mlrP, fcbH, nprH, wbcH, milrH) {
    const logo = resolvePlayerLogo(playerId, mlrH, mlrP, fcbH, nprH, wbcH, milrH);

    let html = `<h2 class="section-title">`;
    if (logo) html += makeLogoImg(logo.dark, logo.light, 'player-team-logo') + ' ';
    html += `${player.Name}</h2>`;
    html += `<p class="player-id-display">Player ID: ${playerId}</p>`;

    const formerNames = player['Former Names'];
    const formerArr = Array.isArray(formerNames) ? formerNames : (formerNames ? [formerNames] : []);
    if (formerArr.length) {
        html += `<p class="former-names">Formerly known as: ${formerArr.join(', ')}</p>`;
    }

    // Awards
    const awards = getPlayerAwards(playerId);
    if (awards.length) {
        html += '<div class="awards-container">';
        awards.forEach(award => {
            const seasonTitle = award.seasons?.length ? ` title="${award.seasons.join(', ')}"` : '';
            if (award.cls === 'award-hof') {
                html += `<a href="#/hof"><div class="award-box ${award.cls}"${seasonTitle}>${award.text}</div></a>`;
            } else if (award.seasons?.length) {
                const last = award.seasons[award.seasons.length - 1];
                html += `<a href="#/awards?season=${last}"><div class="award-box ${award.cls}"${seasonTitle}>${award.text}</div></a>`;
            } else {
                html += `<div class="award-box ${award.cls}"${seasonTitle}>${award.text}</div>`;
            }
        });
        html += '</div>';
    }

    // Player info — spell out position fully
    const td = state.typeDefinitions;
    const pos  = player.Position;
    const hand = player.Handedness;
    const batType = player['Batting Type'];
    const pitType = player['Pitching Type'];
    const isPitcher     = pos === 'P';
    const isPinchHitter = pos === 'PH';

    let infoHtml = '';
    if (pos)  infoHtml += `<p><strong>Position:</strong> ${POSITION_NAMES[pos] || pos}</p>`;
    if (hand) infoHtml += `<p><strong>Handedness:</strong> ${hand}</p>`;
    // Show batting type for everyone except pure pitchers
    if (!isPitcher && batType && td.batting?.[batType]) {
        infoHtml += `<p><strong>Batting:</strong> ${td.batting[batType]}</p>`;
    }
    // Show pitching type for pitchers and pinch hitters (who also pitch)
    if ((isPitcher || isPinchHitter) && pitType && pitType !== 'POS' && td.pitching?.[pitType]) {
        infoHtml += `<p><strong>Pitching:</strong> ${td.pitching[pitType]}</p>`;
    }
    if (infoHtml) html += `<div class="player-info">${infoHtml}</div>`;

    return html;
}


function resolvePlayerLogo(playerId, mlrH, mlrP, fcbH, nprH, wbcH, milrH) {
    const lastSeason = rows => (rows || [])
        .filter(r => !r.is_sub_row && r['Display Season']?.startsWith('S'))
        .sort((a, b) => getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']))[0];

    // MLR
    const lastMLR = [
        ...mlrH.filter(r => !r.is_sub_row && r['Display Season']?.startsWith('S')),
        ...mlrP.filter(r => !r.is_sub_row && r['Display Season']?.startsWith('S')),
    ].sort((a, b) =>
        getSeasonSort(b['Display Season']) - getSeasonSort(a['Display Season']) ||
        (b['Last Session'] || 0) - (a['Last Session'] || 0)
    )[0];
    if (lastMLR) {
        const fk = recordFranchiseKey(lastMLR);
        return getMlrLogoPair(fk, lastMLR['Display Season']);
    }

    // FCB
    const lastFCB = lastSeason(fcbH);
    if (lastFCB) {
        const season = state.teamHistory.fcb[lastFCB['Display Season']] || {};
        const entry  = season[lastFCB.Team];
        if (entry?.logo_dark) return { dark: entry.logo_dark, light: entry.logo_light };
    }

    // NPR
    const lastNPR = lastSeason(nprH);
    if (lastNPR) {
        const pair = getHistoricalLogoPair('npr', lastNPR.Team, lastNPR['Display Season']);
        if (pair) return pair;
    }

    // WBC
    const lastWBC = lastSeason(wbcH);
    if (lastWBC) {
        const pair = getHistoricalLogoPair('wbc', lastWBC.Team, lastWBC['Display Season']);
        if (pair) return pair;
    }

    // MiLR
    const lastMiLR = lastSeason(milrH);
    if (lastMiLR) {
        const pair = getMilrLogoPair(lastMiLR.Team, lastMiLR['Display Season']);
        if (pair) return pair;
    }

    return null;
}

// ── Row attachment ────────────────────────────────────────────────────────────

function attachCareerRow(rows, cacheKey, playerId) {
    const career = (state.stats[cacheKey] || []).find(r => r.ID === playerId);
    if (career) {
        rows.push({ ...career, 'Display Season': 'Career', Team: '', Franchise: '', is_sub_row: false });
    }
}

// Franchise rows: one per franchise the player appeared for (multi-team entries excluded)
function attachFranchiseRows(rows, cacheKey, playerId) {
    const byTeam = (state.stats[cacheKey] || []).filter(r =>
        r.ID === playerId && r.Franchise && !/^\d+TM$/.test(r.Franchise)
    );
    for (const r of byTeam) {
        rows.push({ ...r, 'Display Season': 'Franchise', Team: r.Franchise, is_sub_row: false });
    }
}

// ── Primary role ──────────────────────────────────────────────────────────────

function determinePrimaryRole(mlrH, mlrP) {
    const seasonH = mlrH.filter(r => r['Display Season']?.startsWith('S') && !r.is_sub_row);
    const seasonP = mlrP.filter(r => r['Display Season']?.startsWith('S') && !r.is_sub_row);

    const lastHS = seasonH.length ? Math.max(...seasonH.map(r => getSeasonSort(r['Display Season']))) : -1;
    const lastPS = seasonP.length ? Math.max(...seasonP.map(r => getSeasonSort(r['Display Season']))) : -1;

    if (lastPS > lastHS) return 'pitcher';
    if (lastHS > lastPS) return 'hitter';
    if (lastHS > 0) {
        const ds   = seasonH.find(r => getSeasonSort(r['Display Season']) === lastHS)?.['Display Season'];
        const recH = seasonH.find(r => r['Display Season'] === ds);
        const recP = seasonP.find(r => r['Display Season'] === ds);
        if (recP && recH) {
            if (recP.G > recH.G) return 'pitcher';
            if (recP.G === recH.G && (recP.BF || 0) > (recH.PA || 0)) return 'pitcher';
        } else if (recP) return 'pitcher';
    }
    return 'hitter';
}

// ── Sorting ───────────────────────────────────────────────────────────────────

// Sort order: regular season rows → career row → franchise rows
function rowScore(r) {
    if (r['Display Season'] === 'Franchise') return 3;
    if (r['Display Season'] === 'Career')    return 2;
    return 0;
}

function sortStats(rows) {
    rows.sort((a, b) => {
        const sa = rowScore(a), sb = rowScore(b);
        if (sa !== sb) return sa - sb;
        if (sa === 3) {
            // Both Franchise: sort by PA/IP desc, then by franchise key
            const pa = (b.PA || b.IP || 0) - (a.PA || a.IP || 0);
            return pa !== 0 ? pa : (a.Team || '').localeCompare(b.Team || '');
        }
        if (sa !== 0) return 0; // Career: only one
        // Regular season rows
        const diff = getSeasonSort(a['Display Season']) - getSeasonSort(b['Display Season']);
        if (diff !== 0) return diff;
        return (a.is_sub_row ? 1 : 0) - (b.is_sub_row ? 1 : 0);
    });
}

// ── Stats rendering ───────────────────────────────────────────────────────────

function renderLeagueStats(container, label, lgH, lgP, primaryRole, league) {
    const prefix = label ? `${label} ` : '';
    if (primaryRole === 'pitcher') {
        if (lgP.length) container.innerHTML += createStatsSection(`${prefix}Pitching Stats`, lgP, true,  league);
        if (lgH.length) container.innerHTML += createStatsSection(`${prefix}Batting Stats`,  lgH, false, league);
    } else {
        if (lgH.length) container.innerHTML += createStatsSection(`${prefix}Batting Stats`,  lgH, false, league);
        if (lgP.length) container.innerHTML += createStatsSection(`${prefix}Pitching Stats`, lgP, true,  league);
    }
}

function renderLeagueWithPlayoffToggle(container, label, regH, regP, poH, poP, primaryRole, regLeague, poLeague) {
    const hasPlayoffs = poH.length || poP.length;

    if (!hasPlayoffs) {
        renderLeagueStats(container, label, regH, regP, primaryRole, regLeague);
        return;
    }

    const tabBar = document.createElement('div');
    tabBar.className = 'season-type-tabs';
    tabBar.innerHTML = `
        <button class="season-type-tab active" data-tab="regular" data-text="Regular Season">Regular Season</button>
        <button class="season-type-tab" data-tab="playoff" data-text="Postseason">Postseason</button>`;
    container.appendChild(tabBar);

    const regDiv = document.createElement('div');
    regDiv.style.marginTop = '10px';
    renderLeagueStats(regDiv, label, regH, regP, primaryRole, regLeague);
    container.appendChild(regDiv);

    const poLabel = label ? `${label} Postseason` : 'Postseason';
    const poDiv = document.createElement('div');
    poDiv.style.display = 'none';
    poDiv.style.marginTop = '10px';
    renderLeagueStats(poDiv, poLabel, poH, poP, primaryRole, poLeague);
    container.appendChild(poDiv);

    tabBar.querySelectorAll('.season-type-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            tabBar.querySelectorAll('.season-type-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const showPlayoff = btn.dataset.tab === 'playoff';
            regDiv.style.display = showPlayoff ? 'none' : '';
            poDiv.style.display  = showPlayoff ? '' : 'none';
            setStickyColumnOffsets();
        });
    });
}

function createStatsSection(title, rows, isPitching, league) {
    sortStats(rows);
    const groups = isPitching ? STAT_DEFINITIONS.pitching : STAT_DEFINITIONS.batting;
    let html = `<div class="stats-section"><h3 class="section-title">${title}</h3>`;

    for (const [groupName, cols] of Object.entries(groups)) {
        html += `<h4>${groupName}</h4>`;
        html += '<div class="stats-table-container"><table class="stats-table"><thead><tr>';
        cols.forEach((col, i) => {
            const cls  = i < 2 ? ` class="sticky-col col-${i}"` : '';
            const lbl  = colHeaderLabel(col);
            const desc = STAT_DESCRIPTIONS[col] || '';
            html += `<th${cls} title="${desc}">${lbl}</th>`;
        });
        html += '</tr></thead><tbody>';

        rows.forEach((r, idx) => {
            const isFranchise = r['Display Season'] === 'Franchise';
            const isCareer    = r['Display Season'] === 'Career';
            let rowCls = '';
            if (isCareer)    rowCls = 'career-row';
            else if (isFranchise) rowCls = 'franchise-row sub-row';
            else if (r.is_sub_row) rowCls = 'sub-row';
            html += `<tr class="${rowCls}" data-original-index="${idx}">`;
            cols.forEach((col, i) => {
                const cls = i < 2 ? ` class="sticky-col col-${i}"` : '';
                html += buildCell(col, r, isPitching, isCareer, isFranchise, groupName, league, cls);
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
    }
    return html + '</div>';
}

function colHeaderLabel(col) {
    if (col === 'Display Season') return 'Season';
    if (col === 'Batting Type' || col === 'Pitching Type') return 'Type';
    return col;
}

function buildCell(col, r, isPitching, isCareer, isFranchise, groupName, league, tdCls) {
    const isOpponent = groupName === 'Opponent Stats';

    if (col === 'Display Season') {
        // Franchise rows show a blank season cell
        return `<td${tdCls}>${isFranchise ? '' : (r['Display Season'] || '-')}</td>`;
    }

    if (col === 'Team') {
        return buildTeamCell(r, isCareer, isFranchise, league, tdCls);
    }

    if (col === 'Batting Type' || col === 'Pitching Type') {
        const code     = r[col] || '';
        const category = col === 'Batting Type' ? 'batting' : 'pitching';
        const fullName = code && state.typeDefinitions[category]?.[code] ? state.typeDefinitions[category][code] : '';
        return `<td${tdCls} title="${fullName}">${code || '-'}</td>`;
    }

    // All other stat cells
    let val = r[col];
    if (val !== null && val !== undefined) {
        val = suppressRateStat(col, val, r, isPitching, isOpponent);
    }
    return `<td${tdCls}>${formatStat(col, val)}</td>`;
}

function suppressRateStat(col, val, r, isPitching, isOpponent) {
    const ip  = r.IP  || 0, ab  = r.AB  || 0, pa  = r.PA  || 0;
    const bb  = r.BB  || 0, bf  = r.BF  || 0;
    const w   = r.W   || 0, l   = r.L   || 0, opp = r.OPP || 0;
    const sb  = r.SB  || 0, cs  = r.CS  || 0;

    if (isPitching && !isOpponent) {
        if (['ERA','FIP','WHIP','H6','HR6','BB6','SO6','ERA-'].includes(col) && ip === 0) return null;
        if (col === 'SO/BB' && bb === 0) return null;
        if (col === 'W-L%' && (w + l) === 0) return null;
        if (col === 'SV%'  && opp === 0) return null;
        if (['HR%','K%','BB%','GB%','FB%','GB/FB'].includes(col) && bf === 0) return null;
    } else if (isPitching && isOpponent) {
        if (['BA','OBP','SLG','OPS','BABIP'].includes(col) && bf === 0) return null;
        if (col === 'SB%' && (sb + cs) === 0) return null;
    } else {
        if (['BA','ISO','BABIP','SLG','OPS','OPS+'].includes(col) && ab === 0) return null;
        if (['OBP','HR%','K%','BB%','GB%','FB%','GB/FB'].includes(col) && pa === 0) return null;
        if (col === 'SB%' && (sb + cs) === 0) return null;
    }
    return val;
}

function buildTeamCell(r, isCareer, isFranchise, league, tdCls) {
    const team = r.Team || '';
    const isMultiTeam = /^\d+TM$/.test(team);
    const ds = r['Display Season'] || '';

    // Career and Franchise rows are not clickable links
    if (isCareer || isFranchise || isMultiTeam || !team || !ds.startsWith('S')) {
        return `<td${tdCls}>${team || ''}</td>`;
    }

    let franchiseKey = team;
    let lgParam = '';
    if (league === 'mlr' || league === 'mlr_playoff') {
        franchiseKey = getFranchiseKey(team, ds);
    } else if (league === 'milr' || league === 'milr_playoff') {
        lgParam = '&league=milr';
    } else if (league === 'fcb') {
        lgParam = '&league=fcb';
    } else {
        lgParam = `&league=${league}`;
    }

    return `<td${tdCls}><span class="team-link" data-team="${encodeURIComponent(franchiseKey)}" data-season="${ds}" data-league="${league}" style="cursor:pointer;text-decoration:underline">${team}</span></td>`;
}

// ── League tab grid ───────────────────────────────────────────────────────────

function buildLeagueTabGrid(container, leagues, primaryRole) {
    let totalCols = 0;
    const colStarts = [];
    for (const lg of leagues) {
        const hasRegular = lg.regH.length || lg.regP.length;
        const hasPlayoffs = lg.poH.length || lg.poP.length;
        const span = (hasRegular && hasPlayoffs) ? 2 : 1;
        colStarts.push({ colStart: totalCols + 1, span });
        totalCols += span;
    }

    const grid = document.createElement('div');
    grid.className = 'league-tab-grid';
    grid.style.gridTemplateColumns = Array(totalCols).fill('auto').join(' ');

    const contentWrap = document.createElement('div');
    contentWrap.className = 'league-tab-content';
    const allCells = [];

    leagues.forEach((lg, gIdx) => {
        const hasRegular = lg.regH.length || lg.regP.length;
        const hasPlayoffs = lg.poH.length || lg.poP.length;
        const { colStart } = colStarts[gIdx];

        if (hasRegular && hasPlayoffs) {
            const header = document.createElement('button');
            header.className = 'lt-header';
            header.textContent = lg.label;
            header.style.gridColumn = `${colStart} / span 2`;
            header.style.gridRow = '1';
            const regCellIdx = allCells.length;
            header.addEventListener('click', () => { activate(regCellIdx); setStickyColumnOffsets(); });
            grid.appendChild(header);

            const regContent = document.createElement('div');
            renderLeagueStats(regContent, null, lg.regH, lg.regP, primaryRole, lg.regLeague);
            contentWrap.appendChild(regContent);
            const regBtn = document.createElement('button');
            regBtn.className = 'lt-cell lt-sub';
            regBtn.textContent = 'Regular Season';
            regBtn.dataset.text = 'Regular Season';
            regBtn.style.gridColumn = `${colStart}`;
            regBtn.style.gridRow = '2';
            grid.appendChild(regBtn);
            allCells.push({ btn: regBtn, contentDiv: regContent, header });

            const poContent = document.createElement('div');
            renderLeagueStats(poContent, null, lg.poH, lg.poP, primaryRole, lg.poLeague);
            contentWrap.appendChild(poContent);
            const poBtn = document.createElement('button');
            poBtn.className = 'lt-cell lt-sub';
            poBtn.textContent = 'Postseason';
            poBtn.dataset.text = 'Postseason';
            poBtn.style.gridColumn = `${colStart + 1}`;
            poBtn.style.gridRow = '2';
            grid.appendChild(poBtn);
            allCells.push({ btn: poBtn, contentDiv: poContent, header });
        } else {
            const content = document.createElement('div');
            renderLeagueStats(content, null,
                hasRegular ? lg.regH : lg.poH,
                hasRegular ? lg.regP : lg.poP,
                primaryRole,
                hasRegular ? lg.regLeague : lg.poLeague
            );
            contentWrap.appendChild(content);
            const btn = document.createElement('button');
            btn.className = 'lt-cell';
            btn.textContent = lg.label;
            btn.dataset.text = lg.label;
            btn.style.gridColumn = `${colStart}`;
            btn.style.gridRow = '1 / span 2';
            grid.appendChild(btn);
            allCells.push({ btn, contentDiv: content, header: null });
        }
    });

    const activate = (idx) => {
        allCells.forEach((cell, i) => {
            cell.btn.classList.toggle('active', i === idx);
            cell.contentDiv.style.display = i === idx ? '' : 'none';
        });
        const activeHeader = allCells[idx]?.header || null;
        grid.querySelectorAll('.lt-header').forEach(h => {
            h.classList.toggle('active-parent', h === activeHeader);
        });
    };

    allCells.forEach((cell, idx) => {
        cell.contentDiv.style.display = 'none';
        cell.btn.addEventListener('click', () => {
            activate(idx);
            setStickyColumnOffsets();
        });
    });

    // Build mobile dropdown
    const leagueGroups = [];
    {
        let ci = 0;
        for (const lg of leagues) {
            const hasRegular = lg.regH.length || lg.regP.length;
            const hasPlayoffs = lg.poH.length || lg.poP.length;
            if (hasRegular && hasPlayoffs) {
                leagueGroups.push({ label: lg.label, regIdx: ci, poIdx: ci + 1 });
                ci += 2;
            } else {
                leagueGroups.push({ label: lg.label, regIdx: ci, poIdx: null });
                ci += 1;
            }
        }
    }

    const mobileWrap = document.createElement('div');
    mobileWrap.className = 'lt-mobile';

    const mobileRow = document.createElement('div');
    mobileRow.className = 'lt-mobile-row';

    const mobileSelect = document.createElement('select');
    mobileSelect.className = 'lt-league-select';
    leagueGroups.forEach((grp, i) => {
        const opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = grp.label;
        mobileSelect.appendChild(opt);
    });

    const mobileToggle = document.createElement('div');
    mobileToggle.className = 'lt-season-toggle';

    const mobileRegBtn = document.createElement('button');
    mobileRegBtn.className = 'lt-season-btn active';
    mobileRegBtn.textContent = 'Regular Season';

    const mobilePoBtn = document.createElement('button');
    mobilePoBtn.className = 'lt-season-btn';
    mobilePoBtn.textContent = 'Postseason';

    mobileToggle.appendChild(mobileRegBtn);
    mobileToggle.appendChild(mobilePoBtn);
    mobileRow.appendChild(mobileSelect);
    mobileRow.appendChild(mobileToggle);
    mobileWrap.appendChild(mobileRow);

    let mobileIsPlayoffs = false;

    const updateMobileState = (grpIdx) => {
        const grp = leagueGroups[grpIdx];
        const hasBoth = grp.poIdx !== null;
        mobileToggle.style.display = hasBoth ? '' : 'none';
        mobileRegBtn.classList.toggle('active', !mobileIsPlayoffs);
        mobilePoBtn.classList.toggle('active', mobileIsPlayoffs);
        activate(mobileIsPlayoffs && hasBoth ? grp.poIdx : grp.regIdx);
        setStickyColumnOffsets();
    };

    mobileSelect.addEventListener('change', () => {
        mobileIsPlayoffs = false;
        updateMobileState(parseInt(mobileSelect.value));
    });
    mobileRegBtn.addEventListener('click', () => {
        mobileIsPlayoffs = false;
        updateMobileState(parseInt(mobileSelect.value));
    });
    mobilePoBtn.addEventListener('click', () => {
        mobileIsPlayoffs = true;
        updateMobileState(parseInt(mobileSelect.value));
    });

    if (leagueGroups.length > 0) mobileToggle.style.display = leagueGroups[0].poIdx !== null ? '' : 'none';

    if (allCells.length > 0) activate(0);

    container.appendChild(mobileWrap);
    container.appendChild(grid);
    container.appendChild(contentWrap);
}

// ── Toggle sections (MiLR, FCB, GIB, ECO, NPR, WBC) ─────────────────────────

function addToggle(btnWrap, contentWrap, label, storageKey, league, lgH, lgP, primaryRole, poH = [], poP = [], playoffKey = null) {
    const isVisible = localStorage.getItem(storageKey) === 'true';

    const btn = document.createElement('button');
    btn.textContent = isVisible ? `[Hide ${label}]` : `[Show ${label}]`;
    btn.style.cssText = 'background:none;border:none;color:var(--text-color);text-decoration:underline;font-weight:normal;padding:0;cursor:pointer;margin-right:10px';
    btnWrap.appendChild(btn);

    const inner = document.createElement('div');
    inner.className = 'toggle-league-section';
    inner.style.display = isVisible ? 'block' : 'none';

    const buildContent = () => {
        const d = document.createElement('div');
        renderLeagueWithPlayoffToggle(d, label, lgH, lgP, poH, poP, primaryRole, league, playoffKey);
        return d;
    };

    if (isVisible) {
        const built = buildContent();
        inner.appendChild(built);
        built.querySelectorAll('.stats-table').forEach(makeTableSortable);
    }
    contentWrap.appendChild(inner);

    btn.addEventListener('click', () => {
        const hidden = inner.style.display === 'none';
        if (hidden && !inner.children.length) {
            const built = buildContent();
            inner.appendChild(built);
            wireTeamLinks(inner);
            built.querySelectorAll('.stats-table').forEach(makeTableSortable);
            setStickyColumnOffsets();
        }
        inner.style.display = hidden ? 'block' : 'none';
        btn.textContent = hidden ? `[Hide ${label}]` : `[Show ${label}]`;
        localStorage.setItem(storageKey, hidden);
        if (hidden) setStickyColumnOffsets();
    });
}

// ── Team link wiring ──────────────────────────────────────────────────────────

export function wireTeamLinks(container) {
    container.querySelectorAll('.team-link[data-team]').forEach(el => {
        el.addEventListener('click', () => {
            const team   = decodeURIComponent(el.dataset.team);
            const season = el.dataset.season;
            const league = el.dataset.league || 'mlr';
            const lgParam = league !== 'mlr' ? `&league=${league}` : '';
            window.location.hash = `#/team-stats?season=${season}&team=${encodeURIComponent(team)}${lgParam}`;
        });
    });
}

// ── Table sorting ─────────────────────────────────────────────────────────────

function makeTableSortable(table) {
    const headers = table.querySelectorAll('thead th');
    const container  = table.closest('.stats-table-container');
    const groupNameEl = container?.previousElementSibling;
    const groupName  = groupNameEl?.textContent || '';
    const isPitching = groupName.includes('Pitching') && !groupName.includes('Batting');
    const isOpponent = groupName === 'Opponent Stats';

    headers.forEach((th, colIdx) => {
        const stat = th.textContent.replace(/[↑↓]/, '').trim();
        if (stat === 'Season' || stat === 'Team') return;
        th.style.cursor = 'pointer';

        th.addEventListener('click', () => {
            const tbody = table.querySelector('tbody');
            if (!tbody) return;
            const allRows      = [...tbody.querySelectorAll('tr')];
            const pinnedRows   = allRows.filter(r => r.classList.contains('career-row') || r.classList.contains('franchise-row'));
            const dataRows     = allRows.filter(r => !r.classList.contains('career-row') && !r.classList.contains('franchise-row'));

            const cur         = th.dataset.sortDir;
            const lowerBetter = isOpponent
                ? !['SB','CS','DP'].includes(stat)
                : (isPitching ? LOWER_BETTER_PITCH.has(stat) : LOWER_BETTER_BAT.has(stat));
            const primary = lowerBetter ? 'asc' : 'desc';
            const next    = !cur ? primary : cur === primary ? (lowerBetter ? 'desc' : 'asc') : 'default';

            headers.forEach(h => { delete h.dataset.sortDir; h.querySelector('.sort-arrow')?.remove(); });

            if (next === 'default') {
                dataRows.sort((a, b) => parseInt(a.dataset.originalIndex || 0) - parseInt(b.dataset.originalIndex || 0));
            } else {
                th.dataset.sortDir = next;
                const arrow = document.createElement('span');
                arrow.className = 'sort-arrow';
                arrow.innerHTML = next === 'asc' ? ' &uarr;' : ' &darr;';
                th.appendChild(arrow);

                const isIP = stat === 'IP';
                dataRows.sort((a, b) => {
                    const at = a.cells[colIdx]?.textContent.replace(/[↑↓]/,'').trim() || '-';
                    const bt = b.cells[colIdx]?.textContent.replace(/[↑↓]/,'').trim() || '-';
                    const av = isIP ? parseIPStr(at) : (at === '-' ? (next === 'asc' ? Infinity : -Infinity) : parseFloat(at));
                    const bv = isIP ? parseIPStr(bt) : (bt === '-' ? (next === 'asc' ? Infinity : -Infinity) : parseFloat(bt));
                    return next === 'asc' ? av - bv : bv - av;
                });
            }

            tbody.innerHTML = '';
            dataRows.forEach(r => tbody.appendChild(r));
            // Career row stays before Franchise rows, both pinned at bottom
            pinnedRows
                .sort((a, b) => (a.classList.contains('franchise-row') ? 1 : 0) - (b.classList.contains('franchise-row') ? 1 : 0))
                .forEach(r => tbody.appendChild(r));
        });
    });
}

function parseIPStr(s) {
    if (!s || s === '-') return -Infinity;
    const [inn, outs] = s.split('.').map(Number);
    return (inn || 0) + (outs || 0) / 3;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function filterPlayer(data, id) {
    return data.filter(r => r.ID === id &&
        r['Display Season'] !== 'Type' &&
        r['Display Season'] !== 'Franchise-Type');
}
