import { state } from '../state.js';
import { loadStats, loadTeamStats } from '../data.js';
import { formatStat, getSeasonSort, getFranchiseKey, getMlrTeamEntry, getMlrLogo, getMlrTeamName,
         getMilrTeamName, getFcbTeamName, getFcbLogo, getHistoricalTeamName, getHistoricalLogoPair,
         getDivisionsForSeason, getMlrLogoPair, getFcbLogoPair, makeLogoImg } from '../utils.js';
import { STAT_DEFINITIONS, STAT_DESCRIPTIONS } from '../constants.js';

// ── Team list / Standings ─────────────────────────────────────────────────────

// Leagues available in the team stats league selector, in display order
const TEAM_LEAGUES = [
    { key: 'mlr',   label: 'MLR'   },
    { key: 'milr',  label: 'MiLR'  },
    { key: 'fcb',   label: 'FCB'   },
    { key: 'gib',   label: 'GIB'   },
    { key: 'eco',   label: 'ECO'   },
    { key: 'npr',   label: 'NPR'   },
    { key: 'wbc',   label: 'WBC'   },
];

export async function displayTeamList(season, league = 'mlr') {
    const container = document.getElementById('team-stats-view');
    container.innerHTML = '<p>Loading...</p>';

    try {
        await loadTeamStats(league);

        const divs = state.divisions[league] || {};
        const allSeasons = Object.keys(divs).sort((a, b) => getSeasonSort(a) - getSeasonSort(b));

        const currentSeason = (season && allSeasons.includes(season))
            ? season
            : allSeasons[allSeasons.length - 1] || 'S1';
        const idx = allSeasons.indexOf(currentSeason);
        const prevSeason = idx > 0 ? allSeasons[idx - 1] : null;
        const nextSeason = idx < allSeasons.length - 1 ? allSeasons[idx + 1] : null;

        const teamPitching = (state.stats[`${league}_team_pitching`] || [])
            .filter(r => r['Display Season'] === currentSeason);
        const records = buildTeamRecords(teamPitching, league, currentSeason);
        const divisionMap = getDivisionsForSeason(league, currentSeason);

        const lgParam = league !== 'mlr' ? `&league=${league}` : '';

        const leagueOptions = TEAM_LEAGUES.map(l =>
            `<option value="${l.key}" ${l.key === league ? 'selected' : ''}>${l.label}</option>`
        ).join('');
        const seasonOptions = allSeasons.map(s =>
            `<option value="${s}" ${s === currentSeason ? 'selected' : ''}>Season ${s.slice(1)}</option>`
        ).join('');

        let html = `<div class="team-stats-header">
            <h2 class="section-title">
                Standings —
                <select id="team-league-select" class="title-season-select">${leagueOptions}</select>
                <select id="team-season-select" class="title-season-select">${seasonOptions}</select>
            </h2>
            <div class="season-nav-buttons">
                ${prevSeason ? `<a href="#/team-stats?season=${prevSeason}${lgParam}" class="season-nav-button">&lt; Prev Season</a>` : ''}
                ${nextSeason ? `<a href="#/team-stats?season=${nextSeason}${lgParam}" class="season-nav-button">Next Season &gt;</a>` : ''}
            </div>
        </div>`;

        html += '<div class="standings-columns">';
        if (divisionMap) {
            html += renderDivisionMap(divisionMap, records, league, currentSeason, lgParam);
        } else {
            // No division data — show a single league-wide standings table
            const teams = [...new Set(teamPitching.map(r => r.Team).filter(t => t && !/^\d+TM$/.test(t)))];
            html += renderDivisionCard('League Standings', teams, records, league, currentSeason, lgParam);
        }
        html += '</div>';

        container.innerHTML = html;

        container.querySelector('#team-league-select').addEventListener('change', e => {
            const newLeague = e.target.value;
            const newLgParam = newLeague !== 'mlr' ? `&league=${newLeague}` : '';
            // Drop the season when switching leagues — let it default to the latest
            window.location.hash = `#/team-stats${newLgParam ? `?${newLgParam.slice(1)}` : ''}`;
        });
        container.querySelector('#team-season-select').addEventListener('change', e => {
            window.location.hash = `#/team-stats?season=${e.target.value}${lgParam}`;
        });
        container.querySelectorAll('.team-link, .team-list-item').forEach(el => {
            el.addEventListener('click', () => {
                const abbr = el.dataset.team;
                window.location.hash = `#/team-stats?season=${currentSeason}&team=${encodeURIComponent(abbr)}${lgParam}`;
            });
        });
    } catch (err) {
        console.error(err);
        container.innerHTML = '<p>Failed to load standings data.</p>';
    }
}

