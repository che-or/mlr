import { loadSingleGameRecords, loadAchievements } from '../data.js';
import { formatStat, getMlrTeamName, getMlrTeamAbbr, getTeamName, getLogoPair } from '../utils.js';
import { state } from '../state.js';
import { LEAGUES_WITH_PLAYOFFS, LEAGUE_LABELS } from '../constants.js';

// Set at the top of renderSingleGameRecords() to the league currently being
// viewed, so the module-level formatting helpers below can stay league-aware
// without threading a parameter through every call.
let currentLeague = 'mlr';

const OPTIONS = [
    { value: 'player_batter',    label: 'Player Batting',              type: 'player',      side: 'batter'     },
    { value: 'player_pitcher',   label: 'Player Pitching',             type: 'player',      side: 'pitcher'    },
    { value: 'team_batter',      label: 'Team Batting',                type: 'team',        side: 'batter'     },
    { value: 'team_pitcher',     label: 'Team Pitching',               type: 'team',        side: 'pitcher'    },
    { value: 'combined_batter',  label: 'Combined Batting',            type: 'combined',    side: 'batter'     },
    { value: 'combined_pitcher', label: 'Combined Pitching',           type: 'combined',    side: 'pitcher'    },
    { value: 'no_hitters',    label: 'No-Hitters',   type: 'achievement', key: 'no_hitters'                         },
    { value: 'perfect_games', label: 'Perfect Games', type: 'achievement', key: 'no_hitters', filter: h => h.perfect },
    { value: 'cycles',     label: 'Cycles',      type: 'achievement', key: 'cycles'    },
    { value: 'triangles',  label: 'Triangles',   type: 'achievement', key: 'triangles' },
    { value: 'multi_hr',   label: '3+ HR Games', type: 'achievement', key: 'multi_hr'  },
];

// Leagues available in the single-game-records league selector, in display order
const SGR_LEAGUES = [
    { key: 'mlr',  label: 'MLR'  },
    { key: 'milr', label: 'MiLR' },
    { key: 'fcb',  label: 'FCB'  },
    { key: 'gib',  label: 'GIB'  },
    { key: 'eco',  label: 'ECO'  },
    { key: 'npr',  label: 'NPR'  },
    { key: 'wbc',  label: 'WBC'  },
];

function logoHtml(franchise, season) {
    const pair = getLogoPair(currentLeague, franchise, season);
    if (!pair) return '';
    const isLight = document.documentElement.classList.contains('light-mode');
    const src = (isLight && pair.light) ? pair.light : pair.dark;
    const lightAttr = pair.light ? ` data-logo-light="${pair.light}"` : '';
    return `<img src="${src}" data-logo-dark="${pair.dark}"${lightAttr} class="draft-pick-logo" alt="${franchise}" style="vertical-align:middle;margin-right:3px"> `;
}

function playerLink(id) {
    const player = state.allPlayers.find(p => p.ID === id);
    const name = player ? player.Name : `#${id}`;
    return `<a href="#/stats" class="player-link" data-player-id="${id}">${name}</a>`;
}

function teamLink(franchise, season) {
    const name = (currentLeague === 'mlr' || currentLeague === 'mlr_playoff')
        ? getMlrTeamName(franchise, season)
        : getTeamName(currentLeague, franchise, season);
    const baseLeague = currentLeague.replace(/_playoff$/, '');
    const lgParam = baseLeague !== 'mlr' ? `&league=${baseLeague}` : '';
    return `<a href="#/team-stats?season=${season}&team=${encodeURIComponent(franchise)}${lgParam}">${name}</a>`;
}

function gameStr(h) {
    const prefix = h.location === 'Home' ? 'vs' : '@';
    return `${h.season}.${h.session} ${prefix} ${getMlrTeamAbbr(h.opponent, h.season)}`;
}

function line(content) {
    return `<span style="display:block;margin-bottom:5px">${content}</span>`;
}

