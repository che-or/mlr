import { state } from './state.js';

// ── Number formatting ────────────────────────────────────────────────────────

// Opponent pitching stats (BA, OBP, SLG, OPS, BABIP) share column names with
// hitting stats in the new data format — no separate *A suffix variants exist.
const THREE_DECIMAL_STATS = new Set([
    'BA', 'BARISP', 'OBP', 'SLG', 'OPS', 'ISO', 'BABIP', 'W-L%', 'SV%',
    'nOBP', 'nSLG',
]);
const ZERO_DECIMAL_STATS = new Set(['OPS+', 'ERA-']);
const TWO_DECIMAL_STATS = new Set(['ERA', 'WHIP', 'FIP', 'GB/FB', 'WAR', 'RE24', 'WPA', 'Avg Diff']);
const ONE_DECIMAL_STATS = new Set(['H6', 'HR6', 'BB6', 'SO6', 'SO/BB']);

export function formatStat(stat, value) {
    if (value === undefined || value === null) return '-';
    if (typeof value !== 'number') return value;

    if (ZERO_DECIMAL_STATS.has(stat)) return Math.round(value).toString();
    if (THREE_DECIMAL_STATS.has(stat)) {
        const s = value.toFixed(3);
        return s.startsWith('0.') ? s.slice(1) : s;  // drop leading zero: .314 not 0.314
    }
    if (TWO_DECIMAL_STATS.has(stat)) return value.toFixed(2);
    if (ONE_DECIMAL_STATS.has(stat)) return value.toFixed(1);
    if (stat === 'IP') {
        const innings = Math.floor(value);
        const outs = Math.round((value - innings) * 3);
        return outs === 3 ? `${innings + 1}.0` : `${innings}.${outs}`;
    }
    if (stat.includes('%')) return (value * 100).toFixed(1);
    return Math.round(value);
}

// Parses a rendered table cell's text back into a value usable in a numeric sort comparator.
// "Inf." is a real (extreme) value, not a missing one, so it always sorts as +Infinity —
// unlike a blank cell ('-'), which sorts toward whichever end of the list is "last" for the
// current direction, regardless of that direction, so missing values stay out of the way.
export function parseSortValue(text, direction) {
    const t = (text ?? '').trim();
    if (t === 'Inf.') return Infinity;
    const v = parseFloat(t);
    return isNaN(v) ? (direction === 'asc' ? Infinity : -Infinity) : v;
}

// ── Franchise key from a stats record ────────────────────────────────────────
// The Franchise field in stats records IS the franchise key.
// Multi-team rows have Franchise = "2TM", "3TM", etc. — fall back to Last Team.
export function recordFranchiseKey(r) {
    return (r.Franchise && !/^\d+TM$/.test(r.Franchise)) ? r.Franchise : (r['Last Team'] || r.Team);
}

// ── Manual logo overrides ────────────────────────────────────────────────────
// From docs/data/logo_overrides.json (hand-maintained; not touched by the
// Python pipeline). See that file's "_readme" for the schema.

// Returns an override franchise key for a player's MLR logo in a given season,
// for season/award-scoped displays (awards page). `awardKey` is the award code
// shown on the awards page (e.g. "AS", "SS", "MVP"); pass null/undefined when
// there's no specific award context. Returns null if no override applies.
export function getSeasonLogoOverride(playerId, season, awardKey) {
    const entry = state.logoOverrides.player_season?.[playerId];
    const value = entry?.[season];
    if (value == null) return null;
    if (typeof value === 'string') return value;
    return (awardKey && value[awardKey]) || value.default || null;
}

// Returns a full override { league, franchise, season } for a player's
// default (player-page header) logo, or null if none applies.
export function getPlayerDefaultLogoOverride(playerId) {
    return state.logoOverrides.player_default?.[playerId] || null;
}

// ── Season helpers ───────────────────────────────────────────────────────────

// Convert display season string to a sortable number.
// "S8A" → 7.1, "S8B" → 7.2, "S1" → 1, "S12" → 12
export function getSeasonSort(season) {
    if (!season) return 0;
    if (season === 'S8A') return 7.1;
    if (season === 'S8B') return 7.2;
    const n = parseInt(season.replace(/^S/, ''));
    return isNaN(n) ? 0 : n;
}

// ── Team / franchise helpers (MLR) ──────────────────────────────────────────

// Returns the franchise key for an MLR abbreviation+season.
// e.g. getFranchiseKey('TEX', 'S3') → 'CLE'
export function getFranchiseKey(abbr, displaySeason) {
    const seasonNum = parseInt(displaySeason.replace(/^S/, ''));
    for (const key in state.teamHistory.mlr) {
        const entries = state.teamHistory.mlr[key];
        if (Array.isArray(entries) && entries.some(e =>
            e.abbr === abbr && seasonNum >= e.start && (e.end === 9999 || seasonNum <= e.end)
        )) return key;
    }
    return abbr;
}

