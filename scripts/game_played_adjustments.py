import numpy as np
import pandas as pd
from pathlib import Path

from load_gamelogs import _load_player_types
from get_hitting_stats import _calculate_hitting_rate_stats, _calculate_ops_plus

_SCRIPT_DIR = Path(__file__).resolve().parent
_ADJ_PATH = _SCRIPT_DIR.parent / 'data' / 'game_played_adjustments.csv'
_RAW_GAMELOG_DIR = _SCRIPT_DIR.parent / 'data' / 'raw_gamelogs'

# Counting / neutral columns that must be 0 (not NaN) on a synthetic row so downstream
# sums and weighted averages stay finite.
_ZERO_COLS = [
    'HR', '3B', '2B', '1B', 'BB', 'IBB', 'FO', 'SO', 'Auto K', 'PO', 'RGO', 'LGO', 'LO',
    'SF', 'SH', 'GO', 'GIDP', 'GITP', 'SB 2B', 'SB 3B', 'SB Home', 'CS 2B', 'CS 3B', 'CS Home',
    'SB', 'CS', '1RHR', '2RHR', '3RHR', '4RHR', 'H_RISP', 'AB_RISP',
    'H', 'PA', 'AB', 'TB', 'TB+', 'R', 'RBI', 'Total Diff', 'Total Plays', 'RE24', 'WPA', 'WAR',
    '0 Diffs', '500 Diffs',
    'nH', 'nTB', 'nBB', 'nFO', 'nSH', 'nPA', 'nAB', 'nSF',
]
# Columns that are constant within a season - copied from a real row of the same season.
_SEASON_CONST_COLS = ['SF value', 'lgnH', 'lgnBB', 'lgnPA', 'lgnAB', 'lgnTB', 'lgnOBP', 'lgnSLG']
_PLAYER_ATTR_COLS = ['Name', 'Batting Type', 'Pitching Type', 'Handedness', 'Position']


def _parse_season(raw):
    '''
    Normalize a sheet Season value. Mirrors load_gamelogs.py and
    determine_pitcher_decisions.py: '8A' -> 8.1, '8B' -> 8.2, else int.

    Output: (season_value, base_int, is_b_half)
    '''
    s = str(raw).strip()
    if s[-1:].upper() == 'A':
        return int(s[:-1]) + 0.1, int(s[:-1]), False
    if s[-1:].upper() == 'B':
        return int(s[:-1]) + 0.2, int(s[:-1]), True
    return int(s), int(s), False


def _game_key(base_int, raw_game_id, is_b):
    '''Canonical Game ID, matching load_gamelogs.py (Season*1000 + rawID, +500 for 8B).'''
    return int(base_int) * 1000 + int(raw_game_id) + (500 if is_b else 0)


def _display_season(season_value):
    if float(season_value).is_integer():
        return f'S{int(season_value)}'
    base = int(season_value)
    return f'S{base}A' if round(season_value - base, 1) == 0.1 else f'S{base}B'


def load_adjustments(path=_ADJ_PATH):
    '''Read the raw game-played adjustments sheet export, or an empty frame if absent.'''
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame(columns=['ID', 'Name', 'League', 'Season', 'Session', 'Game ID', 'Team', 'Notes'])


def _normalize(adj_df, league):
    '''
    Filter to a league (case-insensitive), normalize Season, and compute GameKey.

    Output columns: ID, Season, Session, Team, GameKey, RawSeason (deduplicated).
    Notes is deliberately ignored - every listed game is credited.
    '''
    cols = ['ID', 'Season', 'Session', 'Team', 'GameKey', 'RawSeason']
    df = adj_df[adj_df['League'].astype(str).str.lower() == league.lower()].copy()
    if df.empty:
        return pd.DataFrame(columns=cols)

    parsed = df['Season'].map(_parse_season)
    df['RawSeason'] = df['Season'].astype(str).str.strip()
    df['Season'] = parsed.map(lambda t: t[0])
    df['GameKey'] = [
        _game_key(base, gid, is_b)
        for (_, base, is_b), gid in zip(parsed, df['Game ID'])
    ]
    df['ID'] = df['ID'].astype(int)
    df['Session'] = df['Session'].astype(int)
    df['Team'] = df['Team'].astype(str).str.strip()

    return df[cols].drop_duplicates()


