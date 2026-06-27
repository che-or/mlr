import { state } from '../state.js';
import { loadStats } from '../data.js';
import { formatStat, getSeasonSort, getTeamName, getMlrFranchiseLabel } from '../utils.js';
import { wireTeamLinks } from './player.js';
import {
    COUNTING_STATS, STAT_DEFINITIONS, STAT_DESCRIPTIONS,
    LEADERBOARD_ONLY_STATS, LEAGUES_WITH_BREAKDOWNS, LEAGUES_WITH_CAREER, LEAGUES_WITH_FRANCHISE,
} from '../constants.js';

// Lower is better regardless of batting/pitching context
const LOWER_IS_BETTER = new Set([
    'ERA', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'ERA-',
]);
// Lower is better only in batting context (e.g. K% = strikeout rate)
const LOWER_IS_BETTER_BATTING = new Set(['GB%', 'GB/FB', 'K%', 'Avg Diff']);
// Lower is better only in pitching context (opponent stats)
const LOWER_IS_BETTER_PITCHING = new Set([
    'BA', 'BABIP', 'BB%', 'FB%', 'HR%', 'OBP', 'OPS', 'RE24', 'SB%', 'SLG',
]);
const CAN_BE_NEGATIVE = new Set(['WAR', 'WPA', 'RE24']);

// All-time qualifier defaults keyed by league (not adjustable by the user, but shown as editable input)
const ALLTIME_DEFAULTS = {
    pa:  { mlr: 100, milr: 100, fcb: 10, mlr_playoff: 20, milr_playoff: 20, gib: 20 },
    ip:  { mlr: 50,  milr: 50,  fcb: 10, mlr_playoff: 10, milr_playoff: 10, gib: 20 },
    dec: { mlr: 10,  milr: 10,  fcb: 3,  mlr_playoff: 3,  milr_playoff: 3,  gib: 5  },
    sv:  { mlr: 10,  milr: 10,  fcb: 2,  mlr_playoff: 2,  milr_playoff: 2,  gib: 2  },
    att: { mlr: 20,  milr: 20,  fcb: 5,  mlr_playoff: 5,  milr_playoff: 5,  gib: 5  },
};

function getAlltimeMin(key, league) {
    return ALLTIME_DEFAULTS[key]?.[league] ?? ALLTIME_DEFAULTS[key].mlr;
}

// Per-season qualifier defaults keyed by league (pre-fills the user-adjustable inputs)
const SEASON_DEFAULTS = {
    dec: { mlr: 3, milr: 3, fcb: 3, mlr_playoff: 2, milr_playoff: 2, gib: 3, eco: 2, npr: 3, wbc: 3 },
    sv:  { mlr: 3, milr: 3, fcb: 1, mlr_playoff: 1, milr_playoff: 1, gib: 1, eco: 1, npr: 1, wbc: 2 },
    att: { mlr: 5, milr: 5, fcb: 3, mlr_playoff: 3, milr_playoff: 3, gib: 3, eco: 1, npr: 1, wbc: 1 },
};

function getSeasonMin(key, league) {
    return SEASON_DEFAULTS[key]?.[league] ?? SEASON_DEFAULTS[key].mlr;
}

function updateSeasonDefaults(league) {
    const decEl = document.getElementById('min-decisions');
    const svEl  = document.getElementById('min-opp');
    const attEl = document.getElementById('min-attempts');
    if (decEl) decEl.value = getSeasonMin('dec', league);
    if (svEl)  svEl.value  = getSeasonMin('sv',  league);
    if (attEl) attEl.value = getSeasonMin('att', league);
}

// ── Control wiring ────────────────────────────────────────────────────────────

