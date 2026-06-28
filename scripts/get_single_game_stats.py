import pandas as pd
import numpy as np

PLAYOFF_ROUNDS = ['PC', 'CS', 'DS', 'WC']  # most-recent first

BATTER_STATS = ['2B', '3B', 'Auto K', 'BB', 'CS', 'FO', 'GIDP', 'H', 'HR', 'IBB',
                'LGO', 'PA', 'PO', 'R', 'RBI', 'RE24', 'RGO', 'SB', 'SO', 'TB',
                'WAR', 'WPA']

PITCHER_STATS = ['2B', '300+ Pitches', '3B', '400+ Pitches', 'Auto BB', 'BB', 'BF',
                 'CS', 'DP', 'ER', 'FO', 'H', 'HR', 'IBB', 'IP', 'LGO', 'PO',
                 'RE24', 'RGO', 'SB', 'SO', 'WAR', 'WPA']


# ---------------------------------------------------------------------------
# Shared pivot-table helpers
# ---------------------------------------------------------------------------

def _hitting_pivot_stats(df, cols):
    '''
    Core hitting stat computation given a groupby key (cols).
    Returns a DataFrame indexed by cols with all BATTER_STATS columns
    plus the intermediate '1B' column.
    '''
    by_exact = pd.pivot_table(df, index=cols, columns='Exact Result',
                              aggfunc='size', fill_value=0)
    by_old = pd.pivot_table(df, index=cols, columns=['Exact Result', 'Old Result'],
                            aggfunc='size', fill_value=0)

    s = pd.DataFrame(index=by_exact.index)

    s['HR'] = by_exact.get('HR', 0)
    s['3B'] = by_exact.get('3B', 0)
    s['2B'] = by_exact.get('2B', 0)
    s['1B'] = by_exact.get('1B', 0) + by_exact.get('BUNT 1B', 0)

    s['BB'] = (by_exact.get('BB', 0) + by_exact.get('IBB', 0)
               + by_exact.get('AUTO BB', 0))
    s['IBB'] = by_exact.get('IBB', 0)

    s['FO'] = by_exact.get('FO', 0)
    s['SO'] = (by_exact.get('K', 0) + by_exact.get('AUTO K', 0)
               + by_exact.get('BUNT K', 0))
    s['Auto K'] = by_exact.get('AUTO K', 0)
    s['PO'] = by_exact.get('PO', 0)
    s['RGO'] = by_exact.get('RGO', 0)

    lo = by_old.get(('LGO', 'LO'), 0)
    s['LGO'] = by_exact.get('LGO', 0) - lo

    s['GIDP'] = (by_old.get(('RGO', 'DP'), 0) + by_old.get(('LGO', 'DP'), 0)
                 + by_exact.get('BUNT DP', 0))

    s['SB'] = (by_exact.get('STEAL 2B', 0) + by_exact.get('STEAL 3B', 0)
               + by_exact.get('STEAL HOME', 0) + by_exact.get('MSTEAL 3B', 0)
               + by_exact.get('MSTEAL HOME', 0))
    s['CS'] = (by_exact.get('CS 2B', 0) + by_exact.get('CS 3B', 0)
               + by_exact.get('CS HOME', 0) + by_exact.get('CMS 3B', 0)
               + by_exact.get('CMS HOME', 0))

    s['H'] = s['1B'] + s['2B'] + s['3B'] + s['HR']
    s['TB'] = s['1B'] + 2 * s['2B'] + 3 * s['3B'] + 4 * s['HR']

    sh = by_exact.get('BUNT SAC', 0)
    bunt_go = by_exact.get('BUNT GO', 0)
    bunt_dp = by_exact.get('BUNT DP', 0)
    s['PA'] = (s['H'] + s['BB'] + s['FO'] + s['SO'] + s['PO'] + s['RGO']
               + s['LGO'] + lo + sh + bunt_go + bunt_dp)

    s['R'] = df.groupby(cols)['Run'].sum()
    s['RBI'] = df.groupby(cols)['RBI'].sum()
    s['RE24'] = df.groupby(cols)['RE24'].sum()
    s['WAR'] = df.groupby(cols)['Batter WAR'].sum()
    s['WPA'] = df.groupby(cols)['Batter WPA'].sum()

    return s


