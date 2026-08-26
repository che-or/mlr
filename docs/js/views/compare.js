import { state } from '../state.js';
import { loadStats, getPlayerById, searchPlayers } from '../data.js';
import { formatStat } from '../utils.js';
import { STAT_DESCRIPTIONS, STAT_DEFINITIONS, LEAGUES_WITH_CAREER } from '../constants.js';

const LEAGUES_WITH_CAREER_SET = new Set(LEAGUES_WITH_CAREER);

// Mirror the exact columns shown on player pages, stripping metadata-only columns
const META_COLS = new Set(['Display Season', 'Team', 'Batting Type', 'Pitching Type']);
const COMPARE_STATS = {
    hitting: Object.fromEntries(
        Object.entries(STAT_DEFINITIONS.batting).map(([k, v]) => [k, v.filter(c => !META_COLS.has(c))])
    ),
    pitching: Object.fromEntries(
        Object.entries(STAT_DEFINITIONS.pitching).map(([k, v]) => [k, v.filter(c => !META_COLS.has(c))])
    ),
};

function statDirection(stat, type) {
    if (type === 'pitching') {
        const d = {
            // Volume / durability
            G: 1, GS: 1, GF: 1, CG: 1, SHO: 1, IP: 1, BF: 1, OPP: 1,
            // Win/loss
            W: 1, L: -1, 'W-L%': 1, SV: 1, HLD: 1, BS: -1,
            // Rate — ERA family
            ERA: -1, 'ERA-': -1, FIP: -1, WHIP: -1,
            H6: -1, HR6: -1, BB6: -1, SO6: 1, 'SO/BB': 1,
            // Batted ball — for pitchers GB is better, FB is worse
            'GB%': 1, 'FB%': -1, 'GB/FB': 1,
            // Per-event outcomes
            'K%': 1, 'BB%': -1, 'HR%': -1,
            SO: 1, H: -1, HR: -1, BB: -1, IBB: -1, 'Auto BB': -1, ER: -1, DP: 1,
            // Advanced
            WAR: 1, RE24: -1, WPA: 1, 'Avg Diff': 1,
            // Opponent batting (lower is better for the pitcher)
            BA: -1, OBP: -1, SLG: -1, OPS: -1, BABIP: -1, SB: -1, CS: 1, 'SB%': -1,
        };
        return d[stat] ?? 0;
    }
    // Hitting
    const d = {
        // Volume
        G: 1, PA: 1, AB: 1,
        // Counting
        R: 1, H: 1, '2B': 1, '3B': 1, HR: 1, RBI: 1, TB: 1, BB: 1, IBB: 1, SF: 1, SH: 1,
        SB: 1, CS: -1, SO: -1, 'Auto K': -1, GIDP: -1,
        // Rate
        BA: 1, OBP: 1, SLG: 1, OPS: 1, 'OPS+': 1, ISO: 1, BABIP: 1,
        'HR%': 1, 'K%': -1, 'BB%': 1, 'SB%': 1,
        // Batted ball — for hitters fewer GB / more FB = more power potential
        'GB%': -1, 'FB%': 1, 'GB/FB': -1,
        // Advanced
        WAR: 1, RE24: 1, WPA: 1, 'Avg Diff': -1,
    };
    return d[stat] ?? 0;
}

// Module-level state
let slotIds   = [null, null, null, null];
let slotCount = 2;
let lastCompareHash = '';

export function renderCompare() {
    const container = document.getElementById('compare-view');
    if (container.dataset.rendered) {
        syncFromUrl();
        return;
    }
    container.dataset.rendered = '1';

    const seasons    = ['Career', ...[...state.seasonsWithStats].slice().reverse()];
    const seasonOpts = seasons.map(s => `<option value="${s}">${s}</option>`).join('');

    container.innerHTML = `
        <div class="compare-controls">
            <div class="compare-slots-area">
                <div id="compare-slots"></div>
                <button id="compare-add-slot" class="compare-add-btn">+ Add Player</button>
            </div>
            <div class="compare-control-row">
                <span class="control-item">
                    <label for="compare-season">Season:</label>
                    <select id="compare-season">${seasonOpts}</select>
                </span>
                <span class="control-item">
                    <label for="compare-league">League:</label>
                    <select id="compare-league">
                        <option value="mlr">MLR</option>
                        <option value="mlr_playoff">MLR Playoffs</option>
                        <option value="milr">MiLR</option>
                        <option value="milr_playoff">MiLR Playoffs</option>
                        <option value="fcb">FCB</option>
                        <option value="gib">GIB</option>
                        <option value="eco">ECO</option>
                        <option value="npr">NPR</option>
                        <option value="wbc">WBC</option>
                    </select>
                </span>
                <span class="control-item">
                    <label for="compare-type">Type:</label>
                    <select id="compare-type">
                        <option value="hitting">Hitting</option>
                        <option value="pitching">Pitching</option>
                    </select>
                </span>
                <span class="control-item">
                    <button id="compare-btn">Compare</button>
                </span>
            </div>
        </div>
        <div id="compare-result"></div>`;

    renderSlots(container);

    container.querySelector('#compare-add-slot').addEventListener('click', () => {
        if (slotCount < 4) {
            slotCount++;
            renderSlots(container);
        }
    });

    container.querySelector('#compare-btn').addEventListener('click', () => {
        runCompare(container);
    });

    document.addEventListener('click', e => {
        if (!e.target.closest('.compare-slot')) {
            document.querySelectorAll('.compare-suggestions').forEach(d => { d.style.display = 'none'; });
        }
    });

    syncFromUrl();
}