export function initLeaderboardControls() {
    document.getElementById('leaderboard-entity-select').addEventListener('change', () => {
        populateLeaderboardStatSelect();
    });
    document.getElementById('leaderboard-league-select').addEventListener('change', () => {
        populateLeaderboardStatSelect();
    });
    document.getElementById('leaderboard-type-select').addEventListener('change', () => {
        populateLeaderboardStatSelect();
    });
    document.getElementById('leaderboard-stat-select').addEventListener('change', updateMinimumControls);
    document.getElementById('leaderboard-button').addEventListener('click', renderLeaderboard);
}

// ── Stat select ───────────────────────────────────────────────────────────────

export function populateLeaderboardStatSelect() {
    const league = document.getElementById('leaderboard-league-select').value;
    const type   = document.getElementById('leaderboard-type-select').value;
    const sel    = document.getElementById('leaderboard-stat-select');
    const prev   = sel.value;

    const tableGroup = type === 'batting' ? STAT_DEFINITIONS.batting : STAT_DEFINITIONS.pitching;
    const extra      = type === 'batting' ? LEADERBOARD_ONLY_STATS.hitting : LEADERBOARD_ONLY_STATS.pitching;
    const skip       = new Set(['Display Season', 'Team', 'Batting Type', 'Pitching Type']);

    const allStats = [...new Set([
        ...Object.values(tableGroup).flat(),
        ...extra,
    ])].filter(s => !skip.has(s)).sort();

    sel.innerHTML = '<option value="">-- Select Stat --</option>';
    allStats.forEach(stat => {
        const opt = document.createElement('option');
        opt.value = stat;
        opt.textContent = stat;
        sel.appendChild(opt);
    });

    if (prev && sel.querySelector(`option[value="${prev}"]`)) sel.value = prev;

    updateMinimumControls();
    updateSeasonDefaults(league);
    updateMlrFilters(league, type);
}

function updateMinimumControls() {
    const stat      = document.getElementById('leaderboard-stat-select').value;
    const type      = document.getElementById('leaderboard-type-select').value;
    const batting   = document.getElementById('batting-minimum-controls');
    const pitching  = document.getElementById('pitching-minimum-controls');
    const attempts  = document.getElementById('attempts-minimum-controls');
    const decisions = document.getElementById('decisions-minimum-controls');
    const opp       = document.getElementById('opp-minimum-controls');

    [batting, pitching, attempts, decisions, opp].forEach(el => { el.style.display = 'none'; });

    const isTeam = document.getElementById('leaderboard-entity-select')?.value === 'team';
    if (isTeam) return;

    if (stat === 'SB%') {
        attempts.style.display = 'inline-block';
    } else if (stat === 'W-L%') {
        decisions.style.display = 'inline-block';
    } else if (stat === 'SV%') {
        opp.style.display = 'inline-block';
    } else if (!COUNTING_STATS.includes(stat) && stat) {
        if (type === 'batting') batting.style.display = 'inline-block';
        else pitching.style.display = 'inline-block';
    }
}

function updateMlrFilters(league, type) {
    const isTeam = document.getElementById('leaderboard-entity-select')?.value === 'team';
    const hasBreakdowns = !isTeam && LEAGUES_WITH_BREAKDOWNS.includes(league);
    document.querySelectorAll('.mlr-filter').forEach(el => {
        el.style.display = hasBreakdowns ? '' : 'none';
    });
    if (hasBreakdowns) {
        populateTeamFilter();
        populateTypeFilter(type);
    } else {
        const teamSel = document.getElementById('leaderboard-team-filter');
        const typeSel = document.getElementById('leaderboard-type-filter');
        if (teamSel) teamSel.value = '';
        if (typeSel) typeSel.value = '';
    }
}

function populateTeamFilter() {
    const sel  = document.getElementById('leaderboard-team-filter');
    const prev = sel.value;
    sel.innerHTML = '<option value="">All Teams</option>';
    Object.keys(state.teamHistory.mlr).sort().forEach(key => {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = key;
        sel.appendChild(opt);
    });
    if (prev && sel.querySelector(`option[value="${prev}"]`)) sel.value = prev;
}

