import { loadSingleGameRecords, loadAchievements } from '../data.js';
import { formatStat, getMlrLogoPair, getMlrTeamName, getMlrTeamAbbr } from '../utils.js';
import { state } from '../state.js';

const OPTIONS = [
    { value: 'player_batter',    label: 'Player Batting',              type: 'player',      side: 'batter'     },
    { value: 'player_pitcher',   label: 'Player Pitching',             type: 'player',      side: 'pitcher'    },
    { value: 'team_batter',      label: 'Team Batting',                type: 'team',        side: 'batter'     },
    { value: 'team_pitcher',     label: 'Team Pitching',               type: 'team',        side: 'pitcher'    },
    { value: 'combined_batter',  label: 'Combined Batting',            type: 'combined',    side: 'batter'     },
    { value: 'combined_pitcher', label: 'Combined Pitching',           type: 'combined',    side: 'pitcher'    },
    { value: 'no_hitters',    label: 'No-Hitters',   type: 'achievement', key: 'no_hitters'                         },
    { value: 'perfect_games', label: 'Perfect Games', type: 'achievement', key: 'no_hitters', filter: h => h.perfect },
    { value: 'cycles',              label: 'Cycles',      type: 'achievement', key: 'cycles'               },
    { value: 'multi_hr',            label: '3+ HR Games',                 type: 'achievement', key: 'multi_hr'             },
];

function logoHtml(franchise, season) {
    const pair = getMlrLogoPair(franchise, season);
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
    const name = getMlrTeamName(franchise, season);
    return `<a href="#/team-stats?season=${season}&team=${encodeURIComponent(franchise)}">${name}</a>`;
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
    if (key === 'cycles') return `${h.h} H (${h.hr} HR, ${h['3b']} 3B, ${h['2b']} 2B)`;
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

function buildAchievementsTable(mlrList, poList, key) {
    const nameHeader = key === 'no_hitters' ? 'Pitcher' : 'Player';
    const detailHeader = key === 'no_hitters' ? 'Stats'
        : key === 'cycles' ? 'Hit line'
        : 'HR';
    const sep  = `<td style="border-left:2px solid var(--border-color);padding:0;width:8px"></td>`;
    const none = `<td colspan="3" style="color:var(--subtle-text-color);font-weight:normal;font-style:italic;text-align:center">None</td>`;

    const len = Math.max(mlrList.length, poList.length);
    let body = '';
    if (len === 0) {
        body = `<tr><td colspan="7" style="text-align:left;color:var(--subtle-text-color)">None recorded</td></tr>`;
    } else {
        for (let i = 0; i < len; i++) {
            const mlrCells = (i === 0 && mlrList.length === 0) ? none : achCells(mlrList[i], key);
            const poCells  = (i === 0 && poList.length === 0)  ? none : achCells(poList[i], key);
            body += `<tr>${mlrCells}${sep}${poCells}</tr>`;
        }
    }

    return `<table class="stats-table" style="font-size:0.9em;width:100%;table-layout:fixed"><thead>
        <tr>
            <th colspan="3" style="text-align:center;width:calc(50% - 4px)">MLR</th>
            <th style="padding:0;width:8px"></th>
            <th colspan="3" style="text-align:center;width:calc(50% - 4px)">Playoffs</th>
        </tr><tr>
            <th>${nameHeader}</th><th style="text-align:left">Game</th><th>${detailHeader}</th>
            <th style="padding:0"></th>
            <th>${nameHeader}</th><th style="text-align:left">Game</th><th>${detailHeader}</th>
        </tr></thead><tbody>${body}</tbody></table>`;
}

function buildTable(mlrRecords, poRecords, opt) {
    const isPlayer   = opt.type === 'player';
    const isCombined = opt.type === 'combined';

    const holderHeader = isCombined ? 'Game' : (isPlayer ? 'Player (game)' : 'Team (game)');

    let html = `<table class="stats-table" style="font-size:0.9em"><thead><tr>
        <th>Stat</th>
        <th>MLR</th>
        <th style="text-align:left">${holderHeader}</th>
        <th>Playoffs</th>
        <th style="text-align:left">${holderHeader}</th>
    </tr></thead><tbody>`;

    const stats = Object.keys(mlrRecords).sort();
    for (const stat of stats) {
        const mlr = mlrRecords[stat];
        const po  = poRecords[stat];
        const mlrVal = formatStat(stat, mlr.record);
        const poVal  = formatStat(stat, po.record);

        let mlrHolders, poHolders;
        if (isCombined) {
            mlrHolders = combinedHolderLines(mlr);
            poHolders  = combinedHolderLines(po);
        } else {
            const nameFn = isPlayer
                ? (h => playerLink(h.id))
                : (h => teamLink(h.team, h.season));
            mlrHolders = holderLines(mlr, nameFn);
            poHolders  = holderLines(po, nameFn);
        }

        html += `<tr>
            <td>${stat}</td>
            <td><strong>${mlrVal}</strong></td>
            <td style="text-align:left">${mlrHolders}</td>
            <td><strong>${poVal}</strong></td>
            <td style="text-align:left">${poHolders}</td>
        </tr>`;
    }
    return html + '</tbody></table>';
}

export async function renderSingleGameRecords() {
    const container = document.getElementById('single-game-records-view');
    container.innerHTML = '<p>Loading...</p>';

    let data;
    try {
        const [mlr, po, mlrAch, poAch] = await Promise.all([
            loadSingleGameRecords('mlr'),
            loadSingleGameRecords('mlr_playoff'),
            loadAchievements('mlr'),
            loadAchievements('mlr_playoff'),
        ]);
        data = { mlr, po, mlrAch, poAch };
    } catch (err) {
        container.innerHTML = '<p>Failed to load single-game records.</p>';
        return;
    }

    const selectHtml = `<select id="sgr-select">
        ${OPTIONS.map(o => `<option value="${o.value}">${o.label}</option>`).join('')}
    </select>`;

    container.innerHTML = `
        <style>#sgr-table-container .stats-table td { vertical-align:top }</style>
        <h2 class="section-title">Single-Game Records</h2>
        <div style="margin:10px 0 16px">
            <label for="sgr-select" style="margin-right:6px">Record Board:</label>
            ${selectHtml}
        </div>
        <div id="sgr-table-container"></div>`;

    const sel = document.getElementById('sgr-select');
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

    function updateTable() {
        const opt = OPTIONS.find(o => o.value === sel.value);
        if (!opt) return;
        if (opt.type === 'achievement') {
            const applyFilter = list => opt.filter ? list.filter(opt.filter) : list;
            tableContainer.innerHTML = buildAchievementsTable(
                applyFilter(data.mlrAch[opt.key] || []),
                applyFilter(data.poAch[opt.key]  || []),
                opt.key,
            );
            wirePlayerLinks();
        } else {
            const mlrRecords = data.mlr[opt.type][opt.side];
            const poRecords  = data.po[opt.type][opt.side];
            tableContainer.innerHTML = buildTable(mlrRecords, poRecords, opt);
            if (opt.type === 'player') wirePlayerLinks();
        }
    }

    sel.addEventListener('change', updateTable);
    updateTable();
}
