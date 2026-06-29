import pandas as pd
import numpy as np
from get_single_game_stats import _ip_to_display


HIT_RESULTS   = frozenset(['1B', 'BUNT 1B', '2B', '3B', 'HR'])
REACH_RESULTS = frozenset(['1B', 'BUNT 1B', '2B', '3B', 'HR', 'BB', 'IBB', 'AUTO BB'])


def _inning_sort_key(inning_str):
    """'T5' -> 9, 'B5' -> 10 for within-game chronological ordering."""
    try:
        s = str(inning_str)
        return int(s[1:]) * 2 + (0 if s.startswith('T') else 1)
    except (ValueError, IndexError):
        return 9999


def _s(val):
    """Safe string conversion, returning '' for NaN/None."""
    try:
        if pd.isna(val):
            return ''
    except (TypeError, ValueError):
        pass
    return str(val)


def _get_franchise_schedule(hitting_game_stats):
    """Returns dict (Season, Franchise) -> sorted list of Sessions."""
    schedule = {}
    for (season, franchise), grp in hitting_game_stats.groupby(['Season', 'Franchise']):
        schedule[(season, franchise)] = sorted(grp['Session'].unique().tolist())
    return schedule


def _pa_outs(exact, old):
    """Outs on a single pitching PA; matches _pitching_pivot_stats IP formula."""
    if exact in ('K', 'AUTO K', 'BUNT K', 'FO', 'PO', 'BUNT SAC', 'BUNT GO',
                 'CS 2B', 'CS 3B', 'CS HOME', 'CMS 3B', 'CMS HOME'):
        return 1
    if exact == 'RGO':
        return 2 if old == 'DP' else 1
    if exact == 'LGO':
        if old in ('LO', 'DP'):
            return 2
        if old == 'TP':
            return 3
        return 1
    if exact == 'BUNT DP':
        return 3
    return 0


def _build_result(records, n=10, active_ids=None):
    """
    records: list of (streak_len, start_ds, start_sess, end_ds, end_sess, end_sn, pid)
    Returns {entries: top-n list, tie_at_boundary: {count, record}|None}.
    If active_ids is provided, filters records to only those pids before ranking.
    """
    if active_ids is not None:
        records = [r for r in records if r[6] in active_ids]
    if not records:
        return {'entries': [], 'tie_at_boundary': None}
    sorted_records = sorted(records, key=lambda r: (r[0], r[5], r[4]), reverse=True)
    entries = [
        {
            'record': r[0],
            'id': int(r[6]),
            'season_start': str(r[1]),
            'session_start': int(r[2]),
            'season_end': str(r[3]),
            'session_end': int(r[4]),
        }
        for r in sorted_records[:n]
    ]
    tie_at_boundary = None
    if len(sorted_records) > n and sorted_records[n][0] == sorted_records[n - 1][0]:
        tie_val = sorted_records[n - 1][0]
        count = sum(1 for r in sorted_records if r[0] == tie_val)
        tie_at_boundary = {'count': count, 'record': tie_val}
    return {'entries': entries, 'tie_at_boundary': tie_at_boundary}


def _build_ip_result(records, n=10, active_ids=None):
    """Like _build_result but streak_len is outs; record displayed as IP string."""
    if active_ids is not None:
        records = [r for r in records if r[6] in active_ids]
    if not records:
        return {'entries': [], 'tie_at_boundary': None}
    sorted_records = sorted(records, key=lambda r: (r[0], r[5], r[4]), reverse=True)
    entries = [
        {
            'record': _ip_to_display(r[0] / 3),
            'id': int(r[6]),
            'season_start': str(r[1]),
            'session_start': int(r[2]),
            'season_end': str(r[3]),
            'session_end': int(r[4]),
        }
        for r in sorted_records[:n]
    ]
    tie_at_boundary = None
    if len(sorted_records) > n and sorted_records[n][0] == sorted_records[n - 1][0]:
        tie_val = sorted_records[n - 1][0]
        count = sum(1 for r in sorted_records if r[0] == tie_val)
        tie_at_boundary = {'count': count, 'record': _ip_to_display(tie_val / 3)}
    return {'entries': entries, 'tie_at_boundary': tie_at_boundary}


# PA types that are NOT real plate appearances (steals, Manfred runners, trailing multisteals).
# Everything else (1=regular, 2=variant, 3=bunt, 8=IBB, 9=AUTO K, 10=AUTO BB) counts as a real PA.
_NON_PA_TYPES = frozenset([0, 4, 5, 6, 15])