function populateTypeFilter(type) {
    const sel  = document.getElementById('leaderboard-type-filter');
    const prev = sel.value;
    sel.innerHTML = '<option value="">All Types</option>';
    const defs = state.typeDefinitions;
    const map  = type === 'batting' ? defs.batting : defs.pitching;
    if (!map) return;

    const mainTypes = new Set();
    for (const key of Object.keys(map)) {
        // For pitching: "EG-B" → "EG"; for batting: keep full code
        mainTypes.add(key.includes('-') ? key.split('-')[0] : key);
    }
    [...mainTypes].sort().forEach(code => {
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = code;
        sel.appendChild(opt);
    });

    if (prev && sel.querySelector(`option[value="${prev}"]`)) sel.value = prev;
}

// ── Leaderboard rendering ─────────────────────────────────────────────────────

async function renderLeaderboard() {
    const display = document.getElementById('leaderboards-content-display');
    display.innerHTML = '<p>Loading...</p>';

    const league    = document.getElementById('leaderboard-league-select').value;
    const type      = document.getElementById('leaderboard-type-select').value;
    const stat      = document.getElementById('leaderboard-stat-select').value;
    const topN      = parseInt(document.getElementById('leaderboard-length').value) || 10;
    const reverse   = document.getElementById('reverse-sort').checked;
    const selTeam   = document.getElementById('leaderboard-team-filter')?.value || '';
    const selType   = document.getElementById('leaderboard-type-filter')?.value || '';
    const isTeam    = (document.getElementById('leaderboard-entity-select')?.value || 'player') === 'team';

    if (!stat) { display.innerHTML = '<p>Please select a stat.</p>'; return; }

    const isHitting   = type === 'batting';
    const isCounting  = COUNTING_STATS.includes(stat);
    const lowerBetter = LOWER_IS_BETTER.has(stat)
        || (isHitting  && LOWER_IS_BETTER_BATTING.has(stat))
        || (!isHitting && LOWER_IS_BETTER_PITCHING.has(stat));
    // direction: 1 = ascending (lower first), -1 = descending (higher first)
    // Default: higher-is-better stats descend; lower-is-better stats ascend; reverse flips both
    const direction = (lowerBetter !== reverse) ? 1 : -1;

    const minPA      = parseFloat(document.getElementById('min-pa')?.value) || 2.0;
    const minOuts    = parseInt(document.getElementById('min-outs')?.value) || 3;
    const minAtt     = parseInt(document.getElementById('min-attempts')?.value) || 5;
    const minDec     = parseInt(document.getElementById('min-decisions')?.value) || 3;
    const minOpp     = parseInt(document.getElementById('min-opp')?.value) || 3;

    try {
        let seasonData, careerData, teamHittingData, franchiseData;

        if (isTeam) {
            const hasFranchise = LEAGUES_WITH_FRANCHISE.includes(league);
            [seasonData, franchiseData] = await Promise.all([
                loadStats(league, isHitting ? 'team_hitting' : 'team_pitching'),
                hasFranchise ? loadStats(league, isHitting ? 'franchise_hitting' : 'franchise_pitching') : Promise.resolve([]),
            ]);
            careerData      = [];
            teamHittingData = [];
        } else {
            const seasonKey  = isHitting ? 'hitting'        : 'pitching';
            const hasBreakdowns = LEAGUES_WITH_BREAKDOWNS.includes(league);
            const careerKey  = isHitting
                ? (selTeam && selType && hasBreakdowns ? 'hitting_by_team_type'
                   : selType && hasBreakdowns ? 'hitting_by_type'
                   : selTeam && hasBreakdowns ? 'hitting_by_team'
                   : 'career_hitting')
                : (selTeam && selType && hasBreakdowns ? 'pitching_by_team_type'
                   : selType && hasBreakdowns ? 'pitching_by_type'
                   : selTeam && hasBreakdowns ? 'pitching_by_team'
                   : 'career_pitching');

            [seasonData, careerData, teamHittingData] = await Promise.all([
                loadStats(league, seasonKey),
                LEAGUES_WITH_CAREER.includes(league) || ((selTeam || selType) && hasBreakdowns)
                    ? loadStats(league, careerKey)
                    : Promise.resolve([]),
                loadStats(league, 'team_hitting'),
            ]);
        }

        // ── All-Time card ──────────────────────────────────────────────────
        const cards = [];
        const atQualInfo = getAllTimeQualInfo(stat, isHitting, isCounting, league);
        if (!isTeam && careerData.length) {
            const atRows = filterCareer(careerData, stat, isHitting, isCounting, selTeam, selType, minAtt, minDec, atQualInfo?.default);
            atRows.sort((a, b) => direction * ((a[stat] ?? (direction === 1 ? Infinity : -Infinity)) - (b[stat] ?? (direction === 1 ? Infinity : -Infinity))));
            cards.push({ label: 'All-Time', type: 'all-time', data: atRows, qualInfo: atQualInfo });
        }
        if (isTeam && franchiseData?.length) {
            const atRows = filterFranchiseRows(franchiseData, stat, isCounting);
            atRows.sort((a, b) => direction * ((a[stat] ?? (direction === 1 ? Infinity : -Infinity)) - (b[stat] ?? (direction === 1 ? Infinity : -Infinity))));
            cards.push({ label: 'All-Time', type: 'all-time', isTeamMode: true, isFranchise: true, league, data: atRows });
        }

        // ── Per-season cards ───────────────────────────────────────────────
        const displaySeasons = [...new Set(
            seasonData.filter(r => r['Display Season']?.startsWith('S')).map(r => r['Display Season'])
        )].sort((a, b) => getSeasonSort(b) - getSeasonSort(a));

        // Use max team G as the effective game count per season.
        // This reflects actual games played, prorating qualifiers for active seasons
        // and handling byes/short seasons correctly.
        const seasonGames = {};
        for (const ds of displaySeasons) {
            seasonGames[ds] = teamHittingData
                .filter(r => r['Display Season'] === ds)
                .reduce((m, r) => Math.max(m, r.G || 0), 0);
        }

        // ── Single Season card (only shown when there are multiple seasons) ─
        if (displaySeasons.length > 1) {
            const ssRows = isTeam
                ? filterTeamSeasonRows(seasonData, null, stat, isCounting)
                : filterSeasonRows(seasonData, null, stat, isHitting, isCounting, selTeam, selType, minPA, minOuts, minAtt, minDec, minOpp, seasonGames);
            ssRows.sort((a, b) => direction * ((a[stat] ?? (direction === 1 ? Infinity : -Infinity)) - (b[stat] ?? (direction === 1 ? Infinity : -Infinity))));
            cards.push({ label: 'Single Season', type: 'single-season', isTeamMode: isTeam, league, data: ssRows, qualLabel: '' });
        }

        for (const ds of displaySeasons) {
            const rows = isTeam
                ? filterTeamSeasonRows(seasonData, ds, stat, isCounting)
                : filterSeasonRows(seasonData, ds, stat, isHitting, isCounting, selTeam, selType, minPA, minOuts, minAtt, minDec, minOpp, seasonGames);
            rows.sort((a, b) => direction * ((a[stat] ?? (direction === 1 ? Infinity : -Infinity)) - (b[stat] ?? (direction === 1 ? Infinity : -Infinity))));
            const games = seasonGames[ds] || 0;
            const qualLabel = isTeam ? '' : buildSeasonQualLabel(stat, isHitting, isCounting, minPA, minOuts, minAtt, minDec, minOpp, games);
            cards.push({ label: `Season ${ds.slice(1)}`, type: 'season', isTeamMode: isTeam, league, data: rows, qualLabel });
        }

        // ── Render ─────────────────────────────────────────────────────────
        display.innerHTML = `<h2 class="section-title">${stat} Leaderboards</h2>`;

        const mobileSelector = document.createElement('div');
        mobileSelector.className = 'lb-mobile-selector';

        const prevBtn = document.createElement('button');
        prevBtn.className = 'lb-nav-btn';
        prevBtn.textContent = '‹';

        const mobileSelect = document.createElement('select');
        mobileSelect.className = 'lb-mobile-select';
        cards.forEach((card, i) => {
            const opt = document.createElement('option');
            opt.value = String(i);
            opt.textContent = card.label;
            mobileSelect.appendChild(opt);
        });

        const nextBtn = document.createElement('button');
        nextBtn.className = 'lb-nav-btn';
        nextBtn.textContent = '›';

        if (cards.length <= 1) {
            prevBtn.style.display = 'none';
            nextBtn.style.display = 'none';
        }
        mobileSelector.appendChild(prevBtn);
        mobileSelector.appendChild(mobileSelect);
        mobileSelector.appendChild(nextBtn);
        display.appendChild(mobileSelector);

        const grid = document.createElement('div');
        grid.className = 'leaderboard-grid';
        const cardEls = cards.map(card => {
            const el = buildCard(card, stat, topN);
            grid.appendChild(el);
            return el;
        });

        const setActiveCard = (idx) => {
            mobileSelect.value = String(idx);
            cardEls.forEach((el, i) => el.classList.toggle('lb-active', i === idx));
        };

        if (cardEls.length > 0) cardEls[0].classList.add('lb-active');
        mobileSelect.addEventListener('change', () => setActiveCard(parseInt(mobileSelect.value)));
        prevBtn.addEventListener('click', () => setActiveCard((parseInt(mobileSelect.value) - 1 + cardEls.length) % cardEls.length));
        nextBtn.addEventListener('click', () => setActiveCard((parseInt(mobileSelect.value) + 1) % cardEls.length));
        display.appendChild(grid);
        wirePlayerLinks(display);
        wireTeamLinks(display);

        // ── All-Time qualifier input ───────────────────────────────────────
        if (careerData.length && atQualInfo) {
            const atCardEl = grid.children[0];
            atCardEl.addEventListener('change', e => {
                if (!e.target.classList.contains('alltime-qual-input')) return;
                const newQual = parseFloat(e.target.value);
                if (isNaN(newQual) || newQual < 0) return;
                const newRows = filterCareer(careerData, stat, isHitting, isCounting, selTeam, selType, minAtt, minDec, newQual);
                newRows.sort((a, b) => direction * ((a[stat] ?? (direction === 1 ? Infinity : -Infinity)) - (b[stat] ?? (direction === 1 ? Infinity : -Infinity))));
                atCardEl.querySelector('.card-table-wrap').innerHTML = buildTableHTML(newRows, stat, topN, false, false);
                wirePlayerLinks(atCardEl);
            });
        }

    } catch (err) {
        console.error(err);
        display.innerHTML = '<p>Failed to load leaderboard data.</p>';
    }
}

