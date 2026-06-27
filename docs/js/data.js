import { state } from './state.js';
import { LEAGUES_WITH_CAREER, LEAGUES_WITH_BREAKDOWNS } from './constants.js';

// Derive the docs/ root from this module's own URL so paths work regardless
// of which directory the server is rooted at.
// This file is at docs/js/data.js, so one level up is docs/.
const ROOT      = new URL('..', import.meta.url).href.replace(/\/$/, '');
const DATA      = ROOT + '/data';
const GENERATED = ROOT + '/generated';

// ── File path registry ───────────────────────────────────────────────────────

function statPath(league, type) {
    // type: 'hitting' | 'pitching' | 'team_hitting' | 'team_pitching'
    //       'career_hitting' | 'career_pitching'
    //       'hitting_by_team' | 'pitching_by_team'
    //       'hitting_by_type' | 'pitching_by_type'
    //       'hitting_by_team_type' | 'pitching_by_team_type'
    const map = {
        hitting:               `${GENERATED}/${league}_hitting_stats.json`,
        pitching:              `${GENERATED}/${league}_pitching_stats.json`,
        team_hitting:          `${GENERATED}/${league}_team_hitting_stats.json`,
        team_pitching:         `${GENERATED}/${league}_team_pitching_stats.json`,
        career_hitting:        `${GENERATED}/${league}_career_hitting_stats.json`,
        career_pitching:       `${GENERATED}/${league}_career_pitching_stats.json`,
        hitting_by_team:       `${GENERATED}/${league}_hitting_stats_by_team.json`,
        pitching_by_team:      `${GENERATED}/${league}_pitching_stats_by_team.json`,
        hitting_by_type:       `${GENERATED}/${league}_hitting_stats_by_type.json`,
        pitching_by_type:      `${GENERATED}/${league}_pitching_stats_by_type.json`,
        hitting_by_team_type:  `${GENERATED}/${league}_hitting_stats_by_team_type.json`,
        pitching_by_team_type: `${GENERATED}/${league}_pitching_stats_by_team_type.json`,
        franchise_hitting:     `${GENERATED}/${league}_franchise_hitting_stats.json`,
        franchise_pitching:    `${GENERATED}/${league}_franchise_pitching_stats.json`,
    };
    return map[type] || null;
}

// ── Core data (loaded once on startup) ───────────────────────────────────────

export async function loadCoreData() {
    const [
        allPlayers,
        glossary,
        typeDefinitions,
        awards,
        mlrTeamHistory,
        milrTeamHistory,
        fcbTeamHistory,
        ecoTeamHistory,
        nprTeamHistory,
        wbcTeamHistory,
        gibTeamHistory,
        mlrDivisions,
        milrDivisions,
        fcbDivisions,
        ecoDivisions,
        nprDivisions,
        wbcDivisions,
        gibDivisions,
    ] = await Promise.all([
        fetch(`${GENERATED}/all_players.json`).then(r => r.json()),
        fetch(`${ROOT}/glossary.json`).then(r => r.json()),
        fetch(`${DATA}/type_definitions.json`).then(r => r.json()),
        fetch(`${DATA}/awards.json`).then(r => r.json()),
        fetch(`${DATA}/mlr_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/milr_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/fcb_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/eco_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/npr_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/wbc_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/gib_team_history.json`).then(r => r.json()),
        fetch(`${DATA}/mlr_divisions.json`).then(r => r.json()),
        fetch(`${DATA}/milr_divisions.json`).then(r => r.json()),
        fetch(`${DATA}/fcb_divisions.json`).then(r => r.json()),
        fetch(`${DATA}/eco_divisions.json`).then(r => r.json()),
        fetch(`${DATA}/npr_divisions.json`).then(r => r.json()),
        fetch(`${DATA}/wbc_divisions.json`).then(r => r.json()),
        fetch(`${DATA}/gib_divisions.json`).then(r => r.json()),
    ]);

    state.allPlayers = allPlayers;
    state.glossary = glossary;
    state.typeDefinitions = typeDefinitions;
    state.awards = awards;
    state.teamHistory.mlr = mlrTeamHistory;
    state.teamHistory.milr = milrTeamHistory;
    state.teamHistory.fcb = fcbTeamHistory;
    state.teamHistory.eco = ecoTeamHistory;
    state.teamHistory.npr = nprTeamHistory;
    state.teamHistory.wbc = wbcTeamHistory;
    state.teamHistory.gib = gibTeamHistory;
    state.divisions.mlr = mlrDivisions;
    state.divisions.milr = milrDivisions;
    state.divisions.fcb = fcbDivisions;
    state.divisions.eco = ecoDivisions;
    state.divisions.npr = nprDivisions;
    state.divisions.wbc = wbcDivisions;
    state.divisions.gib = gibDivisions;

    buildPlayerMap();
    buildSeasonsWithStats();
}