def _prep_pa_df(gamelog_df):
    """Filter to real PAs, add inning sort key, sort chronologically."""
    df = gamelog_df[~gamelog_df['PA Type'].isin(_NON_PA_TYPES)].copy()
    df['_ik'] = df['Inning'].apply(_inning_sort_key)
    return df.sort_values(['Season', 'Session', '_ik'])


# ---------------------------------------------------------------------------
# Consecutive games played
# ---------------------------------------------------------------------------

def get_consecutive_games_played(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None):
    """Longest streak of consecutive team games in which a player appeared."""
    # Full schedule (including current session) for gap-detection during traversal
    franchise_schedule = _get_franchise_schedule(hitting_game_stats)
    # Schedule without current session for tail-check: a player who hasn't appeared
    # in the in-progress game shouldn't have their streak broken by it.
    if cur_season is not None and cur_session is not None:
        hgs_excl = hitting_game_stats[
            ~((hitting_game_stats['Season'] == cur_season) & (hitting_game_stats['Session'] == cur_session))
        ]
        sched_excl = _get_franchise_schedule(hgs_excl)
    else:
        sched_excl = franchise_schedule

    df = hitting_game_stats.sort_values(['ID', 'Season', 'Session'])

    all_time = []
    active = []

    for pid, grp in df.groupby('ID'):
        cur_len = 0
        cur_start_ds = cur_start_sess = None
        best_len = 0
        best_start_ds = best_start_sess = best_end_ds = best_end_sess = None
        best_end_sn = -1
        last_ds = last_sess = last_sn = None

        prev_season = prev_session = prev_franchise = None

        for _, row in grp.iterrows():
            season   = row['Season']
            session  = row['Session']
            ds       = row['Display Season']
            franchise = row['Franchise']

            if prev_season is None:
                cur_len = 1
                cur_start_ds, cur_start_sess = ds, session
            else:
                consecutive = False

                if season == prev_season and franchise == prev_franchise:
                    team_sess = franchise_schedule.get((season, franchise), [])
                    consecutive = not any(prev_session < s < session for s in team_sess)

                elif season == prev_season + 1:
                    # Cross-season: player must have played last game of prev season
                    # AND first game of new season (note: split seasons not supported)
                    prev_team = franchise_schedule.get((prev_season, prev_franchise), [])
                    curr_team = franchise_schedule.get((season, franchise), [])
                    played_last  = not any(s > prev_session for s in prev_team)
                    played_first = not any(s < session     for s in curr_team)
                    consecutive = played_last and played_first

                elif season == prev_season and franchise != prev_franchise:
                    # Mid-season franchise change: new team must not have played
                    # any games before this player's first appearance for them
                    curr_team = franchise_schedule.get((season, franchise), [])
                    consecutive = not any(s < session for s in curr_team)

                # season gap > 1: consecutive stays False

                if consecutive:
                    cur_len += 1
                else:
                    cur_len = 1
                    cur_start_ds, cur_start_sess = ds, session

            if cur_len > best_len:
                best_len = cur_len
                best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
                best_end_ds, best_end_sess, best_end_sn = ds, session, season

            prev_season, prev_session, prev_franchise = season, session, franchise
            last_ds, last_sess, last_sn = ds, session, season

        # Tail-check for active streak: did the team play completed sessions after the
        # player's last appearance? If so, the streak is broken. We use sched_excl
        # (without the current in-progress session) so players not yet in today's game
        # aren't penalized.
        active_cur_len = cur_len
        if last_sn is not None and prev_franchise is not None and cur_len > 0:
            team_sess_excl = sched_excl.get((last_sn, prev_franchise), [])
            if any(s > last_sess for s in team_sess_excl):
                active_cur_len = 0

        if best_len > 0:
            all_time.append((best_len, best_start_ds, best_start_sess,
                             best_end_ds, best_end_sess, best_end_sn, pid))
        if active_cur_len > 0 and last_ds is not None:
            active.append((active_cur_len, cur_start_ds, cur_start_sess,
                           last_ds, last_sess, last_sn, pid))

    return {'all_time': _build_result(all_time), 'active': _build_result(active, active_ids=active_ids)}


# ---------------------------------------------------------------------------
# Game-based hitting / on-base streaks
# ---------------------------------------------------------------------------