// ── Filtering helpers ─────────────────────────────────────────────────────────

function filterCareer(data, stat, isHitting, isCounting, selTeam, selType, minAtt, minDec, atQualMin) {
    let rows = data.filter(r => r[stat] !== undefined && r[stat] !== null);

    if (selTeam) rows = rows.filter(r => r.Franchise === selTeam);
    if (selType) {
        if (isHitting) rows = rows.filter(r => r['Batting Type'] === selType);
        else           rows = rows.filter(r => r['Pitching Type'] === selType);
    }

    if (!isCounting) {
        if (stat === 'SB%') {
            rows = rows.filter(r => (r.SB || 0) + (r.CS || 0) >= (atQualMin ?? minAtt));
        } else if (stat === 'W-L%') {
            rows = rows.filter(r => (r.W || 0) + (r.L || 0) >= (atQualMin ?? ALLTIME_MIN_DEC));
        } else if (stat === 'SV%') {
            rows = rows.filter(r => (r.OPP || 0) >= (atQualMin ?? 10));
        } else {
            if (isHitting) rows = rows.filter(r => (r.PA || 0) >= (atQualMin ?? ALLTIME_MIN_PA));
            else           rows = rows.filter(r => (r.IP || 0) >= (atQualMin ?? ALLTIME_MIN_IP));
        }
    }
    if (isCounting && !CAN_BE_NEGATIVE.has(stat)) rows = rows.filter(r => (r[stat] || 0) > 0);
    return rows;
}