function holderLines(rec, nameFn) {
    function fmt(h) {
        return `${logoHtml(h.team, h.season)}${nameFn(h)} (${gameStr(h)})`;
    }
    if ('holders' in rec) {
        return rec.holders.map(h => line(fmt(h))).join('');
    }
    const h = rec.most_recent;
    return `${rec.tie_count} tied, most recent: ${fmt(h)}`;
}

function combinedHolderLines(rec) {
    function fmt(h) {
        return `${logoHtml(h.away, h.season)}${teamLink(h.away, h.season)} @ ${logoHtml(h.home, h.season)}${teamLink(h.home, h.season)} (${h.season}.${h.session})`;
    }
    if ('holders' in rec) {
        return rec.holders.map(h => line(fmt(h))).join('');
    }
    const h = rec.most_recent;
    return `${rec.tie_count}-way tie, most recent: ${fmt(h)}`;
}

function achGameStr(h) {
    const prefix = h.location === 'Home' ? 'vs' : '@';
    return `${h.season}.${h.session} ${prefix} ${getMlrTeamAbbr(h.opponent, h.season)}`;
}

function achDetail(h, key) {
    if (key === 'no_hitters') {
        return h.combined
            ? h.pitchers.map(p => `${p.ip} IP, ${p.so} SO, ${p.bb} BB`).join('<br>')
            : `${h.ip} IP, ${h.so} SO, ${h.bb} BB`;
    }
    if (key === 'cycles' || key === 'triangles') return `${h.h} H (${h.hr} HR, ${h['3b']} 3B, ${h['2b']} 2B)`;
    return `${h.hr} HR`;
}

function achCells(h, key) {
    if (!h) return '<td></td><td></td><td></td>';
    let who;
    if (key === 'no_hitters' && h.combined) {
        const names = h.pitchers.map(p => playerLink(p.id)).join('<br>');
        who = `<span style="display:inline-flex;align-items:flex-start;gap:4px">${logoHtml(h.team, h.season)}<span>${names}</span></span>`;
    } else {
        who = `${logoHtml(h.team, h.season)}${playerLink(h.id)}`;
    }
    return `<td style="font-weight:normal">${who}</td><td style="text-align:left">${achGameStr(h)}</td><td>${achDetail(h, key)}</td>`;
}

function buildAchievementsTable(columns, key) {
    const nameHeader = key === 'no_hitters' ? 'Pitcher' : 'Player';
    const detailHeader = key === 'no_hitters' ? 'Stats'
        : (key === 'cycles' || key === 'triangles') ? 'Hit line'
        : 'HR';
    const sep  = `<td style="border-left:2px solid var(--border-color);padding:0;width:8px"></td>`;
    const none = `<td colspan="3" style="color:var(--subtle-text-color);font-weight:normal;font-style:italic;text-align:center">None</td>`;

    const len = Math.max(...columns.map(c => c.list.length));
    let desktopBody = '';
    if (len === 0) {
        const totalCols = columns.length * 3 + (columns.length - 1);
        desktopBody = `<tr><td colspan="${totalCols}" style="color:var(--subtle-text-color);font-weight:normal;font-style:italic;text-align:center">None</td></tr>`;
    } else {
        for (let i = 0; i < len; i++) {
            const rowCells = columns.map(c => (i === 0 && c.list.length === 0) ? none : achCells(c.list[i], key));
            desktopBody += `<tr>${rowCells.join(sep)}</tr>`;
        }
    }

    const colWidth = columns.length === 2 ? 'calc(50% - 4px)' : '100%';
    const headSep = `<th style="padding:0;width:8px"></th>`;
    const headRow1 = columns.map(c => `<th colspan="3" style="text-align:center;width:${colWidth}">${c.label}</th>`).join(headSep);
    const subHeadCell = `<th>${nameHeader}</th><th style="text-align:left">Game</th><th>${detailHeader}</th>`;
    const headRow2 = columns.map(() => subHeadCell).join(`<th style="padding:0"></th>`);

    const desktopTable = `<table class="stats-table" style="font-size:0.9em;width:100%;table-layout:fixed"><thead>
        <tr>${headRow1}</tr><tr>${headRow2}</tr>
    </thead><tbody>${desktopBody}</tbody></table>`;

    function mobileAchBody(list) {
        if (list.length === 0) return `<tr><td colspan="3" style="color:var(--subtle-text-color);font-weight:normal;font-style:italic;text-align:center">None</td></tr>`;
        return list.map(h => `<tr>${achCells(h, key)}</tr>`).join('');
    }

    const mobileTable = columns.map((c, i) => `
        <p class="sgr-section-label"${i > 0 ? ' style="margin-top:1em"' : ''}>${c.label}</p>
        <table class="stats-table" style="font-size:0.9em;width:100%"><thead>
            <tr><th>${nameHeader}</th><th style="text-align:left">Game</th><th>${detailHeader}</th></tr>
        </thead><tbody>${mobileAchBody(c.list)}</tbody></table>`).join('');

    return `<div class="sgr-desktop">${desktopTable}</div><div class="sgr-mobile">${mobileTable}</div>`;
}