def _pitching_pivot_stats(df, cols):
    '''
    Core pitching stat computation given a groupby key (cols).
    Returns a DataFrame indexed by cols with all PITCHER_STATS columns.
    '''
    by_exact = pd.pivot_table(df, index=cols, columns='Exact Result',
                              aggfunc='size', fill_value=0)
    by_old = pd.pivot_table(df, index=cols, columns=['Exact Result', 'Old Result'],
                            aggfunc='size', fill_value=0)

    s = pd.DataFrame(index=by_exact.index)

    s['HR'] = by_exact.get('HR', 0)
    s['3B'] = by_exact.get('3B', 0)
    s['2B'] = by_exact.get('2B', 0)
    s['1B'] = by_exact.get('1B', 0) + by_exact.get('BUNT 1B', 0)

    s['BB'] = (by_exact.get('BB', 0) + by_exact.get('IBB', 0)
               + by_exact.get('AUTO BB', 0))
    s['IBB'] = by_exact.get('IBB', 0)
    s['Auto BB'] = by_exact.get('AUTO BB', 0)

    s['FO'] = by_exact.get('FO', 0)
    s['SO'] = (by_exact.get('K', 0) + by_exact.get('AUTO K', 0)
               + by_exact.get('BUNT K', 0))
    s['PO'] = by_exact.get('PO', 0)
    s['RGO'] = by_exact.get('RGO', 0)

    lo = by_old.get(('LGO', 'LO'), 0)
    tp = by_old.get(('LGO', 'TP'), 0)
    s['LGO'] = by_exact.get('LGO', 0) - lo

    sh = by_exact.get('BUNT SAC', 0)
    bunt_go = by_exact.get('BUNT GO', 0)
    bunt_dp = by_exact.get('BUNT DP', 0)

    s['DP'] = (by_old.get(('RGO', 'DP'), 0) + by_old.get(('LGO', 'DP'), 0)
               + bunt_dp)

    s['SB'] = (by_exact.get('STEAL 2B', 0) + by_exact.get('STEAL 3B', 0)
               + by_exact.get('STEAL HOME', 0) + by_exact.get('MSTEAL 3B', 0)
               + by_exact.get('MSTEAL HOME', 0))
    s['CS'] = (by_exact.get('CS 2B', 0) + by_exact.get('CS 3B', 0)
               + by_exact.get('CS HOME', 0) + by_exact.get('CMS 3B', 0)
               + by_exact.get('CMS HOME', 0))

    s['H'] = s['1B'] + s['2B'] + s['3B'] + s['HR']
    s['BF'] = (s['H'] + s['BB'] + s['FO'] + s['SO'] + s['PO'] + s['RGO']
               + s['LGO'] + lo + sh + bunt_go + bunt_dp)

    s['IP'] = (s['FO'] + s['SO'] + s['PO'] + s['RGO'] + s['LGO']
               + 2 * lo + s['DP'] + 2 * tp + sh
               + bunt_go + 2 * bunt_dp + s['CS']) / 3

    s['ER'] = df.groupby(cols)['Run'].sum()
    s['RE24'] = df.groupby(cols)['RE24'].sum()
    s['WAR'] = df.groupby(cols)['Pitcher WAR'].sum()
    s['WPA'] = df.groupby(cols)['Pitcher WPA'].sum()
    s['300+ Pitches'] = df.groupby(cols)['Diff'].apply(lambda x: (x >= 300).sum())
    s['400+ Pitches'] = df.groupby(cols)['Diff'].apply(lambda x: (x >= 400).sum())

    return s


def _get_game_home_away(df):
    '''
    Returns a DataFrame indexed by Game ID with columns Away and Home,
    derived from the Inning column (T prefix = away team batting, B = home).
    '''
    away = (df[df['Inning'].str.startswith('T')]
            .groupby('Game ID')['Batter Franchise'].first()
            .rename('Away'))
    home = (df[df['Inning'].str.startswith('B')]
            .groupby('Game ID')['Batter Franchise'].first()
            .rename('Home'))
    return pd.concat([away, home], axis=1)


def _add_location(stats, game_ha, franchise_col):
    '''
    Adds a Location column ('Home' or 'Away') to a per-game stats DataFrame.
    franchise_col is the column in stats that holds the team's franchise name.
    Defaults to 'Away' for games with no bottom innings (edge case).
    '''
    stats = stats.merge(game_ha[['Home']], on='Game ID', how='left')
    stats['Location'] = np.where(stats[franchise_col] == stats['Home'], 'Home', 'Away')
    return stats.drop(columns=['Home'])


# ---------------------------------------------------------------------------
# Per-player per-game stats
# ---------------------------------------------------------------------------

def get_hitting_game_stats(df):
    '''
    Per-player per-game hitting stats.

    Output columns: ID, Game ID, Season, Display Season, Session, Team,
    Franchise, Opponent, Location, plus all BATTER_STATS.
    '''
    cols = ['Hitter ID', 'Game ID', 'Season', 'Display Season', 'Session',
            'Batter Team', 'Batter Franchise', 'Pitcher Franchise']

    stats = _hitting_pivot_stats(df, cols).reset_index()
    stats = stats.rename(columns={
        'Hitter ID': 'ID',
        'Batter Team': 'Team',
        'Batter Franchise': 'Franchise',
        'Pitcher Franchise': 'Opponent',
    })
    stats = _add_location(stats, _get_game_home_away(df), 'Franchise')
    return stats