function filterSeasonRows(data, displaySeason, stat, isHitting, isCounting, selTeam, selType, minPA, minOuts, minAtt, minDec, minOpp, seasonGames) {
    let rows = data.filter(r => r[stat] !== undefined && r[stat] !== null
        && (selTeam ? r.Franchise === selTeam : !r.is_sub_row)
        && r['Display Season']?.startsWith('S'));
    if (displaySeason) rows = rows.filter(r => r['Display Season'] === displaySeason);
    if (selType) {
        if (isHitting) rows = rows.filter(r => r['Batting Type'] === selType);
        else           rows = rows.filter(r => r['Pitching Type (Main)'] === selType);
    }

    if (!isCounting) {
        rows = rows.filter(r => {
            const ds    = r['Display Season'];
            const games = seasonGames[ds] || 0;
            if (!games) return false;
            if (stat === 'SB%')  return (r.SB || 0) + (r.CS || 0) >= minAtt;
            if (stat === 'W-L%') return (r.W  || 0) + (r.L  || 0) >= minDec;
            if (stat === 'SV%')  return (r.OPP || 0) >= minOpp;
            if (isHitting) return (r.PA || 0) >= minPA * games;
            return Math.round((r.IP || 0) * 3) >= minOuts * games;
        });
    }
    if (isCounting && !CAN_BE_NEGATIVE.has(stat)) rows = rows.filter(r => (r[stat] || 0) > 0);
    return rows;
}

