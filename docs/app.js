document.addEventListener('DOMContentLoaded', () => {
    const API = {
        hitting: './data/hitting_stats.json',
        pitching: './data/pitching_stats.json',
        players: './data/player_id_map.json',
        seasons: './data/season_games_map.json',
        scouting: './data/scouting_reports.json',
        glossary: './data/glossary.json'
    };

    const state = {
        hittingStats: [],
        pitchingStats: [],
        players: {},
        seasons: {},
        scoutingReports: {},
        glossaryData: {},
        playerMap: new Map(),
        currentPlayerId: null
    };

    const elements = {
        loader: document.getElementById('loader'),
        app: document.getElementById('app'),
        
        statsView: document.getElementById('stats-view'),
        leaderboardsView: document.getElementById('leaderboards-view'),
        glossaryView: document.getElementById('glossary-view'),
        
        statsTab: document.getElementById('stats-tab'),
        leaderboardsTab: document.getElementById('leaderboards-tab'),
        scoutingTab: document.getElementById('scouting-tab'),
        glossaryTab: document.getElementById('glossary-tab'),

        playerSearch: document.getElementById('player-search'),
        playerSuggestions: document.getElementById('player-suggestions'),
        statsContentDisplay: document.getElementById('stats-content-display'),

        leaderboardTypeSelect: document.getElementById('leaderboard-type-select'),
        leaderboardStatSelect: document.getElementById('leaderboard-stat-select'),
        leaderboardButton: document.getElementById('leaderboard-button'),
        leaderboardLength: document.getElementById('leaderboard-length'),
        leaderboardTeamFilter: document.getElementById('leaderboard-team-filter'),
        reverseSort: document.getElementById('reverse-sort'),
        leaderboardsContentDisplay: document.getElementById('leaderboards-content-display')
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
        hitting_tables: {
            'Hitting Stats': ['Season', 'Team', 'WAR', 'G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'IBB', 'SO', 'Auto K', 'BA', 'OBP', 'SLG', 'OPS', 'OPS+'],
            'Advanced Hitting': ['Season', 'Team', 'TB', 'GIDP', 'SH', 'SF', 'BABIP', 'ISO', 'HR%', 'SO%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24', 'SB%', 'Avg Diff']
        },
        pitching_tables: {
            'Pitching Stats': ['Season', 'Team', 'WAR', 'W', 'L', 'W-L%', 'ERA', 'G', 'GS', 'GF', 'CG', 'SHO', 'SV', 'HLD', 'IP', 'H', 'ER', 'HR', 'BB', 'IBB', 'Auto BB', 'SO', 'BF', 'ERA+'],
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
        'ERA+': 'ERA adjusted for park and league',
        'FIP': 'Fielding Independent Pitching',
        'WHIP': 'Walks + Hits per Inning Pitched',
        'H6': 'Hits per 6 Innings',
        'HR6': 'Home Runs per 6 Innings',
        'BB6': 'Walks per 6 Innings',
        'SO6': 'Strikeouts per 6 Innings',
        'SO/BB': 'Strikeout to Walk Ratio',
        'K%': 'Strikeout Percentage',
    };

    const LEADERBOARD_ONLY_STATS = {
        hitting: ['1B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO'],
        pitching: ['1B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO']
    };

    const teamFranchises = {
        "ANA": [{ abbr: "CLE", start: 4, end: 5 }, { abbr: "LAA", start: 6, end: 8 }, {abbr: "ANA", start: 9, end: Infinity }],
        "ARI": [{ abbr: "ARI", start: 1, end: Infinity }],
        "ATL": [{ abbr: "ATL", start: 1, end: 1 }, { abbr: "MTL", start: 2, end: 3 }, { abbr: "ATL", start: 4, end: Infinity }],
        "BAL": [{ abbr: "BAL", start: 4, end: Infinity }],
        "BOS": [{ abbr: "BOS", start: 2, end: Infinity }],
        "CHC": [{ abbr: "CHC", start: 3, end: Infinity }],
        "CIN": [{ abbr: "CLE", start: 2, end: 3 }, { abbr: "CIN", start: 4, end: Infinity }],
        "CLE": [{ abbr: "TEX", start: 2, end: 5 }, { abbr: "CLE", start: 6, end: Infinity }],
        "COL": [{ abbr: "COL", start: 2, end: Infinity }],
        "CWS": [{ abbr: "CWS", start: 4, end: Infinity }],
        "DET": [{ abbr: "DET", start: 1, end: Infinity }],
        "FLA": [{ abbr: "MIA", start: 3, end: 10 }, { abbr: "FLA", start: 11, end: Infinity }],
        "HOU": [{ abbr: "HOU", start: 1, end: Infinity }],
        "KCR": [{ abbr: "KCR", start: 3, end: Infinity }],
        "LAD": [{ abbr: "LAD", start: 2, end: Infinity }],
        "MIL": [{ abbr: "NYM", start: 1, end: 1 }, { abbr: "MIL", start: 2, end: Infinity }],
        "MIN": [{ abbr: "MIN", start: 4, end: Infinity }],
        "MIN (S1-2)": [{ abbr: "MIN", start: 1, end: 2}],
        "MTL": [{ abbr: "MTL", start: 4, end: Infinity }],
        "NYM": [{ abbr: "NYM", start: 3, end: Infinity }],
        "NYY": [{ abbr: "NYY", start: 3, end: Infinity }],
        "OAK": [{ abbr: "OAK", start: 1, end: Infinity }],
        "PHI": [{ abbr: "PHI", start: 1, end: Infinity }],
        "PIT": [{ abbr: "PIT", start: 1, end: Infinity }],
        "SDP": [{ abbr: "SDP", start: 2, end: Infinity }],
        "SEA": [{ abbr: "SEA", start: 4, end: Infinity }],
        "SEA (S2)": [{ abbr: "SEA", start: 2, end: 2}],
        "SFG": [{ abbr: "SFG", start: 2, end: Infinity }],
        "STL": [{ abbr: "STL", start: 2, end: Infinity }],
        "TBR": [{ abbr: "TBD", start: 2, end: 2 }, { abbr: "TBR", start: 3, end: Infinity }],
        "TEX": [{ abbr: "BAL", start: 1, end: 2 }, { abbr: "LAA", start: 3, end: 5 }, { abbr: "TEX", start: 6, end: Infinity }],
        "TOR": [{ abbr: "TOR", start: 1, end: Infinity }],
        "WSH (S1-2)": [{ abbr: "WAS", start: 1, end: 1 }, { abbr: "WSH", start: 2, end: 2 }]
    };

    const loadData = async () => {
        try {
            const [hitting, pitching, players, seasons, scouting, glossary] = await Promise.all([
                fetch(API.hitting).then(res => res.json()),
                fetch(API.pitching).then(res => res.json()),
                fetch(API.players).then(res => res.json()),
                fetch(API.seasons).then(res => res.json()),
                fetch(API.scouting).then(res => res.json()),
                fetch(API.glossary).then(res => res.json())
            ]);

            state.hittingStats = parseCompactData(hitting);
            state.pitchingStats = parseCompactData(pitching);
            state.players = players;
            state.seasons = seasons;
            state.scoutingReports = scouting;
            state.glossaryData = glossary;

            for (const id in players) {
                const player = players[id];
                state.playerMap.set(player.currentName.toLowerCase(), parseInt(id));
                if (player.formerNames) {
                    player.formerNames.forEach(name => {
                        state.playerMap.set(name.toLowerCase(), parseInt(id));
                    });
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

    const updateView = () => {
        const path = window.location.hash || '#/stats';
        
        if (path !== '#/stats' && path !== '#/leaderboards' && path !== '#/glossary' && path !== '#/scouting') {
            window.location.hash = '#/stats';
            return;
        }

        const isStats = path === '#/stats';
        const isLeaderboards = path === '#/leaderboards';
        const isGlossary = path === '#/glossary';
        const isScouting = path === '#/scouting';

        elements.statsView.style.display = (isStats || isScouting) ? 'block' : 'none';
        elements.leaderboardsView.style.display = isLeaderboards ? 'block' : 'none';
        elements.glossaryView.style.display = isGlossary ? 'flex' : 'none';

        elements.statsTab.classList.toggle('active', isStats);
        elements.leaderboardsTab.classList.toggle('active', isLeaderboards);
        elements.scoutingTab.classList.toggle('active', isScouting);
        elements.glossaryTab.classList.toggle('active', isGlossary);

        if (isStats || isScouting) {
            if (state.currentPlayerId) {
                displayPlayerPage(state.currentPlayerId);
            } else {
                elements.statsContentDisplay.innerHTML = '<p>Search for a player to see their stats.</p>';
            }
        }

        if (isLeaderboards && elements.leaderboardStatSelect.options.length <= 1) {
            populateLeaderboardStatSelect();
        }
        if (isGlossary) {
            renderGlossary();
        }
    };

    const renderGlossary = () => {
        const sidebar = document.getElementById('glossary-sidebar');
        const content = document.getElementById('glossary-content');
        
        sidebar.innerHTML = '';
        content.innerHTML = '';

        const statList = document.createElement('ul');
        statList.className = 'glossary-stat-list';

        const stats = Object.keys(state.glossaryData);

        stats.forEach(stat => {
            const statItem = document.createElement('li');
            statItem.textContent = `${state.glossaryData[stat].name} (${stat})`;
            statItem.dataset.stat = stat;
            statItem.addEventListener('click', () => {
                displayGlossaryEntry(stat);
                // Active class handling
                document.querySelectorAll('.glossary-stat-list li').forEach(item => item.classList.remove('active'));
                statItem.classList.add('active');
            });
            statList.appendChild(statItem);
        });

        sidebar.appendChild(statList);

        // Display the first stat by default
        if (stats.length > 0) {
            displayGlossaryEntry(stats[0]);
            sidebar.querySelector('li').classList.add('active');
        }
    };

    const displayGlossaryEntry = (stat) => {
        const content = document.getElementById('glossary-content');
        const entry = state.glossaryData[stat];
        if (!entry) {
            content.innerHTML = '<p>Select a stat from the sidebar.</p>';
            return;
        }

        let entryHTML = `<h2 class="section-title">${entry.name} (${stat})</h2>`;
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
            entry.sections.forEach(section => {
                entryHTML += `<h4>${section.title}</h4>`;
                entryHTML += section.content;
            });
        }
        
        content.innerHTML = entryHTML;
    };

    const initializeApp = () => {
        window.addEventListener('hashchange', updateView);
        updateView(); // Initial view
        
        elements.playerSearch.addEventListener('input', handlePlayerSearch);
        elements.leaderboardButton.addEventListener('click', handleLeaderboardView);
        elements.leaderboardTypeSelect.addEventListener('change', populateLeaderboardStatSelect);
        populateTeamFilter();

        elements.leaderboardsContentDisplay.addEventListener('click', (event) => {
            const cell = event.target.closest('.player-name-cell');
            if (cell && cell.dataset.playerId) {
                const playerId = parseInt(cell.dataset.playerId, 10);
                if (!isNaN(playerId)) {
                    const playerName = state.players[playerId].currentName;
                    
                    window.location.hash = '#/stats';
                    
                    elements.playerSearch.value = playerName;
                    elements.playerSuggestions.innerHTML = '';
                    displayPlayerPage(playerId);
                }
            }
        });
    };

    const populateLeaderboardStatSelect = () => {
        const type = elements.leaderboardTypeSelect.value;
        const statSelect = elements.leaderboardStatSelect;
        statSelect.innerHTML = '<option value="">-- Select Stat --</option>'; // Clear existing options

        const stats = (type === 'batting') 
            ? Object.values(STAT_DEFINITIONS.hitting_tables).flat().concat(LEADERBOARD_ONLY_STATS.hitting)
            : Object.values(STAT_DEFINITIONS.pitching_tables).flat().concat(LEADERBOARD_ONLY_STATS.pitching);

        const uniqueStats = [...new Set(stats)].sort();
        uniqueStats.forEach(stat => {
            if (stat === 'Season' || stat === 'Team') return;
            const option = document.createElement('option');
            option.value = stat;
            option.textContent = stat;
            statSelect.appendChild(option);
        });
    };

                    const handleLeaderboardView = () => {

                        const stat = elements.leaderboardStatSelect.value;

                        if (!stat) return;

                

                        const type = elements.leaderboardTypeSelect.value;

                        const selectedTeam = elements.leaderboardTeamFilter.value;

                        const isHitting = type === 'batting';

                        const reverseSort = elements.reverseSort.checked;

                        const sortModifier = reverseSort ? -1 : 1;

                        

                        let statKey = stat;

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

                                'HR%', 'K%', 'BB%', 'GB%', 'FB%', 'GB/FB'

                            ];

                        }

                        const lowerIsBetter = lowerIsBetterStats.includes(stat);

                

                        if (stat === 'W-L%') {

                            const data = state.pitchingStats;

                

                            // All-Time

                            const careerData = data.filter(d => d.Season === 'Career');

                            const min_decisions_career = 10;

                            let allTimeLeaderboard = careerData.filter(p => ((p.W || 0) + (p.L || 0)) >= min_decisions_career);

                            allTimeLeaderboard.sort((a, b) => sortModifier * ((b['W-L%'] || 0) - (a['W-L%'] || 0)));

                            leaderboards['All-Time'] = {

                                type: 'all-time',

                                data: allTimeLeaderboard,

                                isCountingStat: false,

                                min_qual: min_decisions_career,

                                min_qual_key: 'Decisions'

                            };

                

                            // Single Season

                            let singleSeasonData = data.filter(d => d.Season !== 'Career');

                            if (selectedTeam) {
                                const franchise = teamFranchises[selectedTeam];
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

                            const min_decisions_season = 3;

                            let singleSeasonLeaderboard = singleSeasonData.filter(p => ((p.W || 0) + (p.L || 0)) >= min_decisions_season);

                            singleSeasonLeaderboard.sort((a, b) => sortModifier * ((b['W-L%'] || 0) - (a['W-L%'] || 0)));

                            leaderboards['Single Season'] = {

                                type: 'single-season',

                                data: singleSeasonLeaderboard,

                                isCountingStat: false,

                                min_qual: min_decisions_season,

                                min_qual_key: 'Decisions'

                            };

                

                            // Individual Seasons

                            const allSeasons = Object.keys(state.seasons).sort((a, b) => parseInt(b.slice(1)) - parseInt(a.slice(1)));

                            for (const season of allSeasons) {

                                let seasonData = data.filter(d => d.Season === season);

                                if (selectedTeam) {
                                    const franchise = teamFranchises[selectedTeam];
                                    if (franchise) {
                                        const seasonNum = parseInt(season.slice(1));
                                        const correctAbbr = franchise.find(f => seasonNum >= f.start && seasonNum <= f.end)?.abbr;
                                        if (correctAbbr) {
                                            seasonData = seasonData.filter(p => p.Team === correctAbbr);
                                        } else {
                                            seasonData = []; // This franchise didn't exist this season.
                                        }
                                    } else {
                                        seasonData = seasonData.filter(p => p.Team === selectedTeam);
                                    }
                                } else {
                                    seasonData = seasonData.filter(p => !p.is_sub_row);
                                }

                                let leaderboardData = seasonData.filter(p => ((p.W || 0) + (p.L || 0)) >= min_decisions_season);

                                leaderboardData.sort((a, b) => sortModifier * ((b['W-L%'] || 0) - (a['W-L%'] || 0)));

                                leaderboards[season] = {

                                    type: 'season',

                                    data: leaderboardData,

                                    isCountingStat: false,

                                    min_qual: min_decisions_season,

                                    min_qual_key: 'Decisions'

                                };

                            }

                        } else {

                            const countingStats = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'IBB', 'SO', 'Auto K', 'TB', 'GIDP', 'SH', 'SF', 'W', 'L', 'GS', 'GF', 'CG', 'SHO', 'SV', 'HLD', 'IP', 'ER', 'BF', '1B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO'];

                            const isCountingStat = countingStats.includes(stat);

                

                            let data, min_qual_key;

                            if (isHitting) {

                                data = state.hittingStats;

                                min_qual_key = 'PA';

                                if (stat === 'GO') {

                                    data.forEach(p => { p.GO = (p.LGO || 0) + (p.RGO || 0); });

                                }

                            } else {

                                data = state.pitchingStats;

                                min_qual_key = 'IP';

                                if (stat === 'GO') {

                                    data.forEach(p => { p.GO = (p.LGO || 0) + (p.RGO || 0); });

                                }

                            }

                

                            // All-Time

                            const careerData = data.filter(d => d.Season === 'Career');

                            const min_qual_career = isHitting ? 100 : 50;

                            let allTimeLeaderboard = isCountingStat ? careerData : careerData.filter(p => (p[min_qual_key] || 0) >= min_qual_career);

                            if (isCountingStat) {

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

                            let singleSeasonData = data.filter(d => d.Season !== 'Career');

                            if (selectedTeam) {
                                const franchise = teamFranchises[selectedTeam];
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

                            let singleSeasonLeaderboard;

                            if (isCountingStat) {

                                singleSeasonLeaderboard = singleSeasonData;

                            } else {

                                singleSeasonLeaderboard = singleSeasonData.filter(p => {

                                    const gamesInSeason = state.seasons[p.Season] || 0;

                                    const season_min_qual = isHitting ? gamesInSeason * 2 : gamesInSeason * 1;

                                    return (p[min_qual_key] || 0) >= season_min_qual;

                                });

                            }

                            if (isCountingStat) {

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

                            const allSeasons = Object.keys(state.seasons).sort((a, b) => parseInt(b.slice(1)) - parseInt(a.slice(1)));

                            for (const season of allSeasons) {

                                const min_qual = isHitting ? (state.seasons[season] || 0) * 2 : (state.seasons[season] || 0) * 1;

                                let seasonData = data.filter(d => d.Season === season);

                                if (selectedTeam) {
                                    const franchise = teamFranchises[selectedTeam];
                                    if (franchise) {
                                        const seasonNum = parseInt(season.slice(1));
                                        const correctAbbr = franchise.find(f => seasonNum >= f.start && seasonNum <= f.end)?.abbr;
                                        if (correctAbbr) {
                                            seasonData = seasonData.filter(p => p.Team === correctAbbr);
                                        } else {
                                            seasonData = []; // This franchise didn't exist this season.
                                        }
                                    } else {
                                        seasonData = seasonData.filter(p => p.Team === selectedTeam);
                                    }
                                } else {
                                    seasonData = seasonData.filter(p => !p.is_sub_row);
                                }

                                let leaderboardData = isCountingStat ? seasonData : seasonData.filter(p => (p[min_qual_key] || 0) >= min_qual);

                                if (isCountingStat) {

                                    leaderboardData = leaderboardData.filter(p => p[statKey] > 0);

                                }

                                leaderboardData.sort((a, b) => sortModifier * (lowerIsBetter ? (a[statKey] || 0) - (b[statKey] || 0) : (b[statKey] || 0) - (a[statKey] || 0)));

                                leaderboards[season] = {

                                    type: 'season',

                                    data: leaderboardData,

                                    isCountingStat: isCountingStat,

                                    min_qual: min_qual,

                                    min_qual_key: min_qual_key

                                };

                            }

                        }

                

                        renderLeaderboardGrid(leaderboards, stat, statKey, isHitting);

                    };

    const renderLeaderboardGrid = (leaderboards, stat, statKey, isHitting) => {
        const leaderboardSize = parseInt(elements.leaderboardLength.value) || 10;
        elements.leaderboardsContentDisplay.innerHTML = `<h2 class="section-title">${stat} Leaderboards</h2>`;

        const gridContainer = document.createElement('div');
        gridContainer.className = 'leaderboard-grid';

        const gridOrder = ['All-Time', 'Single Season', ...Object.keys(state.seasons).sort((a, b) => parseInt(b.slice(1)) - parseInt(a.slice(1)))];

        for (const key of gridOrder) {
            const leaderboardInfo = leaderboards[key];
            if (!leaderboardInfo) continue;
            
            const fullLeaderboard = leaderboardInfo.data;
            let leaderboard = fullLeaderboard.slice(0, leaderboardSize);
            let tieInfo = null;

            if (fullLeaderboard.length > leaderboardSize && fullLeaderboard[leaderboardSize-1][statKey] === fullLeaderboard[leaderboardSize][statKey]) {
                const tieValue = fullLeaderboard[leaderboardSize-1][statKey];
                if (tieValue !== 0 && tieValue !== null && tieValue !== undefined) {
                    let firstTieIndex = leaderboardSize - 1;
                    while (firstTieIndex > 0 && fullLeaderboard[firstTieIndex - 1][statKey] === tieValue) {
                        firstTieIndex--;
                    }
                    const tieCount = fullLeaderboard.filter(p => p[statKey] === tieValue).length;
                    leaderboard = fullLeaderboard.slice(0, firstTieIndex);
                    tieInfo = { count: tieCount, value: tieValue };
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
                title = `<h4>Season ${key.slice(1)}</h4>`;
            }

            if (!leaderboardInfo.isCountingStat && leaderboardInfo.type !== 'single-season') {
                const qual_text = `${leaderboardInfo.min_qual} ${leaderboardInfo.min_qual_key}`;
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
            let lastValue = null;
            let lastRank = 0;
            leaderboard.forEach((p, i) => {
                const rank = i + 1;
                const currentValue = p[statKey];

                let displayRank;
                if (i > 0 && currentValue === lastValue) {
                    displayRank = lastRank;
                } else {
                    displayRank = rank;
                }

                const id = p[isHitting ? 'Hitter ID' : 'Pitcher ID'];
                const playerName = state.players[id] ? state.players[id].currentName : 'Unknown';
                let row = `<tr><td>${displayRank}</td><td class="player-name-cell" data-player-id="${id}" style="cursor: pointer; text-decoration: underline;">${playerName}</td>`;
                if (leaderboardInfo.type === 'season') row += `<td>${p.Team || ''}</td>`;
                if (leaderboardInfo.type === 'single-season') row += `<td>${p.Season.slice(1)}</td>`;
                row += `<td>${formatStat(stat, p[statKey])}</td></tr>`;
                tbody.innerHTML += row;

                lastValue = currentValue;
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

    const displayScoutingReport = (playerId) => {
        const report = state.scoutingReports[playerId];
        if (!report) {
            elements.statsContentDisplay.innerHTML += `<p>No scouting report available.</p>`;
            return;
        }
        elements.statsContentDisplay.innerHTML += `<h3 class="section-title">Scouting Report</h3>`;

        const mainGrid = document.createElement('div');
        mainGrid.className = 'scouting-report-grid';

        const leftColumn = document.createElement('div');
        leftColumn.className = 'scouting-report-left';

        const rightColumn = document.createElement('div');
        rightColumn.className = 'scouting-report-right';

        // --- Favorite Pitches ---
        if (report.top_5_pitches) {
            const section = document.createElement('div');
            section.className = 'scouting-section';
            const title = document.createElement('h3');
            title.textContent = 'Favorite Pitches';
            section.appendChild(title);

            const pitches = Object.entries(report.top_5_pitches)
                .map(([pitch, count]) => ({ pitch, count }))
                .sort((a, b) => b.count - a.count);

            if (pitches.length > 0) {
                const container = document.createElement('div');
                container.className = 'horizontal-items-container';
                pitches.forEach(p => {
                    const item = document.createElement('div');
                    item.className = 'info-item';
                    const valueDiv = document.createElement('div');
                    valueDiv.className = 'info-item-value';
                    valueDiv.textContent = p.pitch;
                    const labelDiv = document.createElement('div');
                    labelDiv.className = 'info-item-label';
                    labelDiv.textContent = `${p.count}x`;
                    item.appendChild(valueDiv);
                    item.appendChild(labelDiv);
                    container.appendChild(item);
                });
                section.appendChild(container);
            } else {
                section.innerHTML += '<p>No pitch data available.</p>';
            }
            leftColumn.appendChild(section);
        }

        // --- Tendencies ---
        if (report.tendencies) {
            const section = document.createElement('div');
            section.className = 'scouting-section';
            const title = document.createElement('h3');
            title.textContent = 'Tendencies';
            section.appendChild(title);

            const tendencyNameMap = {
                'repeat_percentage': 'Double Up Rate',
                'has_tripled_up': 'Ever Tripled Up?',
                'swing_match_rate': 'Previous Swing Rate',
                'diff_match_rate': 'Previous Difference Rate',
                'meme_percentage': 'Meme Rate'
            };

            const container = document.createElement('div');
            container.className = 'horizontal-items-container';
            for(const [key, value] of Object.entries(report.tendencies)){
                const item = document.createElement('div');
                item.className = 'info-item';
                const valueDiv = document.createElement('div');
                valueDiv.className = 'info-item-value';
                
                let displayValue;
                if (typeof value === 'boolean') {
                    displayValue = value ? 'Yes' : 'No';
                } else {
                    displayValue = `${value}%`;
                }
                valueDiv.textContent = displayValue;

                const labelDiv = document.createElement('div');
                labelDiv.className = 'info-item-label';
                labelDiv.textContent = tendencyNameMap[key] || key.replace(/_/g, ' ');
                item.appendChild(valueDiv);
                item.appendChild(labelDiv);
                container.appendChild(item);
            }
            section.appendChild(container);
            leftColumn.appendChild(section);
        }

        // --- Recent Game Line Graph ---
        if (report.recent_game_info && report.recent_game_info.pitches && report.recent_game_info.pitches.length > 0) {
            const section = document.createElement('div');
            section.className = 'scouting-section';
            
            const game_info = report.recent_game_info;
            const titleText = `${game_info.pitcher_team} ${game_info.season}.${game_info.session} vs. ${game_info.opponent}`;
            
            const title = document.createElement('h3');
            title.textContent = titleText;
            section.appendChild(title);

            const canvas = document.createElement('canvas');
            section.appendChild(canvas);

            new Chart(canvas, {
                type: 'line',
                data: {
                    labels: Array.from({ length: game_info.pitches.length }, (_, i) => i + 1),
                    datasets: [{
                        label: 'Pitch Number',
                        data: game_info.pitches,
                        borderColor: '#FF4500',
                        backgroundColor: 'rgba(255, 69, 0, 0.2)',
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        y: { ticks: { color: '#D7DADC' }, grid: { color: '#343536' } },
                        x: { ticks: { color: '#D7DADC' }, grid: { color: '#343536' }, title: { display: true, text: 'Pitch in Sequence' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
            
            leftColumn.appendChild(section);
        }

        // --- Histograms ---
        if (report.histograms) {
            const section = document.createElement('div');
            section.className = 'scouting-section';

            const sectionHeader = document.createElement('div');
            sectionHeader.className = 'scouting-section-header';

            const title = document.createElement('h3');
            title.textContent = 'Pitch Histograms';
            sectionHeader.appendChild(title);

            const controlsWrapper = document.createElement('div');
            controlsWrapper.className = 'histogram-header-controls';

            const nValueSpan = document.createElement('span');
            nValueSpan.className = 'histogram-n-value';
            controlsWrapper.appendChild(nValueSpan);
            
            const titleMap = {
                'overall': 'All Pitches',
                'first_of_game': 'First Pitch of Game',
                'first_of_inning': 'First Pitch of Inning',
                'risp': 'Pitches with Runners in Scoring Position'
            };

            const select = document.createElement('select');
            select.className = 'histogram-select';

            const situationalGroup = document.createElement('optgroup');
            situationalGroup.label = 'Situational';
            for (const key in report.histograms) {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = titleMap[key] || key.replace(/_/g, ' ');
                situationalGroup.appendChild(option);
            }
            select.appendChild(situationalGroup);

            if (report.conditional_histograms) {
                const conditionalGroup = document.createElement('optgroup');
                conditionalGroup.label = 'Conditional (After...)';
                const sortedKeys = Object.keys(report.conditional_histograms).sort((a, b) => {
                    return parseInt(a.split('_')[1]) - parseInt(b.split('_')[1]);
                });
                for (const key of sortedKeys) {
                    const option = document.createElement('option');
                    option.value = key;
                    let friendlyName = `After ${key.split('_')[1]}`;
                    if (key === 'after_000s') {
                        friendlyName = 'After 0s';
                    }
                    option.textContent = friendlyName;
                    conditionalGroup.appendChild(option);
                }
                select.appendChild(conditionalGroup);
            }

            if (report.season_histograms) {
                const seasonGroup = document.createElement('optgroup');
                seasonGroup.label = 'By Season';
                const sortedSeasons = Object.keys(report.season_histograms).sort((a, b) => {
                    return parseInt(a.slice(1)) - parseInt(b.slice(1));
                });
                for (const season of sortedSeasons) {
                    const option = document.createElement('option');
                    option.value = season;
                    option.textContent = `Season ${season.slice(1)}`;
                    seasonGroup.appendChild(option);
                }
                select.appendChild(seasonGroup);
            }
            
            controlsWrapper.appendChild(select);
            sectionHeader.appendChild(controlsWrapper);
            section.appendChild(sectionHeader);

            const chartWrapper = document.createElement('div');
            chartWrapper.className = 'chart-wrapper';
            section.appendChild(chartWrapper);

            const renderChart = (key) => {
                chartWrapper.innerHTML = '';
                
                let data;
                if (key.startsWith('after_')) {
                    data = report.conditional_histograms[key];
                } else if (key.startsWith('S')) {
                    data = report.season_histograms[key];
                } else {
                    data = report.histograms[key];
                }

                if (!data) {
                    nValueSpan.textContent = '';
                    return;
                }

                const totalN = data.reduce((sum, bin) => sum + bin.count, 0);
                nValueSpan.textContent = `N = ${totalN}`;

                const chartContainer = document.createElement('div');
                chartContainer.className = 'chart-container';

                const chartLabels = data.map(bin => {
                    const lower_bound = parseInt(bin.label.split('-')[0], 10);
                    if (lower_bound === 1) return '0s';
                    return `${Math.floor(lower_bound / 100) * 100}s`;
                });
                const chartCounts = data.map(bin => bin.count);

                const canvas = document.createElement('canvas');
                chartContainer.appendChild(canvas);
                chartWrapper.appendChild(chartContainer);

                new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: chartLabels,
                        datasets: [{
                            label: 'Count',
                            data: chartCounts,
                            backgroundColor: 'rgba(255, 69, 0, 0.6)',
                            borderColor: 'rgba(255, 69, 0, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true, ticks: { color: '#D7DADC' }, grid: { color: '#343536' } },
                            x: { ticks: { color: '#D7DADC' }, grid: { display: false } }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            };

            renderChart(select.value);

            select.addEventListener('change', (event) => {
                renderChart(event.target.value);
            });

            rightColumn.appendChild(section);
        }

        mainGrid.appendChild(leftColumn);
        mainGrid.appendChild(rightColumn);
        elements.statsContentDisplay.appendChild(mainGrid);
    };



    const handlePlayerSearch = (event) => {
        const query = event.target.value.toLowerCase();
        elements.playerSuggestions.innerHTML = '';
        if (query.length < 2) return;

        const suggestions = new Map(); // Use a map to avoid duplicate players

        // Search by name
        for (const [name, id] of state.playerMap.entries()) {
            if (name.toLowerCase().includes(query)) {
                if (!suggestions.has(id)) {
                    suggestions.set(id, state.players[id].currentName);
                }
            }
        }

        // Search by ID
        if (/^-?\d+$/.test(query)) {
            const id = parseInt(query);
            if (state.players[id] && !suggestions.has(id)) {
                suggestions.set(id, state.players[id].currentName);
            }
        }

        let count = 0;
        for (const [id, name] of suggestions) {
            if (count >= 10) break;
            const div = document.createElement('div');
            div.textContent = name;
            div.className = 'suggestion-item';
            div.addEventListener('click', () => {
                elements.playerSearch.value = name;
                elements.playerSuggestions.innerHTML = '';
                displayPlayerPage(id);
            });
            elements.playerSuggestions.appendChild(div);
            count++;
        }
    };

    const populateTeamFilter = () => {
        const teamFilter = elements.leaderboardTeamFilter;
        if (!teamFilter) return;
        const teams = Object.keys(teamFranchises).sort();
        teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team;
            option.textContent = team;
            teamFilter.appendChild(option);
        });
    };

    const teamLogos = {
        'ANA': './img/logos/ANA.svg',
        'ARI': './img/logos/ARI.svg',
        'ATL': './img/logos/ATL.svg',
        'BAL': './img/logos/BAL.svg',
        'BOS': './img/logos/BOS.svg',
        'CHC': './img/logos/CHC.svg',
        'CIN': './img/logos/CIN.svg',
        'CLE': './img/logos/CLE.svg',
        'COL': './img/logos/COL.svg',
        'CWS': './img/logos/CWS.svg',
        'DET': './img/logos/DET.svg',
        'FLA': './img/logos/FLA.svg',
        'HOU': './img/logos/HOU.svg',
        'KCR': './img/logos/KCR.svg',
        'LAA': './img/logos/LAA.svg',
        'LAD': './img/logos/LAD.svg',
        'MIA': './img/logos/MIA.svg',
        'MIL': './img/logos/MIL.svg',
        'MIN': './img/logos/MIN.svg',
        'MTL': './img/logos/MTL.svg',
        'NYM': './img/logos/NYM.svg',
        'NYY': './img/logos/NYY.svg',
        'OAK': './img/logos/OAK.svg',
        'PHI': './img/logos/PHI.svg',
        'PIT': './img/logos/PIT.svg',
        'SDP': './img/logos/SDP.svg',
        'SFG': './img/logos/SFG.svg',
        'SEA': './img/logos/SEA.svg',
        'STL': './img/logos/STL.svg',
        'TBD': './img/logos/TBD.svg',
        'TBR': './img/logos/TBR.svg',
        'TEX': './img/logos/TEX.svg',
        'TOR': './img/logos/TOR.svg',
        'WAS': './img/logos/WAS.svg',
        'WSH': './img/logos/WSH.svg'
    };

    const displayPlayerPage = (playerId) => {
        state.currentPlayerId = playerId;
        elements.statsContentDisplay.innerHTML = '';
        const player = state.players[playerId];
        if (!player) return;

        const path = window.location.hash || '#/stats';
        const isScouting = path === '#/scouting';
        const isStats = path === '#/stats';

        const playerName = player.currentName;

        const hittingStats = state.hittingStats.filter(s => s['Hitter ID'] === playerId);
        const pitchingStats = state.pitchingStats.filter(s => s['Pitcher ID'] === playerId);

        let mostRecentTeam = null;
        const allStats = [...hittingStats, ...pitchingStats];

        if (allStats.length > 0) {
            const lastSeasonStats = allStats
                .filter(s => s.Season && s.Season.startsWith('S') && !s.is_sub_row)
                .sort((a, b) => parseInt(b.Season.slice(1)) - parseInt(a.Season.slice(1)))[0];
            
            if (lastSeasonStats) {
                mostRecentTeam = lastSeasonStats['Last Team'];
            }
        }

        let titleHTML = `<h2 class="section-title">${playerName}</h2>`;
        if (mostRecentTeam && teamLogos[mostRecentTeam]) {
            titleHTML = `<h2 class="section-title"><img src="${teamLogos[mostRecentTeam]}" class="player-team-logo"> ${playerName}</h2>`;
        }

        titleHTML += `<p class="player-id-display">Player ID: ${playerId}</p>`;
        if (player.formerNames && player.formerNames.length > 0) {
            titleHTML += `<p class="former-names">Formerly known as: ${player.formerNames.join(', ')}</p>`;
        }
        elements.statsContentDisplay.innerHTML = titleHTML;

        if (isStats) {
            if (hittingStats.length > 0) {
                hittingStats.sort((a, b) => {
                    if (a.Season === 'Career') return 1;
                    if (b.Season === 'Career') return -1;
                    
                    const seasonA = parseInt(a.Season.slice(1));
                    const seasonB = parseInt(b.Season.slice(1));
                    if (seasonA !== seasonB) {
                        return seasonA - seasonB;
                    }

                    // For same season, main row (is_sub_row=false) comes first
                    const subRowA = a.is_sub_row ? 1 : 0;
                    const subRowB = b.is_sub_row ? 1 : 0;
                    return subRowA - subRowB;
                });
                elements.statsContentDisplay.innerHTML += createStatsTable('Hitting Stats', hittingStats, STAT_DEFINITIONS, false, true);
            }

            if (pitchingStats.length > 0) {
                pitchingStats.sort((a, b) => {
                    if (a.Season === 'Career') return 1;
                    if (b.Season === 'Career') return -1;
                    
                    const seasonA = parseInt(a.Season.slice(1));
                    const seasonB = parseInt(b.Season.slice(1));
                    if (seasonA !== seasonB) {
                        return seasonA - seasonB;
                    }

                    // For same season, main row (is_sub_row=false) comes first
                    const subRowA = a.is_sub_row ? 1 : 0;
                    const subRowB = b.is_sub_row ? 1 : 0;
                    return subRowA - subRowB;
                });
                elements.statsContentDisplay.innerHTML += createStatsTable('Pitching Stats', pitchingStats, STAT_DEFINITIONS, true, true);
            }
        }

        if (isScouting) {
            displayScoutingReport(playerId);
        }
    };

    const createStatsTable = (title, stats, statDefinitions, isPitching, bySeason = false) => {
        let html = `<h3 class="section-title">${title}</h3>`;
        const statGroups = isPitching ? statDefinitions.pitching_tables : statDefinitions.hitting_tables;

        for (const groupName in statGroups) {
            const groupStats = statGroups[groupName];
            html += `<h4>${groupName}</h4>`;
            html += '<table class="stats-table">';
            html += '<thead><tr>';
            groupStats.forEach(stat => {
                const description = STAT_DESCRIPTIONS[stat] || '';
                html += `<th title="${description}">${stat}</th>`;
            });
            html += '</tr></thead>';
            html += '<tbody>';
            const data = bySeason ? stats : [stats];
            data.forEach(s => {
                let rowClass = (bySeason && s.Season === 'Career') ? 'career-row' : '';
                if (s.is_sub_row) {
                    rowClass += ' sub-row';
                }
                html += `<tr class="${rowClass}">`;
                groupStats.forEach(stat => {
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
                    } else {
                        if (stat === 'SO') statKey = 'K';
                        else if (stat === 'BA') statKey = 'AVG';
                    }
                    let value = s[statKey];
                    if (stat === 'Season') {
                        value = s.Season === 'Career' ? 'Career' : s.Season.replace('S', '');
                    }
                    if (stat === 'Team') {
                        value = s.Team || '';
                    }
                    html += `<td>${formatStat(stat, value)}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
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

    loadData();
});