function renderDivisionMap(divisionMap, records, league, season, lgParam) {
    // Handle nested (AL/NL) or flat division structure
    const isNested = Object.values(divisionMap).every(v => typeof v === 'object' && !Array.isArray(v));
    if (!isNested) {
        return Object.entries(divisionMap).map(([divName, teams]) =>
            renderDivisionCard(divName, teams, records, league, season, lgParam)
        ).join('');
    }
    return Object.entries(divisionMap).map(([lg, divs]) =>
        Object.entries(divs).map(([divName, teams]) =>
            renderDivisionCard(`${lg} ${divName}`, teams, records, league, season, lgParam)
        ).join('')
    ).join('');
}

function renderDivisionCard(divName, teams, records, league, season, lgParam) {
    const standings = teams.map(abbr => ({ abbr, ...(records[abbr] || { W: 0, L: 0, PCT: 0 }) }))
        .sort((a, b) => b.PCT - a.PCT);

    // Games back relative to division leader
    const leader = standings[0];
    standings.forEach(t => {
        const gb = ((leader.W - t.W) + (t.L - leader.L)) / 2;
        if (gb === 0)      t.GB = '-';           // leader and any tied teams
        else if (gb % 1)   t.GB = gb.toFixed(1); // half-game: show one decimal
        else               t.GB = gb.toString();  // whole number: no decimal
    });

    const isMLR = league === 'mlr' || league === 'mlr_playoff';

    let html = `<div class="division-standings-container">
        <h3 class="division-title">${divName}</h3>
        <table class="stats-table standings-table">
            <thead><tr><th>Team</th><th>W</th><th>L</th><th>PCT</th><th>GB</th></tr></thead>
            <tbody>`;
    for (const t of standings) {
        let logo = '';
        let name = t.abbr;
        if (isMLR) {
            const fk = getFranchiseKey(t.abbr, season);
            const pair = getMlrLogoPair(fk, season);
            name = getMlrTeamName(fk, season);
            logo = pair ? makeLogoImg(pair.dark, pair.light, 'standings-logo') : '';
        } else if (league === 'milr' || league === 'milr_playoff') {
            name = getMilrTeamName(t.abbr, season);
        } else if (league === 'fcb') {
            name = getFcbTeamName(t.abbr, season);
            const pair = getFcbLogoPair(t.abbr, season);
            logo = pair ? makeLogoImg(pair.dark, pair.light, 'standings-logo') : '';
        } else {
            name = getHistoricalTeamName(league, t.abbr, season);
            const pair = getHistoricalLogoPair(league, t.abbr, season);
            logo = pair ? makeLogoImg(pair.dark, pair.light, 'standings-logo') : '';
        }
        html += `<tr>
            <td><span class="team-link" data-team="${t.abbr}" style="cursor:pointer">${logo}${name}</span></td>
            <td>${t.W}</td><td>${t.L}</td>
            <td>${formatStat('W-L%', t.PCT)}</td>
            <td>${t.GB}</td>
        </tr>`;
    }
    html += '</tbody></table></div>';
    return html;
}

function teamListCard(abbr, league, season, lgParam) {
    return `<div class="team-list-item" data-team="${abbr}">
        <p class="team-list-name">${abbr}</p>
    </div>`;
}

function buildTeamRecords(teamPitching, league, season) {
    const records = {};
    for (const r of teamPitching) {
        const abbr = r.Team;
        if (!abbr || abbr === '2TM') continue;
        const w = r.W || 0, l = r.L || 0;
        records[abbr] = { W: w, L: l, PCT: r['W-L%'] || 0 };
    }
    return records;
}

// ── Individual team page ──────────────────────────────────────────────────────

