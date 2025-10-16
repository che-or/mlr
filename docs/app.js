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
        playerMap: new Map()
    };

    const elements = {
        loader: document.getElementById('loader'),
        app: document.getElementById('app'),
        
        statsView: document.getElementById('stats-view'),
        leaderboardsView: document.getElementById('leaderboards-view'),
        glossaryView: document.getElementById('glossary-view'),
        
        statsTab: document.getElementById('stats-tab'),
        leaderboardsTab: document.getElementById('leaderboards-tab'),
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
        
        if (path !== '#/stats' && path !== '#/leaderboards' && path !== '#/glossary') {
            window.location.hash = '#/stats';
            return;
        }

        const isStats = path === '#/stats';
        const isLeaderboards = path === '#/leaderboards';
        const isGlossary = path === '#/glossary';

        elements.statsView.style.display = isStats ? 'block' : 'none';
        elements.leaderboardsView.style.display = isLeaderboards ? 'block' : 'none';
        elements.glossaryView.style.display = isGlossary ? 'flex' : 'none';

        elements.statsTab.classList.toggle('active', isStats);
        elements.leaderboardsTab.classList.toggle('active', isLeaderboards);
        elements.glossaryTab.classList.toggle('active', isGlossary);

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
                                singleSeasonData = singleSeasonData.filter(p => p.Team === selectedTeam);
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
                                    seasonData = seasonData.filter(p => p.Team === selectedTeam);
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
                                singleSeasonData = singleSeasonData.filter(p => p.Team === selectedTeam);
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
                                    seasonData = seasonData.filter(p => p.Team === selectedTeam);
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
        const container = document.createElement('div');
        container.className = 'scouting-report';

        // Tendencies
        let tendenciesHTML = '<div class="scouting-section"><h3>Tendencies</h3><div class="tendency-grid">';
        for(const [key, value] of Object.entries(report.tendencies)){
            tendenciesHTML += `<div class="tendency-item"><div class="label">${key.replace(/_/g, ' ')}</div><div class="value">${value}${typeof value === 'number' ? '%' : ''}</div></div>`;
        }
        tendenciesHTML += '</div></div>';
        container.innerHTML += tendenciesHTML;

        // Histograms
        let histogramsHTML = '<div class="scouting-section"><h3>Pitch Histograms</h3>';
        for(const [key, data] of Object.entries(report.histograms)){
            histogramsHTML += `<h4>${key.replace(/_/g, ' ')}</h4>`;
            const maxCount = Math.max(...data.map(d => d.count));
            data.forEach(bin => {
                const barWidth = maxCount > 0 ? (bin.count / maxCount) * 100 : 0;
                histogramsHTML += `<div class="histogram-bar"><div class="histogram-label">${bin.label}</div><div class="histogram-bar-inner" style="width: ${barWidth}%;">${bin.count}</div></div>`;
            });
        }
        histogramsHTML += '</div>';
        container.innerHTML += histogramsHTML;

        elements.statsContentDisplay.appendChild(container);
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
        const teams = Object.keys(teamLogos).sort();
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
        'WSH': './img/logos/WSH.svg'
    };

    const displayPlayerPage = (playerId) => {
        elements.statsContentDisplay.innerHTML = '';
        const player = state.players[playerId];
        if (!player) return;

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

        displayScoutingReport(playerId);
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