function filterTeamSeasonRows(data, displaySeason, stat, isCounting) {
    let rows = data.filter(r =>
        r[stat] !== undefined && r[stat] !== null
        && r['Display Season']?.startsWith('S')
    );
    if (displaySeason) rows = rows.filter(r => r['Display Season'] === displaySeason);
    if (isCounting && !CAN_BE_NEGATIVE.has(stat)) rows = rows.filter(r => (r[stat] || 0) > 0);
    return rows;
}

function filterFranchiseRows(data, stat, isCounting) {
    let rows = data.filter(r => r[stat] !== undefined && r[stat] !== null);
    if (isCounting && !CAN_BE_NEGATIVE.has(stat)) rows = rows.filter(r => (r[stat] || 0) > 0);
    return rows;
}

// ── Qualifier label helpers ───────────────────────────────────────────────────

// Returns { label, default } describing the all-time qualifier for a stat, or null for counting stats.
function getAllTimeQualInfo(stat, isHitting, isCounting, league) {
    if (isCounting) return null;
    if (stat === 'SB%')  return { label: 'attempts min', default: getAlltimeMin('att', league) };
    if (stat === 'W-L%') return { label: 'decisions min', default: getAlltimeMin('dec', league) };
    if (stat === 'SV%')  return { label: 'save opp min', default: getAlltimeMin('sv',  league) };
    return isHitting
        ? { label: 'PA min', default: getAlltimeMin('pa', league) }
        : { label: 'IP min', default: getAlltimeMin('ip', league) };
}

