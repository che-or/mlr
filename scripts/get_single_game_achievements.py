import pandas as pd
from get_single_game_stats import _ip_to_display, make_round_label_fn


def get_no_hitters(pitching_game_stats, is_playoff=False):
    '''
    Returns all no-hitters (individual and combined), sorted most recent first.
    Individual (combined=False): single CG pitcher, H=0. Includes id, ip, so.
    Combined (combined=True): multiple pitchers, team H=0. Includes pitcher_ids.
    perfect=True when H=0 and BB=0.
    '''
    team_game = pitching_game_stats.groupby(['Game ID', 'Franchise']).agg(
        H=('H', 'sum'),
        BB=('BB', 'sum'),
        SO=('SO', 'sum'),
        IP=('IP', 'sum'),
        pitcher_count=('ID', 'count'),
        pitcher_ids=('ID', list),
        Season=('Season', 'first'),
        Display_Season=('Display Season', 'first'),
        Session=('Session', 'first'),
        Opponent=('Opponent', 'first'),
        Location=('Location', 'first'),
    ).reset_index()

    nh = team_game[team_game['H'] == 0].copy()
    nh['perfect'] = nh['BB'] == 0

    _round = make_round_label_fn(pitching_game_stats) if is_playoff else None
    results = []
    for _, row in nh.sort_values(['Season', 'Session', 'Game ID'], ascending=False).iterrows():
        sess = _round(row['Display_Season'], row['Session']) if is_playoff else int(row['Session'])
        is_combined = row['pitcher_count'] > 1
        entry = {
            'combined': bool(is_combined),
            'team': row['Franchise'],
            'opponent': row['Opponent'],
            'location': row['Location'],
            'season': row['Display_Season'],
            'session': sess,
            'perfect': bool(row['perfect']),
            'bb': int(row['BB']),
        }
        if is_combined:
            game_pitchers = pitching_game_stats[
                (pitching_game_stats['Game ID'] == row['Game ID']) &
                (pitching_game_stats['Franchise'] == row['Franchise'])
            ]
            entry['pitchers'] = [
                {'id': int(p['ID']), 'ip': _ip_to_display(p['IP']), 'so': int(p['SO']), 'bb': int(p['BB'])}
                for _, p in game_pitchers.iterrows()
            ]
        else:
            entry['id'] = int(row['pitcher_ids'][0])
            entry['so'] = int(row['SO'])
            entry['ip'] = _ip_to_display(row['IP'])
        results.append(entry)
    return results


def get_cycles(hitting_game_stats, is_playoff=False):
    '''
    Returns all games where a batter hit for the cycle (>=1 each of 1B, 2B, 3B, HR).
    Sorted chronologically.
    Each entry: {id, team, opponent, location, season, session, h, 2b, 3b, hr}
    '''
    hg = hitting_game_stats.copy()
    hg['1B'] = hg['H'] - hg['2B'] - hg['3B'] - hg['HR']
    cycles = hg[(hg['1B'] >= 1) & (hg['2B'] >= 1) & (hg['3B'] >= 1) & (hg['HR'] >= 1)]

    _round = make_round_label_fn(hitting_game_stats) if is_playoff else None
    results = []
    for _, row in cycles.sort_values(['Season', 'Session', 'Game ID'], ascending=False).iterrows():
        sess = _round(row['Display Season'], row['Session']) if is_playoff else int(row['Session'])
        results.append({
            'id': int(row['ID']),
            'team': row['Franchise'],
            'opponent': row['Opponent'],
            'location': row['Location'],
            'season': row['Display Season'],
            'session': sess,
            'h': int(row['H']),
            '2b': int(row['2B']),
            '3b': int(row['3B']),
            'hr': int(row['HR']),
        })
    return results


def get_triangles(hitting_game_stats, is_playoff=False):
    '''
    Returns all games where a batter recorded a "triangle": >=1 2B, >=1 3B,
    and >=1 HR in a single game (no minimum 1B required, unlike a cycle).
    All cycles are triangles, but not all triangles are cycles.
    Sorted chronologically.
    Each entry: {id, team, opponent, location, season, session, h, 2b, 3b, hr}
    '''
    hg = hitting_game_stats.copy()
    triangles = hg[(hg['2B'] >= 1) & (hg['3B'] >= 1) & (hg['HR'] >= 1)]

    _round = make_round_label_fn(hitting_game_stats) if is_playoff else None
    results = []
    for _, row in triangles.sort_values(['Season', 'Session', 'Game ID'], ascending=False).iterrows():
        sess = _round(row['Display Season'], row['Session']) if is_playoff else int(row['Session'])
        results.append({
            'id': int(row['ID']),
            'team': row['Franchise'],
            'opponent': row['Opponent'],
            'location': row['Location'],
            'season': row['Display Season'],
            'session': sess,
            'h': int(row['H']),
            '2b': int(row['2B']),
            '3b': int(row['3B']),
            'hr': int(row['HR']),
        })
    return results


def get_multi_hr_games(hitting_game_stats, min_hr=3, is_playoff=False):
    '''
    Returns all games where a batter hit min_hr or more home runs.
    Sorted by HR count descending, then chronologically.
    Each entry: {id, team, opponent, location, season, session, hr}
    '''
    multi = hitting_game_stats[hitting_game_stats['HR'] >= min_hr].copy()
    _round = make_round_label_fn(hitting_game_stats) if is_playoff else None
    results = []
    for _, row in multi.sort_values(['HR', 'Season', 'Session', 'Game ID'], ascending=[False, False, False, False]).iterrows():
        sess = _round(row['Display Season'], row['Session']) if is_playoff else int(row['Session'])
        results.append({
            'id': int(row['ID']),
            'team': row['Franchise'],
            'opponent': row['Opponent'],
            'location': row['Location'],
            'season': row['Display Season'],
            'session': sess,
            'hr': int(row['HR']),
        })
    return results


