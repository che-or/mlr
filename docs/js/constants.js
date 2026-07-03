// Stats that do not need a minimum PA/IP qualifier in leaderboards.
// Derived from the 'cols' lists in get_hitting_stats.py and get_pitching_stats.py,
// excluding internal neutral columns (nH, nTB, nER, etc.) that are calculation-only.
export const COUNTING_STATS = [
    // Shared hitting + pitching
    'G', 'H', '1B', '2B', '3B', 'HR', 'BB', 'IBB', 'SO', 'SB', 'CS',
    'FO', 'PO', 'RGO', 'LGO', 'LO', 'GO', 'SF', 'SH', 'AB', 'TB',
    'RE24', 'WPA', 'WAR', '0 Diffs', '500 Diffs',
    // Hitting-only
    'PA', 'R', 'RBI', 'Auto K', 'GIDP', 'GITP', '1RHR', '2RHR', '3RHR', '4RHR', 'TB+',
    // Pitching-only
    'IP', 'ER', 'BF', 'Auto BB', 'W', 'L', 'SV', 'HLD', 'BS',
    'GS', 'GF', 'CG', 'SHO', 'OPP', 'DP', 'TP',
    '300+ Pitches', '400+ Pitches',
];

// Columns shown in each stats table on the player scouting report.
// 'Display Season' replaces the old 'Season'; 'Batting Type' replaces 'Type'.
export const STAT_DEFINITIONS = {
    batting: {
        'Standard Batting': [
            'Display Season', 'Team', 'Batting Type', 'WAR', 'G', 'PA', 'AB',
            'R', 'H', '2B', '3B', 'HR', 'RBI', 'SB', 'CS', 'BB', 'IBB', 'SO',
            'Auto K', 'BA', 'OBP', 'SLG', 'OPS', 'OPS+',
        ],
        'Advanced Batting': [
            'Display Season', 'Team', 'TB', 'GIDP', 'SH', 'SF', 'BABIP', 'ISO',
            'HR%', 'K%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24', 'SB%', 'Avg Diff',
        ],
    },
    pitching: {
        'Standard Pitching': [
            'Display Season', 'Team', 'Pitching Type', 'WAR', 'W', 'L', 'W-L%',
            'ERA', 'G', 'GS', 'GF', 'CG', 'SHO', 'SV', 'OPP', 'HLD', 'IP',
            'H', 'ER', 'HR', 'BB', 'IBB', 'Auto BB', 'SO', 'BF', 'ERA-',
        ],
        'Advanced Pitching': [
            'Display Season', 'Team', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'SO6',
            'SO/BB', 'HR%', 'K%', 'BB%', 'GB%', 'FB%', 'GB/FB', 'WPA', 'RE24', 'Avg Diff',
        ],
        'Opponent Stats': [
            'Display Season', 'Team', 'BA', 'OBP', 'SLG', 'OPS', 'BABIP', 'DP', 'SB', 'CS', 'SB%',
        ],
    },
};

// Short descriptions shown as table header tooltips
export const STAT_DESCRIPTIONS = {
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
    'OPS+': 'OPS adjusted for park and league (100 = average)',
    'TB': 'Total Bases',
    'TB+': 'Total Bases Plus',
    'GIDP': 'Grounded Into Double Play',
    'SH': 'Sacrifice Hits (Bunts)',
    'SF': 'Sacrifice Flies',
    'BABIP': 'Batting Average on Balls In Play',
    'ISO': 'Isolated Power',
    'HR%': 'Home Run Percentage',
    'K%': 'Strikeout Percentage',
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
    'BS': 'Blown Saves',
    'OPP': 'Save Opportunities',
    'DP': 'Double Plays',
    'TP': 'Triple Plays',
    'GITP': 'Grounded Into Triple Play',
    '0 Diffs': '0 Diffs',
    '500 Diffs': '500 Diffs',
    '1RHR': 'Solo Home Runs',
    '2RHR': '2-Run Home Runs',
    '3RHR': '3-Run Home Runs',
    '4RHR': 'Grand Slams',
    '300+ Pitches': '300+ Pitches',
    '400+ Pitches': '400+ Pitches',
    'SV%': 'Save Percentage',
    'IP': 'Innings Pitched',
    'ER': 'Earned Runs',
    'Auto BB': 'Automatic Walks',
    'BF': 'Batters Faced',
    'ERA-': 'ERA adjusted for park and league (100 = average, lower is better)',
    'FIP': 'Fielding Independent Pitching',
    'WHIP': 'Walks + Hits per Inning Pitched',
    'H6': 'Hits per 6 Innings',
    'HR6': 'Home Runs per 6 Innings',
    'BB6': 'Walks per 6 Innings',
    'SO6': 'Strikeouts per 6 Innings',
    'SO/BB': 'Strikeout to Walk Ratio',
    'Batting Type': 'Batting Type',
    'Pitching Type': 'Pitching Type',
    'Display Season': 'Season',
    'Team': 'Team',
};

// Stats that appear in leaderboards but not in the player stats tables
export const LEADERBOARD_ONLY_STATS = {
    hitting: ['1B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO', 'GITP', '0 Diffs', '500 Diffs', '1RHR', '2RHR', '3RHR', '4RHR', 'TB+'],
    pitching: ['1B', '2B', '3B', 'RGO', 'LGO', 'GO', 'FO', 'PO', 'LO', 'DP', 'TP', 'SV%', 'BS', '0 Diffs', '500 Diffs', '300+ Pitches', '400+ Pitches'],
};


// Leagues that have by-team and by-type breakdown files
export const LEAGUES_WITH_BREAKDOWNS = ['mlr', 'mlr_playoff'];

// Leagues that have career stat files
export const LEAGUES_WITH_CAREER = ['mlr', 'mlr_playoff', 'milr', 'milr_playoff', 'fcb', 'gib'];

// Leagues that have franchise (all-time aggregated team) stat files
export const LEAGUES_WITH_FRANCHISE = ['mlr', 'mlr_playoff'];

// Leagues that have a separate playoff dataset
export const LEAGUES_WITH_PLAYOFFS = ['mlr', 'milr'];

// Display names for leagues
export const LEAGUE_LABELS = {
    mlr: 'MLR',
    milr: 'MiLR',
    fcb: 'FCB',
    mlr_playoff: 'MLR Playoffs',
    milr_playoff: 'MiLR Playoffs',
    gib: 'GIB',
    eco: 'ECO',
    npr: 'NPR',
    wbc: 'WBC',
};