def _game_streak(hitting_game_stats, condition_fn, active_ids=None, cur_season=None, cur_session=None):
    """Generic game-based streak. condition_fn(row) -> bool (True = continues streak)."""
    df = hitting_game_stats.sort_values(['ID', 'Season', 'Session'])

    all_time = []
    active = []

    for pid, grp in df.groupby('ID'):
        cur_len = 0
        cur_start_ds = cur_start_sess = None
        best_len = 0
        best_start_ds = best_start_sess = best_end_ds = best_end_sess = None
        best_end_sn = -1
        last_ds = last_sess = last_sn = None

        # Snapshot of active-streak state just before the current in-progress session.
        # If the current session doesn't continue the streak, we fall back to this.
        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = False

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(row):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
                if is_current:
                    current_continued = True
            else:
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            if cur_len > best_len:
                best_len = cur_len
                best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
                best_end_ds, best_end_sess, best_end_sn = ds, sess, sn

            last_ds, last_sess, last_sn = ds, sess, sn

        if best_len > 0:
            all_time.append((best_len, best_start_ds, best_start_sess,
                             best_end_ds, best_end_sess, best_end_sn, pid))

        # For active: if the current session didn't continue the streak, revert to pre-game state.
        if had_current and not current_continued:
            act_len = snap_len
            act_start_ds, act_start_sess = snap_start_ds, snap_start_sess
            act_end_ds, act_end_sess, act_end_sn = snap_last_ds, snap_last_sess, snap_last_sn
        else:
            act_len = cur_len
            act_start_ds, act_start_sess = cur_start_ds, cur_start_sess
            act_end_ds, act_end_sess, act_end_sn = last_ds, last_sess, last_sn

        if act_len > 0 and act_end_ds is not None:
            active.append((act_len, act_start_ds, act_start_sess,
                           act_end_ds, act_end_sess, act_end_sn, pid))

    return {'all_time': _build_result(all_time), 'active': _build_result(active, active_ids=active_ids)}


def get_hitting_streak(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None):
    """Longest hitting streak (consecutive games played with at least one hit)."""
    return _game_streak(hitting_game_stats, lambda r: r['H'] > 0, active_ids=active_ids,
                        cur_season=cur_season, cur_session=cur_session)


def get_onbase_streak(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None):
    """Longest on-base streak (consecutive games with H + BB > 0)."""
    return _game_streak(hitting_game_stats, lambda r: r['H'] + r['BB'] > 0, active_ids=active_ids,
                        cur_season=cur_season, cur_session=cur_session)


# ---------------------------------------------------------------------------
# Scoreless innings streak
# ---------------------------------------------------------------------------

def get_scoreless_innings_streak(gamelog_df, active_ids=None, cur_season=None, cur_session=None):
    """
    Longest scoreless innings streak for pitchers: outs recorded between runs allowed.
    Record is displayed as an IP string (e.g. '12.1').
    """
    df = _prep_pa_df(gamelog_df)

    all_time = []
    active = []

    for pid, grp in df.groupby('Pitcher ID'):
        cur_outs = 0
        cur_start_ds = cur_start_sess = None
        cur_end_ds = cur_end_sess = cur_end_sn = None
        best_outs = 0
        best_start_ds = best_start_sess = None
        best_end_ds = best_end_sess = best_end_sn = None

        snap_outs = 0
        snap_start_ds = snap_start_sess = None
        snap_end_ds = snap_end_sess = snap_end_sn = None
        had_current = False
        current_had_runs = False

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if is_current and not had_current:
                snap_outs = cur_outs
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_end_ds, snap_end_sess, snap_end_sn = cur_end_ds, cur_end_sess, cur_end_sn
                had_current = True

            runs = row.get('Run') or 0
            try:
                runs = float(runs)
            except (TypeError, ValueError):
                runs = 0

            if runs > 0:
                if is_current:
                    current_had_runs = True
                cur_outs = 0
                cur_start_ds = cur_start_sess = None
                cur_end_ds = cur_end_sess = cur_end_sn = None
            else:
                exact = _s(row.get('Exact Result'))
                old   = _s(row.get('Old Result'))
                outs  = _pa_outs(exact, old)
                if outs > 0:
                    if cur_outs == 0:
                        cur_start_ds, cur_start_sess = ds, sess
                    cur_outs += outs
                    cur_end_ds, cur_end_sess, cur_end_sn = ds, sess, sn
                    if cur_outs > best_outs:
                        best_outs = cur_outs
                        best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
                        best_end_ds, best_end_sess, best_end_sn = cur_end_ds, cur_end_sess, cur_end_sn

        if best_outs > 0:
            all_time.append((best_outs, best_start_ds, best_start_sess,
                             best_end_ds, best_end_sess, best_end_sn, pid))

        if had_current and current_had_runs:
            act_outs = snap_outs
            act_start_ds, act_start_sess = snap_start_ds, snap_start_sess
            act_end_ds, act_end_sess, act_end_sn = snap_end_ds, snap_end_sess, snap_end_sn
        else:
            act_outs = cur_outs
            act_start_ds, act_start_sess = cur_start_ds, cur_start_sess
            act_end_ds, act_end_sess, act_end_sn = cur_end_ds, cur_end_sess, cur_end_sn

        if act_outs > 0:
            active.append((act_outs, act_start_ds, act_start_sess,
                           act_end_ds, act_end_sess, act_end_sn, pid))

    return {'all_time': _build_ip_result(all_time), 'active': _build_ip_result(active, active_ids=active_ids)}