// Returns { name, abbr, logo_dark, logo_light } for an MLR franchise+season.
export function getMlrTeamEntry(franchiseKey, displaySeason) {
    const seasonNum = parseInt(displaySeason.replace(/^S/, ''));
    const entries = state.teamHistory.mlr[franchiseKey];
    if (!entries) return null;
    return entries.find(e => seasonNum >= e.start && (e.end === 9999 || seasonNum <= e.end)) || null;
}

// Returns the logo path for an MLR franchise+season, respecting dark/light mode.
export function getMlrLogo(franchiseKey, displaySeason) {
    const entry = getMlrTeamEntry(franchiseKey, displaySeason);
    if (!entry) return null;
    const isLight = document.documentElement.classList.contains('light-mode');
    return isLight ? entry.logo_light : entry.logo_dark;
}

// Returns the full team name for an MLR franchise+season.
export function getMlrTeamName(franchiseKey, displaySeason) {
    const entry = getMlrTeamEntry(franchiseKey, displaySeason);
    return entry ? entry.name : franchiseKey;
}

// Returns the season-specific abbreviation for an MLR franchise+season.
export function getMlrTeamAbbr(franchiseKey, displaySeason) {
    const entry = getMlrTeamEntry(franchiseKey, displaySeason);
    return entry ? entry.abbr : franchiseKey;
}

// Returns the current (most recent) team name for an MLR franchise key.
export function getMlrFranchiseName(franchiseKey) {
    const entries = state.teamHistory.mlr[franchiseKey];
    if (!entries) return franchiseKey;
    const current = entries.find(e => e.end === 9999);
    return current ? current.name : (entries[entries.length - 1]?.name || franchiseKey);
}

// Returns a display label for a franchise in leaderboards.
// Defunct franchises get a season-range suffix to distinguish them from active ones with the same name.
export function getMlrFranchiseLabel(franchiseKey) {
    const entries = state.teamHistory.mlr[franchiseKey];
    if (!entries) return franchiseKey;
    const isActive = entries.some(e => e.end === 9999);
    const name = isActive
        ? entries.find(e => e.end === 9999).name
        : (entries[entries.length - 1]?.name || franchiseKey);
    if (isActive) return name;
    const minS = Math.min(...entries.map(e => e.start));
    const maxS = Math.max(...entries.map(e => e.end === 9999 ? e.start : e.end));
    return minS === maxS ? `${name} (S${minS})` : `${name} (S${minS}–S${maxS})`;
}

// ── Team helpers (season-keyed leagues: MiLR, FCB, GIB, ECO, NPR, WBC) ─────

// MiLR history: { S3: { BAY: "Bayside Fish & Ships", ... } }
// Entries may be plain strings or objects { name, logo_dark, logo_light }.
export function getMilrTeamName(abbr, displaySeason) {
    const season = state.teamHistory.milr[displaySeason];
    if (!season) return abbr;
    const entry = season[abbr];
    return (typeof entry === 'string' ? entry : entry?.name) || abbr;
}

export function getMilrLogoPair(abbr, displaySeason) {
    const season = state.teamHistory.milr[displaySeason];
    if (!season) return null;
    const entry = season[abbr];
    if (!entry || typeof entry === 'string' || !entry.logo_dark) return null;
    return { dark: entry.logo_dark, light: entry.logo_light };
}

// FCB history: { S3: { ABB: "Team Name", ... } }  (plain name strings)
export function getFcbTeamName(abbr, displaySeason) {
    const season = state.teamHistory.fcb[displaySeason];
    if (!season) return abbr;
    const entry = season[abbr];
    return (typeof entry === 'string' ? entry : entry?.name) || abbr;
}

export function getFcbLogo(abbr, displaySeason) {
    const season = state.teamHistory.fcb[displaySeason];
    if (!season) return null;
    const entry = season[abbr];
    if (!entry || typeof entry === 'string') return null;
    const isLight = document.documentElement.classList.contains('light-mode');
    return (isLight ? entry.logo_light : entry.logo_dark) || null;
}

// Generic lookup for historical leagues (ECO, NPR, WBC, GIB)
// Supports plain strings { S1: { ABBR: "Name" } }, objects { S1: { ABBR: { name, logo_dark, logo_light } } },
// and string pointer references ({ S3: "S2" })
export function getHistoricalTeamName(league, abbr, displaySeason) {
    const hist = state.teamHistory[league];
    if (!hist) return abbr;
    let season = hist[displaySeason];
    if (typeof season === 'string') season = hist[season]; // resolve pointer
    const entry = season && season[abbr];
    return (typeof entry === 'object' ? entry?.name : entry) || abbr;
}

export function getHistoricalLogoPair(league, abbr, displaySeason) {
    const hist = state.teamHistory[league];
    if (!hist) return null;
    let season = hist[displaySeason];
    if (typeof season === 'string') season = hist[season]; // resolve pointer
    const entry = season && season[abbr];
    if (!entry || typeof entry !== 'object' || !entry.logo_dark) return null;
    return { dark: entry.logo_dark, light: entry.logo_light };
}