function buildSeasonQualLabel(stat, isHitting, isCounting, minPA, minOuts, minAtt, minDec, minOpp, games) {
    if (isCounting || !games) return '';
    if (stat === 'SB%')  return `${minAtt} attempts min`;
    if (stat === 'W-L%') return `${minDec} decisions min`;
    if (stat === 'SV%')  return `${minOpp} save opp min`;
    let qual;
    if (isHitting) {
        qual = Math.ceil(minPA * games);
    } else {
        const ipVal  = minOuts * games / 3;
        const inn    = Math.floor(ipVal);
        const outs   = Math.round((ipVal - inn) * 3);
        qual = outs === 3 ? `${inn + 1}.0` : `${inn}.${outs}`;
    }
    const key = isHitting ? 'PA' : 'IP';
    return `${qual} ${key} min`;
}

// ── Card builder ──────────────────────────────────────────────────────────────

function buildTableHTML(data, stat, topN, showTeam, showSeason) {
    let rows = data.slice(0, topN);
    let tieInfo = null;

    if (data.length > topN) {
        const last = data[topN - 1], next = data[topN];
        if (last && next && last[stat] === next[stat]) {
            const tieVal = last[stat];
            let firstTie = topN - 1;
            while (firstTie > 0 && data[firstTie - 1][stat] === tieVal) firstTie--;
            const count = data.filter(r => r[stat] === tieVal).length;
            rows = data.slice(0, firstTie);
            tieInfo = { count, value: tieVal };
        }
    }

    let html = '<table class="stats-table"><thead><tr><th>Rank</th><th>Player</th>';
    if (showTeam)   html += '<th class="lb-short-col">Team</th>';
    if (showSeason) html += '<th class="lb-short-col">Season</th>';
    html += `<th>${stat}</th></tr></thead><tbody>`;

    let lastVal = null, lastRank = 0;
    rows.forEach((r, i) => {
        const rank     = i + 1;
        const dispRank = (i > 0 && r[stat] === lastVal) ? lastRank : rank;
        lastVal = r[stat]; lastRank = dispRank;
        const name = state.allPlayers.find(p => p.ID === r.ID)?.Name || r.Name || `#${r.ID}`;
        html += `<tr>
            <td>${dispRank}</td>
            <td class="player-name-cell" data-player-id="${r.ID}" style="cursor:pointer;text-decoration:underline">${name}</td>
            ${showTeam   ? `<td class="lb-short-col">${r.Team || ''}</td>` : ''}
            ${showSeason ? `<td class="lb-short-col">${(r['Display Season'] || '').slice(1)}</td>` : ''}
            <td>${formatStat(stat, r[stat])}</td>
        </tr>`;
    });

    if (tieInfo) {
        const cols = 2 + (showTeam ? 1 : 0) + (showSeason ? 1 : 0) + 1;
        html += `<tr><td class="tie-info" colspan="${cols}">${tieInfo.count} players tied with ${formatStat(stat, tieInfo.value)}</td></tr>`;
    }

    html += '</tbody></table>';
    return html;
}

function buildTeamTableHTML(data, stat, topN, showSeason, league) {
    let rows = data.slice(0, topN);
    let tieInfo = null;

    if (data.length > topN) {
        const last = data[topN - 1], next = data[topN];
        if (last && next && last[stat] === next[stat]) {
            const tieVal = last[stat];
            let firstTie = topN - 1;
            while (firstTie > 0 && data[firstTie - 1][stat] === tieVal) firstTie--;
            const count = data.filter(r => r[stat] === tieVal).length;
            rows = data.slice(0, firstTie);
            tieInfo = { count, value: tieVal };
        }
    }

    let html = '<table class="stats-table"><thead><tr><th>Rank</th><th>Team</th>';
    if (showSeason) html += '<th class="lb-short-col">Season</th>';
    html += `<th>${stat}</th></tr></thead><tbody>`;

    let lastVal = null, lastRank = 0;
    rows.forEach((r, i) => {
        const rank     = i + 1;
        const dispRank = (i > 0 && r[stat] === lastVal) ? lastRank : rank;
        lastVal = r[stat]; lastRank = dispRank;

        const ds      = r['Display Season'];
        const abbr    = r.Team;
        const name    = getTeamName(league, abbr, ds);
        const lgAttr  = league !== 'mlr' ? ` data-league="${league}"` : '';

        html += `<tr>
            <td>${dispRank}</td>
            <td class="team-link" data-team="${encodeURIComponent(abbr)}" data-season="${ds}"${lgAttr}
                style="cursor:pointer;text-decoration:underline">${name}</td>
            ${showSeason ? `<td class="lb-short-col">${(ds || '').slice(1)}</td>` : ''}
            <td>${formatStat(stat, r[stat])}</td>
        </tr>`;
    });

    if (tieInfo) {
        const cols = 2 + (showSeason ? 1 : 0) + 1;
        html += `<tr><td class="tie-info" colspan="${cols}">${tieInfo.count} teams tied with ${formatStat(stat, tieInfo.value)}</td></tr>`;
    }
    html += '</tbody></table>';
    return html;
}

