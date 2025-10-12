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
        hitting_tables: {
            'Hitting Stats': ['Season', 'Team', 'WAR', 'G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'IBB', 'SO', 'Auto K', 'BA', 'OBP', 'SLG', 'OPS', 'OPS+'],
            'Advanced Hitting': ['Season', 'Team', 'TB', 'GIDP', 'SH', 'SF', 'BABIP', 'ISO', 'HR%', 'SO%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24', 'SB%']
        },
        pitching_tables: {
            'Pitching Stats': ['Season', 'Team', 'WAR', 'W', 'L', 'W-L%', 'ERA', 'G', 'GS', 'GF', 'CG', 'SHO', 'SV', 'HLD', 'IP', 'H', 'ER', 'HR', 'BB', 'IBB', 'Auto BB', 'SO', 'BF', 'ERA+'],
            'Advanced Pitching': ['Season', 'Team', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'SO6', 'SO/BB', 'HR%', 'K%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24'],
            'Opponent Stats': ['Season', 'Team', 'BA', 'OBP', 'SLG', 'OPS', 'BABIP']
        }
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
        const allStats = [].concat(...Object.values(STAT_DEFINITIONS));
        const uniqueStats = [...new Set(allStats)].sort();
        uniqueStats.forEach(stat => {
            const option = document.createElement('option');
            option.value = stat;
            option.textContent = stat;
            elements.leaderboardStatSelect.appendChild(option);
        });
    };

    const handleLeaderboardView = () => {
        const stat = elements.leaderboardStatSelect.value;
        const season = elements.leaderboardSeasonSelect.value;
        if (!stat) return;

        const isHitting = [ ...STAT_DEFINITIONS.hitting_standard, ...STAT_DEFINITIONS.hitting_advanced, ...STAT_DEFINITIONS.hitting_batted_ball, ...STAT_DEFINITIONS.hitting_rate ].includes(stat);
        const isPitching = [ ...STAT_DEFINITIONS.pitching_standard, ...STAT_DEFINITIONS.pitching_advanced, ...STAT_DEFINITIONS.pitching_rate, ...STAT_DEFINITIONS.pitching_opponent, ...STAT_DEFINITIONS.pitching_batted_ball ].includes(stat);
        const lowerIsBetter = ['ERA', 'WHIP', 'FIP', 'Avg Diff'].includes(stat);

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
        elements.contentDisplay.innerHTML += `<h3 class="section-title">Scouting Report</h3>`;
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

    const populateSeasonSelect = () => {
        const seasons = Object.keys(state.seasons).sort((a, b) => parseInt(b.slice(1)) - parseInt(a.slice(1)));
        seasons.forEach(season => {
            const option = document.createElement('option');
            option.value = season;
            option.textContent = `Season ${season.slice(1)}`;
            elements.leaderboardSeasonSelect.appendChild(option);
        });
    };

    const handlePlayerSearch = (event) => {
        const query = event.target.value.toLowerCase();
        elements.playerSuggestions.innerHTML = '';
        if (query.length < 2) return;

        const suggestions = [];
        for (const [name, id] of state.playerMap.entries()) {
            if (name.toLowerCase().includes(query)) {
                suggestions.push({ name, id });
            }
        }

        suggestions.slice(0, 10).forEach(({ name, id }) => {
            const div = document.createElement('div');
            div.textContent = state.players[id];
            div.className = 'suggestion-item';
            div.addEventListener('click', () => {
                elements.playerSearch.value = state.players[id];
                elements.playerSuggestions.innerHTML = '';
                displayPlayerPage(id);
            });
            elements.playerSuggestions.appendChild(div);
        });
    };

    const displayPlayerPage = (playerId) => {
        elements.contentDisplay.innerHTML = '';
        const playerName = state.players[playerId];

        elements.contentDisplay.innerHTML = `<h2 class="section-title">${playerName}</h2>`;

        const hittingStats = state.hittingStats.filter(s => s['Hitter ID'] === playerId);
        if (hittingStats.length > 0) {
            const careerHitting = calculateCareerStats(hittingStats, false);
            const statsWithCareer = [...hittingStats, { ...careerHitting, Season: 'Career' }];
            elements.contentDisplay.innerHTML += createStatsTable('Hitting Stats', statsWithCareer, STAT_DEFINITIONS, false, true);
        }

        const pitchingStats = state.pitchingStats.filter(s => s['Pitcher ID'] === playerId);
        if (pitchingStats.length > 0) {
            const careerPitching = calculateCareerStats(pitchingStats, true);
            const statsWithCareer = [...pitchingStats, { ...careerPitching, Season: 'Career' }];
            elements.contentDisplay.innerHTML += createStatsTable('Pitching Stats', statsWithCareer, STAT_DEFINITIONS, true, true);
        }

        displayScoutingReport(playerId);
    };

        const createStatsTable = (title, stats, statDefinitions, isPitching, bySeason = false) => {

            let html = `<h3 class="section-title">${title}</h3>`;

            

            const statGroups = isPitching

                ? statDefinitions.pitching_tables

                : statDefinitions.hitting_tables;

    

            for (const groupName in statGroups) {

                const groupStats = statGroups[groupName];

                html += `<h4>${groupName}</h4>`;

                html += '<table class="stats-table">';

                html += '<thead><tr>';

                

                groupStats.forEach(stat => {

                    html += `<th>${stat}</th>`;

                });

    

                html += '</tr></thead>';

                html += '<tbody>';

    

                const data = bySeason ? stats : [stats];

                data.forEach(s => {

                    const rowClass = (bySeason && s.Season === 'Career') ? 'career-row' : '';

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

    const calculateCareerStats = (stats, isPitching) => {
        const career = {};

        const summedHitting = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'IBB', 'K', 'Auto K', 'SB', 'CS', 'GIDP', 'SH', 'SF', 'WAR', 'RE24', 'WPA', 'TB'];
        const summedPitching = ['G', 'GS', 'GF', 'CG', 'SHO', 'W', 'L', 'SV', 'HLD', 'IP', 'BF', 'H', 'R', 'BB', 'IBB', 'Auto BB', 'K', 'HR', 'WAR', 'RE24', 'WPA'];

        const summedStats = isPitching ? summedPitching : summedHitting;

        stats.forEach(s => {
            summedStats.forEach(stat => {
                career[stat] = (career[stat] || 0) + (s[stat] || 0);
            });
        });

        if (isPitching) {
            career['W-L%'] = (career['W'] + career['L']) > 0 ? career['W'] / (career['W'] + career['L']) : 0;
            career['ERA'] = career['IP'] > 0 ? (career['R'] / career['IP']) * 6 : 0;
            career['WHIP'] = career['IP'] > 0 ? (career['BB'] + career['H']) / career['IP'] : 0;
            career['H/6'] = career['IP'] > 0 ? (career['H'] / career['IP']) * 6 : 0;
            career['HR/6'] = career['IP'] > 0 ? (career['HR'] / career['IP']) * 6 : 0;
            career['BB/6'] = career['IP'] > 0 ? (career['BB'] / career['IP']) * 6 : 0;
            career['K/6'] = career['IP'] > 0 ? (career['K'] / career['IP']) * 6 : 0;
            career['K/BB'] = career['BB'] > 0 ? career['K'] / career['BB'] : 0;
            career['HR%_A'] = career['BF'] > 0 ? career['HR'] / career['BF'] : 0;
            career['K%_A'] = career['BF'] > 0 ? career['K'] / career['BF'] : 0;
            career['BB%_A'] = career['BF'] > 0 ? career['BB'] / career['BF'] : 0;

            let total_era_plus = 0, total_fip = 0, total_ip_for_avg = 0;
            let total_baa = 0, total_obpa = 0, total_slga = 0, total_babip_a = 0, total_gb_a = 0, total_fb_a = 0, total_bf_for_avg = 0;
            stats.forEach(s => {
                const ip = s['IP'] || 0;
                const bf = s['BF'] || 0;
                if (ip > 0) {
                    total_era_plus += (s['ERA+'] || 0) * ip;
                    total_fip += (s['FIP'] || 0) * ip;
                    total_ip_for_avg += ip;
                }
                if (bf > 0) {
                    total_baa += (s['BAA'] || 0) * bf;
                    total_obpa += (s['OBPA'] || 0) * bf;
                    total_slga += (s['SLGA'] || 0) * bf;
                    total_babip_a += (s['BABIP_A'] || 0) * bf;
                    total_gb_a += (s['GB%_A'] || 0) * bf;
                    total_fb_a += (s['FB%_A'] || 0) * bf;
                    total_bf_for_avg += bf;
                }
            });

            if (total_ip_for_avg > 0) {
                career['ERA+'] = total_era_plus / total_ip_for_avg;
                career['FIP'] = total_fip / total_ip_for_avg;
            }
            if (total_bf_for_avg > 0) {
                career['BAA'] = total_baa / total_bf_for_avg;
                career['OBPA'] = total_obpa / total_bf_for_avg;
                career['SLGA'] = total_slga / total_bf_for_avg;
                career['OPSA'] = career['OBPA'] + career['SLGA'];
                career['BABIP_A'] = total_babip_a / total_bf_for_avg;
                career['GB%_A'] = total_gb_a / total_bf_for_avg;
                career['FB%_A'] = total_fb_a / total_bf_for_avg;
                career['GB/FB_A'] = career['FB%_A'] > 0 ? career['GB%_A'] / career['FB%_A'] : 0;
            }

        } else { // Hitting
            career['AVG'] = career['AB'] > 0 ? career['H'] / career['AB'] : 0;
            career['OBP'] = career['PA'] > 0 ? (career['H'] + career['BB']) / career['PA'] : 0;
            career['SLG'] = career['AB'] > 0 ? (career['H'] + career['2B'] + (career['3B'] * 2) + (career['HR'] * 3)) / career['AB'] : 0;
            career['OPS'] = career['OBP'] + career['SLG'];
            career['ISO'] = career['SLG'] - career['AVG'];
            career['BABIP'] = (career['AB'] - career['K'] - career['HR'] + career['SF']) > 0 ? (career['H'] - career['HR']) / (career['AB'] - career['K'] - career['HR'] + career['SF']) : 0;
            career['HR%'] = career['PA'] > 0 ? career['HR'] / career['PA'] : 0;
            career['SO%'] = career['PA'] > 0 ? career['K'] / career['PA'] : 0;
            career['BB%'] = career['PA'] > 0 ? career['BB'] / career['PA'] : 0;
            career['SB%'] = (career['SB'] + career['CS']) > 0 ? career['SB'] / (career['SB'] + career['CS']) : 0;

            let total_ops_plus = 0, total_gb = 0, total_fb = 0;
            let total_pa_for_avg = 0;
            stats.forEach(s => {
                const pa = s['PA'] || 0;
                if (pa > 0) {
                    total_ops_plus += (s['OPS+'] || 0) * pa;
                    total_gb += (s['GB%'] || 0) * pa;
                    total_fb += (s['FB%'] || 0) * pa;
                    total_pa_for_avg += pa;
                }
            });

            if (total_pa_for_avg > 0) {
                career['OPS+'] = total_ops_plus / total_pa_for_avg;
                career['GB%'] = total_gb / total_pa_for_avg;
                career['FB%'] = total_fb / total_pa_for_avg;
                career['GB/FB'] = career['FB%'] > 0 ? career['GB%'] / career['FB%'] : 0;
            }
        }

        return career;
    };

    const formatStat = (stat, value) => {
        if (value === undefined || value === null) return '-';
        if (typeof value === 'number') {
            if (['AVG', 'OBP', 'SLG', 'OPS', 'ISO', 'BAA', 'OBPA', 'SLGA', 'OPSA', 'BABIP', 'BABIP_A', 'W-L%'].includes(stat)) {
                const formatted = value.toFixed(3);
                if (formatted.startsWith('0.')) {
                    return formatted.substring(1);
                }
                return formatted;
            }
            if (['ERA', 'WHIP', 'FIP', 'H/6', 'HR/6', 'BB/6', 'K/6', 'K/BB', 'GB/FB', 'GB/FB_A'].includes(stat)) {
                return value.toFixed(2);
            }
            if (['WAR', 'RE24', 'WPA'].includes(stat)) {
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
