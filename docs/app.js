document.addEventListener('DOMContentLoaded', () => {
    const API = {
        hitting: './data/hitting_stats.json',
        pitching: './data/pitching_stats.json',
        milrHitting: './data/milr_hitting_stats.json',
        milrPitching: './data/milr_pitching_stats.json',
        fcbHitting: './data/fcb_hitting_stats.json',
        fcbPitching: './data/fcb_pitching_stats.json',
        players: './data/player_id_map.json',
        milrPlayerIdMap: './data/milr_player_id_map.json',
        fcbPlayerIdMap: './data/fcb_player_id_map.json',
        seasons: './data/season_games_map.json',
        glossary: './data/glossary.json',
        divisions: './data/divisions.json',
        milrDivisions: './data/milr_divisions.json',
        fcbDivisions: './data/fcb_divisions.json',
        teamHistory: './data/team_history.json',
        milrTeamHistory: './data/milr_team_history.json',
        fcbTeamHistory: './data/fcb_team_history.json',
        teamHitting: './data/team_hitting_stats.json',
        teamPitching: './data/team_pitching_stats.json',
        milrTeamHitting: './data/milr_team_hitting_stats.json',
        milrTeamPitching: './data/milr_team_pitching_stats.json',
        fcbTeamHitting: './data/fcb_team_hitting_stats.json',
        fcbTeamPitching: './data/fcb_team_pitching_stats.json',
        gamelogErrors: './data/gamelog-errors.json',
        typeDefinitions: './data/type_definitions.json',
        playerInfo: './data/player_info.json',
        awards: './data/awards.json',
        currentSeasonInfo: './data/current_season_info.json'
    };

    const state = {
        hittingStats: [],
        pitchingStats: [],
        milrHittingStats: [],
        milrPitchingStats: [],
        fcbHittingStats: [],
        fcbPitchingStats: [],
        teamHittingStats: [],
        teamPitchingStats: [],
        milrTeamHittingStats: [],
        milrTeamPitchingStats: [],
        fcbTeamHittingStats: [],
        fcbTeamPitchingStats: [],
        players: {},
        seasons: {},
        glossaryData: {},
        divisions: {},
        milrDivisions: {},
        fcbDivisions: {},
        teamHistory: {},
        milrTeamHistory: {},
        fcbTeamHistory: {},
        gamelogErrors: [],
        typeDefinitions: {},
        playerInfo: {},
        awards: {},
        currentSeasonInfo: {},
        playerMap: new Map(),
        currentPlayerId: null,
        lastTeamStatsUrl: '#/team-stats',
        seasonsWithStats: []
    };

    const elements = {
        loader: document.getElementById('loader'),
        app: document.getElementById('app'),
        
        homeView: document.getElementById('home-view'),
        statsView: document.getElementById('stats-view'),
        leaderboardsView: document.getElementById('leaderboards-view'),
        glossaryView: document.getElementById('glossary-view'),
        teamStatsView: document.getElementById('team-stats-view'),
        awardsView: document.getElementById('awards-view'),
        hofView: document.getElementById('hof-view'),
        
        homeTab: document.getElementById('home-tab'),
        statsTab: document.getElementById('stats-tab'),
        teamStatsTab: document.getElementById('team-stats-tab'),
        leaderboardsTab: document.getElementById('leaderboards-tab'),
        glossaryTab: document.getElementById('glossary-tab'),

        playerSearch: document.getElementById('player-search'),
        playerSuggestions: document.getElementById('player-suggestions'),
        statsContentDisplay: document.getElementById('stats-content-display'),

        leaderboardLeagueSelect: document.getElementById('leaderboard-league-select'),
        leaderboardTypeSelect: document.getElementById('leaderboard-type-select'),
        leaderboardStatSelect: document.getElementById('leaderboard-stat-select'),
        leaderboardButton: document.getElementById('leaderboard-button'),
        leaderboardLength: document.getElementById('leaderboard-length'),
        leaderboardTeamFilter: document.getElementById('leaderboard-team-filter'),
        leaderboardTypeFilter: document.getElementById('leaderboard-type-filter'),
        reverseSort: document.getElementById('reverse-sort'),
        leaderboardsContentDisplay: document.getElementById('leaderboards-content-display'),
        minPa: document.getElementById('min-pa'),
        minOuts: document.getElementById('min-outs'),
        battingMinimumControls: document.getElementById('batting-minimum-controls'),
        pitchingMinimumControls: document.getElementById('pitching-minimum-controls'),
        attemptsMinimumControls: document.getElementById('attempts-minimum-controls'),
        decisionsMinimumControls: document.getElementById('decisions-minimum-controls'),
        minPaLabel: document.querySelector('label[for="min-pa"]'),
        minOutsLabel: document.querySelector('label[for="min-outs"]'),
        minAttempts: document.getElementById('min-attempts'),
        minDecisions: document.getElementById('min-decisions'),
        themeSwitch: document.getElementById('theme-switch-input')
    };

    const COUNTING_STATS = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'IBB', 'SO', 'Auto K', 'TB', 'GIDP', 'SH', 'SF', 'W', 'L', 'GS', 'GF', 'CG', 'SHO', 'SV', 'HLD', 'IP', 'ER', 'Auto BB', 'AUTO BB', 'BF', '1B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO', 'WAR', 'WPA', 'RE24'];

    const handleStatSelectChange = () => {
        const stat = elements.leaderboardStatSelect.value;
        const isCounting = COUNTING_STATS.includes(stat);

        // Hide all minimum controls by default
        elements.battingMinimumControls.style.display = 'none';
        elements.pitchingMinimumControls.style.display = 'none';
        elements.attemptsMinimumControls.style.display = 'none';
        elements.decisionsMinimumControls.style.display = 'none';
        
        elements.minPa.classList.add('disabled-input');
        elements.minPaLabel.classList.add('disabled-input');
        elements.minOuts.classList.add('disabled-input');
        elements.minOutsLabel.classList.add('disabled-input');

        if (stat === 'SB%') {
            elements.attemptsMinimumControls.style.display = 'inline-block';
        } else if (stat === 'W-L%') {
            elements.decisionsMinimumControls.style.display = 'inline-block';
        } else if (!isCounting) {
            const type = elements.leaderboardTypeSelect.value;
            if (type === 'batting') {
                elements.battingMinimumControls.style.display = 'inline-block';
                elements.minPa.classList.remove('disabled-input');
                elements.minPaLabel.classList.remove('disabled-input');
            } else {
                elements.pitchingMinimumControls.style.display = 'inline-block';
                elements.minOuts.classList.remove('disabled-input');
                elements.minOutsLabel.classList.remove('disabled-input');
            }
        }
    };

    const parseCompactData = (response) => {
        const { columns, data } = response;
        return data.map(row => {
            const obj = {};
            columns.forEach((col, i) => {
                obj[col] = row[i];
            });
            return obj;
        });
    };

    const STAT_DEFINITIONS = {
        batting_tables: {
            'Standard Batting': ['Season', 'Team', 'Type', 'WAR', 'G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'IBB', 'SO', 'Auto K', 'BA', 'OBP', 'SLG', 'OPS', 'OPS+'],
            'Advanced Batting': ['Season', 'Team', 'TB', 'GIDP', 'SH', 'SF', 'BABIP', 'ISO', 'HR%', 'SO%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24', 'SB%', 'Avg Diff']
        },
        pitching_tables: {
            'Standard Pitching': ['Season', 'Team', 'Type', 'WAR', 'W', 'L', 'W-L%', 'ERA', 'G', 'GS', 'GF', 'CG', 'SHO', 'SV', 'HLD', 'IP', 'H', 'ER', 'HR', 'BB', 'IBB', 'Auto BB', 'SO', 'BF', 'ERA-'],
            'Advanced Pitching': ['Season', 'Team', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'SO6', 'SO/BB', 'HR%', 'K%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24', 'Avg Diff'],
            'Opponent Stats': ['Season', 'Team', 'BA', 'OBP', 'SLG', 'OPS', 'BABIP', 'SB', 'CS', 'SB%']
        }
    };

    const STAT_DESCRIPTIONS = {
        'WAR': 'Wins Above Replacement',
        'G': 'Games Played',
        'PA': 'Plate Appearances',
        'AB': 'At Bats',
        'R': 'Runs Scored',
        'H': 'Hits',
        '2B': 'Doubles',
        '3B': 'Triples',
        'HR': 'Home Runs',
        'RBI': 'Runs Batted In',
        'SB': 'Stolen Bases',
        'CS': 'Caught Stealing',
        'BB': 'Walks (Bases on Balls)',
        'IBB': 'Intentional Walks',
        'SO': 'Strikeouts',
        'Auto K': 'Automatic Strikeouts',
        'BA': 'Batting Average',
        'OBP': 'On-base Percentage',
        'SLG': 'Slugging Percentage',
        'OPS': 'On-base Plus Slugging',
        'OPS+': 'OPS adjusted for park and league',
        'TB': 'Total Bases',
        'GIDP': 'Grounded Into Double Play',
        'SH': 'Sacrifice Hits (Bunts)',
        'SF': 'Sacrifice Flies',
        'BABIP': 'Batting Average on Balls In Play',
        'ISO': 'Isolated Power',
        'HR%': 'Home Run Percentage',
        'SO%': 'Strikeout Percentage',
        'BB%': 'Walk Percentage',
        'GB%': 'Ground Ball Percentage',
        'FB%': 'Fly Ball Percentage',
        'GB/FB': 'Ground Ball to Fly Ball Ratio',
        'WPA': 'Win Probability Added',
        'RE24': 'Run Expectancy based on 24 base-out states',
        'SB%': 'Stolen Base Percentage',
        'Avg Diff': 'Average Difference',
        'W': 'Wins',
        'L': 'Losses',
        'W-L%': 'Win-Loss Percentage',
        'ERA': 'Earned Run Average',
        'GS': 'Games Started',
        'GF': 'Games Finished',
        'CG': 'Complete Games',
        'SHO': 'Shutouts',
        'SV': 'Saves',
        'HLD': 'Holds',
        'IP': 'Innings Pitched',
        'ER': 'Earned Runs',
        'Auto BB': 'Automatic Walks',
        'BF': 'Batters Faced',
        'ERA-': 'ERA Minus - ERA adjusted for park and league, where 100 is average and lower is better',
        'FIP': 'Fielding Independent Pitching',
        'WHIP': 'Walks + Hits per Inning Pitched',
        'H6': 'Hits per 6 Innings',
        'HR6': 'Home Runs per 6 Innings',
        'BB6': 'Walks per 6 Innings',
        'SO6': 'Strikeouts per 6 Innings',
        'SO/BB': 'Strikeout to Walk Ratio',
        'K%': 'Strikeout Percentage',
    };

    const setStickyColumnOffsets = () => {
        // Only run if on mobile view for tables
        if (window.innerWidth > 900) {
            const secondColumnCells = document.querySelectorAll('#stats-content-display .col-1');
            secondColumnCells.forEach(cell => {
                cell.style.left = '';
            });
            return;
        }

        const tables = document.querySelectorAll('#stats-content-display .stats-table');
        tables.forEach(table => {
            const firstHeaderCell = table.querySelector('th.col-0');
            if (firstHeaderCell) {
                const width = firstHeaderCell.offsetWidth;
                const secondColumnCells = table.querySelectorAll('.col-1');
                secondColumnCells.forEach(cell => {
                    cell.style.left = `${width}px`;
                });
            }
        });
    };

    const getSeasonForSort = (season) => {
        if (season === 'S-8') return 8.1;
        if (season === 'S8') return 8.2;
        return parseInt(season.slice(1));
    };

    const formatSeasonName = (season, isMiLR, isFcb) => {
        if (isMiLR) {
            if (season === 'S-8') return 'S8A';
            if (season === 'S8') return 'S8B';
        }
        return season;
    };

    const GLOSSARY_GROUPS = {
        "General": ["WAR", "WPA", "RE24"],
        "Batting": ["BA", "OBP", "SLG", "OPS", "ISO", "BABIP", "OPS+"],
        "Pitching": ["W", "L", "SV", "HLD", "ERA", "WHIP", "FIP", "ERA-"]
    };

    const LEADERBOARD_ONLY_STATS = {
        hitting: ['1B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO'],
        pitching: ['1B', '2B', '3B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO']
    };




    const loadData = async () => {
        try {
            const [
                hitting, pitching, players, seasons, glossary, divisions, teamHistory, 
                teamHitting, teamPitching, gamelogErrors, typeDefinitions, 
                playerInfo, awards, currentSeasonInfo,
                milrHitting, milrPitching, milrDivisions, milrTeamHistory, milrPlayerIdMap,
                milrTeamHitting, milrTeamPitching,
                fcbHitting, fcbPitching, fcbDivisions, fcbTeamHistory, fcbPlayerIdMap,
                fcbTeamHitting, fcbTeamPitching
            ] = await Promise.all([
                fetch(API.hitting).then(res => res.json()),
                fetch(API.pitching).then(res => res.json()),
                fetch(API.players).then(res => res.json()),
                fetch(API.seasons).then(res => res.json()),
                fetch(API.glossary).then(res => res.json()),
                fetch(API.divisions).then(res => res.json()),
                fetch(API.teamHistory).then(res => res.json()),
                fetch(API.teamHitting).then(res => res.json()),
                fetch(API.teamPitching).then(res => res.json()),
                fetch(API.gamelogErrors).then(res => res.json()),
                fetch(API.typeDefinitions).then(res => res.json()),
                fetch(API.playerInfo).then(res => res.json()),
                fetch(API.awards).then(res => res.json()),
                fetch(API.currentSeasonInfo).then(res => res.json()),
                fetch(API.milrHitting).then(res => res.json()),
                fetch(API.milrPitching).then(res => res.json()),
                fetch(API.milrDivisions).then(res => res.json()),
                fetch(API.milrTeamHistory).then(res => res.json()),
                fetch(API.milrPlayerIdMap).then(res => res.json()),
                fetch(API.milrTeamHitting).then(res => res.json()),
                fetch(API.milrTeamPitching).then(res => res.json()),
                fetch(API.fcbHitting).then(res => res.json()),
                fetch(API.fcbPitching).then(res => res.json()),
                fetch(API.fcbDivisions).then(res => res.json()),
                fetch(API.fcbTeamHistory).then(res => res.json()),
                fetch(API.fcbPlayerIdMap).then(res => res.json()),
                fetch(API.fcbTeamHitting).then(res => res.json()),
                fetch(API.fcbTeamPitching).then(res => res.json())
            ]);

            state.hittingStats = parseCompactData(hitting);
            state.pitchingStats = parseCompactData(pitching);
            state.teamHittingStats = parseCompactData(teamHitting);
            state.teamPitchingStats = parseCompactData(teamPitching);
            state.milrTeamHittingStats = parseCompactData(milrTeamHitting);
            state.milrTeamPitchingStats = parseCompactData(milrTeamPitching);
            state.milrHittingStats = parseCompactData(milrHitting);
            state.milrPitchingStats = parseCompactData(milrPitching);
            state.fcbHittingStats = parseCompactData(fcbHitting);
            state.fcbPitchingStats = parseCompactData(fcbPitching);
            state.fcbTeamHittingStats = parseCompactData(fcbTeamHitting);
            state.fcbTeamPitchingStats = parseCompactData(fcbTeamPitching);
            state.players = players; // Start with major league players

            // Merge MiLR players
            for (const playerId in milrPlayerIdMap) {
                const milrPlayer = milrPlayerIdMap[playerId];
                if (state.players[playerId]) {
                    // Player exists in both MLR and MiLR
                    const mlrPlayer = state.players[playerId];

                    const getMostRecentRecord = (stats, playerId) => {
                        const hittingStats = stats.hitting.filter(s => s['Hitter ID'] == parseInt(playerId) && s.Season.startsWith('S'));
                        const pitchingStats = stats.pitching.filter(s => s['Pitcher ID'] == parseInt(playerId) && s.Season.startsWith('S'));
                        const allStats = [...hittingStats, ...pitchingStats];

                        if (allStats.length === 0) {
                            return null;
                        }

                        allStats.sort((a, b) => {
                            const seasonA = getSeasonForSort(a.Season);
                            const seasonB = getSeasonForSort(b.Season);
                            if (seasonB !== seasonA) return seasonB - seasonA;
                            return (b['Last Session'] || 0) - (a['Last Session'] || 0);
                        });

                        return allStats[0];
                    };

                    const lastMlrRecord = getMostRecentRecord({ hitting: state.hittingStats, pitching: state.pitchingStats }, playerId);
                    const lastMilrRecord = getMostRecentRecord({ hitting: state.milrHittingStats, pitching: state.milrPitchingStats }, playerId);

                    if (!mlrPlayer.formerNames) {
                        mlrPlayer.formerNames = [];
                    }

                    const lastMlrSeason = lastMlrRecord ? getSeasonForSort(lastMlrRecord.Season) : -1;
                    const lastMlrSession = lastMlrRecord ? (lastMlrRecord['Last Session'] || 0) : -1;
                    const lastMilrSeason = lastMilrRecord ? getSeasonForSort(lastMilrRecord.Season) : -1;
                    const lastMilrSession = lastMilrRecord ? (lastMilrRecord['Last Session'] || 0) : -1;



                    // MiLR is more recent if its season is greater, or if seasons are same and session is greater.
                    // Tie goes to MLR.
                    if (lastMilrSeason > lastMlrSeason || (lastMilrSeason === lastMlrSeason && lastMilrSession > lastMlrSession)) {
                        if (milrPlayer.currentName !== mlrPlayer.currentName) {
                            // MiLR is more recent and name is different, so swap them
                            const oldMlrName = mlrPlayer.currentName;
                            mlrPlayer.currentName = milrPlayer.currentName;
                            if (!mlrPlayer.formerNames.includes(oldMlrName)) {
                                mlrPlayer.formerNames.push(oldMlrName);
                            }
                        }
                    } else {
                        // MLR is more recent, or it's a tie, so MLR name is kept. Add MiLR name to former names if different.
                        if (milrPlayer.currentName !== mlrPlayer.currentName) {
                            if (!mlrPlayer.formerNames.includes(milrPlayer.currentName)) {
                                mlrPlayer.formerNames.push(milrPlayer.currentName);
                            }
                        }
                    }

                    // Merge formerNames from MiLR
                    if (milrPlayer.formerNames) {
                        for (const formerName of milrPlayer.formerNames) {
                            if (formerName !== mlrPlayer.currentName && !mlrPlayer.formerNames.includes(formerName)) {
                                mlrPlayer.formerNames.push(formerName);
                            }
                        }
                    }
                } else {
                    // Player only exists in MiLR, add them as-is
                    state.players[playerId] = milrPlayer;
                }
            }

            // Merge FCB players
            for (const playerId in fcbPlayerIdMap) {
                const fcbPlayer = fcbPlayerIdMap[playerId];
                if (state.players[playerId]) {
                    // Player exists in both MLR/MiLR and FCB
                    const existingPlayer = state.players[playerId];

                    const getMostRecentRecord = (stats, playerId) => {
                        const hittingStats = stats.hitting.filter(s => s['Hitter ID'] == parseInt(playerId) && s.Season.startsWith('S'));
                        const pitchingStats = stats.pitching.filter(s => s['Pitcher ID'] == parseInt(playerId) && s.Season.startsWith('S'));
                        const allStats = [...hittingStats, ...pitchingStats];

                        if (allStats.length === 0) {
                            return null;
                        }

                        allStats.sort((a, b) => {
                            const seasonA = getSeasonForSort(a.Season);
                            const seasonB = getSeasonForSort(b.Season);
                            if (seasonB !== seasonA) return seasonB - seasonA;
                            return (b['Last Session'] || 0) - (a['Last Session'] || 0);
                        });

                        return allStats[0];
                    };

                    const lastExistingRecord = getMostRecentRecord({ hitting: [...state.hittingStats, ...state.milrHittingStats], pitching: [...state.pitchingStats, ...state.milrPitchingStats] }, playerId);
                    const lastFcbRecord = getMostRecentRecord({ hitting: state.fcbHittingStats, pitching: state.fcbPitchingStats }, playerId);

                    if (!existingPlayer.formerNames) {
                        existingPlayer.formerNames = [];
                    }

                    const lastExistingSeason = lastExistingRecord ? getSeasonForSort(lastExistingRecord.Season) : -1;
                    const lastExistingSession = lastExistingRecord ? (lastExistingRecord['Last Session'] || 0) : -1;
                    const lastFcbSeason = lastFcbRecord ? getSeasonForSort(lastFcbRecord.Season) : -1;
                    const lastFcbSession = lastFcbRecord ? (lastFcbRecord['Last Session'] || 0) : -1;

                    if (lastFcbSeason > lastExistingSeason || (lastFcbSeason === lastExistingSeason && lastFcbSession > lastExistingSession)) {
                        if (fcbPlayer.currentName !== existingPlayer.currentName) {
                            const oldName = existingPlayer.currentName;
                            existingPlayer.currentName = fcbPlayer.currentName;
                            if (!existingPlayer.formerNames.includes(oldName)) {
                                existingPlayer.formerNames.push(oldName);
                            }
                        }
                    } else {
                        if (fcbPlayer.currentName !== existingPlayer.currentName) {
                            if (!existingPlayer.formerNames.includes(fcbPlayer.currentName)) {
                                existingPlayer.formerNames.push(fcbPlayer.currentName);
                            }
                        }
                    }

                    if (fcbPlayer.formerNames) {
                        for (const formerName of fcbPlayer.formerNames) {
                            if (formerName !== existingPlayer.currentName && !existingPlayer.formerNames.includes(formerName)) {
                                existingPlayer.formerNames.push(formerName);
                            }
                        }
                    }
                } else {
                    // Player only exists in FCB, add them as-is
                    state.players[playerId] = fcbPlayer;
                }
            }

            state.seasons = seasons;
            state.glossaryData = glossary;
            state.divisions = divisions;
            state.teamHistory = teamHistory;
            state.gamelogErrors = gamelogErrors;
            state.typeDefinitions = typeDefinitions;
            state.playerInfo = playerInfo;
            state.awards = awards;
            state.currentSeasonInfo = currentSeasonInfo;
            state.milrDivisions = milrDivisions;
            state.milrTeamHistory = milrTeamHistory;
            state.fcbDivisions = fcbDivisions;
            state.fcbTeamHistory = fcbTeamHistory;

            const seasonsWithStats = new Set();
            state.hittingStats.forEach(s => {
                if (s.Season && s.Season.startsWith('S') && !s.is_sub_row) {
                    seasonsWithStats.add(s.Season);
                }
            });
            state.pitchingStats.forEach(s => {
                if (s.Season && s.Season.startsWith('S') && !s.is_sub_row) {
                    seasonsWithStats.add(s.Season);
                }
            });
            state.seasonsWithStats = Array.from(seasonsWithStats).sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1)));

            state.playerMap = new Map();
            for (const id in state.players) {
                const player = state.players[id];
                const playerId = parseInt(id);

                const addNameToMap = (name) => {
                    const lowerCaseName = name.toLowerCase();
                    if (!state.playerMap.has(lowerCaseName)) {
                        state.playerMap.set(lowerCaseName, []);
                    }
                    const ids = state.playerMap.get(lowerCaseName);
                    if (!ids.includes(playerId)) {
                        ids.push(playerId);
                    }
                };

                addNameToMap(player.currentName);
                if (player.formerNames) {
                    player.formerNames.forEach(addNameToMap);
                }
            }

            elements.loader.style.display = 'none';
            elements.app.style.display = 'block';
            initializeApp();
        } catch (error) {
            console.error("Failed to load data:", error);
            elements.loader.innerHTML = "<p>Failed to load data. Please refresh the page.</p>";
        }
    };

    const seededRandom = (seed) => {
        return function() {
          var t = seed += 0x6D2B79F5;
          t = Math.imul(t ^ t >>> 15, t | 1);
          t ^= t + Math.imul(t ^ t >>> 7, t | 61);
          return ((t ^ t >>> 14) >>> 0) / 4294967296;
        }
    };

    const getFeaturedEntities = () => {
        const today = new Date();
        const seed = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate();
        const random = seededRandom(seed);

        const playerIds = Object.keys(state.players);
        
        // Select two distinct random players
        let randomIndex1 = Math.floor(random() * playerIds.length);
        let randomIndex2 = Math.floor(random() * playerIds.length);
        while (randomIndex1 === randomIndex2) { // Ensure distinct players
            randomIndex2 = Math.floor(random() * playerIds.length);
        }
        let featuredPlayerId1 = playerIds[randomIndex1];
        let featuredPlayerId2 = playerIds[randomIndex2];

        // --- Process Player 1 ---
        const playerHittingStats1 = state.hittingStats.filter(s => s['Hitter ID'] === parseInt(featuredPlayerId1));
        const playerPitchingStats1 = state.pitchingStats.filter(s => s['Pitcher ID'] === parseInt(featuredPlayerId1));
        const allPlayerStats1 = [...playerHittingStats1, ...playerPitchingStats1];

        let firstSeason1 = Infinity;
        let lastSeason1 = -Infinity;
        let mostRecentTeamAbbr1 = '';
        let mostRecentSeasonForPlayer1 = '';

        if (allPlayerStats1.length > 0) {
            for (const stat of allPlayerStats1) {
                if (stat.Season && stat.Season.startsWith('S')) {
                    const seasonNum = parseInt(stat.Season.slice(1));
                    if (!isNaN(seasonNum)) {
                        firstSeason1 = Math.min(firstSeason1, seasonNum);
                        lastSeason1 = Math.max(lastSeason1, seasonNum);
                    }
                }
            }
            const lastSeasonStats1 = allPlayerStats1
                .filter(s => s.Season && s.Season.startsWith('S') && !s.is_sub_row)
                .sort((a, b) => parseInt(b.Season.slice(1)) - parseInt(a.Season.slice(1)))[0];
            
            if (lastSeasonStats1) {
                mostRecentTeamAbbr1 = lastSeasonStats1['Last Team'] || lastSeasonStats1['Team'];
                mostRecentSeasonForPlayer1 = lastSeasonStats1.Season;
            }
        }
        const featuredPlayerSeasonRange1 = (firstSeason1 === Infinity || lastSeason1 === -Infinity) ? 'N/A' : (firstSeason1 === lastSeason1 ? `S${firstSeason1}` : `S${firstSeason1}-S${lastSeason1}`);
        const featuredPlayerMostRecentTeamKey1 = mostRecentTeamAbbr1 ? getFranchiseKeyFromAbbr(mostRecentTeamAbbr1, mostRecentSeasonForPlayer1) : '';
        const featuredPlayerMostRecentSeason1 = mostRecentSeasonForPlayer1;

        // --- Process Player 2 ---
        const playerHittingStats2 = state.hittingStats.filter(s => s['Hitter ID'] === parseInt(featuredPlayerId2));
        const playerPitchingStats2 = state.pitchingStats.filter(s => s['Pitcher ID'] === parseInt(featuredPlayerId2));
        const allPlayerStats2 = [...playerHittingStats2, ...playerPitchingStats2];

        let firstSeason2 = Infinity;
        let lastSeason2 = -Infinity;
        let mostRecentTeamAbbr2 = '';
        let mostRecentSeasonForPlayer2 = '';

        if (allPlayerStats2.length > 0) {
            for (const stat of allPlayerStats2) {
                if (stat.Season && stat.Season.startsWith('S')) {
                    const seasonNum = parseInt(stat.Season.slice(1));
                    if (!isNaN(seasonNum)) {
                        firstSeason2 = Math.min(firstSeason2, seasonNum);
                        lastSeason2 = Math.max(lastSeason2, seasonNum);
                    }
                }
            }
            const lastSeasonStats2 = allPlayerStats2
                .filter(s => s.Season && s.Season.startsWith('S') && !s.is_sub_row)
                .sort((a, b) => parseInt(b.Season.slice(1)) - parseInt(a.Season.slice(1)))[0];
            
            if (lastSeasonStats2) {
                mostRecentTeamAbbr2 = lastSeasonStats2['Last Team'] || lastSeasonStats2['Team'];
                mostRecentSeasonForPlayer2 = lastSeasonStats2.Season;
            }
        }
        const featuredPlayerSeasonRange2 = (firstSeason2 === Infinity || lastSeason2 === -Infinity) ? 'N/A' : (firstSeason2 === lastSeason2 ? `S${firstSeason2}` : `S${firstSeason2}-S${lastSeason2}`);
        const featuredPlayerMostRecentTeamKey2 = mostRecentTeamAbbr2 ? getFranchiseKeyFromAbbr(mostRecentTeamAbbr2, mostRecentSeasonForPlayer2) : '';
        const featuredPlayerMostRecentSeason2 = mostRecentSeasonForPlayer2;


        // --- Select a random team franchise and a valid season for it ---
        const teamKeys = Object.keys(state.teamHistory);
        const featuredTeamKey = teamKeys[Math.floor(random() * teamKeys.length)];
        const franchiseEntries = state.teamHistory[featuredTeamKey];
        let featuredTeamSeason = 'S1';

        if (franchiseEntries && franchiseEntries.length > 0) {
            const possibleSeasons = [];
            for (const entry of franchiseEntries) {
                for (let s = entry.start; s <= (entry.end === 9999 ? parseInt([...state.seasonsWithStats].sort((a,b)=>parseInt(b.slice(1))-parseInt(a.slice(1)))[0].slice(1)) : entry.end); s++) {
                    possibleSeasons.push(`S${s}`);
                }
            }
            if (possibleSeasons.length > 0) {
                featuredTeamSeason = possibleSeasons[Math.floor(random() * possibleSeasons.length)];
            }
        }

        return {
            featuredPlayerId1: parseInt(featuredPlayerId1),
            featuredPlayerSeasonRange1: featuredPlayerSeasonRange1,
            featuredPlayerMostRecentTeamKey1: featuredPlayerMostRecentTeamKey1,
            featuredPlayerMostRecentSeason1: featuredPlayerMostRecentSeason1,

            featuredPlayerId2: parseInt(featuredPlayerId2),
            featuredPlayerSeasonRange2: featuredPlayerSeasonRange2,
            featuredPlayerMostRecentTeamKey2: featuredPlayerMostRecentTeamKey2,
            featuredPlayerMostRecentSeason2: featuredPlayerMostRecentSeason2,

            featuredTeamKey: featuredTeamKey,
            featuredTeamSeason: featuredTeamSeason
        };
    };

    const updateView = () => {
        window.scrollTo(0, 0);
        const path = window.location.hash || '#/home';

        // Reset all views and tabs
        elements.homeView.style.display = 'none';
        elements.statsView.style.display = 'none';
        elements.leaderboardsView.style.display = 'none';
        elements.glossaryView.style.display = 'none';
        elements.teamStatsView.style.display = 'none';
        elements.awardsView.style.display = 'none';
        elements.hofView.style.display = 'none';

        elements.homeTab.classList.remove('active');
        elements.statsTab.classList.remove('active');
        elements.teamStatsTab.classList.remove('active');
        elements.leaderboardsTab.classList.remove('active');
        elements.glossaryTab.classList.remove('active');

        // Parse URL parameters once if it's a team stats path
        let isTeamStatsPath = path.startsWith('#/team-stats');
        let seasonParam = null;
        let teamParam = null;
        let leagueParam = null;

        if (isTeamStatsPath) {
            const url = new URL('http://dummy.com/' + path.substring(1));
            seasonParam = url.searchParams.get('season');
            teamParam = url.searchParams.get('team');
            leagueParam = url.searchParams.get('league');
        }

        if (path === '#/home') {
            elements.homeView.style.display = 'block';
            elements.homeTab.classList.add('active');
            renderHome();
        } else if (path === '#/gamelog-errors') {
            elements.homeView.style.display = 'block';
            renderGamelogErrors();
        } else if (isTeamStatsPath && teamParam) { // Specific team page (has 'team' parameter)
            // This branch handles #/team-stats?season=S11&team=ATL
            displayTeamStatsPage(decodeURIComponent(teamParam), seasonParam, leagueParam === 'milr', leagueParam === 'fcb');
            elements.teamStatsView.style.display = 'block';
            elements.teamStatsTab.classList.add('active');
        } else if (isTeamStatsPath) { // Team list page (might have 'season' but no 'team')
            // This branch handles #/team-stats or #/team-stats?season=S10
            displayTeamList(seasonParam, leagueParam === 'milr', leagueParam === 'fcb');
            elements.teamStatsView.style.display = 'block';
            elements.teamStatsTab.classList.add('active');
        } else if (path === '#/stats') {
            const isStats = path === '#/stats';
            elements.statsView.style.display = 'block';
            elements.statsTab.classList.toggle('active', isStats);
            if (state.currentPlayerId) {
                displayPlayerPage(state.currentPlayerId);
            } else {
                elements.statsContentDisplay.innerHTML = '<p>Search for a player to see their stats.</p>';
            }
        } else if (path === '#/leaderboards') {
            elements.leaderboardsView.style.display = 'block';
            elements.leaderboardsTab.classList.add('active');
            if (elements.leaderboardStatSelect.options.length <= 1) {
                populateLeaderboardStatSelect();
            }
        } else if (path.startsWith('#/awards')) {
            elements.awardsView.style.display = 'block';
            renderAwards();
        } else if (path === '#/hof') {
            elements.hofView.style.display = 'block';
            renderHofPage();
        } else if (path === '#/glossary') {
            elements.glossaryView.style.display = 'flex';
            elements.glossaryTab.classList.add('active');
            renderGlossary();
        } else {
            // Default to home page if hash is invalid or empty
            window.location.hash = '#/home';
        }
    };

    const hasAwards = (seasonAwards) => {
        if (!seasonAwards) return false;
        if (seasonAwards.PCMVP && seasonAwards.PCMVP.length > 0) return true;
        for (const league of ['AL', 'NL']) {
            if (seasonAwards[league]) {
                for (const award in seasonAwards[league]) {
                    if (seasonAwards[league][award] && seasonAwards[league][award].length > 0) return true;
                }
            }
        }
        return false;
    };

    const getPlayerTeamInfoForSeason = (playerId, season) => {
        const playerHittingStats = state.hittingStats.filter(s => s['Hitter ID'] === playerId && s.Season === season && !s.is_sub_row);
        const playerPitchingStats = state.pitchingStats.filter(s => s['Pitcher ID'] === playerId && s.Season === season && !s.is_sub_row);
        const allStats = [...playerHittingStats, ...playerPitchingStats];
        
        let teamAbbr = '';
        if (allStats.length > 0) {
            teamAbbr = allStats[0]['Last Team'] || allStats[0].Team;
        }
        
        const franchiseKey = getFranchiseKeyFromAbbr(teamAbbr, season);
        const logo = getTeamLogoBySeason(franchiseKey, season);
        
        return { teamAbbr, franchiseKey, logo };
    };

    const renderAwards = () => {
        const awardsView = elements.awardsView;
        const seasonsWithAwards = Object.keys(state.awards).filter(key => key.startsWith('S') && hasAwards(state.awards[key]));
        const seasons = seasonsWithAwards.sort((a, b) => parseInt(b.slice(1)) - parseInt(a.slice(1)));

        const awardsData = state.awards;
        const metadata = awardsData._metadata || {};

        let selectedSeason = seasons.length > 0 ? seasons[0] : null;
        const urlParams = new URLSearchParams(window.location.hash.split('?')[1]);
        if (urlParams.has('season') && seasons.includes(urlParams.get('season'))) {
            selectedSeason = urlParams.get('season');
        }

        const currentSeasonIndex = seasons.indexOf(selectedSeason);
        const nextSeason = currentSeasonIndex > 0 ? seasons[currentSeasonIndex - 1] : null;
        const prevSeason = currentSeasonIndex < seasons.length - 1 ? seasons[currentSeasonIndex + 1] : null;

        let content = `<div class="awards-header team-stats-header">
                        <h2 class="section-title">Awards - `;
        if (seasons.length > 0) {
            content += `<select id="awards-season-select" class="title-season-select">`;
            seasons.forEach(season => {
                content += `<option value="${season}" ${season === selectedSeason ? 'selected' : ''}>${season.replace('S', 'Season ')}</option>`;
            });
            content += `</select>`;
        }
        content += `</h2>
                    <div class="season-nav-buttons">`;
        if (prevSeason) {
            content += `<a href="#/awards?season=${prevSeason}" class="season-nav-button">&lt; Prev Season</a>`;
        }
        if (nextSeason) {
            content += `<a href="#/awards?season=${nextSeason}" class="season-nav-button">Next Season &gt;</a>`;
        }
        content += `</div></div>`;

        if (!selectedSeason) {
            content += '<p>No awards data available for any season.</p>';
            awardsView.innerHTML = content;
            return;
        }

        const seasonAwards = awardsData[selectedSeason];
        if (!hasAwards(seasonAwards)) {
            content += '<p>No awards data available for this season.</p>';
        } else {
            content += '<div class="awards-container">';
        
            content += `<div class="league-toggle-buttons">
                            <button class="league-toggle-button active" data-league="al">American League</button>
                            <button class="league-toggle-button" data-league="nl">National League</button>
                        </div>`;
            content += '<div class="leagues-wrapper">';
            ['AL', 'NL'].forEach(league => {
                const leagueName = league === 'AL' ? 'American League' : 'National League';
                content += `<div class="league-column league-${league.toLowerCase()}">`;
                content += `<h3 class="league-title">${leagueName} Awards</h3>`;
                const leagueAwards = seasonAwards[league];

                if (leagueAwards) {
                    const majorAwards = [
                        ['MVP', 'CYA'],
                        ['ROTY', 'RPOTY'],
                        ['BT', 'ERAT'],
                        ['GMOTY']
                    ];
                    const silverSluggers = 'SS';
                    const allStars = 'AS';

                    content += '<div class="awards-sub-section">';
                    content += '<div class="awards-major-section">';
                    majorAwards.forEach(row => {
                        content += '<div class="awards-major-row">';
                        row.forEach(awardKey => {
                            if (leagueAwards[awardKey] && leagueAwards[awardKey].length > 0) {
                                content += `<div class="award-category">
                                                <h4>${metadata[awardKey] || awardKey}</h4>
                                                <div class="award-winners-list">`;
                                if (awardKey === 'GMOTY' && leagueAwards[awardKey].length > 1) {
                                    const playerIds = leagueAwards[awardKey];
                                    const firstPlayerId = playerIds[0];
                                    const { logo } = getPlayerTeamInfoForSeason(firstPlayerId, selectedSeason);
                                    
                                    const playerLinks = playerIds.map(id => {
                                        const player = state.players[id];
                                        return `<a href="#/stats" class="player-link" data-player-id="${id}">${player.currentName}</a>`;
                                    });

                                    content += `<div class="award-winner-item">
                                                    ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                    ${playerLinks.join(' & ')}
                                                </div>`;
                                } else {
                                    leagueAwards[awardKey].forEach(playerId => {
                                        const player = state.players[playerId];
                                        if (player) {
                                            const { logo } = getPlayerTeamInfoForSeason(playerId, selectedSeason);
                                            content += `<div class="award-winner-item">
                                                            ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                            <a href="#/stats" class="player-link" data-player-id="${playerId}">${player.currentName}</a>
                                                        </div>`;
                                        }
                                    });
                                }
                                content += `</div></div>`;
                            }
                        });
                        content += '</div>';
                    });
                    content += '</div>';
                    content += '</div>';

                    if (leagueAwards[silverSluggers] && typeof leagueAwards[silverSluggers] === 'object' && Object.keys(leagueAwards[silverSluggers]).length > 0) {
                        content += `<h4 class="awards-sub-title">${leagueName} Silver Sluggers</h4>`;
                        content += '<div class="awards-sub-section">';
                        content += `<div class="award-category">`;

                        const ssAwards = leagueAwards[silverSluggers];
                        const col1_positions = ['C', '1B', '2B', '3B', 'DH'];
                        const col2_positions = ['SS', 'LF', 'CF', 'RF', 'OF', 'P'];

                        const renderColumn = (positions) => {
                            let colContent = '';
                            positions.forEach(position => {
                                if (ssAwards[position]) {
                                    const playerIds = Array.isArray(ssAwards[position]) ? ssAwards[position] : [ssAwards[position]];
                                    
                                    if (position === 'OF' && playerIds.length > 1) {
                                        playerIds.forEach(playerId => {
                                            const player = state.players[playerId];
                                            if (player) {
                                                const { logo } = getPlayerTeamInfoForSeason(playerId, selectedSeason);
                                                colContent += `
                                                    <div class="award-winner-item-pos">
                                                        <span class="award-position-label">${position}</span>
                                                        <div class="award-player-info-pos">
                                                            <div class="award-player-item-pos">
                                                                ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                                <a href="#/stats" class="player-link" data-player-id="${playerId}">${player.currentName}</a>
                                                            </div>
                                                        </div>
                                                    </div>
                                                `;
                                            }
                                        });
                                    } else {
                                        colContent += `<div class="award-winner-item-pos">
                                                        <span class="award-position-label">${position}</span>
                                                        <div class="award-player-info-pos">`;

                                        playerIds.forEach((playerId, index) => {
                                            const player = state.players[playerId];
                                            if (player) {
                                                const { logo } = getPlayerTeamInfoForSeason(playerId, selectedSeason);

                                                colContent += `
                                                    <div class="award-player-item-pos">
                                                        ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                        <a href="#/stats" class="player-link" data-player-id="${playerId}">${player.currentName}</a>
                                                    </div>
                                                `;
                                            }
                                        });
                                        colContent += `</div></div>`;
                                    }
                                }
                            });
                            return colContent;
                        }
                        
                        const col1_content = renderColumn(col1_positions);
                        const col2_content = renderColumn(col2_positions);

                        content += `<div class="ss-winners-list">`;
                        if (col1_content) {
                            content += `<div class="ss-winners-col">${col1_content}</div>`;
                        }
                        if (col2_content) {
                            content += `<div class="ss-winners-col">${col2_content}</div>`;
                        }
                        content += `</div>`; // end ss-winners-list

                        content += `</div></div>`;
                    }

                    if (leagueAwards[allStars] && typeof leagueAwards[allStars] === 'object' && Object.keys(leagueAwards[allStars]).length > 0) {
                        content += `<h4 class="awards-sub-title">${leagueName} All-Star Team</h4>`;
                        content += '<div class="awards-sub-section">';
                        content += `<div class="award-category">
                                        <div class="all-star-team">`;

                        const asAwards = leagueAwards[allStars];
                        const startersOrder = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'DH'];

                        // GMs
                        if (asAwards.GM && asAwards.GM.length > 0) {
                            content += `<div class="as-section as-gms">
                                            <h5>General Manager</h5>
                                            <div class="as-gm-list">`;
                            if (asAwards.GM.length > 1) {
                                // Multiple GMs
                                const playerIds = asAwards.GM;

                                                                    const playerInfos = playerIds.map(id => {
                                                                    const player = state.players[id];
                                                                    if (!player) return null;
                                
                                                                    const { logo } = getPlayerTeamInfoForSeason(id, selectedSeason);
                                                                    
                                                                    return {
                                                                        id: id,
                                                                        name: player.currentName,
                                                                        logo: logo
                                                                    };
                                                                }).filter(Boolean);
                                const firstLogo = playerInfos.length > 0 ? playerInfos[0].logo : null;
                                const allLogosSame = playerInfos.every(p => p.logo === firstLogo);

                                if (allLogosSame) {
                                    const playerLinks = playerInfos.map(p => `<a href="#/stats" class="player-link" data-player-id="${p.id}">${p.name}</a>`);
                                    content += `<div class="award-winner-item">
                                                    ${firstLogo ? `<img src="${firstLogo}" class="award-team-logo">` : ''}
                                                    ${playerLinks.join(' & ')}
                                                </div>`;
                                } else {
                                    const joinedPlayerHtml = playerInfos.map(p => 
                                        `<span class="award-winner-item" style="display: inline-flex;">${p.logo ? `<img src="${p.logo}" class="award-team-logo">` : ''}<a href="#/stats" class="player-link" data-player-id="${p.id}">${p.name}</a></span>`
                                    ).join(' & ');

                                    content += `<div class="award-winner-item">${joinedPlayerHtml}</div>`;
                                }
                            } else {
                                // Single GM
                                const playerId = asAwards.GM[0];
                                const player = state.players[playerId];
                                if (player) {
                                    const { logo } = getPlayerTeamInfoForSeason(playerId, selectedSeason);
                                    content += `<div class="award-winner-item">
                                                    ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                    <a href="#/stats" class="player-link" data-player-id="${playerId}">${player.currentName}</a>
                                                </div>`;
                                }
                            }
                            content += `</div></div>`;
                        }

                        // Starters and Pitchers
                        content += `<div class="as-main-roster">`;

                        // Starters (left column)
                        content += `<div class="as-section as-starters">
                                        <h5>Starting Lineup</h5>
                                        <div class="as-player-list">`;
                        startersOrder.forEach(position => {
                            if (asAwards[position]) {
                                const playerIds = Array.isArray(asAwards[position]) ? asAwards[position] : [asAwards[position]];
                                playerIds.forEach(playerId => {
                                    const player = state.players[playerId];
                                    if (player) {
                                        const { logo } = getPlayerTeamInfoForSeason(playerId, selectedSeason);
                                        content += `<div class="award-winner-item">
                                                        <span class="award-position-label">${position}</span>
                                                        ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                        <a href="#/stats" class="player-link" data-player-id="${playerId}">${player.currentName}</a>
                                                    </div>`;
                                    }
                                });
                            }
                        });
                        content += `</div></div>`;
                        
                        // Pitchers (right column)
                        if (asAwards.P && asAwards.P.length > 0) {
                            content += `<div class="as-section as-pitchers">
                                            <h5>Pitchers</h5>
                                            <div class="as-player-list">`;
                            asAwards.P.forEach(playerId => {
                                const player = state.players[playerId];
                                if (player) {
                                    const { logo } = getPlayerTeamInfoForSeason(playerId, selectedSeason);
                                    content += `<div class="award-winner-item">
                                                    ${logo ? `<img src="${logo}" class="award-team-logo">` : ''}
                                                    <a href="#/stats" class="player-link" data-player-id="${playerId}">${player.currentName}</a>
                                                </div>`;
                                }
                            });
                            content += `</div></div>`;
                        }

                        content += `</div>`; // end as-main-roster

                        // Reserves
                        if (asAwards.R && asAwards.R.length > 0) {
                            content += `<div class="as-section as-reserves">
                                            <h5>Reserves</h5>`;
                            
                            const reservesData = asAwards.R.map(playerId => {
                                const player = state.players[playerId];
                                if (!player) return null;

                                const playerHittingStats = state.hittingStats.filter(s => s['Hitter ID'] === playerId && s.Season === selectedSeason && !s.is_sub_row);
                                const playerPitchingStats = state.pitchingStats.filter(s => s['Pitcher ID'] === playerId && s.Season === selectedSeason && !s.is_sub_row);
                                const allPlayerSeasonStats = [...playerHittingStats, ...playerPitchingStats];
                                
                                let teamAbbr = '';
                                if (allPlayerSeasonStats.length > 0) {
                                    teamAbbr = allPlayerSeasonStats[0]['Last Team'] || allPlayerSeasonStats[0].Team;
                                }

                                const franchiseKey = getFranchiseKeyFromAbbr(teamAbbr, selectedSeason);
                                const logo = getTeamLogoBySeason(franchiseKey, selectedSeason);

                                return {
                                    playerId: playerId,
                                    playerName: player.currentName,
                                    teamAbbr: teamAbbr,
                                    logo: logo
                                };
                            }).filter(Boolean);

                            reservesData.sort((a, b) => {
                                if (a.teamAbbr < b.teamAbbr) return -1;
                                if (a.teamAbbr > b.teamAbbr) return 1;
                                if (a.playerName < b.playerName) return -1;
                                if (a.playerName > b.playerName) return 1;
                                return 0;
                            });

                            const midpoint = Math.ceil(reservesData.length / 2);
                            const col1 = reservesData.slice(0, midpoint);
                            const col2 = reservesData.slice(midpoint);

                            content += `<div class="as-reserves-list">`;
                            content += `<div class="as-reserves-col">`;
                            col1.forEach(reserve => {
                                content += `<div class="award-winner-item">
                                                ${reserve.logo ? `<img src="${reserve.logo}" class="award-team-logo">` : ''}
                                                <a href="#/stats" class="player-link" data-player-id="${reserve.playerId}">${reserve.playerName}</a>
                                            </div>`;
                            });
                            content += `</div>`; // end col1

                            if (col2.length > 0) {
                                content += `<div class="as-reserves-col">`;
                                col2.forEach(reserve => {
                                    content += `<div class="award-winner-item">
                                                    ${reserve.logo ? `<img src="${reserve.logo}" class="award-team-logo">` : ''}
                                                    <a href="#/stats" class="player-link" data-player-id="${reserve.playerId}">${reserve.playerName}</a>
                                                </div>`;
                                });
                                content += `</div>`; // end col2
                            }
                            content += `</div></div>`;
                        }

                        content += `</div></div>`;
                        content += `</div>`;
                    }
                }
                content += `</div>`; // end league-column
            });
            content += '</div>'; // end leagues-wrapper
            content += '</div>'; // end awards-container
        }

        awardsView.innerHTML = content;

        const wrapper = awardsView.querySelector('.leagues-wrapper');
        const toggleButtons = awardsView.querySelector('.league-toggle-buttons');

        const setLeagueView = (league) => {
            if (wrapper) {
                wrapper.classList.remove('show-al', 'show-nl');
                wrapper.classList.add(`show-${league}`);
            }
            if (toggleButtons) {
                const currentActive = toggleButtons.querySelector('.active');
                if (currentActive) currentActive.classList.remove('active');
                const newActive = toggleButtons.querySelector(`[data-league=${league}]`);
                if (newActive) newActive.classList.add('active');
            }
            localStorage.setItem('awardsSelectedLeague', league);
        };

        const savedLeague = localStorage.getItem('awardsSelectedLeague');
        const urlLeague = new URLSearchParams(window.location.hash.split('?')[1]).get('league');

        if (urlLeague && ['al', 'nl'].includes(urlLeague)) {
            setLeagueView(urlLeague);
        } else if (savedLeague && ['al', 'nl'].includes(savedLeague)) {
            setLeagueView(savedLeague);
        } else {
            setLeagueView('al'); // Default to AL
        }

        if (toggleButtons) {
            toggleButtons.addEventListener('click', (event) => {
                const button = event.target.closest('.league-toggle-button');
                if (!button) return;

                const league = button.dataset.league;
                if (!league) return;
                
                setLeagueView(league);
            });
        }

        if (seasons.length > 0) {
            document.getElementById('awards-season-select').addEventListener('change', (event) => {
                const newSeason = event.target.value;
                window.location.hash = `#/awards?season=${newSeason}`;
            });
        }
    };

    const renderHofPage = () => {
        const hofView = elements.hofView;
        const awardsData = state.awards;
    
        let content = `<div class="hof-page-container">
                        <h2 class="section-title">Hall of Fame</h2>
                        <p class="hof-note"><em>* denotes active player</em></p>`;
    
        if (!awardsData.HOF || awardsData.HOF.length === 0) {
            content += '<p>No players have been inducted into the Hall of Fame.</p>';
            content += '</div>';
            hofView.innerHTML = content;
            return;
        }
    
        const hofPlayers = awardsData.HOF.map(playerId => {
            return { id: playerId, data: state.players[playerId] };
        }).filter(p => p.data);
    
        hofPlayers.sort((a, b) => a.data.currentName.localeCompare(b.data.currentName));
        
        content += '<div class="hof-grid">';
    
        const currentSeason = state.currentSeasonInfo.season;
        const currentSession = state.currentSeasonInfo.session;
        const prevSeason = 'S' + (parseInt(currentSeason.slice(1)) - 1);
        const isActiveThreshold = 5;
    
        hofPlayers.forEach(p => {
            const playerId = p.id;
            const player = p.data;
            
            const playerHittingStats = state.hittingStats.filter(s => s['Hitter ID'] === playerId && s.Season.startsWith('S') && !s.is_sub_row);
            const playerPitchingStats = state.pitchingStats.filter(s => s['Pitcher ID'] === playerId && s.Season.startsWith('S') && !s.is_sub_row);
            const allStats = [...playerHittingStats, ...playerPitchingStats];
            
            let isActive = allStats.some(s => s.Season === currentSeason);
            if (!isActive && currentSession < isActiveThreshold) {
                isActive = allStats.some(s => s.Season === prevSeason);
            }

            const latestStats = allStats.sort((a, b) => parseInt(b.Season.slice(1)) - parseInt(a.Season.slice(1)));

            let logo = '';
            if (latestStats.length > 0) {
                const mostRecentStat = latestStats[0];
                const mostRecentSeason = mostRecentStat.Season;
                const mostRecentTeam = mostRecentStat['Last Team'] || mostRecentStat.Team;
                
                const franchiseKey = getFranchiseKeyFromAbbr(mostRecentTeam, mostRecentSeason);
                logo = getTeamLogoBySeason(franchiseKey, mostRecentSeason);
            }
            
            content += `<div class="hof-player-card">
                            <a href="#/stats" class="player-link" data-player-id="${playerId}">
                                <div class="hof-player-logo-container">
                                    ${logo ? `<img src="${logo}" alt="${player.currentName} team logo">` : '<div class="hof-placeholder-logo"></div>'}
                                </div>
                                <p>${player.currentName}${isActive ? '*' : ''}</p>
                            </a>
                        </div>`;
        });
    
        content += '</div></div>';
    
        hofView.innerHTML = content;
    };

    const renderHome = () => {
        const { 
            featuredPlayerId1, featuredPlayerSeasonRange1, featuredPlayerMostRecentTeamKey1, featuredPlayerMostRecentSeason1,
            featuredPlayerId2, featuredPlayerSeasonRange2, featuredPlayerMostRecentTeamKey2, featuredPlayerMostRecentSeason2,
            featuredTeamKey, featuredTeamSeason 
        } = getFeaturedEntities();

        const featuredPlayer1 = state.players[featuredPlayerId1];
        const featuredPlayer2 = state.players[featuredPlayerId2];

        const featuredTeamName = getTeamNameBySeason(featuredTeamKey, featuredTeamSeason);
        const featuredTeamLogo = getTeamLogoBySeason(featuredTeamKey, featuredTeamSeason);

        const playerMostRecentTeamLogo1 = getTeamLogoBySeason(featuredPlayerMostRecentTeamKey1, featuredPlayerMostRecentSeason1);
        const playerMostRecentTeamLogo2 = getTeamLogoBySeason(featuredPlayerMostRecentTeamKey2, featuredPlayerMostRecentSeason2);

        let awardsLink = '';
        if (Object.keys(state.awards).some(key => key.startsWith('S') && hasAwards(state.awards[key]))) {
            awardsLink = `<li><a href="#/awards"><strong>Awards:</strong></a> Season-by-season award winners.</li>`;
        }
        let hofLink = '';
        if (state.awards.HOF && state.awards.HOF.length > 0) {
            hofLink = `<li><a href="#/hof"><strong>Hall of Fame:</strong></a> View the members of the Hall of Fame.</li>`;
        }

        elements.homeView.innerHTML = `
            <div class="welcome-container">
                <h2 class="section-title">Welcome to MLR Reference!</h2>
                <p>MLR Reference is your (unofficial) guide to all regular season stats for Major League Redditball (MLR).</p>
                <p>Here you can find:</p>
                <ul>
                    <li><a href="#/stats"><strong>Player Stats:</strong></a> Detailed batting and pitching statistics for every player in MLR history. Players can be searched by name (including former names) or player ID.</li>
                    <li><a href="#/team-stats"><strong>Team Stats:</strong></a> Season-by-season standings and team statistics.</li>
                    <li><a href="#/leaderboards"><strong>Leaderboards:</strong></a> All-time and single-season leaderboards for a variety of stats.</li>
                    ${awardsLink}
                    ${hofLink}
                    <li><a href="#/glossary"><strong>Glossary:</strong></a> Definitions and equations for advanced and calculated stats.</li>
                    <li><a href="#/gamelog-errors"><strong>Known Gamelog Errors:</strong></a> A list of known errors in the gamelogs. All these errors have been corrected for this app.</li>
                    <li><a href="https://forms.gle/nmLNL5PbF6bXrXpo9" target="_blank"><strong>Feedback:</strong></a> Have a suggestion or found a bug? Let me know!</li>
                </ul>
                <br>
                <p>Potential future features:</p>
                <ul>
                    <li> Box scores for each game.</li>
                    <li> Postseason stats.</li>
                    <li> Player comparison.</li>
                    <li> Outcome calculator.</li>
                </ul>

                <h3 class="section-title">Today's Features</h3>
                <div class="featured-section">
                    <div class="featured-item">
                        <h4>Featured Player</h4>
                        <a href="#/stats" class="player-link" data-player-id="${featuredPlayerId1}">
                            ${playerMostRecentTeamLogo1 ? `<img src="${playerMostRecentTeamLogo1}" alt="${featuredPlayer1.currentName} team logo" class="team-list-logo">` : ''}
                            <p>${featuredPlayer1 ? featuredPlayer1.currentName : 'N/A'}</p>
                            <p class="featured-player-season-range">${featuredPlayerSeasonRange1}</p>
                        </a>
                    </div>
                    <div class="featured-item">
                        <h4>Featured Player</h4>
                        <a href="#/stats" class="player-link" data-player-id="${featuredPlayerId2}">
                            ${playerMostRecentTeamLogo2 ? `<img src="${playerMostRecentTeamLogo2}" alt="${featuredPlayer2.currentName} team logo" class="team-list-logo">` : ''}
                            <p>${featuredPlayer2 ? featuredPlayer2.currentName : 'N/A'}</p>
                            <p class="featured-player-season-range">${featuredPlayerSeasonRange2}</p>
                        </a>
                    </div>
                    <div class="featured-item">
                        <h4>Featured Team</h4>
                        <a href="#/team-stats?season=${featuredTeamSeason}&team=${featuredTeamKey}">
                            ${featuredTeamLogo ? `<img src="${featuredTeamLogo}" alt="${featuredTeamName} logo" class="team-list-logo">` : ''}
                            <p>${featuredTeamSeason} ${featuredTeamName || 'N/A'}</p>
                        </a>
                    </div>
                    <div class="featured-item action-item">
                        <h4>Discover More!</h4>
                        <button id="random-player-button" class="action-button">Random Player</button>
                    </div>
                </div>
                <br>

                <h3 class="section-title">Frequently Asked Questions</h3>
                <p>Why is my WAR different than it appears in the roster sheet?</p>
                <p><i>Like any good baseball statistics site, MLR Reference has its own WAR formula. MLR Reference WAR (also known as "cheWAR") is calculated using RE24. More information about WAR calculation can be found in the glossary.</i></p>
                <br>
                <p>Why do my franchise total stat lines include teams I've never played for?</p>
                <p><i>The franchise total stat lines use the abbreviations that are currently used by the franchise. For example, S2-S5 Texas Rangers has been Cleveland Guardians since S6, so even players who only played during the TEX era will have CLE in their franchise totals.</i></p>
            </div>
        `;
    };

    const renderGlossary = () => {
        const sidebar = document.getElementById('glossary-sidebar');
        const content = document.getElementById('glossary-content');
        
        sidebar.innerHTML = '';
        content.innerHTML = '<p>Select a stat from the sidebar to view its definition.</p>';

        for (const groupName in GLOSSARY_GROUPS) {
            const groupHeader = document.createElement('h4');
            groupHeader.className = 'glossary-group-header';
            groupHeader.innerHTML = `<span class="arrow">&#9658;</span> ${groupName}`;
            sidebar.appendChild(groupHeader);
    
            const statList = document.createElement('ul');
            statList.className = 'glossary-stat-list collapsed';

            groupHeader.addEventListener('click', () => {
                groupHeader.classList.toggle('expanded');
                statList.classList.toggle('collapsed');
            });
    
            const statsInGroup = GLOSSARY_GROUPS[groupName];
            statsInGroup.forEach(stat => {
                if (state.glossaryData[stat]) {
                    const statItem = document.createElement('li');
                    statItem.textContent = `${stat} - ${state.glossaryData[stat].name}`;
                    statItem.dataset.stat = stat;
                    statItem.addEventListener('click', (e) => {
                        e.stopPropagation(); // Prevent group from collapsing when item is clicked
                        displayGlossaryEntry(stat);
                        document.querySelectorAll('#glossary-sidebar li').forEach(item => item.classList.remove('active'));
                        statItem.classList.add('active');
                    });
                    statList.appendChild(statItem);
                }
            });
            sidebar.appendChild(statList);
        }
    };

    const displayGlossaryEntry = (stat) => {
        const content = document.getElementById('glossary-content');
        const entry = state.glossaryData[stat];
        if (!entry) {
            content.innerHTML = '<p>Select a stat from the sidebar.</p>';
            return;
        }

        let entryHTML = `<h2 class="section-title">${stat} - ${entry.name}</h2>`;
        entryHTML += `<p>${entry.definition}</p>`;

        if (entry.conditional_rules) {
            entryHTML += '<h4>Conditional Rules:</h4>';
            entryHTML += '<ul>';
            entry.conditional_rules.forEach(rule => {
                entryHTML += `<li>${rule}</li>`;
            });
            entryHTML += '</ul>';
        }

        if (entry.sections) {
            entryHTML += entry.sections.map(section => `<h4>${section.title}</h4>${section.content}`).join('');
        }
        
        content.innerHTML = entryHTML;
    };

    const renderGamelogErrors = () => {
        let content = '<div class="welcome-container">';
        content += '<h2 class="section-title">Known Gamelog Errors</h2>';

        if (state.gamelogErrors && state.gamelogErrors.length > 0) {
            state.gamelogErrors.forEach(error => {
                const header = `${error.season}.${error.session} (Game ${error.game}), ${error.away_team} @ ${error.home_team}`;
                content += `<div class="gamelog-error-item">`;
                content += `<h4>${header.replace(/null/g, 'N/A')}</h4>`;
                content += `<p>${error.description || 'No description provided.'}</p>`;
                content += `</div>`;
            });
        } else {
            content += '<p>No known gamelog errors.</p>';
        }

        content += '</div>';
        elements.homeView.innerHTML = content;
    };

    const initializeApp = () => {
        const fcbOption = document.createElement('option');
        fcbOption.value = 'fcb';
        fcbOption.textContent = 'FCB';
        elements.leaderboardLeagueSelect.appendChild(fcbOption);

        window.addEventListener('hashchange', updateView);

        const themeSwitch = elements.themeSwitch;
        const currentTheme = localStorage.getItem('theme');

        function setTheme(theme) {
            if (theme === 'light-mode') {
                document.documentElement.classList.add('light-mode');
                themeSwitch.checked = true;
            } else {
                document.documentElement.classList.remove('light-mode');
                themeSwitch.checked = false;
            }
        }

        if (currentTheme) {
            setTheme(currentTheme);
        } else {
			setTheme('dark-mode');
		}

        themeSwitch.addEventListener('change', () => {
            if (themeSwitch.checked) {
                document.documentElement.classList.add('light-mode');
                localStorage.setItem('theme', 'light-mode');
            } else {
                document.documentElement.classList.remove('light-mode');
                localStorage.setItem('theme', 'dark-mode');
            }
            updateView();
        });

        
        const leaderboardLengthInput = elements.leaderboardLength;
        
        // Set default minimums for leaderboards
        elements.minPa.value = (2.0).toFixed(1);
        elements.minOuts.value = 3;
        elements.minAttempts.value = 3;
        elements.minDecisions.value = 3;

        updateView(); // Initial view
        
        elements.playerSearch.addEventListener('input', handlePlayerSearch);
        elements.leaderboardButton.addEventListener('click', handleLeaderboardView);
        elements.leaderboardLeagueSelect.addEventListener('change', () => {
            const selectedLeague = elements.leaderboardLeagueSelect.value;
            const mlrFilters = document.querySelectorAll('.mlr-filter');
            if (selectedLeague === 'milr' || selectedLeague === 'fcb') {
                mlrFilters.forEach(filter => filter.style.display = 'none');
            } else {
                mlrFilters.forEach(filter => filter.style.display = 'inline-block');
            }
            populateTeamFilter();
        });
        elements.leaderboardTypeSelect.addEventListener('change', populateLeaderboardStatSelect);
        elements.leaderboardStatSelect.addEventListener('change', handleStatSelectChange);
        populateTeamFilter();

        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (window.location.hash === '#/stats') {
                    setStickyColumnOffsets();
                }
            }, 100);
        });

        elements.homeTab.addEventListener('click', () => { window.location.hash = '#/home'; });
        elements.statsTab.addEventListener('click', () => { window.location.hash = '#/stats'; });
        elements.teamStatsTab.addEventListener('click', () => { window.location.hash = '#/team-stats'; });
        elements.leaderboardsTab.addEventListener('click', () => { window.location.hash = '#/leaderboards'; });
        elements.glossaryTab.addEventListener('click', () => { window.location.hash = '#/glossary'; });

        elements.app.addEventListener('click', (event) => {
            const teamLink = event.target.closest('.team-link');
            if (teamLink) {
                const team = teamLink.dataset.team;
                const season = teamLink.dataset.season;
                const isMiLR = teamLink.dataset.milr === 'true';
                const isFcb = teamLink.dataset.fcb === 'true';
                if (team && season) {
                    let hashPath = `#/team-stats?season=${season}&team=${team}`;
                    if (isMiLR) {
                        hashPath += '&league=milr';
                    } else if (isFcb) {
                        hashPath += '&league=fcb';
                    }
                    state.lastTeamStatsUrl = hashPath; // Update state for immediate use
                    window.location.hash = hashPath; // Still update hash for immediate view change
                }
            }

            const playerLink = event.target.closest('.player-link');
            if (playerLink) {
                const playerId = parseInt(playerLink.dataset.playerId, 10);
                if (!isNaN(playerId)) {
                    const playerName = state.players[playerId].currentName;
                    window.location.hash = '#/stats'; // Go to player stats view
                    elements.playerSearch.value = playerName;
                    elements.playerSuggestions.innerHTML = '';
                    elements.playerSuggestions.style.display = 'none';
                    displayPlayerPage(playerId);
                }
            }

            // Existing leaderboard player click logic
            const leaderboardPlayerCell = event.target.closest('.player-name-cell');
            if (leaderboardPlayerCell && leaderboardPlayerCell.dataset.playerId) {
                const playerId = parseInt(leaderboardPlayerCell.dataset.playerId, 10);
                if (!isNaN(playerId)) {
                    const playerName = state.players[playerId].currentName;
                    window.location.hash = '#/stats';
                    elements.playerSearch.value = playerName;
                    elements.playerSuggestions.innerHTML = '';
                    elements.playerSuggestions.style.display = 'none';
                    displayPlayerPage(playerId);
                }
            }

            // Handle random player button click via delegation
            const randomPlayerButton = event.target.closest('#random-player-button');
            if (randomPlayerButton) {
                goToRandomPlayerPage();
            }
        });
    };

    const populateLeaderboardStatSelect = () => {
        const type = elements.leaderboardTypeSelect.value;
        const statSelect = elements.leaderboardStatSelect;
        const previouslySelectedStat = statSelect.value;
        const typeFilter = elements.leaderboardTypeFilter;
        const previouslySelectedType = typeFilter.value;

        if (type === 'batting') {
            elements.battingMinimumControls.style.display = 'inline-block';
            elements.pitchingMinimumControls.style.display = 'none';
        } else {
            elements.battingMinimumControls.style.display = 'none';
            elements.pitchingMinimumControls.style.display = 'inline-block';
        }

        statSelect.innerHTML = '<option value="">-- Select Stat --</option>'; // Clear existing options

        const stats = (type === 'batting') 
            ? Object.values(STAT_DEFINITIONS.batting_tables).flat().concat(LEADERBOARD_ONLY_STATS.hitting)
            : Object.values(STAT_DEFINITIONS.pitching_tables).flat().concat(LEADERBOARD_ONLY_STATS.pitching);

        const uniqueStats = [...new Set(stats)].sort();
        let newOptionsExist = false;
        uniqueStats.forEach(stat => {
            if (stat === 'Season' || stat === 'Team' || stat === 'Type') return;
            const option = document.createElement('option');
            option.value = stat;
            option.textContent = stat;
            statSelect.appendChild(option);
            if (stat === previouslySelectedStat) {
                newOptionsExist = true;
            }
        });

        if (newOptionsExist) {
            statSelect.value = previouslySelectedStat;
        }

        // --- New logic to populate type filter ---
        typeFilter.innerHTML = '<option value="">All Types</option>';
        const playerTypesMap = (type === 'batting') ? state.typeDefinitions.batting : state.typeDefinitions.pitching;
        
        if (playerTypesMap) {
            const mainTypes = new Set();
            if (type === 'batting') {
                for (const typeKey in playerTypesMap) {
                    mainTypes.add(typeKey);
                }
            } else { // pitching
                for (const typeKey in playerTypesMap) {
                    const mainType = typeKey.split('-')[0];
                    mainTypes.add(mainType);
                }
            }
            const sortedMainTypes = Array.from(mainTypes).sort();

            sortedMainTypes.forEach(mainType => {
                const option = document.createElement('option');
                option.value = mainType;
                option.textContent = mainType;
                typeFilter.appendChild(option);
            });
        }
        if (previouslySelectedType && typeFilter.querySelector(`option[value="${previouslySelectedType}"]`)) {
            typeFilter.value = previouslySelectedType;
        }
    };

    const handleLeaderboardView = () => {
        const stat = elements.leaderboardStatSelect.value;
        if (!stat) return;

        const selectedLeague = elements.leaderboardLeagueSelect.value;
        const isMiLR = selectedLeague === 'milr';
        const isFcb = selectedLeague === 'fcb';

        const type = elements.leaderboardTypeSelect.value;
        const selectedTeam = (isMiLR || isFcb) ? '' : elements.leaderboardTeamFilter.value;
        const selectedType = (isMiLR || isFcb) ? '' : elements.leaderboardTypeFilter.value;
        const isHitting = type === 'batting';
        const reverseSort = elements.reverseSort.checked;
        const sortModifier = reverseSort ? -1 : 1;
        
        let statKey = stat;
        let data = isHitting ? (isMiLR ? state.milrHittingStats : (isFcb ? state.fcbHittingStats : state.hittingStats)) : (isMiLR ? state.milrPitchingStats : (isFcb ? state.fcbPitchingStats : state.pitchingStats));
        
        if (isHitting) {
            if (stat === 'SO') statKey = 'K';
            else if (stat === 'BA') statKey = 'AVG';
        } else { // isPitching
            if (stat === 'SO') statKey = 'K';
            else if (stat === 'ER') statKey = 'R';
            else if (stat === 'H6') statKey = 'H/6';
            else if (stat === 'HR6') statKey = 'HR/6';
            else if (stat === 'BB6') statKey = 'BB/6';
            else if (stat === 'SO6') statKey = 'K/6';
            else if (stat === 'SO/BB') statKey = 'K/BB';
            else if (stat === 'GB%') statKey = 'GB%_A';
            else if (stat === 'FB%') statKey = 'FB%_A';
            else if (stat === 'GB/FB') statKey = 'GB/FB_A';
            else if (stat === 'BA') statKey = 'BAA';
            else if (stat === 'OBP') statKey = 'OBPA';
            else if (stat === 'SLG') statKey = 'SLGA';
            else if (stat === 'OPS') statKey = 'OPSA';
            else if (stat === 'BABIP') statKey = 'BABIP_A';
            else if (stat === 'HR%') statKey = 'HR%_A';
            else if (stat === 'K%') statKey = 'K%_A';
            else if (stat === 'BB%') statKey = 'BB%_A';
            else if (stat === 'SB') statKey = 'SB_A';
            else if (stat === 'CS') statKey = 'CS_A';
            else if (stat === 'SB%') statKey = 'SB%_A';
            else if (stat === '2B') statKey = '2B_A';
            else if (stat === '3B') statKey = '3B_A';
        }
        
        const leaderboards = {};
        let lowerIsBetterStats = [];
        if (isHitting) {
            lowerIsBetterStats = ['Avg Diff'];
        } else { // isPitching
            lowerIsBetterStats = [
                'ERA', 'WHIP', 'FIP', 'RE24',
                'BAA', 'OBPA', 'SLGA', 'OPSA', 'BABIP_A',
                'H6', 'HR6', 'BB6',
                'BA', 'OBP', 'SLG', 'OPS', 'BABIP',
                'HR%', 'BB%', 'SB%', 'ERA-'
            ];
        }
        const lowerIsBetter = lowerIsBetterStats.includes(stat);
        
        const seasons = isMiLR ? Object.keys(state.milrTeamHistory) : (isFcb ? Object.keys(state.fcbTeamHistory) : state.seasonsWithStats);

        // The rest of the function logic remains the same, but it will now use the correct data and seasons
        // based on the selected league. I am replacing the entire function to ensure all parts are consistent.
        // This includes the filtering logic inside the stat-specific calculations.
        // For MiLR, selectedTeam and selectedType will be empty, so the filtering will be skipped.
        
        if (stat === 'W-L%') {
            const sortFn = (a, b) => {
                const diff = (b['W-L%'] || 0) - (a['W-L%'] || 0);
                if (diff !== 0) return sortModifier * diff;
                const a_decisions = (a.W || 0) + (a.L || 0);
                const b_decisions = (b.W || 0) + (b.L || 0);
                return sortModifier * (b_decisions - a_decisions);
            };

            // All-Time
            let allTimeLeaderboardData;
            if (selectedTeam && selectedType) {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Franchise-Type' && p.Team === selectedTeam && p.Type === selectedType);
            } else if (selectedType) {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Type' && p.Type === selectedType);
            } else if (selectedTeam) {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Franchise' && p.Team === selectedTeam);
            } else {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Career');
            }
            const min_decisions_career = 10;
            let allTimeLeaderboard = allTimeLeaderboardData.filter(p => ((p.W || 0) + (p.L || 0)) >= min_decisions_career);
            allTimeLeaderboard.sort(sortFn);
            leaderboards['All-Time'] = {
                type: 'all-time',
                data: allTimeLeaderboard,
                isCountingStat: false,
                min_qual: min_decisions_career,
                min_qual_key: 'Decisions'
            };

            // Single Season
            let singleSeasonData = data.filter(p => p.Season.startsWith('S'));
            if (selectedTeam) {
                const franchise = state.teamHistory[selectedTeam];
                if (franchise) {
                    singleSeasonData = singleSeasonData.filter(p => {
                        const seasonNum = parseInt(p.Season.slice(1));
                        if (isNaN(seasonNum)) return false;
                        return franchise.some(f => p.Team === f.abbr && seasonNum >= f.start && seasonNum <= f.end);
                    });
                } else {
                    singleSeasonData = singleSeasonData.filter(p => p.Team === selectedTeam);
                }
            } else {
                singleSeasonData = singleSeasonData.filter(p => !p.is_sub_row);
            }
            if (selectedType) {
                singleSeasonData = singleSeasonData.filter(p => p.Type && p.Type.startsWith(selectedType));
            }
            const min_decisions_season = parseInt(elements.minDecisions.value) || 3;
            let singleSeasonLeaderboard = singleSeasonData.filter(p => ((p.W || 0) + (p.L || 0)) >= min_decisions_season);
            singleSeasonLeaderboard.sort(sortFn);
            leaderboards['Single Season'] = {
                type: 'single-season',
                data: singleSeasonLeaderboard,
                isCountingStat: false,
                min_qual: min_decisions_season,
                min_qual_key: 'Decisions'
            };

            // Individual Seasons
            const allSeasons = [...seasons].sort((a, b) => parseInt(b.slice(1)) - parseInt(a.slice(1)));
            for (const season of allSeasons) {
                let seasonData = data.filter(p => p.Season === season);
                if (selectedTeam) {
                    const franchise = state.teamHistory[selectedTeam];
                    if (franchise) {
                        const seasonNum = parseInt(season.slice(1));
                        const correctAbbr = franchise.find(f => seasonNum >= f.start && seasonNum <= f.end)?.abbr;
                        if (correctAbbr) {
                            seasonData = seasonData.filter(p => p.Team === correctAbbr);
                        } else { // This franchise didn't exist this season.
                            seasonData = []; 
                        }
                    } else {
                        seasonData = seasonData.filter(p => p.Team === selectedTeam);
                    }
                } else {
                    seasonData = seasonData.filter(p => !p.is_sub_row);
                }
                if (selectedType) {
                    seasonData = seasonData.filter(p => p.Type && p.Type.startsWith(selectedType));
                }
                let leaderboardData = seasonData.filter(p => ((p.W || 0) + (p.L || 0)) >= min_decisions_season);
                leaderboardData.sort(sortFn);
                leaderboards[season] = {
                    type: 'season',
                    data: leaderboardData,
                    isCountingStat: false,
                    min_qual: min_decisions_season,
                    min_qual_key: 'Decisions'
                };
            }
        } else {
            // This is the generic logic for other stats.
            // It will also be affected by the `data` and `seasons` variables being set based on the league.
            const isCountingStat = COUNTING_STATS.includes(stat);
            
            let min_qual_key;
            if (isHitting) {
                min_qual_key = 'PA';
                if (stat === 'GO') {
                    data.forEach(p => { p.GO = (p.LGO || 0) + (p.RGO || 0); });
                }
            } else { // isPitching
                min_qual_key = 'IP';
                if (stat === 'GO') {
                    data.forEach(p => { p.GO = (p.LGO || 0) + (p.RGO || 0); });
                }
            }
            
            const statsThatCanBeNegative = ['WAR', 'WPA', 'RE24'];

            // All-Time
            let allTimeLeaderboardData;
            if (selectedTeam && selectedType) {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Franchise-Type' && p.Team === selectedTeam && p.Type === selectedType);
            } else if (selectedType) {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Type' && p.Type === selectedType);
            } else if (selectedTeam) {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Franchise' && p.Team === selectedTeam);
            } else {
                allTimeLeaderboardData = data.filter(p => p.Season === 'Career');
            }
            
            const min_qual_career = isHitting ? 100 : 50;
            let allTimeLeaderboard = isCountingStat ? allTimeLeaderboardData : allTimeLeaderboardData.filter(p => (p[min_qual_key] || 0) >= min_qual_career);
            if (isCountingStat && !statsThatCanBeNegative.includes(stat)) {
                allTimeLeaderboard = allTimeLeaderboard.filter(p => p[statKey] > 0);
            }
            allTimeLeaderboard.sort((a, b) => sortModifier * (lowerIsBetter ? (a[statKey] || 0) - (b[statKey] || 0) : (b[statKey] || 0) - (a[statKey] || 0)));
            leaderboards['All-Time'] = {
                type: 'all-time',
                data: allTimeLeaderboard,
                isCountingStat: isCountingStat,
                min_qual: min_qual_career,
                min_qual_key: min_qual_key
            };

            // Single Season
            let singleSeasonData = data.filter(p => p.Season.startsWith('S'));

            // Exclude current season from Single Season leaderboards if it's not halfway through for rate stats
            if (!isCountingStat) {
                const currentSeason = state.currentSeasonInfo.season;
                if (currentSeason) {
                    const totalSessions = state.seasons[currentSeason] || 0;
                    const sessionsSoFar = state.currentSeasonInfo.session || 0;
                    if (totalSessions > 0 && sessionsSoFar <= totalSessions / 2) {
                        singleSeasonData = singleSeasonData.filter(p => p.Season !== currentSeason);
                    }
                }
            }

            if (!isMiLR && !isFcb) {
                if (selectedTeam) {
                    const franchise = state.teamHistory[selectedTeam];
                    if (franchise) {
                        singleSeasonData = singleSeasonData.filter(p => {
                            const seasonNum = parseInt(p.Season.slice(1));
                            if (isNaN(seasonNum)) return false;
                            return franchise.some(f => p.Team === f.abbr && seasonNum >= f.start && seasonNum <= f.end);
                        });
                    } else {
                        singleSeasonData = singleSeasonData.filter(p => p.Team === selectedTeam);
                    }
                } else {
                    singleSeasonData = singleSeasonData.filter(p => !p.is_sub_row);
                }
                if (selectedType) {
                    if (isHitting) {
                        singleSeasonData = singleSeasonData.filter(p => p.Type === selectedType);
                    } else {
                        singleSeasonData = singleSeasonData.filter(p => p.Type && p.Type.startsWith(selectedType));
                    }
                }
            } else {
                singleSeasonData = singleSeasonData.filter(p => !p.is_sub_row);
            }

            let singleSeasonLeaderboard;
            if (isCountingStat) {
                singleSeasonLeaderboard = singleSeasonData;
            } else {
                singleSeasonLeaderboard = singleSeasonData.filter(p => {
                    const season = p.Season;
                    const gamesInSeason = state.seasons[season] || 0;
                    if (gamesInSeason === 0) return false;
                    
                    let sessionsToUse = gamesInSeason;
                    // For the most recent season, use sessions so far.
                    if (season === state.currentSeasonInfo.season) {
                        sessionsToUse = state.currentSeasonInfo.session || gamesInSeason;
                    }
            
                    if (isHitting) {
                        const pa_per_session = parseFloat(elements.minPa.value) || 2.0;
                        const min_pa = pa_per_session * sessionsToUse;
                        return (p.PA || 0) >= min_pa;
                    } else { // isPitching
                        const outs_per_session = parseInt(elements.minOuts.value) || 3;
                        const min_outs = outs_per_session * sessionsToUse;
                        const player_ip = p.IP || 0;
                        const player_outs = Math.round(player_ip * 3);
                        return player_outs >= min_outs;
                    }
                });
            }
            if (isCountingStat && !statsThatCanBeNegative.includes(stat)) {
                singleSeasonLeaderboard = singleSeasonLeaderboard.filter(p => p[statKey] > 0);
            }
            singleSeasonLeaderboard.sort((a, b) => sortModifier * (lowerIsBetter ? (a[statKey] || 0) - (b[statKey] || 0) : (b[statKey] || 0) - (a[statKey] || 0)));
            leaderboards['Single Season'] = {
                type: 'single-season',
                data: singleSeasonLeaderboard,
                isCountingStat: isCountingStat,
                min_qual_key: min_qual_key
            };

            // Individual Seasons
            const allSeasons = [...seasons].sort((a, b) => getSeasonForSort(b) - getSeasonForSort(a));
            for (const season of allSeasons) {
                let seasonData = data.filter(p => p.Season === season);
                if (!isMiLR && !isFcb) {
                    if (selectedTeam) {
                        const franchise = state.teamHistory[selectedTeam];
                        if (franchise) {
                            const seasonNum = parseInt(season.slice(1));
                            const correctAbbr = franchise.find(f => seasonNum >= f.start && seasonNum <= f.end)?.abbr;
                            if (correctAbbr) {
                                seasonData = seasonData.filter(p => p.Team === correctAbbr);
                            } else { // This franchise didn't exist this season.
                                seasonData = []; 
                            }
                        } else {
                            seasonData = seasonData.filter(p => p.Team === selectedTeam);
                        }
                    } else {
                        seasonData = seasonData.filter(p => !p.is_sub_row);
                    }
                    if (selectedType) {
                        if (isHitting) {
                            seasonData = seasonData.filter(p => p.Type === selectedType);
                        } else {
                            seasonData = seasonData.filter(p => p.Type && p.Type.startsWith(selectedType));
                        }
                    }
                } else {
                    seasonData = seasonData.filter(p => !p.is_sub_row);
                }

                const gamesInSeason = state.seasons[season] || 0;
                let sessionsToUse = gamesInSeason;

                // For the most recent season, use sessions so far.
                if (season === state.currentSeasonInfo.season) {
                    sessionsToUse = state.currentSeasonInfo.session || gamesInSeason;
                }

                let min_qual;
                const min_qual_display_key = isHitting ? 'PA' : 'Outs';

                if (isHitting) {
                    const pa_per_session = parseFloat(elements.minPa.value) || 2.0;
                    min_qual = pa_per_session * sessionsToUse;
                } else {
                    const outs_per_session = parseInt(elements.minOuts.value) || 3;
                    min_qual = outs_per_session * sessionsToUse;
                }

                let leaderboardData = isCountingStat ? seasonData : seasonData.filter(p => {
                    if (isHitting) {
                        return (p[min_qual_key] || 0) >= min_qual;
                    } else { // isPitching
                        const player_ip = p.IP || 0;
                        const player_outs = Math.round(player_ip * 3);
                        return player_outs >= min_qual;
                    }
                });

                if (isCountingStat && !statsThatCanBeNegative.includes(stat)) {
                    leaderboardData = leaderboardData.filter(p => p[statKey] > 0);
                }
                leaderboardData.sort((a, b) => sortModifier * (lowerIsBetter ? (a[statKey] || 0) - (b[statKey] || 0) : (b[statKey] || 0) - (a[statKey] || 0)));
                leaderboards[season] = {
                    type: 'season',
                    data: leaderboardData,
                    isCountingStat: isCountingStat,
                    min_qual: min_qual,
                    min_qual_key: min_qual_display_key
                };
            }
        }
        renderLeaderboardGrid(leaderboards, stat, statKey, isHitting, isMiLR, isFcb, seasons);
    };

    const renderLeaderboardGrid = (leaderboards, stat, statKey, isHitting, isMiLR, isFcb, seasons) => {
        console.log('renderLeaderboardGrid called with leaderboards:', JSON.stringify(leaderboards, null, 2));
        const leaderboardSize = parseInt(elements.leaderboardLength.value) || 10;
        elements.leaderboardsContentDisplay.innerHTML = `<h2 class="section-title">${stat} Leaderboards</h2>`;

        const gridContainer = document.createElement('div');
        gridContainer.className = 'leaderboard-grid';

        const gridOrder = ['All-Time', 'Single Season', ...[...seasons].sort((a, b) => getSeasonForSort(b) - getSeasonForSort(a))];

        for (const key of gridOrder) {
            const leaderboardInfo = leaderboards[key];
            if (!leaderboardInfo) continue;
            
            const fullLeaderboard = leaderboardInfo.data;

            const arePlayersTied = (p1, p2) => {
                if (!p1 || !p2) return false;
                if (p1[statKey] !== p2[statKey]) return false;
                if (stat === 'W-L%') {
                    const p1_dec = (p1.W || 0) + (p1.L || 0);
                    const p2_dec = (p2.W || 0) + (p2.L || 0);
                    return p1_dec === p2_dec;
                }
                if (stat === 'SB%') {
                    const sbKey = isHitting ? 'SB' : 'SB_A';
                    const csKey = isHitting ? 'CS' : 'CS_A';
                    const p1_att = (p1[sbKey] || 0) + (p1[csKey] || 0);
                    const p2_att = (p2[sbKey] || 0) + (p2[csKey] || 0);
                    return p1_att === p2_att;
                }
                return true; // Tied on primary stat, no tie-breaker
            };

            let leaderboard = fullLeaderboard.slice(0, leaderboardSize);
            let tieInfo = null;

            if (fullLeaderboard.length > leaderboardSize) {
                const lastPlayerInSlice = fullLeaderboard[leaderboardSize - 1];
                const firstPlayerOutOfSlice = fullLeaderboard[leaderboardSize];

                if (arePlayersTied(lastPlayerInSlice, firstPlayerOutOfSlice)) {
                    const tieValue = lastPlayerInSlice[statKey];
                    if (tieValue !== null && tieValue !== undefined) {
                        let firstTieIndex = leaderboardSize - 1;
                        while (firstTieIndex > 0 && arePlayersTied(fullLeaderboard[firstTieIndex - 1], lastPlayerInSlice)) {
                            firstTieIndex--;
                        }

                        const tieCount = fullLeaderboard.filter(p => arePlayersTied(p, lastPlayerInSlice)).length;
                        
                        leaderboard = fullLeaderboard.slice(0, firstTieIndex);
                        tieInfo = { count: tieCount, value: tieValue };
                    }
                }
            }

            const seasonCard = document.createElement('div');
            seasonCard.className = 'leaderboard-card';

            let title;
            if (leaderboardInfo.type === 'all-time') {
                title = `<h4>All-Time</h4>`;
            } else if (leaderboardInfo.type === 'single-season') {
                title = `<h4>Single Season</h4>`;
            } else {
                title = `<h4>Season ${formatSeasonName(key, isMiLR, isFcb).slice(1)}</h4>`;
            }

            if (!leaderboardInfo.isCountingStat && leaderboardInfo.type !== 'single-season') {
                let display_min_qual = leaderboardInfo.min_qual;
                let display_min_qual_key = leaderboardInfo.min_qual_key;

                if (leaderboardInfo.min_qual_key === 'Outs') {
                    display_min_qual = leaderboardInfo.min_qual / 3; // Convert outs to IP float
                    display_min_qual_key = 'IP';
                } else if (leaderboardInfo.min_qual_key === 'PA') {
                    display_min_qual = Math.ceil(leaderboardInfo.min_qual);
                }
                const qual_text = `${formatStat(display_min_qual_key, display_min_qual)} ${display_min_qual_key}`;
                title += `<p class="qualifier">(${qual_text} min)</p>`;
            }
            seasonCard.innerHTML = title;

            const table = document.createElement('table');
            table.className = 'stats-table';
            const thead = table.createTHead();
            let headerRow = `<tr><th>Rank</th><th>Player</th>`;
            if (leaderboardInfo.type === 'season') headerRow += `<th>Team</th>`;
            if (leaderboardInfo.type === 'single-season') headerRow += `<th>Season</th>`;
            headerRow += `<th>${stat}</th></tr>`;
            thead.innerHTML = headerRow;
            
            const tbody = table.createTBody();
            let lastPlayer = null;
            let lastRank = 0;
            leaderboard.forEach((p, i) => {
                const rank = i + 1;

                let displayRank;
                if (i > 0 && arePlayersTied(p, lastPlayer)) {
                    displayRank = lastRank;
                } else {
                    displayRank = rank;
                }

                const id = p[isHitting ? 'Hitter ID' : 'Pitcher ID'];
                const playerName = state.players[id] ? state.players[id].currentName : 'Unknown';
                let row = `<tr><td>${displayRank}</td><td class="player-name-cell" data-player-id="${id}" style="cursor: pointer; text-decoration: underline;">${playerName}</td>`;
                if (leaderboardInfo.type === 'season') row += `<td>${p.Team || ''}</td>`;
                if (leaderboardInfo.type === 'single-season') row += `<td>${formatSeasonName(p.Season, isMiLR, isFcb).slice(1)}</td>`;
                row += `<td>${formatStat(stat, p[statKey])}</td></tr>`;
                tbody.innerHTML += row;

                lastPlayer = p;
                lastRank = displayRank;
            });

            if (tieInfo) {
                const colspan = thead.rows[0].cells.length;
                tbody.innerHTML += `<tr><td class="tie-info" colspan="${colspan}">${tieInfo.count} players tied with ${formatStat(stat, tieInfo.value)}</td></tr>`;
            }

            seasonCard.appendChild(table);
            gridContainer.appendChild(seasonCard);
        }

        elements.leaderboardsContentDisplay.appendChild(gridContainer);
    };

    const goToRandomPlayerPage = () => {
        const playerIds = Object.keys(state.players);
        const randomPlayerId = playerIds[Math.floor(Math.random() * playerIds.length)];
        const randomPlayerName = state.players[randomPlayerId].currentName;

        window.location.hash = '#/stats'; // Navigate to player stats view
        elements.playerSearch.value = randomPlayerName;
        elements.playerSuggestions.innerHTML = ''; // Clear any suggestions
        elements.playerSuggestions.style.display = 'none';
        displayPlayerPage(parseInt(randomPlayerId));
    };

    const handlePlayerSearch = (event) => {
        const query = event.target.value.toLowerCase();
        elements.playerSuggestions.innerHTML = '';

        const matchingIds = new Set();

        // Always attempt to search by ID, regardless of query length
        if (/^\d+$/.test(query)) { // Matches one or more digits
            const id = parseInt(query);
            if (state.players[id]) {
                matchingIds.add(id);
            }
        }

        // Only search by name if query length is 2 or more
        if (query.length >= 2) {
            for (const [name, ids] of state.playerMap.entries()) {
                if (name.includes(query)) {
                    ids.forEach(id => matchingIds.add(id));
                }
            }
        }
        
        // If no matches found after both ID and name search
        if (matchingIds.size === 0) {
            elements.playerSuggestions.style.display = 'none';
            return;
        }
        
        // Now we have all matching IDs. Let's build the suggestions and handle name collisions.
        const nameToIds = new Map();
        matchingIds.forEach(id => {
            const currentName = state.players[id].currentName;
            if (!nameToIds.has(currentName)) {
                nameToIds.set(currentName, []);
            }
            nameToIds.get(currentName).push(id);
        });

        elements.playerSuggestions.style.display = 'block';
        let count = 0;

        for (const id of matchingIds) {
            if (count >= 10) break;
            
            const currentName = state.players[id].currentName;
            let suggestionText = currentName;

            if (nameToIds.get(currentName).length > 1) {
                // This name is shared among the matched suggestions. Disambiguate.
                suggestionText += ` (#${id})`;
            }

            const div = document.createElement('div');
            div.textContent = suggestionText;
            div.className = 'suggestion-item';
            div.addEventListener('click', () => {
                elements.playerSearch.value = currentName; // Use original name for search bar
                elements.playerSuggestions.innerHTML = '';
                elements.playerSuggestions.style.display = 'none';
                displayPlayerPage(id);
            });
            elements.playerSuggestions.appendChild(div);
            count++;
        }
    };

    const populateTeamFilter = () => {
        const teamFilter = elements.leaderboardTeamFilter;
        if (!teamFilter) return;
        const teams = Object.keys(state.teamHistory).sort();
        teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team;
            option.textContent = team;
            teamFilter.appendChild(option);
        });
    };



    const getPlayerAwards = (playerId) => {
        const awards = {}; // Key: awardId, Value: array of {season, league}
        const awardsData = state.awards;
        if (!awardsData) return [];

        const metadata = awardsData._metadata || {};

        // Helper to add an award
        const addAward = (awardId, season, league) => {
            if (!awards[awardId]) {
                awards[awardId] = [];
            }
            if (season) {
                if (!awards[awardId].some(a => a.season === season && a.league === league)) {
                    awards[awardId].push({ season: season, league: league });
                }
            } else if (awardId === 'HOF') {
                awards[awardId] = [];
            }
        };

        // HOF
        if (awardsData.HOF && awardsData.HOF.includes(playerId)) {
            addAward('HOF', null, null);
        }

        // Season awards
        for (const seasonKey in awardsData) {
            if (!seasonKey.startsWith('S')) continue;
            
            const seasonData = awardsData[seasonKey];
            
            if (seasonData.PCMVP && seasonData.PCMVP.includes(playerId)) {
                addAward('PCMVP', seasonKey, null); // No league for PCMVP
            }
            if (seasonData.HRD && seasonData.HRD.includes(playerId)) {
                addAward('HRD', seasonKey, null); // No league for HRD
            }

            ['AL', 'NL'].forEach(league => {
                if (seasonData[league]) {
                    for (const awardKey in seasonData[league]) {
                        const awardData = seasonData[league][awardKey];
                        
                        if (awardKey === 'SS' || awardKey === 'AS') {
                            if (typeof awardData === 'object' && awardData !== null && !Array.isArray(awardData)) {
                                for (const position in awardData) {
                                    if (awardKey === 'AS' && position === 'GM') {
                                        continue;
                                    }
                                    const positionWinners = awardData[position];
                                    if (Array.isArray(positionWinners)) {
                                        if (positionWinners.includes(playerId)) {
                                            addAward(awardKey, seasonKey, league);
                                            break;
                                        }
                                    } else {
                                        if (positionWinners === playerId) {
                                            addAward(awardKey, seasonKey, league);
                                            break;
                                        }
                                    }
                                }
                            }
                        } else {
                            if (Array.isArray(awardData) && awardData.includes(playerId)) {
                                addAward(awardKey, seasonKey, league);
                            }
                        }
                    }
                }
            });
        }
        
        const displayList = [];
        const order = ['HOF', 'MVP', 'CYA', 'ROTY', 'RPOTY', 'SS', 'AS', 'BT', 'ERAT', 'GMOTY', 'PCMVP', 'HRD'];

        for (const awardId of order) {
            if (awards[awardId]) {
                const wins = awards[awardId];
                const count = wins.length;
                const name = metadata[awardId] || awardId;

                if (awardId === 'HOF') {
                    displayList.push({ text: name, class: 'award-hof', seasons: [] });
                } else if (count > 0) {
                    const awardText = count > 1 ? `${count}x ${name}` : name;
                    wins.sort((a, b) => parseInt(a.season.slice(1)) - parseInt(b.season.slice(1)));
                    
                    const seasons = wins.map(w => w.season);
                    const lastWin = wins[wins.length - 1];

                    displayList.push({ 
                        text: awardText, 
                        class: `award-${awardId.toLowerCase()}`, 
                        seasons: seasons,
                        lastWin: lastWin 
                    });
                }
            }
        }
        return displayList;
    };

        const displayPlayerPage = (playerId) => {
        state.currentPlayerId = playerId;
        elements.statsContentDisplay.innerHTML = '';
        const player = state.players[playerId];
        if (!player) return;

        const path = window.location.hash || '#/stats';
        const isStats = path === '#/stats';

        const playerName = player.currentName;

        const hittingStats = state.hittingStats.filter(s => s['Hitter ID'] === playerId);
        const pitchingStats = state.pitchingStats.filter(s => s['Pitcher ID'] === playerId);

        // Filter out 'Type' rows from player stat tables
        const filteredHittingStats = hittingStats.filter(s => s.Season !== 'Type' && s.Season !== 'Franchise-Type');
        const filteredPitchingStats = pitchingStats.filter(s => s.Season !== 'Type' && s.Season !== 'Franchise-Type');

        let mostRecentTeam = null;
        let mostRecentSeason = null;
        const allStats = [...filteredHittingStats, ...filteredPitchingStats];

        if (allStats.length > 0) {
            const lastSeasonStats = allStats
                .filter(s => s.Season && s.Season.startsWith('S') && !s.is_sub_row)
                .sort((a, b) => parseInt(b.Season.slice(1)) - parseInt(a.Season.slice(1)))[0];
            
            if (lastSeasonStats) {
                mostRecentTeam = lastSeasonStats['Last Team'] || lastSeasonStats['Team'];
                mostRecentSeason = lastSeasonStats.Season;
            }
        }

        let titleHTML = `<h2 class="section-title">${playerName}</h2>`;
        if (mostRecentTeam && mostRecentSeason) {
            const franchiseKey = getFranchiseKeyFromAbbr(mostRecentTeam, mostRecentSeason);
            const logoUrl = getTeamLogoBySeason(franchiseKey, mostRecentSeason);
            if (logoUrl) {
                titleHTML = `<h2 class="section-title"><img src="${logoUrl}" class="player-team-logo"> ${playerName}</h2>`;
            }
        }

        titleHTML += `<p class="player-id-display">Player ID: ${playerId}</p>`;

        if (player.formerNames && player.formerNames.length > 0) {
            titleHTML += `<p class="former-names">Formerly known as: ${player.formerNames.join(', ')}</p>`;
        }

        const awards = getPlayerAwards(playerId);
        if (awards.length > 0) {
            let awardsHTML = '<div class="awards-container">';
            awards.forEach(award => {
                const seasonTitle = award.seasons && award.seasons.length > 0
                    ? ` title="${award.seasons.join(', ')}"`
                    : '';

                if (award.class === 'award-hof') {
                    awardsHTML += `<a href="#/hof"><div class="award-box ${award.class}"${seasonTitle}>${award.text}</div></a>`;
                } else if (award.seasons && award.seasons.length > 0) {
                    const lastSeason = award.lastWin.season;
                    const league = award.lastWin.league;
                    let href = `#/awards?season=${lastSeason}`;
                    if (league) {
                        href += `&league=${league.toLowerCase()}`;
                    }
                    awardsHTML += `<a href="${href}"><div class="award-box ${award.class}"${seasonTitle}>${award.text}</div></a>`;
                } else {
                    awardsHTML += `<div class="award-box ${award.class}"${seasonTitle}>${award.text}</div>`;
                }
            });
            awardsHTML += '</div>';
            titleHTML += awardsHTML;
        }

        const playerInfo = state.playerInfo[playerId];
        if (playerInfo) {
            let playerInfoHTML = '';
            if (playerInfo.primary_position && state.typeDefinitions.position && state.typeDefinitions.position[playerInfo.primary_position]) {
                playerInfoHTML += `<p><strong>Position:</strong> ${state.typeDefinitions.position[playerInfo.primary_position]}</p>`;
            }
            if (playerInfo.handedness && state.typeDefinitions.handedness && state.typeDefinitions.handedness[playerInfo.handedness]) {
                playerInfoHTML += `<p><strong>Handedness:</strong> ${state.typeDefinitions.handedness[playerInfo.handedness]}</p>`;
            }

            const primaryPosition = playerInfo.primary_position;

            // Batting type should show for any position other than 'P'
            if (primaryPosition !== 'P' && playerInfo.batting_type && state.typeDefinitions.batting && state.typeDefinitions.batting[playerInfo.batting_type]) {
                playerInfoHTML += `<p><strong>Batting:</strong> ${state.typeDefinitions.batting[playerInfo.batting_type]}</p>`;
            }

            // Pitching type should only show for 'P' and 'PH'
            if ((primaryPosition === 'P' || primaryPosition === 'PH') && playerInfo.pitching_type && state.typeDefinitions.pitching && state.typeDefinitions.pitching[playerInfo.pitching_type]) {
                playerInfoHTML += `<p><strong>Pitching:</strong> ${state.typeDefinitions.pitching[playerInfo.pitching_type]}</p>`;
            }
            
            if (playerInfoHTML) {
                titleHTML += `<div class="player-info">${playerInfoHTML}</div>`;
            }
        }
        elements.statsContentDisplay.innerHTML = titleHTML;

        if (isStats) {
            const lastHittingSeasonNum = Math.max(
                -1,
                ...filteredHittingStats
                    .filter(s => s.Season && !s.Season.startsWith('C') && !s.Season.startsWith('F'))
                    .map(s => parseInt(s.Season.slice(1)))
            );
            const lastPitchingSeasonNum = Math.max(
                -1,
                ...filteredPitchingStats
                    .filter(s => s.Season && !s.Season.startsWith('C') && !s.Season.startsWith('F'))
                    .map(s => parseInt(s.Season.slice(1)))
            );
    
            let primaryRole = 'hitter';
    
            if (lastPitchingSeasonNum > lastHittingSeasonNum) {
                primaryRole = 'pitcher';
            } else if (lastHittingSeasonNum > lastPitchingSeasonNum) {
                primaryRole = 'hitter';
            } else if (lastHittingSeasonNum > 0) { // They are equal and positive, so they played both in the same most recent season.
                const lastSeason = `S${lastHittingSeasonNum}`;
                const recentHitting = filteredHittingStats.find(s => s.Season === lastSeason && !s.is_sub_row);
                const recentPitching = filteredPitchingStats.find(s => s.Season === lastSeason && !s.is_sub_row);
    
                if (recentPitching && recentHitting) {
                    if (recentPitching.G > recentHitting.G) {
                        primaryRole = 'pitcher';
                    } else if (recentPitching.G === recentHitting.G) {
                        if ((recentPitching.BF || 0) > (recentHitting.PA || 0)) {
                            primaryRole = 'pitcher';
                        }
                    }
                } else if (recentPitching) { // Only pitching in the last season
                    primaryRole = 'pitcher';
                }
            } else { // No recent season data, check career data
                const careerHitting = filteredHittingStats.find(s => s.Season === 'Career');
                const careerPitching = filteredPitchingStats.find(s => s.Season === 'Career');
                if (careerPitching && !careerHitting) {
                    primaryRole = 'pitcher';
                } else if (careerPitching && careerHitting) {
                    if (careerPitching.G > careerHitting.G) {
                        primaryRole = 'pitcher';
                    } else if (careerPitching.G === careerHitting.G) {
                        if ((careerPitching.BF || 0) > (careerHitting.PA || 0)) {
                            primaryRole = 'pitcher';
                        }
                    }
                }
            }
    
            const renderHitting = () => {
                if (filteredHittingStats.length > 0) {
                    const franchiseFirstSeason = new Map();
                    const allPlayerSeasonStats = filteredHittingStats.filter(s => s.Season.startsWith('S') && (s.is_sub_row || !s.Team.includes('TM')));

                    for (const stat of allPlayerSeasonStats) {
                        const seasonNum = parseInt(stat.Season.slice(1));
                        const teamAbbr = stat.Team;
                        const franchiseKey = getFranchiseKeyFromAbbr(teamAbbr, stat.Season);

                        if (franchiseKey) {
                            if (!franchiseFirstSeason.has(franchiseKey) || seasonNum < franchiseFirstSeason.get(franchiseKey)) {
                                franchiseFirstSeason.set(franchiseKey, seasonNum);
                            }
                        }
                    }

                    filteredHittingStats.sort((a, b) => {
                        const getScore = (season) => {
                            if (season === 'Franchise') return 3;
                            if (season === 'Career') return 2;
                            return 0;
                        }
                        const scoreA = getScore(a.Season);
                        const scoreB = getScore(b.Season);
                        if (scoreA !== scoreB) {
                            return scoreA - scoreB;
                        }

                        if (a.Season === 'Franchise') {
                            const paA = a.PA || 0;
                            const paB = b.PA || 0;
                            if (paB !== paA) {
                                return paB - paA;
                            }
                            const firstSeasonA = franchiseFirstSeason.get(a.Team) || Infinity;
                            const firstSeasonB = franchiseFirstSeason.get(b.Team) || Infinity;
                            if (firstSeasonA !== firstSeasonB) {
                                return firstSeasonA - firstSeasonB;
                            }
                            return a.Team.localeCompare(b.Team);
                        }

                        if (a.Season === 'Career') {
                            return 0; // Should be only one
                        }

                        // Season rows
                        const seasonA = getSeasonForSort(a.Season);
                        const seasonB = getSeasonForSort(b.Season);
                        if (seasonA !== seasonB) {
                            return seasonA - seasonB;
                        }
    
                        const subRowA = a.is_sub_row ? 1 : 0;
                        const subRowB = b.is_sub_row ? 1 : 0;
                        return subRowA - subRowB;
                    });
                    elements.statsContentDisplay.innerHTML += createStatsTable('Batting Stats', filteredHittingStats, STAT_DEFINITIONS, false, true, false);
                }
            };
    
            const renderPitching = () => {
                if (filteredPitchingStats.length > 0) {
                    const franchiseFirstSeason = new Map();
                    const allPlayerSeasonStats = filteredPitchingStats.filter(s => s.Season.startsWith('S') && (s.is_sub_row || !s.Team.includes('TM')));

                    for (const stat of allPlayerSeasonStats) {
                        const seasonNum = parseInt(stat.Season.slice(1));
                        const teamAbbr = stat.Team;
                        const franchiseKey = getFranchiseKeyFromAbbr(teamAbbr, stat.Season);

                        if (franchiseKey) {
                            if (!franchiseFirstSeason.has(franchiseKey) || seasonNum < franchiseFirstSeason.get(franchiseKey)) {
                                franchiseFirstSeason.set(franchiseKey, seasonNum);
                            }
                        }
                    }

                    filteredPitchingStats.sort((a, b) => {
                        const getScore = (season) => {
                            if (season === 'Franchise') return 3;
                            if (season === 'Career') return 2;
                            return 0;
                        }
                        const scoreA = getScore(a.Season);
                        const scoreB = getScore(b.Season);
                        if (scoreA !== scoreB) {
                            return scoreA - scoreB;
                        }

                        if (a.Season === 'Franchise') {
                            const ipA = a.IP || 0;
                            const ipB = b.IP || 0;
                            if (ipB !== ipA) {
                                return ipB - ipA;
                            }
                            const firstSeasonA = franchiseFirstSeason.get(a.Team) || Infinity;
                            const firstSeasonB = franchiseFirstSeason.get(b.Team) || Infinity;
                            if (firstSeasonA !== firstSeasonB) {
                                return firstSeasonA - firstSeasonB;
                            }
                            return a.Team.localeCompare(b.Team);
                        }

                        if (a.Season === 'Career') {
                            return 0; // Should be only one
                        }

                        // Season rows
                        const seasonA = getSeasonForSort(a.Season);
                        const seasonB = getSeasonForSort(b.Season);
                        if (seasonA !== seasonB) {
                            return seasonA - seasonB;
                        }
    
                        const subRowA = a.is_sub_row ? 1 : 0;
                        const subRowB = b.is_sub_row ? 1 : 0;
                        return subRowA - subRowB;
                    });
                    elements.statsContentDisplay.innerHTML += createStatsTable('Pitching Stats', filteredPitchingStats, STAT_DEFINITIONS, true, true, false);
                }
            };
    
            if (primaryRole === 'pitcher') {
                renderPitching();
                renderHitting();
            } else {
                renderHitting();
                renderPitching();
            }

            const milrHittingStats = state.milrHittingStats.filter(s => s['Hitter ID'] === playerId);
            const milrPitchingStats = state.milrPitchingStats.filter(s => s['Pitcher ID'] === playerId);
            const fcbHittingStats = state.fcbHittingStats.filter(s => s['Hitter ID'] === playerId);
            const fcbPitchingStats = state.fcbPitchingStats.filter(s => s['Pitcher ID'] === playerId);

            const hasMilr = milrHittingStats.length > 0 || milrPitchingStats.length > 0;
            const hasFcb = fcbHittingStats.length > 0 || fcbPitchingStats.length > 0;

            if (hasMilr || hasFcb) {
                const buttonsContainer = document.createElement('div');
                buttonsContainer.style.marginTop = '20px';
                
                const minorLeagueContainers = document.createElement('div');

                if (hasMilr) {
                    const toggleButton = document.createElement('button');
                    toggleButton.id = 'toggle-milr-stats';
                    toggleButton.textContent = '[Show MiLR]';
                    toggleButton.style.background = 'none';
                    toggleButton.style.border = 'none';
                    toggleButton.style.color = 'var(--text-color)';
                    toggleButton.style.textDecoration = 'underline';
                    toggleButton.style.fontWeight = 'normal';
                    toggleButton.style.padding = '0';
                    toggleButton.style.cursor = 'pointer';
                    buttonsContainer.appendChild(toggleButton);

                    const milrContainer = document.createElement('div');
                    milrContainer.id = 'milr-stats-container';
                    milrContainer.style.display = 'none';

                    const originalTeamHistory = state.teamHistory;
                    state.teamHistory = state.milrTeamHistory;

                    const renderMilrHitting = () => {
                        if (milrHittingStats.length > 0) {
                            milrHittingStats.sort((a, b) => (getSeasonForSort(a.Season) - getSeasonForSort(b.Season)) || (a.is_sub_row ? 1 : 0) - (b.is_sub_row ? 1 : 0));
                            milrContainer.innerHTML += createStatsTable('MiLR Batting Stats', milrHittingStats, STAT_DEFINITIONS, false, true, true, false);
                        }
                    };
                    const renderMilrPitching = () => {
                        if (milrPitchingStats.length > 0) {
                            milrPitchingStats.sort((a, b) => (getSeasonForSort(a.Season) - getSeasonForSort(b.Season)) || (a.is_sub_row ? 1 : 0) - (b.is_sub_row ? 1 : 0));
                            milrContainer.innerHTML += createStatsTable('MiLR Pitching Stats', milrPitchingStats, STAT_DEFINITIONS, true, true, true, false);
                        }
                    };
                    if (primaryRole === 'pitcher') { renderMilrPitching(); renderMilrHitting(); } else { renderMilrHitting(); renderMilrPitching(); }
                    state.teamHistory = originalTeamHistory;
                    
                    minorLeagueContainers.appendChild(milrContainer);

                    if (localStorage.getItem('milrStatsVisible') === 'true') {
                        milrContainer.style.display = 'block';
                        toggleButton.textContent = '[Hide MiLR]';
                    }
                    toggleButton.addEventListener('click', () => {
                        const isHidden = milrContainer.style.display === 'none';
                        milrContainer.style.display = isHidden ? 'block' : 'none';
                        toggleButton.textContent = isHidden ? '[Hide MiLR]' : '[Show MiLR]';
                        localStorage.setItem('milrStatsVisible', isHidden);
                        if (isHidden) setStickyColumnOffsets();
                    });
                }

                if (hasFcb) {
                    const toggleButton = document.createElement('button');
                    toggleButton.id = 'toggle-fcb-stats';
                    toggleButton.textContent = '[Show FCB]';
                    toggleButton.style.background = 'none';
                    toggleButton.style.border = 'none';
                    toggleButton.style.color = 'var(--text-color)';
                    toggleButton.style.textDecoration = 'underline';
                    toggleButton.style.fontWeight = 'normal';
                    toggleButton.style.padding = '0';
                    toggleButton.style.cursor = 'pointer';
                    if (hasMilr) toggleButton.style.marginLeft = '10px';
                    buttonsContainer.appendChild(toggleButton);

                    const fcbContainer = document.createElement('div');
                    fcbContainer.id = 'fcb-stats-container';
                    fcbContainer.style.display = 'none';

                    const originalTeamHistory = state.teamHistory;
                    state.teamHistory = state.fcbTeamHistory;

                    const renderFcbHitting = () => {
                        if (fcbHittingStats.length > 0) {
                            fcbHittingStats.sort((a, b) => (getSeasonForSort(a.Season) - getSeasonForSort(b.Season)) || (a.is_sub_row ? 1 : 0) - (b.is_sub_row ? 1 : 0));
                            fcbContainer.innerHTML += createStatsTable('FCB Batting Stats', fcbHittingStats, STAT_DEFINITIONS, false, true, false, true);
                        }
                    };
                    const renderFcbPitching = () => {
                        if (fcbPitchingStats.length > 0) {
                            fcbPitchingStats.sort((a, b) => (getSeasonForSort(a.Season) - getSeasonForSort(b.Season)) || (a.is_sub_row ? 1 : 0) - (b.is_sub_row ? 1 : 0));
                            fcbContainer.innerHTML += createStatsTable('FCB Pitching Stats', fcbPitchingStats, STAT_DEFINITIONS, true, true, false, true);
                        }
                    };

                    if (primaryRole === 'pitcher') { renderFcbPitching(); renderFcbHitting(); } else { renderFcbHitting(); renderFcbPitching(); }
                    state.teamHistory = originalTeamHistory;

                    minorLeagueContainers.appendChild(fcbContainer);

                    if (localStorage.getItem('fcbStatsVisible') === 'true') {
                        fcbContainer.style.display = 'block';
                        toggleButton.textContent = '[Hide FCB]';
                    }
                    toggleButton.addEventListener('click', () => {
                        const isHidden = fcbContainer.style.display === 'none';
                        fcbContainer.style.display = isHidden ? 'block' : 'none';
                        toggleButton.textContent = isHidden ? '[Hide FCB]' : '[Show FCB]';
                        localStorage.setItem('fcbStatsVisible', isHidden);
                        if (isHidden) setStickyColumnOffsets();
                    });
                }
                
                elements.statsContentDisplay.appendChild(buttonsContainer);
                elements.statsContentDisplay.appendChild(minorLeagueContainers);
            }


            elements.statsContentDisplay.querySelectorAll('.stats-table').forEach(makeTableSortable);
            setStickyColumnOffsets();
        }
    };

    const makeTableSortable = (table) => {
        const headers = table.querySelectorAll('thead th');
        const groupName = table.previousElementSibling?.textContent;
        const isOpponentStats = groupName === 'Opponent Stats';
        const isHittingTable = groupName?.includes('Batting'); // Changed from Hitting to Batting

        headers.forEach((header, index) => {
            const statName = header.textContent.trim();
            if (['Team'].includes(statName)) return;

            header.style.cursor = 'pointer';

            header.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                if (!tbody) return;

                const lowerIsBetterHitting = ['Avg Diff'];
                const lowerIsBetterPitching = ['ERA', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'RE24', 'HR%', 'BB%', 'ERA-'];
                const opponentStatsHighIsBetter = ['SB', 'CS'];

                let isLowerBetter = false;
                if (isOpponentStats) {
                    if (opponentStatsHighIsBetter.includes(statName)) {
                        isLowerBetter = false;
                    } else {
                        isLowerBetter = true;
                    }
                } else if (isHittingTable) {
                    isLowerBetter = lowerIsBetterHitting.includes(statName);
                } else { // Pitching
                    isLowerBetter = lowerIsBetterPitching.includes(statName);
                }

                const currentSortDir = header.dataset.sortDir;
                let nextSortDir;
                const primarySort = isLowerBetter ? 'asc' : 'desc';
                const secondarySort = isLowerBetter ? 'desc' : 'asc';

                if (!currentSortDir) {
                    nextSortDir = primarySort;
                } else if (currentSortDir === primarySort) {
                    nextSortDir = secondarySort;
                } else {
                    nextSortDir = 'default';
                }

                const rows = Array.from(tbody.querySelectorAll('tr'));
                const staticRows = rows.filter(row => row.classList.contains('career-row') || row.classList.contains('franchise-row'));
                const dataRows = rows.filter(row => !row.classList.contains('career-row') && !row.classList.contains('franchise-row'));

                headers.forEach(h => {
                    delete h.dataset.sortDir;
                    const arrow = h.querySelector('.sort-arrow');
                    if (arrow) arrow.remove();
                });

                if (nextSortDir === 'default') {
                    // Sort by Season (index 0) ascending, then by sub-row status, then by original index
                    dataRows.sort((a, b) => {
                        const aText = a.cells[0].textContent;
                        const bText = b.cells[0].textContent;
                        const seasonA = aText ? parseInt(aText.slice(1)) : 0;
                        const seasonB = bText ? parseInt(bText.slice(1)) : 0;
                        
                        if (seasonA !== seasonB) {
                            return seasonA - seasonB;
                        }

                        // If seasons are the same, main row (not a sub-row) comes first
                        const subRowA = a.classList.contains('sub-row') ? 1 : 0;
                        const subRowB = b.classList.contains('sub-row') ? 1 : 0;
                        if (subRowA !== subRowB) {
                            return subRowA - subRowB;
                        }

                        // If seasons and sub-row status are the same, use original index as tie-breaker
                        const originalIndexA = parseInt(a.dataset.originalIndex || '0');
                        const originalIndexB = parseInt(b.dataset.originalIndex || '0');
                        return originalIndexA - originalIndexB;
                    });
                } else {
                    header.dataset.sortDir = nextSortDir;
                    const arrow = document.createElement('span');
                    arrow.className = 'sort-arrow';
                    arrow.innerHTML = nextSortDir === 'asc' ? ' &uarr;' : ' &darr;';
                    header.appendChild(arrow);

                    const isIP = statName === 'IP';

                    dataRows.sort((a, b) => {
                        const aText = a.cells[index].textContent;
                        const bText = b.cells[index].textContent;

                        let aVal, bVal;

                        if (isIP) {
                            const parseIP = (ip) => {
                                if (ip === '-') return -1;
                                const parts = ip.split('.');
                                return parseFloat(parts[0]) + (parseFloat(parts[1] || 0) / 3);
                            };
                            aVal = parseIP(aText);
                            bVal = parseIP(bText);
                        } else {
                            aVal = aText === '-' ? -Infinity : parseFloat(aText);
                            bVal = bText === '-' ? -Infinity : parseFloat(bText);
                        }

                        if (isNaN(aVal)) aVal = -Infinity;
                        if (isNaN(bVal)) bVal = -Infinity;

                        return nextSortDir === 'asc' ? aVal - bVal : bVal - aVal;
                    });
                }

                tbody.innerHTML = '';
                dataRows.forEach(row => tbody.appendChild(row));
                staticRows.forEach(row => tbody.appendChild(row));
            });
        });
    };

    const displayTeamList = (selectedSeason = null, isMiLR = false, isFcb = false) => {
        elements.teamStatsView.innerHTML = ''; // Clear previous content

        const allSeasons = isMiLR ? Object.keys(state.milrDivisions).sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1))) : (isFcb ? Object.keys(state.fcbDivisions).sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1))) : state.seasonsWithStats);
        const currentSeason = selectedSeason || allSeasons[allSeasons.length - 1]; // Default to latest season
        const currentSeasonIndex = allSeasons.indexOf(currentSeason);
        
        const prevSeason = currentSeasonIndex > 0 ? allSeasons[currentSeasonIndex - 1] : null;
        const nextSeason = currentSeasonIndex < allSeasons.length - 1 ? allSeasons[currentSeasonIndex + 1] : null;

        let leagueParam = isMiLR ? '&league=milr' : (isFcb ? '&league=fcb' : '');
        
        let content = `<div class="team-stats-header">
                        <h2 class="section-title">Standings - 
                            <select id="team-season-select" class="title-season-select">`;
        allSeasons.forEach(season => {
            const isSelected = season === currentSeason ? 'selected' : '';
            content += `<option value="${season}" ${isSelected}>Season ${formatSeasonName(season, isMiLR, isFcb).slice(1)}</option>`;
        });
        content += `        </select>
                        </h2>
                        <div class="season-nav-buttons">`;
        if (prevSeason) {
            content += `<a href="#/team-stats?season=${prevSeason}${leagueParam}" class="season-nav-button">&lt; Prev Season</a>`;
        }
        if (nextSeason) {
            content += `<a href="#/team-stats?season=${nextSeason}${leagueParam}" class="season-nav-button">Next Season &gt;</a>`;
        }
        content += `    </div>
                    </div>`;

        // Calculate records and standings
        const teamRecords = calculateTeamRecords(currentSeason, isMiLR, isFcb);
        const standings = getStandings(currentSeason, teamRecords, isMiLR, isFcb);

        if (Object.keys(standings).length === 0) {
            content += `<p>No standings data available for Season ${currentSeason.slice(1)}.</p>`;
        } else {
            // New container for columns
            content += `<div class="standings-columns">`; // Added
            for (const divisionName in standings) {
                content += `<div class="division-standings-container">`; // Added
                content += `<h3 class="division-title">${divisionName} Division</h3>`;
                content += `<table class="stats-table standings-table">`;
                content += `<thead><tr><th>Team</th><th>W</th><th>L</th><th>PCT</th><th>GB</th></tr></thead>`;
                content += `<tbody>`;
                const divisionTeams = standings[divisionName];
                if (divisionTeams.length > 0) {
                    const leader = divisionTeams[0];
                    divisionTeams.forEach(team => {
                        let gbDisplay;
                        if (team.W === leader.W && team.L === leader.L) {
                            gbDisplay = '-';
                        } else {
                            const gamesBack = ((leader.W - team.W) + (team.L - leader.L)) / 2;
                            gbDisplay = String(gamesBack);
                        }

                        const franchiseKey = getFranchiseKeyFromAbbr(team.teamAbbr, currentSeason, isMiLR, isFcb); // Get franchise key
                        const teamLogoSrc = getTeamLogoBySeason(franchiseKey, currentSeason, isMiLR, isFcb);
                        content += `<tr>`;
                        const teamName = getTeamNameBySeason(franchiseKey, currentSeason, isMiLR, isFcb);
                        content += `<td><span class="team-link" data-team="${encodeURIComponent(franchiseKey)}" data-season="${currentSeason}" data-milr="${isMiLR}" data-fcb="${isFcb}">`; // Use franchiseKey
                        if (teamLogoSrc) {
                            content += `<img src="${teamLogoSrc}" alt="${team.teamAbbr} logo" class="team-list-logo standings-logo"> `;
                        }
                        content += `${teamName}</span></td>`;
                        content += `<td>${team.W}</td>`;
                        content += `<td>${team.L}</td>`;
                        content += `<td>${formatStat('W-L%', team.PCT)}</td>`; // Format PCT
                        content += `<td>${gbDisplay}</td>`;
                        content += `</tr>`;
                    });
                }
                content += `</tbody>`;
                content += `</table>`;
                content += `</div>`; // Added
            }
            content += `</div>`; // Added
        }

        elements.teamStatsView.innerHTML = content;

        // Add event listener for the season select dropdown
        document.getElementById('team-season-select').addEventListener('change', (event) => {
            const newSeason = event.target.value;
            window.location.hash = `#/team-stats?season=${newSeason}${leagueParam}`;
        });
    };

    const displayTeamStatsPage = (teamKey, season, isMiLR = false, isFcb = false) => {
        elements.teamStatsView.innerHTML = ''; // Clear previous content

        // More robust defensive check
        if (!state || !state.hittingStats || !state.pitchingStats) {
            console.error("State or data not fully loaded when trying to display team stats.");
            elements.teamStatsView.innerHTML = "<p>Data is still loading or failed to load. Please try again in a moment.</p>";
            return;
        }

        const hittingStatsToUse = isMiLR ? state.milrHittingStats : (isFcb ? state.fcbHittingStats : state.hittingStats);
        const pitchingStatsToUse = isMiLR ? state.milrPitchingStats : (isFcb ? state.fcbPitchingStats : state.pitchingStats);
        const teamHittingStatsToUse = isMiLR ? state.milrTeamHittingStats : (isFcb ? state.fcbTeamHittingStats : state.teamHittingStats);
        const teamPitchingStatsToUse = isMiLR ? state.milrTeamPitchingStats : (isFcb ? state.fcbTeamPitchingStats : state.teamPitchingStats);

        const seasonNum = parseInt(season.slice(1));
        let actualTeamAbbr = teamKey; // Default to the provided teamKey

        const originalTeamHistory = state.teamHistory;
        state.teamHistory = isMiLR ? state.milrTeamHistory : (isFcb ? state.fcbTeamHistory : state.teamHistory);

        if (!isMiLR && !isFcb) {
            const franchiseEntries = state.teamHistory[teamKey];
            if (franchiseEntries) {
                const entry = franchiseEntries.find(e => seasonNum >= e.start && (e.end === Infinity || seasonNum <= e.end));
                if (entry) {
                    actualTeamAbbr = entry.abbr;
                }
            }
        }

        const seasonHittingStats = hittingStatsToUse.filter(s => s.Season === season && s.Team === actualTeamAbbr);
        const seasonPitchingStats = pitchingStatsToUse.filter(s => s.Season === season && s.Team === actualTeamAbbr);

        const allSeasonsWithStats = isMiLR 
            ? Object.keys(state.milrTeamHistory).map(s => s)
            : (isFcb ? Object.keys(state.fcbTeamHistory).map(s => s) : state.seasonsWithStats);
            
        const allSeasons = allSeasonsWithStats.map(s => parseInt(s.slice(1))).sort((a, b) => a - b);
        const currentSeasonIndex = allSeasons.indexOf(seasonNum);

        let prevSeasonNum = null;
        if (currentSeasonIndex > 0) {
            for (let i = currentSeasonIndex - 1; i >= 0; i--) {
                const sNum = allSeasons[i];
                if (isMiLR) {
                    if (state.milrTeamHistory[`S${sNum}`] && state.milrTeamHistory[`S${sNum}`][teamKey]) {
                        prevSeasonNum = sNum;
                        break;
                    }
                } else if (isFcb) {
                    if (state.fcbTeamHistory[`S${sNum}`] && state.fcbTeamHistory[`S${sNum}`][teamKey]) {
                        prevSeasonNum = sNum;
                        break;
                    }
                } else {
                    if (state.teamHistory[teamKey] && state.teamHistory[teamKey].some(e => sNum >= e.start && sNum <= e.end)) {
                        prevSeasonNum = sNum;
                        break;
                    }
                }
            }
        }

        let nextSeasonNum = null;
        if (currentSeasonIndex < allSeasons.length - 1) {
            for (let i = currentSeasonIndex + 1; i < allSeasons.length; i++) {
                const sNum = allSeasons[i];
                if (isMiLR) {
                    if (state.milrTeamHistory[`S${sNum}`] && state.milrTeamHistory[`S${sNum}`][teamKey]) {
                        nextSeasonNum = sNum;
                        break;
                    }
                } else if (isFcb) {
                    if (state.fcbTeamHistory[`S${sNum}`] && state.fcbTeamHistory[`S${sNum}`][teamKey]) {
                        nextSeasonNum = sNum;
                        break;
                    }
                } else {
                    if (state.teamHistory[teamKey] && state.teamHistory[teamKey].some(e => sNum >= e.start && sNum <= e.end)) {
                        nextSeasonNum = sNum;
                        break;
                    }
                }
            }
        }

        let headerContent = `<div class="team-stats-header">`;
        
        const teamName = getTeamNameBySeason(teamKey, season, isMiLR, isFcb);
        const teamLogoSrc = getTeamLogoBySeason(teamKey, season, isMiLR, isFcb);
        let titleHTML = `<h2 class="section-title">`;
        if (teamLogoSrc) {
            titleHTML += `<img src="${teamLogoSrc}" class="player-team-logo"> `;
        }
        titleHTML += `${teamName} - ${formatSeasonName(season, isMiLR, isFcb).replace('S','Season ')}</h2>`;
        headerContent += titleHTML;

        const leagueParam = isMiLR ? '&league=milr' : (isFcb ? '&league=fcb' : '');
        let navButtonsHTML = `<div class="season-nav-buttons">`;
        if (prevSeasonNum) {
            navButtonsHTML += `<a href="#/team-stats?season=S${prevSeasonNum}&team=${teamKey}${leagueParam}" class="season-nav-button">&lt; Prev Season</a>`;
        }
        if (nextSeasonNum) {
            navButtonsHTML += `<a href="#/team-stats?season=S${nextSeasonNum}&team=${teamKey}${leagueParam}" class="season-nav-button">Next Season &gt;</a>`;
        }
        navButtonsHTML += `</div>`;
        
        headerContent += navButtonsHTML;
        headerContent += `</div>`;

        let content = headerContent;

        if (seasonHittingStats.length > 0) {
            const teamHittingTotals = teamHittingStatsToUse ? teamHittingStatsToUse.find(s => s.Season === season && s.Team === actualTeamAbbr) : null;
            content += createTeamStatsTable('Batting Stats', seasonHittingStats, false, teamHittingTotals, true, isMiLR, isFcb);
        }
        if (seasonPitchingStats.length > 0) {
            const teamPitchingTotals = teamPitchingStatsToUse ? teamPitchingStatsToUse.find(s => s.Season === season && s.Team === actualTeamAbbr) : null;
            content += createTeamStatsTable('Pitching Stats', seasonPitchingStats, true, teamPitchingTotals, true, isMiLR, isFcb);
        }

        elements.teamStatsView.innerHTML = content;
        elements.teamStatsView.querySelectorAll('.stats-table').forEach(makeTableSortable);

        state.teamHistory = originalTeamHistory;

        // Apply default sorting
        elements.teamStatsView.querySelectorAll('.stats-table').forEach(table => {
            const titleElement = table.parentElement.previousElementSibling; // This is the h3 element
            if (titleElement) {
                const title = titleElement.textContent;
                let defaultStat = '';
                if (title.includes('Batting Stats')) {
                    defaultStat = 'PA';
                } else if (title.includes('Pitching Stats')) {
                    defaultStat = 'IP';
                }

                if (defaultStat) {
                    const headers = table.querySelectorAll('thead th');
                    headers.forEach(header => {
                        if (header.textContent.trim() === defaultStat) {
                            header.click(); // Simulate a click to sort
                        }
                    });
                }
            }
        });
    };

    const createTeamStatsTable = (title, stats, isPitching, teamTotals) => {
        let html = `<h3>${title}</h3>`;
        const statKeys = isPitching 
            ? STAT_DEFINITIONS.pitching_tables['Standard Pitching']
            : STAT_DEFINITIONS.batting_tables['Standard Batting'];
        
        const headers = ['Player', ...statKeys.filter(s => s !== 'Season' && s !== 'Team')];

        html += '<div class="stats-table-container">';
        html += '<table class="stats-table">';
        html += '<thead><tr>';
        headers.forEach((stat, colIndex) => {
            const description = STAT_DESCRIPTIONS[stat] || '';
            let th_class = '';
            if (colIndex === 0) {
                th_class = ` class="sticky-col col-0"`;
            }
            html += `<th${th_class} title="${description}">${stat}</th>`;
        });
        html += '</tr></thead>';
        html += '<tbody>';

        stats.sort((a, b) => {
            const aName = state.players[isPitching ? a['Pitcher ID'] : a['Hitter ID']]?.currentName || '';
            const bName = state.players[isPitching ? b['Pitcher ID'] : b['Hitter ID']]?.currentName || '';
            return aName.localeCompare(bName);
        });

        stats.forEach(s => {
            const playerId = isPitching ? s['Pitcher ID'] : s['Hitter ID'];
            const playerName = state.players[playerId]?.currentName || 'Unknown';
            
            html += '<tr>';
            html += `<td class="sticky-col col-0"><span class="player-link" data-player-id="${playerId}" style="cursor: pointer; text-decoration: underline;">${playerName}</span></td>`;
            
            headers.slice(1).forEach(stat => {
                let statKey = stat;
                if (isPitching) {
                    if (stat === 'SO') statKey = 'K';
                    else if (stat === 'ER') statKey = 'R';
                    else if (stat === 'H6') statKey = 'H/6';
                    else if (stat === 'HR6') statKey = 'HR/6';
                    else if (stat === 'BB6') statKey = 'BB/6';
                    else if (stat === 'SO6') statKey = 'K/6';
                    else if (stat === 'SO/BB') statKey = 'K/BB';
                    else if (stat === 'GB%') statKey = 'GB%_A';
                    else if (stat === 'FB%') statKey = 'FB%_A';
                    else if (stat === 'GB/FB') statKey = 'GB/FB_A';
                    else if (stat === 'BA') statKey = 'BAA';
                    else if (stat === 'OBP') statKey = 'OBPA';
                    else if (stat === 'SLG') statKey = 'SLGA';
                    else if (stat === 'OPS') statKey = 'OPSA';
                    else if (stat === 'BABIP') statKey = 'BABIP_A';
                    else if (stat === 'HR%') statKey = 'HR%_A';
                    else if (stat === 'K%') statKey = 'K%_A';
                    else if (stat === 'BB%') statKey = 'BB%_A';
                    else if (stat === 'SB') statKey = 'SB_A';
                    else if (stat === 'CS') statKey = 'CS_A';
                    else if (stat === 'SB%') statKey = 'SB%_A';
                } else { // Hitting
                    if (stat === 'SO') statKey = 'K';
                    else if (stat === 'BA') statKey = 'AVG';
                }
                let value = s[statKey];

                if (isPitching) {
                    const ip = s.IP || 0;
                    const w = s.W || 0;
                    const l = s.L || 0;

                    if (stat === 'ERA' && ip === 0) {
                        value = '-';
                    } else if (stat === 'W-L%' && (w + l) === 0) {
                        value = '-';
                    }
                } else { // Hitting
                    const ab = s.AB || 0;
                    const pa = s.PA || 0;

                    if (stat === 'BA' && ab === 0) {
                        value = '-';
                    } else if ((['OBP', 'SLG', 'OPS'].includes(stat)) && pa === 0) {
                        value = '-';
                    }
                }

                html += `<td>${formatStat(stat, value)}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody>';

        if (teamTotals) {
            html += '<tfoot><tr class="career-row">';
            html += '<td class="sticky-col col-0"><strong>Team Total</strong></td>';
            headers.slice(1).forEach(key => {
                let statKey = key;
                if (isPitching) {
                    if (key === 'SO') statKey = 'K';
                    else if (key === 'ER') statKey = 'R';
                    else if (key === 'H6') statKey = 'H/6';
                    else if (key === 'HR6') statKey = 'HR/6';
                    else if (key === 'BB6') statKey = 'BB/6';
                    else if (key === 'SO6') statKey = 'K/6';
                    else if (key === 'SO/BB') statKey = 'K/BB';
                    else if (key === 'GB%') statKey = 'GB%_A';
                    else if (key === 'FB%') statKey = 'FB%_A';
                    else if (key === 'GB/FB') statKey = 'GB/FB_A';
                    else if (key === 'BA') statKey = 'BAA';
                    else if (key === 'OBP') statKey = 'OBPA';
                    else if (key === 'SLG') statKey = 'SLGA';
                    else if (key === 'OPS') statKey = 'OPSA';
                    else if (key === 'BABIP') statKey = 'BABIP_A';
                    else if (key === 'HR%') statKey = 'HR%_A';
                    else if (key === 'K%') statKey = 'K%_A';
                    else if (key === 'BB%') statKey = 'BB%_A';
                    else if (key === 'SB') statKey = 'SB_A';
                    else if (key === 'CS') statKey = 'CS_A';
                    else if (key === 'SB%') statKey = 'SB%_A';
                } else { // Hitting
                    if (key === 'SO') statKey = 'K';
                    else if (key === 'BA') statKey = 'AVG';
                }
                html += `<td><strong>${formatStat(key, teamTotals[statKey])}</strong></td>`;
            });
            html += '</tr></tfoot>';
        }

        html += '</table></div>';
        return html;
    };

    const createStatsTable = (title, stats, statDefinitions, isPitching, bySeason = false, isMiLR = false, isFcb = false) => {
        let html = `<h3 class="section-title">${title}</h3>`;
        const statGroups = isPitching ? statDefinitions.pitching_tables : statDefinitions.batting_tables;

        for (const groupName in statGroups) {
            const groupStats = statGroups[groupName];
            html += `<h4>${groupName}</h4>`;
            html += '<div class="stats-table-container">';
            html += '<table class="stats-table">';
            html += '<thead><tr>';
            groupStats.forEach((stat, colIndex) => {
                const description = STAT_DESCRIPTIONS[stat] || '';
                let th_class = '';
                if (colIndex < 2) {
                    th_class = ` class="sticky-col col-${colIndex}"`;
                }
                html += `<th${th_class} title="${description}">${stat}</th>`;
            });
            html += '</tr></thead>';
            html += '<tbody>';
            const data = bySeason ? stats : [stats];
            data.forEach((s, index) => {
                let rowClass = '';
                if (bySeason && s.Season === 'Career') {
                    rowClass = 'career-row';
                } else if (bySeason && s.Season === 'Franchise') {
                    rowClass = 'franchise-row sub-row';
                }

                if (s.is_sub_row) {
                    rowClass += ' sub-row';
                }
                html += `<tr class="${rowClass}" data-original-index="${index}">`;
                groupStats.forEach((stat, colIndex) => {
                    let td_class = '';
                    if (colIndex < 2) {
                        td_class = ` class="sticky-col col-${colIndex}"`;
                    }
                    let statKey = stat;
                    if (isPitching) {
                        if (stat === 'SO') statKey = 'K';
                        else if (stat === 'ER') statKey = 'R';
                        else if (stat === 'H6') statKey = 'H/6';
                        else if (stat === 'HR6') statKey = 'HR/6';
                        else if (stat === 'BB6') statKey = 'BB/6';
                        else if (stat === 'SO6') statKey = 'K/6';
                        else if (stat === 'SO/BB') statKey = 'K/BB';
                        else if (stat === 'GB%') statKey = 'GB%_A';
                        else if (stat === 'FB%') statKey = 'FB%_A';
                        else if (stat === 'GB/FB') statKey = 'GB/FB_A';
                        else if (stat === 'BA') statKey = 'BAA';
                        else if (stat === 'OBP') statKey = 'OBPA';
                        else if (stat === 'SLG') statKey = 'SLGA';
                        else if (stat === 'OPS') statKey = 'OPSA';
                        else if (stat === 'BABIP') statKey = 'BABIP_A';
                        else if (stat === 'HR%') statKey = 'HR%_A';
                        else if (stat === 'K%') statKey = 'K%_A';
                        else if (stat === 'BB%') statKey = 'BB%_A';
                        else if (stat === 'SB') statKey = 'SB_A';
                        else if (stat === 'CS') statKey = 'CS_A';
                        else if (stat === 'SB%') statKey = 'SB%_A';
                    } else { // Hitting
                        if (stat === 'SO') statKey = 'K';
                        else if (stat === 'BA') statKey = 'AVG';
                    }

                    let value; // Declare 'value' here

                    if (stat === 'Season' && s.Season === 'Franchise') {
                        html += `<td${td_class}></td>`;
                    } else if (stat === 'Team') {
                        value = s.Team || '';
                        const isMultiTeam = /^\d+TM$/.test(value);
                        if (s.Season !== 'Career' && s.Season !== 'Franchise' && value && !isMultiTeam) { // Only make season-specific teams clickable
                            const franchiseKey = getFranchiseKeyFromAbbr(value, s.Season, isMiLR, isFcb);
                            html += `<td${td_class}><span class="team-link" data-team="${encodeURIComponent(franchiseKey)}" data-season="${s.Season}" data-milr="${isMiLR}" data-fcb="${isFcb}" style="cursor: pointer; text-decoration: underline;">${value}</span></td>`;
                        } else {
                            html += `<td${td_class}>${formatStat(stat, value)}</td>`;
                        }
                    } else {
                        value = s[statKey]; // Assign 'value' here for non-Team stats

                        if (stat === 'Season') {
                            value = formatSeasonName(value, isMiLR, isFcb);
                        }

                        if (isPitching) {
                            const ip = s.IP || 0;
                            const bb = s.BB || 0;
                            const w = s.W || 0;
                            const l = s.L || 0;
                            const bf = s.BF || 0;
                            const sb_a = s.SB_A || 0;
                            const cs_a = s.CS_A || 0;

                            if (groupName === 'Opponent Stats') {
                                if ((['BA', 'OBP', 'SLG', 'OPS', 'BABIP'].includes(stat)) && bf === 0) {
                                    value = '-';
                                } else if (stat === 'SB%' && (sb_a + cs_a) === 0) {
                                    value = '-';
                                }
                            } else {
                                if ((['ERA', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'SO6'].includes(stat)) && ip === 0) {
                                    value = '-';
                                } else if (stat === 'SO/BB' && bb === 0) {
                                    value = '-';
                                } else if (stat === 'W-L%' && (w + l) === 0) {
                                    value = '-';
                                } else if ((['HR%', 'K%', 'BB%', 'GB%', 'FB%', 'GB/FB'].includes(stat)) && bf === 0) {
                                    value = '-';
                                }
                            }
                        } else { // Hitting
                            const ab = s.AB || 0;
                            const pa = s.PA || 0;
                            const sb = s.SB || 0;
                            const cs = s.CS || 0;

                            if ((['BA', 'ISO', 'BABIP', 'OPS+', 'SLG', 'OPS'].includes(stat)) && ab === 0) {
                                value = '-';
                            } else if ((['OBP', 'HR%', 'SO%', 'BB%', 'GB%', 'FB%', 'GB/FB'].includes(stat)) && pa === 0) {
                                value = '-';
                            } else if (stat === 'SB%' && (sb + cs) === 0) {
                                value = '-';
                            }
                        }

                        let cellHTML = `<td${td_class}>${formatStat(stat, value)}</td>`;
                        if (stat === 'Type' && value) {
                            const typeCategory = isPitching ? 'pitching' : 'batting';
                            if (state.typeDefinitions[typeCategory] && state.typeDefinitions[typeCategory][value]) {
                                cellHTML = `<td${td_class} title="${state.typeDefinitions[typeCategory][value]}">${formatStat(stat, value)}</td>`;
                            }
                        }
                        html += cellHTML;
                    }
                });
                html += '</tr>';
            });
            html += '</tbody></table></div>';
        }
        return html;
    };
                    
    const formatStat = (stat, value) => {
        if (value === undefined || value === null) return '-';
        if (typeof value === 'number') {
            if (['AVG', 'OBP', 'SLG', 'OPS', 'ISO', 'BA', 'BAA', 'OBPA', 'SLGA', 'OPSA', 'BABIP', 'BABIP_A', 'W-L%'].includes(stat)) {
                const formatted = value.toFixed(3);
                if (formatted.startsWith('0.')) {
                    return formatted.substring(1);
                }
                return formatted;
            }
            if (['ERA', 'WHIP', 'FIP', 'H/6', 'HR/6', 'BB/6', 'K/6', 'K/BB', 'GB/FB', 'GB/FB_A'].includes(stat)) {
                return value.toFixed(2);
            }
            if (['H6', 'HR6', 'BB6', 'SO6', 'SO/BB'].includes(stat)) {
                return value.toFixed(1);
            }
            if (stat === 'IP') {
                const innings = Math.floor(value);
                const outs = Math.round((value - innings) * 3);
                if (outs === 3) {
                    return (innings + 1).toFixed(1);
                }
                return `${innings}.${outs}`;
            }
            if (['WAR', 'RE24', 'WPA', 'Avg Diff'].includes(stat)) {
                return value.toFixed(2);
            }
            if (stat.includes('%')) {
                return (value * 100).toFixed(1);
            }
            return Math.round(value);
        }
        return value;
    };

    const calculateTeamRecords = (season, isMiLR = false, isFcb = false) => {
        const teamRecords = {};
        const teamPitchingStatsToUse = isMiLR ? state.milrTeamPitchingStats : (isFcb ? state.fcbTeamPitchingStats : state.teamPitchingStats);
        const seasonTeamPitchingStats = teamPitchingStatsToUse.filter(s => s.Season === season);
        const totalGamesInSeason = state.seasons[season] || 0;

        seasonTeamPitchingStats.forEach(teamStat => {
            const teamAbbr = teamStat.Team;
            if (teamAbbr) {
                const wins = teamStat.W || 0;
                const losses = teamStat.L || 0;
                const gamesPlayed = wins + losses;
                const ties = Math.max(0, totalGamesInSeason - gamesPlayed);

                teamRecords[teamAbbr] = {
                    W: wins,
                    L: losses,
                    T: ties,
                    PCT: teamStat['W-L%'] || 0
                };
            }
        });
        return teamRecords;
    };

    const getStandings = (season, teamRecords, isMiLR = false, isFcb = false) => {
        const standings = {};
        const divisionsForSeason = getDivisionsForSeason(season, isMiLR, isFcb); // Use helper

        if (!divisionsForSeason) {
            console.warn(`No division data found for season ${season}`);
            return {};
        }

        for (const divisionName in divisionsForSeason) {
            const teamsInDivision = divisionsForSeason[divisionName];
            const divisionStandings = [];

            teamsInDivision.forEach(teamAbbr => {
                const record = teamRecords[teamAbbr];
                if (record) {
                    divisionStandings.push({ teamAbbr, ...record });
                } else {
                    // Team exists in division but no record found for season (e.g., new team)
                    divisionStandings.push({ teamAbbr, W: 0, L: 0, T: 0, PCT: 0 });
                }
            });

            // Sort teams within the division: highest PCT first
            divisionStandings.sort((a, b) => b.PCT - a.PCT);
            standings[divisionName] = divisionStandings;
        }
        return standings;
    };

    const getDivisionsForSeason = (season, isMiLR = false, isFcb = false) => {
        const divisionsToUse = isMiLR ? state.milrDivisions : (isFcb ? state.fcbDivisions : state.divisions);
        let divisions = divisionsToUse[season];
        // If the value is a string, it's a reference to another season
        if (typeof divisions === 'string') {
            return divisionsToUse[divisions]; // Resolve the reference
        }
        return divisions;
    };

    const getFranchiseKeyFromAbbr = (abbr, season, isMiLR = false, isFcb = false) => {
        const seasonNum = parseInt(season.slice(1));
        const teamHistoryToUse = isMiLR ? state.milrTeamHistory : (isFcb ? state.fcbTeamHistory : state.teamHistory);

        if (isMiLR || isFcb) {
            for (const franchiseKey in teamHistoryToUse) {
                const teamName = teamHistoryToUse[franchiseKey];
                if (teamName === abbr) {
                    return franchiseKey;
                }
            }
            return abbr;
        }

        for (const franchiseKey in teamHistoryToUse) {
            const entries = teamHistoryToUse[franchiseKey];
            if (Array.isArray(entries) && entries.some(entry => entry.abbr === abbr && seasonNum >= entry.start && (entry.end === 9999 || seasonNum <= entry.end))) {
                return franchiseKey;
            }
        }
        return abbr; // Fallback if not found, assume abbr is the franchise key
    };

    const getTeamNameBySeason = (franchiseKey, season, isMiLR = false, isFcb = false) => {
        const seasonNum = parseInt(season.slice(1));
        if (isNaN(seasonNum)) return franchiseKey;

        const historyToUse = isMiLR ? state.milrTeamHistory : (isFcb ? state.fcbTeamHistory : state.teamHistory);

        if (isMiLR || isFcb) {
            if (historyToUse[season] && historyToUse[season][franchiseKey]) {
                return historyToUse[season][franchiseKey];
            }
        } else {
            const teamNameEntries = historyToUse[franchiseKey];
            if (teamNameEntries) {
                const entry = teamNameEntries.find(e => seasonNum >= e.start && (e.end === 9999 || seasonNum <= e.end));
                if (entry) {
                    return entry.name;
                }
            }
        }
        // Fallback for when player is on a team that doesn't exist that season
        const milrHistory = state.milrTeamHistory;
        if (milrHistory[season] && milrHistory[season][franchiseKey]) {
            return milrHistory[season][franchiseKey];
        }

        const fcbHistory = state.fcbTeamHistory;
        if (fcbHistory[season] && fcbHistory[season][franchiseKey]) {
            return fcbHistory[season][franchiseKey];
        }

        return franchiseKey;
    };

const getTeamLogoBySeason = (franchiseKey, season, isMiLR = false, isFcb = false) => {
    if (!franchiseKey || !season) return null;
    const seasonNum = parseInt(season.slice(1));
    if (isNaN(seasonNum)) return null;

    if (isMiLR || isFcb) {
        return null;
    }

    const franchise = state.teamHistory[franchiseKey];
    if (!franchise) return null;

    const teamInfo = franchise.find(t => seasonNum >= t.start && seasonNum <= t.end);
    if (!teamInfo) return null;

    const isLightMode = document.documentElement.classList.contains('light-mode');
    return isLightMode ? teamInfo.logo_light : teamInfo.logo_dark;
};
                    
    loadData();
});