function buildFranchiseTableHTML(data, stat, topN) {
    let rows = data.slice(0, topN);
    let tieInfo = null;

    if (data.length > topN) {
        const last = data[topN - 1], next = data[topN];
        if (last && next && last[stat] === next[stat]) {
            const tieVal = last[stat];
            let firstTie = topN - 1;
            while (firstTie > 0 && data[firstTie - 1][stat] === tieVal) firstTie--;
            const count = data.filter(r => r[stat] === tieVal).length;
            rows = data.slice(0, firstTie);
            tieInfo = { count, value: tieVal };
        }
    }

    let html = `<table class="stats-table"><thead><tr><th>Rank</th><th>Franchise</th><th>${stat}</th></tr></thead><tbody>`;

    let lastVal = null, lastRank = 0;
    rows.forEach((r, i) => {
        const rank     = i + 1;
        const dispRank = (i > 0 && r[stat] === lastVal) ? lastRank : rank;
        lastVal = r[stat]; lastRank = dispRank;
        const name = getMlrFranchiseLabel(r.Franchise);
        html += `<tr>
            <td>${dispRank}</td>
            <td>${name}</td>
            <td>${formatStat(stat, r[stat])}</td>
        </tr>`;
    });

    if (tieInfo) {
        html += `<tr><td class="tie-info" colspan="3">${tieInfo.count} teams tied with ${formatStat(stat, tieInfo.value)}</td></tr>`;
    }
    html += '</tbody></table>';
    return html;
}

function buildCard(card, stat, topN) {
    const el = document.createElement('div');
    el.className = 'leaderboard-card';

    const showTeam   = card.type === 'season' && !card.isTeamMode;
    const showSeason = card.type === 'single-season';

    let html = '<div class="card-header">';
    html += `<h4>${card.label}</h4>`;

    if (card.type === 'all-time' && card.qualInfo) {
        const { label, default: def } = card.qualInfo;
        const step = '1';
        html += `<span class="qualifier"><input class="alltime-qual-input" type="number" value="${def}" min="0" step="${step}" style="width:55px"> ${label}</span>`;
    } else if (card.qualLabel) {
        html += `<span class="qualifier">${card.qualLabel}</span>`;
    }

    html += '</div>';

    const tableHTML = card.isFranchise
        ? buildFranchiseTableHTML(card.data, stat, topN)
        : card.isTeamMode
            ? buildTeamTableHTML(card.data, stat, topN, showSeason, card.league)
            : buildTableHTML(card.data, stat, topN, showTeam, showSeason);

    html += `<div class="card-table-wrap">${tableHTML}</div>`;

    el.innerHTML = html;
    return el;
}

function wirePlayerLinks(container) {
    container.querySelectorAll('.player-name-cell[data-player-id]').forEach(el => {
        el.addEventListener('click', () => {
            const id = parseInt(el.dataset.playerId);
            import('./player.js').then(m => {
                m.displayPlayerPage(id);
                window.location.hash = '#/stats';
            });
        });
    });
}