function renderSlots(container) {
    const slotsDiv = container.querySelector('#compare-slots');
    slotsDiv.innerHTML = '';

    for (let i = 0; i < slotCount; i++) {
        const player   = slotIds[i] ? getPlayerById(slotIds[i]) : null;
        const inputVal = player ? player.Name : '';

        const slot = document.createElement('div');
        slot.className = 'compare-slot';
        slot.dataset.idx = i;
        slot.innerHTML = `
            <div class="compare-slot-inner">
                <input type="text" class="compare-player-input" placeholder="Player ${i + 1}" value="${inputVal}" autocomplete="off">
                <button class="compare-remove-slot" title="Remove">×</button>
            </div>
            <div class="compare-suggestions" style="display:none;"></div>`;

        wireSlot(slot, i, container);
        slotsDiv.appendChild(slot);
    }

    const addBtn = container.querySelector('#compare-add-slot');
    if (addBtn) addBtn.style.display = slotCount >= 4 ? 'none' : '';
}

function wireSlot(slotEl, idx, container) {
    const input  = slotEl.querySelector('.compare-player-input');
    const suggs  = slotEl.querySelector('.compare-suggestions');
    const remove = slotEl.querySelector('.compare-remove-slot');

    input.addEventListener('input', () => {
        const q = input.value.trim();
        if (/^\d+$/.test(q)) {
            const p = getPlayerById(parseInt(q));
            if (p) { showSlotSuggestions([p], suggs, idx); return; }
        }
        slotIds[idx] = null;
        if (q.length < 2) { suggs.style.display = 'none'; return; }
        showSlotSuggestions(searchPlayers(q).slice(0, 8), suggs, idx);
    });

    input.addEventListener('focus', () => {
        const q = input.value.trim();
        if (q.length >= 2 && !slotIds[idx]) {
            showSlotSuggestions(searchPlayers(q).slice(0, 8), suggs, idx);
        }
    });

    remove.addEventListener('click', () => {
        if (slotCount > 2) {
            slotIds.splice(idx, 1);
            slotIds.push(null);
            slotCount--;
        } else {
            slotIds[idx] = null;
        }
        renderSlots(container);
    });
}

function showSlotSuggestions(players, suggs, idx) {
    if (!players.length) { suggs.style.display = 'none'; return; }
    const counts = {};
    players.forEach(p => { counts[p.Name] = (counts[p.Name] || 0) + 1; });
    suggs.innerHTML = players.map(p => {
        const label = counts[p.Name] > 1 ? `${p.Name} (#${p.ID})` : p.Name;
        return `<div class="suggestion-item" data-id="${p.ID}" data-name="${p.Name}">${label}</div>`;
    }).join('');
    suggs.style.display = 'block';

    suggs.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            slotIds[idx] = parseInt(item.dataset.id);
            suggs.closest('.compare-slot').querySelector('.compare-player-input').value = item.dataset.name;
            suggs.style.display = 'none';
        });
    });
}

function syncFromUrl() {
    const hash = window.location.hash;
    if (!hash.startsWith('#/compare?') || hash === lastCompareHash) return;

    try {
        const url    = new URL('http://x/' + hash.slice(1));
        const ids    = (url.searchParams.get('players') || '').split(',').map(Number).filter(Boolean).slice(0, 4);
        const season = url.searchParams.get('season');
        const league = url.searchParams.get('league');
        const type   = url.searchParams.get('type');

        const container = document.getElementById('compare-view');

        if (season) { const s = container.querySelector('#compare-season'); if (s) s.value = season; }
        if (league) { const s = container.querySelector('#compare-league'); if (s) s.value = league; }
        if (type)   { const s = container.querySelector('#compare-type');   if (s) s.value = type; }

        if (ids.length >= 2) {
            slotIds   = [null, null, null, null];
            ids.forEach((id, i) => { slotIds[i] = id; });
            slotCount = Math.max(2, ids.length);
            renderSlots(container);
            runCompare(container);
        }
    } catch (_) {}
}

