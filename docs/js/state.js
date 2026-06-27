// Global application state. Mutated in-place by data.js and view modules.
export const state = {
    // Core data — loaded once at startup
    allPlayers: [],        // from all_players.json: [{ID, Name, Batting Type, Pitching Type, Handedness, Position, Former Names}]
    playerMap: new Map(),  // lowercase name -> [playerIds], built from allPlayers for search
    glossary: {},          // from glossary.json
    typeDefinitions: {},   // from data/type_definitions.json: { batting: {code: name}, pitching: {code: name} }
    awards: {},            // from data/awards.json
    teamHistory: {
        mlr: {},           // franchise-based: { FRANCHISE_KEY: [{name, abbr, start, end, logo_dark, logo_light}] }
        milr: {},          // season-based: { S3: { BAY: "Bayside ...", ... } }
        fcb: {},           // season-based with logo info: { S3: { ABB: { name, logo_dark, logo_light } } }
        eco: {},           // season-based: { S1: { CC: "CC", ... } }
        npr: {},
        wbc: {},
        gib: {},
    },
    divisions: {
        mlr: {},           // { S1: { AL: { East: [...], ... }, NL: {...} } } or string ref to another season
        milr: {},
        fcb: {},
        eco: {},
        npr: {},
        wbc: {},
        gib: {},
    },

    // Lazy-loaded stats — populated on demand, keyed by "<league>_<type>"
    // e.g. "mlr_hitting", "milr_pitching", "mlr_career_hitting", "mlr_hitting_by_team"
    stats: {},

    // Track which stat files have been fetched (prevents duplicate requests)
    loaded: new Set(),

    // Lazy-loaded draft history — populated on first visit to draft view
    draftHistory: null,

    // Lazy-loaded playoff bracket data — keyed by league ('mlr', 'milr')
    playoffBrackets: {},

    // UI state
    currentPlayerId: null,
    lastTeamStatsUrl: '#/team-stats',
    seasonsWithStats: [],  // sorted array of MLR season strings with data, e.g. ["S1","S2",...]
};