// ── Lazy stat loader ─────────────────────────────────────────────────────────

// Returns cached data if already loaded; otherwise fetches and caches.
// key is e.g. "mlr_hitting", "milr_career_pitching", "mlr_hitting_by_team"
export async function loadStats(league, type) {
    const key = `${league}_${type}`;
    if (state.loaded.has(key)) return state.stats[key];

    const path = statPath(league, type);
    if (!path) throw new Error(`No path known for ${key}`);

    state.loaded.add(key); // mark before fetch to prevent duplicate in-flight requests
    try {
        const data = await fetch(path).then(r => r.json());
        state.stats[key] = data;
        return data;
    } catch (err) {
        state.loaded.delete(key); // allow retry on failure
        throw err;
    }
}

// Convenience: load both hitting and pitching for a league at once
export async function loadLeaguePair(league) {
    return Promise.all([loadStats(league, 'hitting'), loadStats(league, 'pitching')]);
}

// Load all stat types for a league that the player page needs
export async function loadForPlayerPage(league) {
    const types = ['hitting', 'pitching'];
    if (LEAGUES_WITH_CAREER.includes(league)) {
        types.push('career_hitting', 'career_pitching');
    }
    if (LEAGUES_WITH_BREAKDOWNS.includes(league)) {
        types.push('hitting_by_team', 'pitching_by_team', 'hitting_by_type', 'pitching_by_type');
    }
    return Promise.all(types.map(t => loadStats(league, t)));
}

// Load team stats for the teams view
export async function loadTeamStats(league) {
    return Promise.all([loadStats(league, 'team_hitting'), loadStats(league, 'team_pitching')]);
}

export async function loadPlayoffBrackets(league) {
    const key = `${league}_playoff_brackets`;
    if (state.loaded.has(key)) return state.playoffBrackets[league];
    state.loaded.add(key);
    try {
        const data = await fetch(`${GENERATED}/${league}_playoff_brackets.json`).then(r => r.json());
        state.playoffBrackets[league] = data;
        return data;
    } catch (err) {
        state.loaded.delete(key);
        throw err;
    }
}

// ── Player index helpers ─────────────────────────────────────────────────────

function buildPlayerMap() {
    state.playerMap.clear();
    for (const player of state.allPlayers) {
        const id = player.ID;
        addToMap(player.Name, id);
        const former = player['Former Names'];
        if (Array.isArray(former)) {
            former.forEach(n => addToMap(n, id));
        } else if (former && typeof former === 'string') {
            addToMap(former, id);
        }
    }
}

function addToMap(name, id) {
    if (!name) return;
    const key = name.toLowerCase();
    if (!state.playerMap.has(key)) state.playerMap.set(key, []);
    const arr = state.playerMap.get(key);
    if (!arr.includes(id)) arr.push(id);
}

export function getPlayerById(id) {
    return state.allPlayers.find(p => p.ID === id) || null;
}

// Search player map — returns array of matching player objects
export function searchPlayers(query) {
    if (!query) return [];
    const q = query.toLowerCase();
    const matchedIds = new Set();
    for (const [name, ids] of state.playerMap) {
        if (name.includes(q)) ids.forEach(id => matchedIds.add(id));
    }
    return [...matchedIds].map(id => getPlayerById(id)).filter(Boolean);
}

// ── Seasons with stats ───────────────────────────────────────────────────────

// Derives the sorted list of MLR seasons that have real data (not sub-rows).
// Called after hitting stats are loaded; stored in state.seasonsWithStats.
export function buildSeasonsWithStats() {
    const mlrSeasons = state.divisions.mlr || {};
    state.seasonsWithStats = Object.keys(mlrSeasons).sort((a, b) => {
        const na = parseInt(a.slice(1)), nb = parseInt(b.slice(1));
        return na - nb;
    });
}