# ---------------------------------------------------------------------------
# PA-level batting streaks (items 5–8)
# ---------------------------------------------------------------------------

def _pa_batter_streak(pa_df, condition_fn, active_ids=None, cur_season=None, cur_session=None):
    """Generic per-batter PA-level streak. condition_fn(exact_result: str) -> bool."""
    all_time = []
    active = []

    for pid, grp in pa_df.groupby('Hitter ID'):
        cur_len = 0
        cur_start_ds = cur_start_sess = None
        best_len = 0
        best_start_ds = best_start_sess = best_end_ds = best_end_sess = None
        best_end_sn = -1
        last_ds = last_sess = last_sn = None

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True  # cleared if any current-session PA breaks the streak

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)
            exact = _s(row.get('Exact Result'))

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(exact):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
            else:
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            if cur_len > best_len:
                best_len = cur_len
                best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
                best_end_ds, best_end_sess, best_end_sn = ds, sess, sn

            last_ds, last_sess, last_sn = ds, sess, sn

        if best_len > 0:
            all_time.append((best_len, best_start_ds, best_start_sess,
                             best_end_ds, best_end_sess, best_end_sn, pid))

        if had_current and not current_continued:
            act_len = snap_len
            act_start_ds, act_start_sess = snap_start_ds, snap_start_sess
            act_end_ds, act_end_sess, act_end_sn = snap_last_ds, snap_last_sess, snap_last_sn
        else:
            act_len = cur_len
            act_start_ds, act_start_sess = cur_start_ds, cur_start_sess
            act_end_ds, act_end_sess, act_end_sn = last_ds, last_sess, last_sn

        if act_len > 0 and act_end_ds is not None:
            active.append((act_len, act_start_ds, act_start_sess,
                           act_end_ds, act_end_sess, act_end_sn, pid))

    return {'all_time': _build_result(all_time), 'active': _build_result(active, active_ids=active_ids)}


def get_pa_hitting_streak(gamelog_df):
    """Consecutive plate appearances with a hit."""
    return _pa_batter_streak(_prep_pa_df(gamelog_df), lambda e: e in HIT_RESULTS)


def get_pa_onbase_streak(gamelog_df):
    """Consecutive plate appearances reaching base (hit or walk)."""
    return _pa_batter_streak(_prep_pa_df(gamelog_df), lambda e: e in REACH_RESULTS)


def get_pa_hitless_streak(gamelog_df):
    """Consecutive plate appearances without a hit."""
    return _pa_batter_streak(_prep_pa_df(gamelog_df), lambda e: e not in HIT_RESULTS)


def get_pa_baseless_streak(gamelog_df):
    """Consecutive plate appearances without reaching base."""
    return _pa_batter_streak(_prep_pa_df(gamelog_df), lambda e: e not in REACH_RESULTS)


# ---------------------------------------------------------------------------
# PA-level pitching streaks (items 9–10)
# ---------------------------------------------------------------------------

def _pa_pitcher_streak(pa_df, condition_fn, active_ids=None, cur_season=None, cur_session=None):
    """Generic per-pitcher consecutive-batters-faced streak. condition_fn(exact) -> bool."""
    all_time = []
    active = []

    for pid, grp in pa_df.groupby('Pitcher ID'):
        cur_len = 0
        cur_start_ds = cur_start_sess = None
        best_len = 0
        best_start_ds = best_start_sess = best_end_ds = best_end_sess = None
        best_end_sn = -1
        last_ds = last_sess = last_sn = None

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)
            exact = _s(row.get('Exact Result'))

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(exact):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
            else:
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            if cur_len > best_len:
                best_len = cur_len
                best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
                best_end_ds, best_end_sess, best_end_sn = ds, sess, sn

            last_ds, last_sess, last_sn = ds, sess, sn

        if best_len > 0:
            all_time.append((best_len, best_start_ds, best_start_sess,
                             best_end_ds, best_end_sess, best_end_sn, pid))

        if had_current and not current_continued:
            act_len = snap_len
            act_start_ds, act_start_sess = snap_start_ds, snap_start_sess
            act_end_ds, act_end_sess, act_end_sn = snap_last_ds, snap_last_sess, snap_last_sn
        else:
            act_len = cur_len
            act_start_ds, act_start_sess = cur_start_ds, cur_start_sess
            act_end_ds, act_end_sess, act_end_sn = last_ds, last_sess, last_sn

        if act_len > 0 and act_end_ds is not None:
            active.append((act_len, act_start_ds, act_start_sess,
                           act_end_ds, act_end_sess, act_end_sn, pid))

    return {'all_time': _build_result(all_time), 'active': _build_result(active, active_ids=active_ids)}