def _load_game_participants(league, norm_adj):
    '''
    (Season_value, GameKey) -> set of team abbreviations that played that game, read
    straight from the raw gamelog CSVs referenced by norm_adj. Used to validate every
    adjustment row and to resolve the opponent for the vs-team split.
    '''
    participants = {}
    for raw_season in sorted(norm_adj['RawSeason'].unique()):
        season_value, base_int, is_b = _parse_season(raw_season)
        path = _RAW_GAMELOG_DIR / f'{league}_raw_gamelog_S{raw_season}.csv'
        if not path.exists():
            continue
        raw = pd.read_csv(path, usecols=['Game ID', 'Batter Team', 'Pitcher Team'])
        raw['GameKey'] = base_int * 1000 + raw['Game ID'].astype(int) + (500 if is_b else 0)
        for game_key, grp in raw.groupby('GameKey'):
            teams = set(grp['Batter Team'].astype(str).str.strip())
            teams |= set(grp['Pitcher Team'].astype(str).str.strip())
            participants[(season_value, int(game_key))] = teams
    return participants


def game_played_appearance_rows(league, seasons, team_franchise=None):
    '''
    Player game appearances from the game-played adjustments, formatted like the batter
    appearance frame in get_streak_records._build_player_game_appearances so they can feed
    the consecutive-games-played streak. Restricted to `seasons` (a collection of Season
    values) to stay consistent with the streak module's per-season cache fast-path.

        team_franchise - optional {(Team, Season): Franchise} lookup; falls back to Team.

    Output columns: ID, Season, Display Season, Session, Franchise (deduped on ID/Season/Session).
    '''
    out_cols = ['ID', 'Season', 'Display Season', 'Session', 'Franchise']
    norm = _normalize(load_adjustments(), league)
    norm = norm[norm['Season'].isin(set(seasons))] if not norm.empty else norm
    if norm.empty:
        return pd.DataFrame(columns=out_cols)

    tf = team_franchise or {}
    out = pd.DataFrame({
        'ID': norm['ID'].astype(int),
        'Season': norm['Season'].values,
        'Display Season': norm['Season'].map(_display_season).values,
        'Session': norm['Session'].astype(int).values,
        'Franchise': [tf.get((t, s), t) for t, s in zip(norm['Team'], norm['Season'])],
    })
    return out.drop_duplicates(subset=['ID', 'Season', 'Session'])