async function runCompare(container) {
    const result = container.querySelector('#compare-result');
    result.innerHTML = '<p>Loading…</p>';

    const season = container.querySelector('#compare-season').value;
    const league = container.querySelector('#compare-league').value;
    const type   = container.querySelector('#compare-type').value;

    const activeIds = slotIds.filter(Boolean);
    if (activeIds.length < 2) {
        result.innerHTML = '<p>Please select at least two players to compare.</p>';
        return;
    }

    const params = new URLSearchParams({ players: activeIds.join(','), season, league, type });
    lastCompareHash = `#/compare?${params}`;
    window.location.hash = lastCompareHash;

    try {
        const fetches = [loadStats(league, type)];
        if (season === 'Career' && LEAGUES_WITH_CAREER_SET.has(league)) {
            fetches.push(loadStats(league, `career_${type}`));
        }
        await Promise.all(fetches);

        const rows = activeIds.map(id => getStatRow(id, season, league, type));
        result.innerHTML = buildCompareTable(activeIds, rows, season, league, type);

        result.querySelectorAll('.compare-player-link').forEach(el => {
            el.addEventListener('click', e => {
                e.preventDefault();
                const id = parseInt(el.dataset.id);
                state.currentPlayerId = id;
                import('./player.js').then(m => {
                    m.displayPlayerPage(id);
                    window.location.hash = '#/stats';
                });
            });
        });
    } catch (err) {
        console.error(err);
        result.innerHTML = '<p>Failed to load comparison data.</p>';
    }
}

function getStatRow(playerId, season, league, type) {
    if (season === 'Career') {
        if (!LEAGUES_WITH_CAREER_SET.has(league)) return null;
        const rows = state.stats[`${league}_career_${type}`] || [];
        return rows.find(r => r.ID === playerId) || null;
    }
    const rows = state.stats[`${league}_${type}`] || [];
    return rows.find(r => r.ID === playerId && r['Display Season'] === season && !r.is_sub_row) || null;
}

function buildCompareTable(ids, rows, season, league, type) {
    const players    = ids.map(id => getPlayerById(id));
    const n          = ids.length;
    const statGroups = COMPARE_STATS[type] || COMPARE_STATS.hitting;

    const headerCells = players.map((p, i) => {
        if (!p) return `<th>Player ${i + 1}</th>`;
        return `<th><a href="#/stats" class="compare-player-link" data-id="${ids[i]}">${p.Name}</a></th>`;
    }).join('');

    const leagueLabel  = league.replace(/_/g, ' ').toUpperCase();
    const seasonLabel  = season;
    const typeLabel    = type.charAt(0).toUpperCase() + type.slice(1);

    let html = `<div class="compare-context-label">${leagueLabel} · ${seasonLabel} · ${typeLabel}</div>
        <table class="stats-table compare-table">
        <thead><tr><th class="compare-stat-name"></th>${headerCells}</tr></thead>
        <tbody>`;

    const noData = rows.every(r => r == null);
    if (noData && season === 'Career' && !LEAGUES_WITH_CAREER_SET.has(league)) {
        html += `<tr><td colspan="${n + 1}" class="compare-no-data">Career stats are not available for this league. Select a specific season.</td></tr>`;
        html += '</tbody></table>';
        return html;
    }

    for (const [section, stats] of Object.entries(statGroups)) {
        html += `<tr class="compare-section-header"><td colspan="${n + 1}">${section}</td></tr>`;

        for (const stat of stats) {
            const raw  = rows.map(r => (r != null && r[stat] != null) ? r[stat] : null);
            const fmtd = raw.map(v => v == null ? '—' : formatStat(stat, v));

            const dir = statDirection(stat, type);
            let bestIndices = new Set();
            if (dir !== 0) {
                // "Inf." is a real (extreme) value, not a missing one - e.g. an infinite SO/BB
                // (zero walks) is genuinely the best possible ratio and should be able to win.
                const nums  = raw.map(v => {
                    if (v == null) return null;
                    if (v === 'Inf.') return Infinity;
                    const n = parseFloat(v);
                    return isNaN(n) ? null : n;
                });
                const valid = nums.filter(v => v !== null);
                if (valid.length >= 2) {
                    const best      = dir === 1 ? Math.max(...valid) : Math.min(...valid);
                    const bestCount = valid.filter(v => v === best).length;
                    // Highlight all tied-for-best, but not when everyone shares the same value
                    if (bestCount < valid.length) {
                        nums.forEach((v, i) => { if (v === best) bestIndices.add(i); });
                    }
                }
            }

            const cells   = fmtd.map((f, i) =>
                `<td class="${bestIndices.has(i) ? 'compare-best' : ''}">${f}</td>`
            ).join('');
            const tooltip = STAT_DESCRIPTIONS[stat] ? ` title="${STAT_DESCRIPTIONS[stat]}"` : '';
            html += `<tr><th class="compare-stat-name"${tooltip}>${stat}</th>${cells}</tr>`;
        }
    }

    html += '</tbody></table>';
    return html;
}