function buildTable(columns, opt) {
    const isPlayer   = opt.type === 'player';
    const isCombined = opt.type === 'combined';

    const holderHeader = isCombined ? 'Game' : (isPlayer ? 'Player (game)' : 'Team (game)');

    const stats = Object.keys(columns[0].records).sort();

    const nameFn = isPlayer
        ? (h => playerLink(h.id))
        : (h => teamLink(h.team, h.season));

    const holdersFor = rec => isCombined ? combinedHolderLines(rec) : holderLines(rec, nameFn);

    let desktopBody = '';
    const mobileBodies = columns.map(() => '');

    for (const stat of stats) {
        let rowCells = '';
        columns.forEach((c, i) => {
            const rec = c.records[stat];
            const val = formatStat(stat, rec.record);
            const holders = holdersFor(rec);
            rowCells += `<td><strong>${val}</strong></td><td style="text-align:left">${holders}</td>`;
            mobileBodies[i] += `<tr><td>${stat}</td><td><strong>${val}</strong></td><td style="text-align:left">${holders}</td></tr>`;
        });
        desktopBody += `<tr><td>${stat}</td>${rowCells}</tr>`;
    }

    const headCells = columns.map(c => `<th>${c.label}</th><th style="text-align:left">${holderHeader}</th>`).join('');
    const desktopTable = `<table class="stats-table" style="font-size:0.9em"><thead><tr>
        <th>Stat</th>${headCells}
    </tr></thead><tbody>${desktopBody}</tbody></table>`;

    const mobileTable = columns.map((c, i) => `
        <p class="sgr-section-label"${i > 0 ? ' style="margin-top:1em"' : ''}>${c.label}</p>
        <table class="stats-table" style="font-size:0.9em;width:100%"><thead>
            <tr><th>Stat</th><th>Record</th><th style="text-align:left">${holderHeader}</th></tr>
        </thead><tbody>${mobileBodies[i]}</tbody></table>`).join('');

    return `<div class="sgr-desktop">${desktopTable}</div><div class="sgr-mobile">${mobileTable}</div>`;
}

