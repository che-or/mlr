import { loadStreakRecords, loadStats } from '../data.js';
import { getMlrLogoPair, recordFranchiseKey } from '../utils.js';
import { state } from '../state.js';

const STREAK_OPTIONS = [
    { value: 'consecutive_games_played', label: 'Consecutive Games Played',             unit: 'G'  },
    { value: 'hitting_streak',           label: 'Hitting Streak',                       unit: 'G'  },
    { value: 'onbase_streak',            label: 'On-Base Streak',                       unit: 'G'  },
    { value: 'scoreless_innings',        label: 'Scoreless Innings Streak',             unit: 'IP' },
    { value: 'pa_hit_streak',            label: 'Consecutive PA with Hit',              unit: 'PA' },
    { value: 'pa_onbase_streak',         label: 'Consecutive PA On Base',               unit: 'PA' },
    { value: 'pa_hitless_streak',        label: 'Consecutive PA without Hit',           unit: 'PA' },
    { value: 'pa_baseless_streak',       label: 'Consecutive PA without Reaching Base', unit: 'PA' },
    { value: 'bf_no_hit_streak',         label: 'Consecutive BF without Hit Allowed',   unit: 'BF' },
    { value: 'bf_no_baserunner_streak',  label: 'Consecutive BF without Baserunner',    unit: 'BF' },
];

function logoHtml(franchise, season) {
    const pair = getMlrLogoPair(franchise, season);
    if (!pair) return '';
    const isLight = document.documentElement.classList.contains('light-mode');
    const src = (isLight && pair.light) ? pair.light : pair.dark;
    const lightAttr = pair.light ? ` data-logo-light="${pair.light}"` : '';
    return `<img src="${src}" data-logo-dark="${pair.dark}"${lightAttr} class="draft-pick-logo" alt="${franchise}" style="vertical-align:middle;margin-right:3px">`;
}

function playerLink(id) {
    const player = state.allPlayers.find(p => p.ID === id);
    const name = player ? player.Name : `#${id}`;
    return `<a href="#/stats" class="player-link" data-player-id="${id}">${name}</a>`;
}

function periodStr(e) {
    const start = `${e.season_start}.${e.session_start}`;
    const end   = `${e.season_end}.${e.session_end}`;
    return start === end ? start : `${start} – ${end}`;
}

function buildFranchiseLookup(hitting, pitching) {
    const map = new Map();
    for (const r of [...hitting, ...pitching]) {
        if (r.is_sub_row) continue;
        const key = `${r.ID}|${r['Display Season']}`;
        if (!map.has(key)) map.set(key, recordFranchiseKey(r));
    }
    return map;
}

function holderLine(e, franchiseLookup) {
    const fk = franchiseLookup.get(`${e.id}|${e.season_end}`);
    const logo = fk ? logoHtml(fk, e.season_end) : '';
    return `<span style="display:block;margin-bottom:3px">${logo}${playerLink(e.id)} (${periodStr(e)})</span>`;
}

function buildTableHtml(list, franchiseLookup, unit) {
    const entries = list.entries || [];

    if (entries.length === 0) {
        return `<table class="stats-table" style="font-size:0.9em;width:100%"><tbody>
            <tr><td colspan="3" style="color:var(--subtle-text-color);font-style:italic;text-align:center">None</td></tr>
        </tbody></table>`;
    }

    // Group consecutive entries by record value so tied players share a row.
    const groups = [];
    for (const e of entries) {
        const last = groups[groups.length - 1];
        if (last && last.record === e.record) {
            last.entries.push(e);
        } else {
            groups.push({ record: e.record, entries: [e] });
        }
    }

    let body = '';
    let rank = 1;
    for (let gi = 0; gi < groups.length; gi++) {
        const g = groups[gi];
        const isLastGroup = gi === groups.length - 1;
        const overflows = isLastGroup && !!list.tie_at_boundary;
        const isTied = g.entries.length > 1 || overflows;
        const rankStr = isTied ? `T${rank}` : `${rank}`;
        const recordStr = unit === 'IP' ? g.record : `${g.record} ${unit}`;

        let playerCell;
        if (overflows) {
            const count = list.tie_at_boundary.count;
            playerCell = `<span style="color:var(--subtle-text-color);font-style:italic">${count} players tied</span>`;
        } else {
            playerCell = g.entries.map(e => holderLine(e, franchiseLookup)).join('');
        }

        body += `<tr>
            <td style="text-align:center;vertical-align:top">${rankStr}</td>
            <td style="vertical-align:top"><strong>${recordStr}</strong></td>
            <td style="text-align:left;vertical-align:top">${playerCell}</td>
        </tr>`;
        rank += g.entries.length;
    }

    return `<table class="stats-table" style="font-size:0.9em;width:100%"><thead>
        <tr><th>Rank</th><th>Streak</th><th style="text-align:left">Player (period)</th></tr>
    </thead><tbody>${body}</tbody></table>`;
}