export async function displayTeamStatsPage(teamAbbr, season, league = 'mlr') {
    const container = document.getElementById('team-stats-view');
    container.innerHTML = '<p>Loading...</p>';

    try {
        await Promise.all([
            loadStats(league, 'hitting'),
            loadStats(league, 'pitching'),
            loadTeamStats(league),
        ]);

        const isMLR = league === 'mlr' || league === 'mlr_playoff';
        const isMiLR = league === 'milr' || league === 'milr_playoff';

        // Resolve display season — URL may pass e.g. "S12"
        const displaySeason = season || state.seasonsWithStats.slice(-1)[0] || 'S1';
        const seasonNum = parseInt(displaySeason.slice(1));

        // Resolve franchise key and actual abbreviation
        const franchiseKey = isMLR ? getFranchiseKey(teamAbbr, displaySeason) : teamAbbr;
        let actualAbbr = teamAbbr;
        if (isMLR) {
            const mlrHist = state.teamHistory.mlr[franchiseKey];
            const entry = mlrHist?.find(e => seasonNum >= e.start && (e.end === 9999 || seasonNum <= e.end));
            if (entry) actualAbbr = entry.abbr;
        }

        // Filter stats for this team+season
        const hitting  = (state.stats[`${league}_hitting`]  || []).filter(r => r['Display Season'] === displaySeason && r.Team === actualAbbr);
        const pitching = (state.stats[`${league}_pitching`] || []).filter(r => r['Display Season'] === displaySeason && r.Team === actualAbbr);
        const teamHit  = (state.stats[`${league}_team_hitting`]  || []).find(r => r['Display Season'] === displaySeason && r.Team === actualAbbr);
        const teamPit  = (state.stats[`${league}_team_pitching`] || []).find(r => r['Display Season'] === displaySeason && r.Team === actualAbbr);

        // Navigation
        const allSeasons = buildTeamSeasons(franchiseKey, league, isMLR, isMiLR);
        const idx = allSeasons.indexOf(displaySeason);
        const prev = idx > 0 ? allSeasons[idx - 1] : null;
        const next = idx < allSeasons.length - 1 ? allSeasons[idx + 1] : null;

        const prevAbbr = isMLR && prev ? (getMlrTeamEntry(franchiseKey, prev)?.abbr ?? teamAbbr) : teamAbbr;
        const nextAbbr = isMLR && next ? (getMlrTeamEntry(franchiseKey, next)?.abbr ?? teamAbbr) : teamAbbr;

        const lgParam = league !== 'mlr' ? `&league=${league}` : '';
        const teamName = isMLR  ? getMlrTeamName(franchiseKey, displaySeason)
                       : isMiLR ? getMilrTeamName(actualAbbr, displaySeason)
                       : league === 'fcb' ? getFcbTeamName(actualAbbr, displaySeason)
                       : getHistoricalTeamName(league, actualAbbr, displaySeason);
        const logoPair = isMLR ? getMlrLogoPair(franchiseKey, displaySeason)
                       : league === 'fcb' ? getFcbLogoPair(actualAbbr, displaySeason)
                       : getHistoricalLogoPair(league, actualAbbr, displaySeason);

        let html = `<div class="team-stats-header">
            <h2 class="section-title">
                ${logoPair ? makeLogoImg(logoPair.dark, logoPair.light, 'player-team-logo') : ''}
                ${teamName} — Season ${displaySeason.slice(1)}
            </h2>
            <div class="season-nav-buttons">
                ${prev ? `<a href="#/team-stats?season=${prev}&team=${prevAbbr}${lgParam}" class="season-nav-button">&lt; Prev Season</a>` : ''}
                ${next ? `<a href="#/team-stats?season=${next}&team=${nextAbbr}${lgParam}" class="season-nav-button">Next Season &gt;</a>` : ''}
            </div>
        </div>`;

        if (hitting.length)  html += createTeamRosterTable('Batting Stats',  hitting,  false, teamHit);
        if (pitching.length) html += createTeamRosterTable('Pitching Stats', pitching, true,  teamPit);

        container.innerHTML = html;
        makeTablesClickable(container);
        wirePlayerLinks(container, league);

    } catch (err) {
        console.error(err);
        container.innerHTML = '<p>Failed to load team data.</p>';
    }
}

function buildTeamSeasons(franchiseKey, league, isMLR, isMiLR) {
    if (isMLR) {
        const entries = state.teamHistory.mlr[franchiseKey] || [];
        const maxSeason = state.seasonsWithStats.length ? parseInt(state.seasonsWithStats.slice(-1)[0].slice(1)) : 1;
        const seasons = [];
        for (const e of entries) {
            for (let s = e.start; s <= Math.min(e.end === 9999 ? maxSeason : e.end, maxSeason); s++) {
                seasons.push(`S${s}`);
            }
        }
        return seasons;
    }
    // MiLR / FCB: use team history keys
    const hist = isMiLR ? state.teamHistory.milr : state.teamHistory.fcb;
    return Object.keys(hist)
        .filter(s => hist[s][franchiseKey])
        .sort((a, b) => getSeasonSort(a) - getSeasonSort(b));
}

