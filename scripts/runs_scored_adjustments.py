import pandas as pd
from pathlib import Path

from game_played_adjustments import (
    _parse_season,
    _game_key,
    _load_game_participants,
)

_SCRIPT_DIR = Path(__file__).resolve().parent
_ADJ_PATH = _SCRIPT_DIR.parent / 'data' / 'runs_scored_adjustments.csv'

_SHEET_COLS = ['League', 'Season', 'Session', 'Game ID', 'Run+', 'Run-', 'Team', 'Notes']


def load_adjustments(path=_ADJ_PATH):
    '''Read the raw runs-scored adjustments sheet export, or an empty frame if absent.'''
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame(columns=_SHEET_COLS)


def _normalize(adj_df, league):
    '''
    Filter to a league (case-insensitive), normalize Season, and compute GameKey.

    Output columns: RunPlus, RunMinus, Season, RawSeason, Session, Team, GameKey
    (RunPlus / RunMinus left as-is - a blank cell stays NaN). Notes is ignored.
    '''
    cols = ['RunPlus', 'RunMinus', 'Season', 'RawSeason', 'Session', 'Team', 'GameKey']
    df = adj_df[adj_df['League'].astype(str).str.lower() == league.lower()].copy()
    if df.empty:
        return pd.DataFrame(columns=cols)

    df = df.rename(columns={'Run+': 'RunPlus', 'Run-': 'RunMinus'})

    parsed = df['Season'].map(_parse_season)
    df['RawSeason'] = df['Season'].astype(str).str.strip()
    df['Season'] = parsed.map(lambda t: t[0])
    df['GameKey'] = [
        _game_key(base, gid, is_b)
        for (_, base, is_b), gid in zip(parsed, df['Game ID'])
    ]
    df['Session'] = df['Session'].astype(int)
    df['Team'] = df['Team'].astype(str).str.strip()

    return df[cols].drop_duplicates()


def apply_hitting_run_adjustments(hitting_stats, league, against=False, participants=None):
    '''
    Re-attribute runs scored in the hitting stats frame. Each sheet row moves one run:
    +1 to the `Run+` player, -1 from the `Run-` player, for the game's `Team`. This
    covers pinch runners who score without a stolen base and extra-innings ghost
    (Manfred) runners - cases the gamelog `Run` column credits to the wrong player, or
    to nobody. Mirrors apply_hitting_game_adjustments in game_played_adjustments.py.

        hitting_stats - per-(ID, Season, Team) hitting stats frame (pre-aggregation)
        league        - lowercase league name (e.g. 'mlr', 'mlr_playoff', 'milr')
        against       - if True, credit/debit the run against the opponent's team
                        (the vs-team split)
        participants  - optional pre-built (Season, GameKey) -> {teams} map

    Only the `R` column is touched (R feeds no rate stat, and every higher
    aggregation sums it). This module does NOT create rows: a Run+/Run- player with
    no line for that (Season, Team) is warned about and skipped - list them in the
    game-played sheet (same doc) so a row exists, since a run implies a game anyway.

    The gamelog `Run` column itself is left untouched, so single-game hitting stats,
    the "most runs in a game" record, and the pitcher scoreless-innings / team
    win-loss streaks keep the raw gamelog attribution.
    '''
    norm = _normalize(load_adjustments(), league)
    if norm.empty:
        return hitting_stats
    if participants is None:
        participants = _load_game_participants(league, norm)

    label = ' (vs-team)' if against else ''

    # Resolve which team each moved run should be credited/debited against.
    deltas, unmatched = [], []
    for r in norm.itertuples(index=False):
        teams = participants.get((r.Season, int(r.GameKey)))
        if not teams or r.Team not in teams:
            unmatched.append((r.Team, r.RawSeason, int(r.GameKey)))
            continue
        if against:
            opponent = teams - {r.Team}
            if len(opponent) != 1:
                unmatched.append((r.Team, r.RawSeason, int(r.GameKey)))
                continue
            credit_team = next(iter(opponent))
        else:
            credit_team = r.Team

        if not pd.isna(r.RunPlus):
            deltas.append({'ID': int(r.RunPlus), 'Season': r.Season, 'Team': credit_team, 'delta': 1})
        if not pd.isna(r.RunMinus):
            deltas.append({'ID': int(r.RunMinus), 'Season': r.Season, 'Team': credit_team, 'delta': -1})

    if unmatched:
        print(f'  WARNING: {len(unmatched)} runs-scored adjustment row(s) for {league}{label} '
              f'matched no real game/team and were skipped: {unmatched[:10]}'
              + (' ...' if len(unmatched) > 10 else ''))
    if not deltas:
        return hitting_stats

    adj = pd.DataFrame(deltas)
    if pd.api.types.is_float_dtype(hitting_stats['Season']):
        adj['Season'] = adj['Season'].astype(float)
    elif bool((adj['Season'] % 1 == 0).all()):
        adj['Season'] = adj['Season'].astype(int)

    key = ['ID', 'Season', 'Team']
    net = adj.groupby(key)['delta'].sum().reset_index(name='dR')

    present = set(zip(hitting_stats['ID'], hitting_stats['Season'], hitting_stats['Team']))
    orphan = net[[
        (i, s, t) not in present for i, s, t in zip(net['ID'], net['Season'], net['Team'])
    ]]
    if len(orphan):
        print(f'  WARNING: {len(orphan)} runs-scored adjustment target(s) for {league}{label} '
              f'have no hitting line for that (Season, Team) and were skipped '
              f'(add them to the game-played sheet): '
              f'{list(orphan[key].itertuples(index=False, name=None))[:10]}')
        net = net[[
            (i, s, t) in present for i, s, t in zip(net['ID'], net['Season'], net['Team'])
        ]]
    if net.empty:
        return hitting_stats

    merged = hitting_stats.merge(net, on=key, how='left')
    matched = merged['dR'].notna()
    merged.loc[matched, 'R'] = merged.loc[matched, 'R'] + merged.loc[matched, 'dR']
    merged = merged.drop(columns='dR')

    added = int((adj['delta'] > 0).sum())
    removed = int((adj['delta'] < 0).sum())
    print(f'  Runs-scored adjustments for {league}{label}: '
          f'+{added} / -{removed} run(s) across {len(net)} player-season row(s).')

    return merged