function buildStreakView(data, opt, franchiseLookup) {
    const streakData = data[opt.value];
    if (!streakData) return '<p>No data for this streak type.</p>';

    const allTimeHtml = buildTableHtml(streakData.all_time, franchiseLookup, opt.unit);
    const activeHtml  = buildTableHtml(streakData.active,   franchiseLookup, opt.unit);

    const sep = `<div style="width:2px;background:var(--border-color);align-self:stretch;flex-shrink:0;margin:0 14px"></div>`;

    const desktop = `<div class="sgr-desktop" style="display:flex;align-items:flex-start">
        <div style="flex:1;min-width:0">
            <p class="sgr-section-label">All-Time</p>
            ${allTimeHtml}
        </div>
        ${sep}
        <div style="flex:1;min-width:0">
            <p class="sgr-section-label">Active</p>
            ${activeHtml}
        </div>
    </div>`;

    const mobile = `<div class="sgr-mobile">
        <p class="sgr-section-label">All-Time</p>
        ${allTimeHtml}
        <p class="sgr-section-label" style="margin-top:1em">Active</p>
        ${activeHtml}
    </div>`;

    return desktop + mobile;
}

function wirePlayerLinks(container) {
    container.querySelectorAll('.player-link[data-player-id]').forEach(el => {
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

export async function renderStreaks() {
    const container = document.getElementById('streaks-view');
    container.innerHTML = '<p>Loading...</p>';

    let data;
    try {
        [data] = await Promise.all([
            loadStreakRecords(),
            loadStats('mlr', 'hitting'),
            loadStats('mlr', 'pitching'),
        ]);
    } catch (_) {
        container.innerHTML = '<p>Failed to load streak records.</p>';
        return;
    }

    const hitting  = state.stats['mlr_hitting']  || [];
    const pitching = state.stats['mlr_pitching'] || [];
    const franchiseLookup = buildFranchiseLookup(hitting, pitching);

    const selectHtml = `<select id="streaks-select">
        ${STREAK_OPTIONS.map(o => `<option value="${o.value}">${o.label}</option>`).join('')}
    </select>`;

    container.innerHTML = `
        <style>
            #streaks-table-container .stats-table td { vertical-align:top }
            .sgr-mobile { display:none }
            .sgr-section-label { margin:0 0 4px; font-weight:bold; font-size:0.95em }
            @media (max-width: 700px) {
                .sgr-desktop { display:none !important }
                .sgr-mobile { display:block }
                .sgr-mobile .stats-table { white-space:normal }
            }
        </style>
        <h2 class="section-title">Streak Records</h2>
        <div style="margin:10px 0 16px">
            <label for="streaks-select" style="margin-right:6px">Streak:</label>
            ${selectHtml}
        </div>
        <div id="streaks-table-container"></div>`;

    const sel = document.getElementById('streaks-select');
    const tableContainer = document.getElementById('streaks-table-container');

    function updateTable() {
        const opt = STREAK_OPTIONS.find(o => o.value === sel.value);
        if (!opt) return;
        tableContainer.innerHTML = buildStreakView(data, opt, franchiseLookup);
        wirePlayerLinks(tableContainer);
    }

    sel.addEventListener('change', updateTable);
    updateTable();
}