function createTeamRosterTable(title, stats, isPitching, totals) {
    const typeCol = isPitching ? 'Pitching Type' : 'Batting Type';
    const cols = isPitching
        ? STAT_DEFINITIONS.pitching['Standard Pitching'].filter(s => s !== 'Display Season' && s !== 'Team')
        : STAT_DEFINITIONS.batting['Standard Batting'].filter(s => s !== 'Display Season' && s !== 'Team');

    const headers = ['Player', ...cols];
    const typeDefs = isPitching ? state.typeDefinitions.pitching : state.typeDefinitions.batting;

    let html = `<h3>${title}</h3><div class="stats-table-container"><table class="stats-table"><thead><tr>`;
    headers.forEach((stat, i) => {
        const cls   = i < 1 ? ` class="sticky-col col-0"` : '';
        const label = (stat === typeCol) ? 'Type' : stat;
        const desc  = STAT_DESCRIPTIONS[stat] || '';
        html += `<th${cls} title="${desc}">${label}</th>`;
    });
    html += '</tr></thead><tbody>';

    const currentName = id => state.allPlayers.find(p => p.ID === id)?.Name || `#${id}`;
    const sortKey = isPitching ? 'IP' : 'PA';
    stats.slice().sort((a, b) => (b[sortKey] || 0) - (a[sortKey] || 0)).forEach(r => {
        html += `<tr><td class="sticky-col col-0"><span class="player-link" data-player-id="${r.ID}" style="cursor:pointer;text-decoration:underline">${currentName(r.ID)}</span></td>`;
        cols.forEach(stat => {
            if (stat === typeCol) {
                const code     = r[stat] || '';
                const fullName = typeDefs?.[code] || '';
                html += `<td title="${fullName}">${code || '-'}</td>`;
                return;
            }
            let val = r[stat];
            if (!isPitching && stat === 'BA'  && (r.AB || 0) === 0) val = null;
            if (isPitching  && stat === 'ERA' && (r.IP || 0) === 0) val = null;
            if (isPitching  && stat === 'W-L%' && (r.W || 0) + (r.L || 0) === 0) val = null;
            html += `<td>${formatStat(stat, val)}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody>';
    if (totals) {
        html += '<tfoot><tr class="career-row"><td class="sticky-col col-0"><strong>Team Total</strong></td>';
        cols.forEach(stat => {
            if (stat === typeCol) { html += '<td>-</td>'; return; }
            html += `<td><strong>${formatStat(stat, totals[stat])}</strong></td>`;
        });
        html += '</tr></tfoot>';
    }
    html += '</table></div>';
    return html;
}

function makeTablesClickable(container) {
    container.querySelectorAll('.stats-table').forEach(table => {
        const headers = table.querySelectorAll('thead th');
        const titleEl = table.closest('.stats-table-container')?.previousElementSibling;
        const isPitching = titleEl?.textContent?.includes('Pitching');
        const isOpponent = titleEl?.textContent?.includes('Opponent');
        const LOWER_BETTER_PITCH = new Set(['ERA', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'RE24', 'HR%', 'BB%', 'ERA-', 'Avg Diff']);

        headers.forEach((th, colIdx) => {
            const stat = th.textContent.trim();
            if (stat === 'Player' || stat === 'Team') return;
            th.style.cursor = 'pointer';
            th.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                if (!tbody) return;
                const rows = [...tbody.querySelectorAll('tr')];
                const cur = th.dataset.sortDir;
                const lowerBetter = isOpponent ? !['SB','CS'].includes(stat) : (isPitching && LOWER_BETTER_PITCH.has(stat));
                const primary = lowerBetter ? 'asc' : 'desc';
                const next = !cur ? primary : cur === primary ? (lowerBetter ? 'desc' : 'asc') : 'default';

                headers.forEach(h => { delete h.dataset.sortDir; h.querySelector('.sort-arrow')?.remove(); });

                if (next === 'default') {
                    rows.sort((a, b) => (a.dataset.originalIndex || 0) - (b.dataset.originalIndex || 0));
                } else {
                    th.dataset.sortDir = next;
                    const arrow = document.createElement('span');
                    arrow.className = 'sort-arrow';
                    arrow.innerHTML = next === 'asc' ? ' &uarr;' : ' &darr;';
                    th.appendChild(arrow);
                    rows.sort((a, b) => {
                        const av = parseFloat(a.cells[colIdx]?.textContent) || (next === 'asc' ? Infinity : -Infinity);
                        const bv = parseFloat(b.cells[colIdx]?.textContent) || (next === 'asc' ? Infinity : -Infinity);
                        return next === 'asc' ? av - bv : bv - av;
                    });
                }
                rows.forEach((r, i) => { r.dataset.originalIndex = r.dataset.originalIndex || i; tbody.appendChild(r); });
            });
        });
    });
}

function wirePlayerLinks(container, league) {
    container.querySelectorAll('.player-link[data-player-id]').forEach(el => {
        el.addEventListener('click', () => {
            const id = parseInt(el.dataset.playerId);
            import('./player.js').then(m => {
                m.displayPlayerPage(id);
                window.location.hash = '#/stats';
            });
        });
    });
}