def get_pitching_game_stats(df):
    '''
    Per-player per-game pitching stats.

    Output columns: ID, Game ID, Season, Display Season, Session, Team,
    Franchise, Opponent, Location, plus all PITCHER_STATS.
    '''
    cols = ['Pitcher ID', 'Game ID', 'Season', 'Display Season', 'Session',
            'Pitcher Team', 'Pitcher Franchise', 'Batter Franchise']

    stats = _pitching_pivot_stats(df, cols).reset_index()
    stats = stats.rename(columns={
        'Pitcher ID': 'ID',
        'Pitcher Team': 'Team',
        'Pitcher Franchise': 'Franchise',
        'Batter Franchise': 'Opponent',
    })
    stats = _add_location(stats, _get_game_home_away(df), 'Franchise')
    return stats


# ---------------------------------------------------------------------------
# Per-team per-game stats
# ---------------------------------------------------------------------------

def get_hitting_team_game_stats(df):
    '''
    Per-team per-game hitting stats (all batters on one team summed).

    Output columns: Team, Opponent, Location, Game ID, Season, Display Season,
    Session, plus all BATTER_STATS.
    '''
    cols = ['Batter Franchise', 'Pitcher Franchise', 'Game ID',
            'Season', 'Display Season', 'Session']

    stats = _hitting_pivot_stats(df, cols).reset_index()
    stats = stats.rename(columns={
        'Batter Franchise': 'Team',
        'Pitcher Franchise': 'Opponent',
    })
    stats = _add_location(stats, _get_game_home_away(df), 'Team')
    return stats


def get_pitching_team_game_stats(df):
    '''
    Per-team per-game pitching stats (all pitchers on one team summed).

    Output columns: Team, Opponent, Location, Game ID, Season, Display Season,
    Session, plus all PITCHER_STATS.
    '''
    cols = ['Pitcher Franchise', 'Batter Franchise', 'Game ID',
            'Season', 'Display Season', 'Session']

    stats = _pitching_pivot_stats(df, cols).reset_index()
    stats = stats.rename(columns={
        'Pitcher Franchise': 'Team',
        'Batter Franchise': 'Opponent',
    })
    stats = _add_location(stats, _get_game_home_away(df), 'Team')
    return stats


# ---------------------------------------------------------------------------
# Both-teams combined per-game stats
# ---------------------------------------------------------------------------

def get_hitting_combined_game_stats(df):
    '''
    Both-teams combined per-game hitting stats.

    Output columns: Game ID, Season, Display Season, Session, Teams (Away @ Home),
    plus all BATTER_STATS.
    Note: RE24 and WPA are near-zero for combined (they are zero-sum).
    '''
    cols = ['Game ID', 'Season', 'Display Season', 'Session']

    stats = _hitting_pivot_stats(df, cols).reset_index()

    game_ha = _get_game_home_away(df)
    game_teams = (game_ha['Away'] + ' @ ' + game_ha['Home']).rename('Teams')
    stats = stats.merge(game_teams, on='Game ID')
    return stats


def get_pitching_combined_game_stats(df):
    '''
    Both-teams combined per-game pitching stats.

    Output columns: Game ID, Season, Display Season, Session, Teams (Away @ Home),
    plus all PITCHER_STATS.
    Note: RE24 and WPA are near-zero for combined (they are zero-sum).
    '''
    cols = ['Game ID', 'Season', 'Display Season', 'Session']

    stats = _pitching_pivot_stats(df, cols).reset_index()

    game_ha = _get_game_home_away(df)
    game_teams = (game_ha['Away'] + ' @ ' + game_ha['Home']).rename('Teams')
    stats = stats.merge(game_teams, on='Game ID')
    return stats


# ---------------------------------------------------------------------------
# Record finders
# ---------------------------------------------------------------------------

def _to_python(val):
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    return val


def make_round_label_fn(per_game_stats):
    '''Returns a function (display_season, session) -> round label for playoff data.'''
    max_sess = per_game_stats.groupby('Display Season')['Session'].max()
    def label(season, session):
        ms = max_sess.get(season)
        if ms is None:
            return str(int(session))
        offset = int(ms) - int(session)
        if 0 <= offset < len(PLAYOFF_ROUNDS):
            return PLAYOFF_ROUNDS[offset]
        return str(int(session))
    return label


