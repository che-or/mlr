document.addEventListener('DOMContentLoaded', () => {
    const API = {
        hitting: './data/hitting_stats.json',
        pitching: './data/pitching_stats.json',
        players: './data/player_id_map.json',
        seasons: './data/season_games_map.json',
        scouting: './data/scouting_reports.json',
        diffs: './data/diff_data.json'
    };

    const state = {
        hittingStats: [],
        pitchingStats: [],
        players: {},
        seasons: {},
        scoutingReports: {},
        diffs: [],
        playerMap: new Map()
    };

    const elements = {
        loader: document.getElementById('loader'),
        app: document.getElementById('app'),
        playerSearch: document.getElementById('player-search'),
        playerSuggestions: document.getElementById('player-suggestions'),
        contentDisplay: document.getElementById('content-display'),
        leaderboardStatSelect: document.getElementById('leaderboard-stat-select'),
        leaderboardSeasonSelect: document.getElementById('leaderboard-season-select'),
        leaderboardButton: document.getElementById('leaderboard-button')
    };

    const STAT_DEFINITIONS = {
        hitting_counting: ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS'],
        hitting_rate: ['AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'Avg Diff'],
        pitching_counting: ['G', 'GS', 'GF', 'CG', 'SHO', 'IP', 'BF', 'H', 'R', 'BB', 'IBB', 'K', 'HR'],
        pitching_rate: ['ERA', 'WHIP', 'Avg Diff']
    };

    const loadData = async () => {
        try {
            const [hitting, pitching, players, seasons, scouting, diffs] = await Promise.all([
                fetch(API.hitting).then(res => res.json()),
                fetch(API.pitching).then(res => res.json()),
                fetch(API.players).then(res => res.json()),
                fetch(API.seasons).then(res => res.json()),
                fetch(API.scouting).then(res => res.json()),
                fetch(API.diffs).then(res => res.json())
            ]);

            state.hittingStats = hitting;
            state.pitchingStats = pitching;
            state.players = players;
            state.seasons = seasons;
            state.scoutingReports = scouting;
            state.diffs = diffs;

            for (const id in players) {
                state.playerMap.set(players[id].toLowerCase(), parseInt(id));
            }

            elements.loader.style.display = 'none';
            elements.app.style.display = 'block';
            initializeApp();
        } catch (error) {
            console.error("Failed to load data:", error);
            elements.loader.innerHTML = "<p>Failed to load data. Please refresh the page.</p>";
        }
    };

    const initializeApp = () => {
        populateLeaderboardSelect();
        populateSeasonSelect();
        elements.playerSearch.addEventListener('input', handlePlayerSearch);
        elements.leaderboardButton.addEventListener('click', handleLeaderboardView);
    };

    const populateLeaderboardSelect = () => {
        const allStats = [...STAT_DEFINITIONS.hitting_counting, ...STAT_DEFINITIONS.hitting_rate, ...STAT_DEFINITIONS.pitching_counting, ...STAT_DEFINITIONS.pitching_rate];
        const uniqueStats = [...new Set(allStats)].sort();
        uniqueStats.forEach(stat => {
            const option = document.createElement('option');
            option.value = stat;
            option.textContent = stat;
            elements.leaderboardStatSelect.appendChild(option);
        });
    };

    const populateSeasonSelect = () => {
        const seasons = Object.keys(state.seasons).sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1)));
        seasons.forEach(season => {
            const option = document.createElement('option');
            option.value = season;
            option.textContent = `Season ${season.slice(1)}`;
            elements.leaderboardSeasonSelect.appendChild(option);
        });
    };

    const handlePlayerSearch = (e) => {
        const query = e.target.value.toLowerCase();
        elements.playerSuggestions.innerHTML = '';
        if (query.length < 2) return;

        const matchingPlayers = Object.entries(state.players)
            .filter(([id, name]) => name.toLowerCase().includes(query))
            .slice(0, 10);

        matchingPlayers.forEach(([id, name]) => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = name;
            item.addEventListener('click', () => {
                elements.playerSearch.value = name;
                elements.playerSuggestions.innerHTML = '';
                displayPlayerStats(parseInt(id));
            });
            elements.playerSuggestions.appendChild(item);
        });
    };

    const displayPlayerStats = (playerId) => {
        const playerName = state.players[playerId];
        elements.contentDisplay.innerHTML = `<h2 class="section-title">Stats for ${playerName} (ID: ${playerId})</h2>`;

        const isPitcher = state.pitchingStats.some(p => p['Pitcher ID'] === playerId);
        if (isPitcher) {
            const scoutButton = document.createElement('button');
            scoutButton.textContent = 'View Scouting Report';
            scoutButton.onclick = () => displayScoutingReport(playerId);
            elements.contentDisplay.appendChild(scoutButton);
        }

        const hitting = state.hittingStats.filter(p => p['Hitter ID'] === playerId);
        const pitching = state.pitchingStats.filter(p => p['Pitcher ID'] === playerId);

        if (hitting.length > 0) {
            elements.contentDisplay.innerHTML += `<h3>Hitting Stats</h3>`;
            elements.contentDisplay.appendChild(createStatsTable(hitting, false));
        }
        if (pitching.length > 0) {
            elements.contentDisplay.innerHTML += `<h3>Pitching Stats</h3>`;
            elements.contentDisplay.appendChild(createStatsTable(pitching, true));
        }
    };

    const createStatsTable = (stats, isPitching) => {
        const table = document.createElement('table');
        table.className = 'stats-table';
        
        const headers = isPitching 
            ? ['Season', 'G', 'GS', 'IP', 'H', 'R', 'BB', 'K', 'HR', 'ERA', 'WHIP', 'Avg Diff'] 
            : ['Season', 'G', 'PA', 'AB', 'H', 'R', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS', 'AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'Avg Diff'];

        const thead = table.createTHead();
        const headerRow = thead.insertRow();
        headers.forEach(h => headerRow.innerHTML += `<th>${h}</th>`);

        const tbody = table.createTBody();
        stats.sort((a, b) => parseInt(a.Season.slice(1)) - parseInt(b.Season.slice(1)))
             .forEach(seasonStats => {
            const row = tbody.insertRow();
            headers.forEach(header => {
                const cell = row.insertCell();
                let value = seasonStats[header] ?? 0;
                cell.textContent = formatStat(header, value);
            });
        });

        // Career Row
        if (stats.length > 1) {
            const careerStats = calculateCareerStats(stats, isPitching);
            const row = tbody.insertRow();
            row.style.fontWeight = 'bold';
            headers.forEach(header => {
                const cell = row.insertCell();
                let value = careerStats[header] ?? 0;
                cell.textContent = formatStat(header, value);
            });
        }

        return table;
    };
    
    const formatStat = (stat, value) => {
        if (value === null || value === undefined) return '';
        if (typeof value !== 'number') return value;

        if (['AVG', 'OBP', 'SLG', 'OPS', 'W-L%'].includes(stat)) {
            return value.toFixed(3).toString().replace(/^0+/, '');
        } else if (['ERA', 'WHIP', 'Avg Diff', 'FIP'].includes(stat)) {
            return value.toFixed(2);
        } else if (stat === 'IP') {
            const innings = Math.floor(value);
            const outs = Math.round((value - innings) * 3);
            if (outs === 3) return (innings + 1).toString();
            return `${innings}.${outs}`;
        } else if (['OPS+', 'ERA+'].includes(stat) || Number.isInteger(value)) {
            return Math.round(value);
        }
        return value.toFixed(2);
    };

    const calculateCareerStats = (stats, isPitching) => {
        const total = { Season: 'Career' };
        const idKey = isPitching ? 'Pitcher ID' : 'Hitter ID';
        const playerId = stats.length > 0 ? stats[0][idKey] : null;

        if (isPitching) {
            const summed_stats = ['G', 'GS', 'GF', 'CG', 'SHO', 'BF', 'H', 'R', 'BB', 'IBB', 'K', 'HR'];
            summed_stats.forEach(key => {
                total[key] = stats.reduce((acc, s) => acc + (s[key] || 0), 0);
            });

            let totalOuts = 0;
            stats.forEach(s => {
                const ip = s.IP || 0;
                const innings = Math.floor(ip);
                const outs = Math.round((ip - innings) * 10);
                totalOuts += (innings * 3) + outs;
            });
            total.IP = Math.floor(totalOuts / 3) + (totalOuts % 3) / 10.0;

            if (total.IP > 0) {
                total.ERA = (total.R * 6) / total.IP;
                total.WHIP = (total.BB + total.H) / total.IP;
            }
            const allDiffs = state.diffs.filter(d => d[idKey] === playerId).map(d => d.Diff);
            if(allDiffs.length > 0) total['Avg Diff'] = allDiffs.reduce((a, b) => a + b, 0) / allDiffs.length;

        } else {
            const summed_stats = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS'];
            summed_stats.forEach(key => {
                total[key] = stats.reduce((acc, s) => acc + (s[key] || 0), 0);
            });

            if (total.AB > 0) {
                total.AVG = total.H / total.AB;
                total.SLG = (total.H - total['2B'] - total['3B'] - total.HR + total['2B'] * 2 + total['3B'] * 3 + total.HR * 4) / total.AB;
            }
            if (total.PA > 0) {
                total.OBP = (total.H + total.BB) / total.PA;
                const weightedOPSPlus = stats.reduce((acc, s) => acc + (s['OPS+'] || 100) * s.PA, 0);
                total['OPS+'] = weightedOPSPlus / total.PA;
            }
            total.OPS = (total.OBP || 0) + (total.SLG || 0);
            const allDiffs = state.diffs.filter(d => d[idKey] === playerId).map(d => d.Diff);
            if(allDiffs.length > 0) total['Avg Diff'] = allDiffs.reduce((a, b) => a + b, 0) / allDiffs.length;
        }
        return total;
    };

    const handleLeaderboardView = () => {
        const stat = elements.leaderboardStatSelect.value;
        const season = elements.leaderboardSeasonSelect.value;
        if (!stat) return;

        const isHitting = STAT_DEFINITIONS.hitting_rate.includes(stat) || STAT_DEFINITIONS.hitting_counting.includes(stat);
        const isPitching = STAT_DEFINITIONS.pitching_rate.includes(stat) || STAT_DEFINITIONS.pitching_counting.includes(stat);
        const lowerIsBetter = ['ERA', 'WHIP', 'Avg Diff'].includes(stat);

        let data, idCol, min_qual, min_qual_key;
        if (isHitting) {
            data = state.hittingStats;
            idCol = 'Hitter ID';
            min_qual_key = 'PA';
            min_qual = (season === 'All-Time') ? 100 : (state.seasons[season] || 0) * 2;
        } else {
            data = state.pitchingStats;
            idCol = 'Pitcher ID';
            min_qual_key = 'IP';
            min_qual = (season === 'All-Time') ? 50 : (state.seasons[season] || 0) * 1;
        }

        let leaderboardData;
        if (season === 'All-Time') {
            const careerData = [];
            const statsByPlayer = new Map();
            data.forEach(s => {
                const id = s[idCol];
                if (!statsByPlayer.has(id)) statsByPlayer.set(id, []);
                statsByPlayer.get(id).push(s);
            });

            for (const [id, playerStats] of statsByPlayer.entries()) {
                const career = calculateCareerStats(playerStats, isPitching);
                career[idCol] = id;
                careerData.push(career);
            }
            leaderboardData = careerData.filter(p => (p[min_qual_key] || 0) >= min_qual);
        } else {
            leaderboardData = data.filter(d => d.Season === season && (d[min_qual_key] || 0) >= min_qual);
        }

        leaderboardData.sort((a, b) => lowerIsBetter ? (a[stat] || 0) - (b[stat] || 0) : (b[stat] || 0) - (a[stat] || 0));
        
        renderLeaderboard(leaderboardData.slice(0, 10), stat, season, min_qual, isHitting, min_qual_key);
    };

    const renderLeaderboard = (leaderboard, stat, season, min_qual, isHitting, min_qual_key) => {
        const qual_text = `${min_qual} ${min_qual_key}`;
        const season_text = season === 'All-Time' ? 'All-Time' : `Season ${season.slice(1)}`;
        elements.contentDisplay.innerHTML = `<h2 class="section-title">${stat} Leaderboard - ${season_text} (${qual_text} min)</h2>`;
        const table = document.createElement('table');
        table.className = 'stats-table';
        const thead = table.createTHead();
        thead.innerHTML = `<tr><th>Rank</th><th>Player</th><th>${stat}</th></tr>`;
        const tbody = table.createTBody();
        leaderboard.forEach((p, i) => {
            const id = p[isHitting ? 'Hitter ID' : 'Pitcher ID'];
            tbody.innerHTML += `<tr><td>${i+1}</td><td>${state.players[id] || 'Unknown'}</td><td>${formatStat(stat, p[stat])}</td></tr>`;
        });
        elements.contentDisplay.appendChild(table);
    };

    const displayScoutingReport = (playerId) => {
        const report = state.scoutingReports[playerId];
        if (!report) {
            elements.contentDisplay.innerHTML += `<p>No scouting report available.</p>`;
            return;
        }
        const playerName = state.players[playerId];
        elements.contentDisplay.innerHTML = `<h2 class="section-title">Scouting Report: ${playerName}</h2>`;
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

        elements.contentDisplay.appendChild(container);
    };

    loadData();
});