def get_bf_no_hit_streak(gamelog_df):
    """Consecutive batters faced without allowing a hit."""
    return _pa_pitcher_streak(_prep_pa_df(gamelog_df), lambda e: e not in HIT_RESULTS)


def get_bf_no_baserunner_streak(gamelog_df):
    """Consecutive batters faced without allowing a baserunner (no hit or walk)."""
    return _pa_pitcher_streak(_prep_pa_df(gamelog_df), lambda e: e not in REACH_RESULTS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_streak_records(gamelog_df, hitting_game_stats):
    """
    Compute all streak records.

    Returns a dict with keys:
      consecutive_games_played, hitting_streak, onbase_streak,
      scoreless_innings, pa_hit_streak, pa_onbase_streak,
      pa_hitless_streak, pa_baseless_streak,
      bf_no_hit_streak, bf_no_baserunner_streak

    Each value: {'all_time': {entries, tie_at_boundary}, 'active': {entries, tie_at_boundary}}.
    Active entries are limited to players who appeared in the most recent season.
    The current in-progress session is included only if the streak was already extended there.
    """
    # Identify the current in-progress session (passed to each streak function so they can
    # snapshot state before it and revert if the streak wasn't continued there).
    cur_season = gamelog_df['Season'].max()
    cur_session = gamelog_df[gamelog_df['Season'] == cur_season]['Session'].max()

    # Compute active player IDs from data excluding the current session.
    # This ensures a player who only debuted in the current in-progress session doesn't
    # displace established active players, and avoids partial-game contamination.
    hgs_excl = hitting_game_stats[
        ~((hitting_game_stats['Season'] == cur_season) & (hitting_game_stats['Session'] == cur_session))
    ]
    gl_excl = gamelog_df[
        ~((gamelog_df['Season'] == cur_season) & (gamelog_df['Session'] == cur_session))
    ]
    max_season = hgs_excl['Season'].max()
    # Separate active ID sets for batters vs pitchers to avoid cross-contamination.
    active_batter_ids = set(hgs_excl[hgs_excl['Season'] == max_season]['ID'].unique())
    pa_recent = gl_excl[(gl_excl['Season'] == max_season) & (~gl_excl['PA Type'].isin(_NON_PA_TYPES))]
    active_pitcher_ids = set(int(p) for p in pa_recent['Pitcher ID'].dropna().unique())

    pa_df = _prep_pa_df(gamelog_df)

    kw = dict(cur_season=cur_season, cur_session=cur_session)
    return {
        'consecutive_games_played': get_consecutive_games_played(
            hitting_game_stats, active_ids=active_batter_ids, **kw),
        'hitting_streak':           get_hitting_streak(
            hitting_game_stats, active_ids=active_batter_ids, **kw),
        'onbase_streak':            get_onbase_streak(
            hitting_game_stats, active_ids=active_batter_ids, **kw),
        'scoreless_innings':        get_scoreless_innings_streak(
            gamelog_df, active_ids=active_pitcher_ids, **kw),
        'pa_hit_streak':            _pa_batter_streak(
            pa_df, lambda e: e in HIT_RESULTS,       active_ids=active_batter_ids, **kw),
        'pa_onbase_streak':         _pa_batter_streak(
            pa_df, lambda e: e in REACH_RESULTS,     active_ids=active_batter_ids, **kw),
        'pa_hitless_streak':        _pa_batter_streak(
            pa_df, lambda e: e not in HIT_RESULTS,   active_ids=active_batter_ids, **kw),
        'pa_baseless_streak':       _pa_batter_streak(
            pa_df, lambda e: e not in REACH_RESULTS, active_ids=active_batter_ids, **kw),
        'bf_no_hit_streak':         _pa_pitcher_streak(
            pa_df, lambda e: e not in HIT_RESULTS,   active_ids=active_pitcher_ids, **kw),
        'bf_no_baserunner_streak':  _pa_pitcher_streak(
            pa_df, lambda e: e not in REACH_RESULTS, active_ids=active_pitcher_ids, **kw),
    }