def _make_record_finder(threshold=5):
    '''Returns a _record() closure with a shared threshold and tiebreaker.'''

    def _record(per_game, stat, ascending=False, holder_fn=None):
        col = per_game[stat]
        record_val = _to_python(col.min() if ascending else col.max())
        tied = per_game[col == record_val].copy()
        n = len(tied)

        if n <= threshold:
            tied = tied.sort_values(['Season', 'Session', 'Game ID'], ascending=False)
            holders = [holder_fn(row) for _, row in tied.iterrows()]
            return {'record': record_val, 'holders': holders}
        else:
            most_recent = tied.sort_values(
                ['Season', 'Session', 'Game ID'], ascending=False
            ).iloc[0]
            return {
                'record': record_val,
                'tie_count': n,
                'most_recent': holder_fn(most_recent),
            }

    return _record


def get_single_game_records(hitting_game_stats, pitching_game_stats, player_names=None, is_playoff=False):
    '''
    Single-game records for individual players.

    Tie logic: <= 5 holders listed; > 5 shows tie_count + most_recent.
    Most-recent tiebreaker: Season desc, Session desc, Game ID desc.
    Pitcher RE24 uses minimum (most negative = best performance).
    Pitcher IP record uses baseball notation (e.g. "7.2" for 7⅔ IP).

    Returns dict with keys 'batter' and 'pitcher'.
    '''
    _record = _make_record_finder()
    _round = make_round_label_fn(hitting_game_stats) if is_playoff else None

    def _player_holder(row):
        sess = _round(row['Display Season'], row['Session']) if is_playoff else int(row['Session'])
        return {
            'id': int(row['ID']),
            'season': row['Display Season'],
            'session': sess,
            'team': row['Franchise'],
            'location': row['Location'],
            'opponent': row['Opponent'],
        }

    batter_records = {
        stat: _record(hitting_game_stats, stat, holder_fn=_player_holder)
        for stat in BATTER_STATS
    }

    pitcher_records = {}
    for stat in PITCHER_STATS:
        rec = _record(pitching_game_stats, stat,
                      ascending=(stat == 'RE24'), holder_fn=_player_holder)
        if stat == 'IP':
            rec['record'] = _ip_to_display(rec['record'])
        pitcher_records[stat] = rec

    return {'batter': batter_records, 'pitcher': pitcher_records}


def get_team_game_records(team_hitting, team_pitching, is_playoff=False):
    '''
    Single-game records for team combined stats.

    Returns dict with keys 'batter' and 'pitcher'.
    '''
    _record = _make_record_finder()
    _round = make_round_label_fn(team_hitting) if is_playoff else None

    def _team_holder(row):
        sess = _round(row['Display Season'], row['Session']) if is_playoff else int(row['Session'])
        return {
            'team': row['Team'],
            'season': row['Display Season'],
            'session': sess,
            'location': row['Location'],
            'opponent': row['Opponent'],
        }

    batter_records = {
        stat: _record(team_hitting, stat, holder_fn=_team_holder)
        for stat in BATTER_STATS
    }

    pitcher_records = {}
    for stat in PITCHER_STATS:
        rec = _record(team_pitching, stat,
                      ascending=(stat == 'RE24'), holder_fn=_team_holder)
        if stat == 'IP':
            rec['record'] = _ip_to_display(rec['record'])
        pitcher_records[stat] = rec

    return {'batter': batter_records, 'pitcher': pitcher_records}


def get_combined_game_records(combined_hitting, combined_pitching, is_playoff=False):
    '''
    Single-game records for both-teams combined stats.

    Returns dict with keys 'batter' and 'pitcher'.
    Note: RE24 and WPA will be near zero since they are zero-sum.
    '''
    _record = _make_record_finder()
    _round = make_round_label_fn(combined_hitting) if is_playoff else None

    def _combined_holder(row):
        away, home = row['Teams'].split(' @ ')
        sess = _round(row['Display Season'], row['Session']) if is_playoff else int(row['Session'])
        return {
            'away': away,
            'home': home,
            'season': row['Display Season'],
            'session': sess,
        }

    batter_records = {
        stat: _record(combined_hitting, stat, holder_fn=_combined_holder)
        for stat in BATTER_STATS
    }

    pitcher_records = {}
    for stat in PITCHER_STATS:
        rec = _record(combined_pitching, stat,
                      ascending=(stat == 'RE24'), holder_fn=_combined_holder)
        if stat == 'IP':
            rec['record'] = _ip_to_display(rec['record'])
        pitcher_records[stat] = rec

    return {'batter': batter_records, 'pitcher': pitcher_records}


def _ip_to_display(ip):
    full = int(ip)
    thirds = round((ip - full) * 3)
    return f'{full}.{thirds}'