def apply_hitting_game_adjustments(hitting_stats, league, against=False, participants=None):
    '''
    Credit manually-tracked games toward hitting G. Mirrors
    _apply_pitcher_decision_adjustments in get_pitching_stats.py.

        hitting_stats - per-(ID, Season, Team) hitting stats frame (pre-aggregation)
        league        - lowercase league name (e.g. 'mlr', 'mlr_playoff')
        against       - if True, credit the game against the opponent's team (vs-team split)
        participants  - optional pre-built (Season, GameKey) -> {teams} map

    A game is added to the player's G_list (a set of canonical Game IDs), so adding a game
    the player did in fact bat in is a harmless no-op. When the player has no row for that
    (Season, Team), a new row is created with 0 counting stats and null rate stats.
    '''
    norm = _normalize(load_adjustments(), league)
    if norm.empty:
        return hitting_stats
    if participants is None:
        participants = _load_game_participants(league, norm)

    label = ' (vs-team)' if against else ''

    # Resolve which team each listed game should be credited to.
    rows, unmatched = [], []
    for r in norm.itertuples(index=False):
        teams = participants.get((r.Season, int(r.GameKey)))
        if not teams or r.Team not in teams:
            unmatched.append((r.ID, r.RawSeason, r.Team, int(r.GameKey)))
            continue
        if against:
            opponent = teams - {r.Team}
            if len(opponent) != 1:
                unmatched.append((r.ID, r.RawSeason, r.Team, int(r.GameKey)))
                continue
            credit_team = next(iter(opponent))
        else:
            credit_team = r.Team
        rows.append({'ID': r.ID, 'Season': r.Season, 'Team': credit_team,
                     'GameKey': int(r.GameKey), 'Session': int(r.Session)})

    if unmatched:
        print(f'  WARNING: {len(unmatched)} game-played adjustment row(s) for {league}{label} '
              f'matched no real game/team and were skipped: {unmatched[:10]}'
              + (' ...' if len(unmatched) > 10 else ''))
    if not rows:
        return hitting_stats

    adj = pd.DataFrame(rows)
    if pd.api.types.is_float_dtype(hitting_stats['Season']):
        adj['Season'] = adj['Season'].astype(float)
    elif bool((adj['Season'] % 1 == 0).all()):
        adj['Season'] = adj['Season'].astype(int)

    key = ['ID', 'Season', 'Team']
    adj_by_key = adj.groupby(key).agg(
        add_keys=('GameKey', lambda s: set(s)),
        session=('Session', 'max'),
    ).reset_index()

    team_franchise = hitting_stats.groupby(['Season', 'Team'])['Franchise'].first()

    # Existing rows: union the new Game IDs into G_list and recompute G.
    merged = hitting_stats.merge(adj_by_key[key + ['add_keys']], on=key, how='left')
    has_add = merged['add_keys'].notna()
    merged.loc[has_add, 'G_list'] = [
        set(gl) | ak for gl, ak in zip(merged.loc[has_add, 'G_list'], merged.loc[has_add, 'add_keys'])
    ]
    merged['G'] = merged['G_list'].apply(len)
    merged = merged.drop(columns='add_keys')

    # Missing rows: build synthetic 0-stat rows.
    present = set(zip(hitting_stats['ID'], hitting_stats['Season'], hitting_stats['Team']))
    missing = adj_by_key[[
        (i, s, t) not in present
        for i, s, t in zip(adj_by_key['ID'], adj_by_key['Season'], adj_by_key['Team'])
    ]]

    if len(missing):
        season_const = hitting_stats.groupby('Season')[_SEASON_CONST_COLS].first()
        attrs = _load_player_types(int(np.ceil(hitting_stats['Season'].max())), league, all_seasons=True)
        attrs = attrs.drop_duplicates(['Season', 'ID']).set_index(['Season', 'ID'])

        recs = []
        for r in missing.itertuples(index=False):
            franchise = team_franchise.get((r.Season, r.Team), r.Team)
            rec = {c: 0 for c in _ZERO_COLS}
            rec.update({
                'ID': r.ID, 'Season': r.Season, 'Team': r.Team, 'Franchise': franchise,
                'Display Season': _display_season(r.Season),
                'G_list': set(r.add_keys), 'G': len(r.add_keys),
                'Last Team': franchise, 'Last Session': r.session,
            })
            for c in _SEASON_CONST_COLS:
                rec[c] = season_const.loc[r.Season, c] if r.Season in season_const.index else np.nan
            attr_row = attrs.loc[(r.Season, r.ID)] if (r.Season, r.ID) in attrs.index else None
            for c in _PLAYER_ATTR_COLS:
                rec[c] = attr_row[c] if attr_row is not None else np.nan
            recs.append(rec)

        new_df = pd.DataFrame(recs)
        with np.errstate(invalid='ignore', divide='ignore'):
            new_df = _calculate_hitting_rate_stats(new_df)
            new_df = _calculate_ops_plus(new_df)
        for c in merged.columns:
            if c not in new_df.columns:
                new_df[c] = np.nan
        merged = pd.concat([merged, new_df[merged.columns]], ignore_index=True)

    # `Last Team` is a season-level value (the last franchise the player appeared for that
    # season) - it drives the multi-team-season logo in the frontend via
    # create_hitting_subrows' `.first()`. A sheet game can be later than any real one, so
    # recompute the winner over real + sheet appearances and broadcast it to every row for
    # that (ID, Season). Only meaningful on the primary (own-team) frame.
    if against:
        print(f'  Game-played adjustments for {league}{label}: '
              f'{int(has_add.sum())} existing row(s) updated, {len(missing)} new row(s) created.')
        return merged

    sheet_last = (adj.sort_values(['ID', 'Season', 'Session', 'GameKey'])
                     .groupby(['ID', 'Season']).tail(1)[['ID', 'Season', 'Team', 'Session']])
    sheet_last['fr'] = [team_franchise.get((s, t), t)
                        for s, t in zip(sheet_last['Season'], sheet_last['Team'])]
    real_last = (hitting_stats.groupby(['ID', 'Season'])
                 .agg(rt=('Last Team', 'first'), rs=('Last Session', 'max')).reset_index())
    sheet_last = sheet_last.merge(real_last, on=['ID', 'Season'], how='left')
    last_team = {
        (r.ID, r.Season): (r.fr if (pd.isna(r.rs) or r.Session > r.rs) else r.rt)
        for r in sheet_last.itertuples(index=False)
    }
    lt_mask = [(i, s) in last_team for i, s in zip(merged['ID'], merged['Season'])]
    merged.loc[lt_mask, 'Last Team'] = [last_team[(i, s)] for i, s in
                                        zip(merged.loc[lt_mask, 'ID'], merged.loc[lt_mask, 'Season'])]

    print(f'  Game-played adjustments for {league}{label}: '
          f'{int(has_add.sum())} existing row(s) updated, {len(missing)} new row(s) created.')

    return merged