// Universal team name resolver — picks the right helper based on league
export function getTeamName(league, abbr, displaySeason) {
    if (!abbr || abbr === '2TM' || abbr === '3TM') return abbr;
    switch (league) {
        case 'mlr':
        case 'mlr_playoff': {
            const key = getFranchiseKey(abbr, displaySeason);
            return getMlrTeamName(key, displaySeason);
        }
        case 'milr':
        case 'milr_playoff':
            return getMilrTeamName(abbr, displaySeason);
        case 'fcb':
            return getFcbTeamName(abbr, displaySeason);
        default:
            return getHistoricalTeamName(league, abbr, displaySeason);
    }
}

// ── Divisions helper ─────────────────────────────────────────────────────────

// Returns the divisions object for a season, resolving string references (pointer seasons).
export function getDivisionsForSeason(league, displaySeason) {
    const divs = state.divisions[league];
    if (!divs) return null;
    const entry = divs[displaySeason];
    if (typeof entry === 'string') return divs[entry]; // resolve pointer
    return entry || null;
}

// ── Seeded random (for home page featured entities) ──────────────────────────

export function seededRandom(seed) {
    return function () {
        let t = seed += 0x6D2B79F5;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

// ── Logo pair helpers ────────────────────────────────────────────────────────

export function getMlrLogoPair(franchiseKey, displaySeason) {
    const entry = getMlrTeamEntry(franchiseKey, displaySeason);
    if (!entry) return null;
    return { dark: entry.logo_dark, light: entry.logo_light };
}

export function getFcbLogoPair(abbr, displaySeason) {
    const season = state.teamHistory.fcb[displaySeason];
    if (!season) return null;
    const entry = season[abbr];
    if (!entry || typeof entry === 'string' || !entry.logo_dark) return null;
    return { dark: entry.logo_dark, light: entry.logo_light };
}

// Universal logo-pair resolver — picks the right helper based on league.
// Unlike getTeamName(), the mlr/mlr_playoff case does NOT translate through
// getFranchiseKey: callers that already hold an MLR franchise key (as opposed
// to a season-specific abbreviation) should pass it straight through.
export function getLogoPair(league, franchise, displaySeason) {
    if (!franchise || franchise === '2TM' || franchise === '3TM') return null;
    switch (league) {
        case 'mlr':
        case 'mlr_playoff':
            return getMlrLogoPair(franchise, displaySeason);
        case 'milr':
        case 'milr_playoff':
            return getMilrLogoPair(franchise, displaySeason);
        case 'fcb':
            return getFcbLogoPair(franchise, displaySeason);
        default:
            return getHistoricalLogoPair(league, franchise, displaySeason);
    }
}

// Renders an <img> that carries both logo paths as data attributes so
// refreshLogos() can swap src without a re-render on theme toggle.
export function makeLogoImg(dark, light, cssClass, alt = '') {
    const isLight = document.documentElement.classList.contains('light-mode');
    const src = (isLight && light) ? light : dark;
    const classAttr = cssClass ? ` class="${cssClass}"` : '';
    const lightAttr = light ? ` data-logo-light="${light}"` : '';
    return `<img src="${src}" data-logo-dark="${dark}"${lightAttr}${classAttr} alt="${alt}">`;
}

export function refreshLogos() {
    const isLight = document.documentElement.classList.contains('light-mode');
    document.querySelectorAll('img[data-logo-dark]').forEach(img => {
        img.src = isLight
            ? (img.dataset.logoLight || img.dataset.logoDark)
            : img.dataset.logoDark;
    });
}

// ── Theme ────────────────────────────────────────────────────────────────────

export function initTheme(switchInput) {
    const saved = localStorage.getItem('theme');
    if (saved === 'light') {
        document.documentElement.classList.add('light-mode');
        switchInput.checked = true;
    }
    switchInput.addEventListener('change', () => {
        if (switchInput.checked) {
            document.documentElement.classList.add('light-mode');
            localStorage.setItem('theme', 'light');
        } else {
            document.documentElement.classList.remove('light-mode');
            localStorage.setItem('theme', 'dark');
        }
        refreshLogos();
    });
}

// ── Sticky column offsets (mobile table scrolling) ───────────────────────────

export function setStickyColumnOffsets(containerSelector = '#stats-content-display') {
    if (window.innerWidth > 900) {
        document.querySelectorAll(`${containerSelector} .col-1`).forEach(c => { c.style.left = ''; });
        return;
    }
    document.querySelectorAll(`${containerSelector} .stats-table`).forEach(table => {
        const first = table.querySelector('th.col-0');
        if (!first) return;
        const w = first.offsetWidth;
        table.querySelectorAll('.col-1').forEach(c => { c.style.left = `${w}px`; });
    });
}