export async function renderSingleGameRecords() {
    const container = document.getElementById('single-game-records-view');
    container.innerHTML = '<p>Loading...</p>';

    const urlParams = new URL('http://x/' + window.location.hash.slice(1));
    const league = urlParams.searchParams.get('league') || 'mlr';
    currentLeague = league;
    const hasPlayoffs = LEAGUES_WITH_PLAYOFFS.includes(league);

    let data;
    try {
        if (hasPlayoffs) {
            const [main, po, mainAch, poAch] = await Promise.all([
                loadSingleGameRecords(league),
                loadSingleGameRecords(`${league}_playoff`),
                loadAchievements(league),
                loadAchievements(`${league}_playoff`),
            ]);
            data = {
                columns: [
                    { label: LEAGUE_LABELS[league] || league.toUpperCase(), records: main, ach: mainAch },
                    { label: 'Playoffs', records: po, ach: poAch },
                ],
            };
        } else {
            const [main, mainAch] = await Promise.all([
                loadSingleGameRecords(league),
                loadAchievements(league),
            ]);
            data = {
                columns: [
                    { label: LEAGUE_LABELS[league] || league.toUpperCase(), records: main, ach: mainAch },
                ],
            };
        }
    } catch (err) {
        container.innerHTML = '<p>Failed to load single-game records.</p>';
        return;
    }

    const initialRecord = urlParams.searchParams.get('record') || OPTIONS[0].value;

    const selectHtml = `<select id="sgr-select">
        ${OPTIONS.map(o => `<option value="${o.value}"${o.value === initialRecord ? ' selected' : ''}>${o.label}</option>`).join('')}
    </select>`;
    const leagueOptions = SGR_LEAGUES.map(l =>
        `<option value="${l.key}"${l.key === league ? ' selected' : ''}>${l.label}</option>`
    ).join('');

    container.innerHTML = `
        <style>
            #sgr-table-container .stats-table td { vertical-align:top }
            .sgr-mobile { display:none }
            .sgr-section-label { margin:0 0 4px; font-weight:bold; font-size:0.95em }
            @media (max-width: 700px) {
                .sgr-desktop { display:none }
                .sgr-mobile { display:block }
                .sgr-mobile .stats-table { white-space:normal }
            }
        </style>
        <h2 class="section-title">Single-Game Records</h2>
        <div style="margin:10px 0 16px">
            <label for="sgr-league-select" style="margin-right:6px">League:</label>
            <select id="sgr-league-select">${leagueOptions}</select>
            <label for="sgr-select" style="margin:0 6px 0 16px">Record Board:</label>
            ${selectHtml}
        </div>
        <div id="sgr-table-container"></div>`;

    const sel       = document.getElementById('sgr-select');
    const leagueSel = document.getElementById('sgr-league-select');
    const tableContainer = document.getElementById('sgr-table-container');

    function wirePlayerLinks() {
        tableContainer.querySelectorAll('.player-link[data-player-id]').forEach(el => {
            el.addEventListener('click', e => {
                e.preventDefault();
                const id = parseInt(el.dataset.playerId);
                import('./player.js').then(m => {
                    m.displayPlayerPage(id);
                    window.location.hash = '#/stats';
                });
            });
        });
    }

    function hashFor(recordValue) {
        const lgParam = league !== 'mlr' ? `&league=${league}` : '';
        return `#/single-game-records?record=${encodeURIComponent(recordValue)}${lgParam}`;
    }

    function updateTable() {
        const opt = OPTIONS.find(o => o.value === sel.value);
        if (!opt) return;
        if (opt.type === 'achievement') {
            const applyFilter = list => opt.filter ? list.filter(opt.filter) : list;
            const columns = data.columns.map(c => ({ label: c.label, list: applyFilter(c.ach[opt.key] || []) }));
            tableContainer.innerHTML = buildAchievementsTable(columns, opt.key);
            wirePlayerLinks();
        } else {
            const columns = data.columns.map(c => ({ label: c.label, records: c.records[opt.type][opt.side] }));
            tableContainer.innerHTML = buildTable(columns, opt);
            if (opt.type === 'player') wirePlayerLinks();
        }
    }

    sel.addEventListener('change', () => {
        history.replaceState(null, '', hashFor(sel.value));
        updateTable();
    });
    leagueSel.addEventListener('change', e => {
        window.location.hash = `#/single-game-records?record=${encodeURIComponent(sel.value)}&league=${e.target.value}`;
    });
    updateTable();
}
