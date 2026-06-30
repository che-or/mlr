import json
import pandas as pd
import numpy as np
from get_single_game_stats import _ip_to_display
from determine_pitcher_decisions import get_game_level_decisions


HIT_RESULTS   = frozenset(['1B', 'BUNT 1B', '2B', '3B', 'HR'])
REACH_RESULTS = frozenset(['1B', 'BUNT 1B', '2B', '3B', 'HR', 'BB', 'IBB', 'AUTO BB'])
SB_RESULTS    = frozenset(['STEAL 2B', 'STEAL 3B', 'STEAL HOME', 'MSTEAL 3B', 'MSTEAL HOME'])
CS_RESULTS    = frozenset(['CS 2B', 'CS 3B', 'CS HOME', 'CMS 3B', 'CMS HOME'])
K_RESULTS     = frozenset(['K', 'AUTO K', 'BUNT K'])

_STEAL_PA_TYPES = frozenset([4, 5, 6, 15])


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


def _build_team_result(records, n=10, active_teams=None):
    """Like _build_result but entity is a team code string rather than a player int."""
    if active_teams is not None:
        records = [r for r in records if r[6] in active_teams]
    if not records:
        return {'entries': [], 'tie_at_boundary': None}
    sorted_records = sorted(records, key=lambda r: (r[0], r[5], r[4]), reverse=True)
    entries = [
        {
            'record': r[0],
            'team': str(r[6]),
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


def _merge_streak_bests(prior_bests, all_time, eid_fn):
    """
    Merge cached best streaks with newly computed ones.
    Allows multiple entries per entity when they tie for the best length.
    prior_bests values may be a single tuple list (old format) or a list-of-tuple-lists (new format).
    Returns {eid_str: [tuple_list, ...]} where all entries share the entity's maximum streak length.
    """
    merged = {}
    for eid_str, val in (prior_bests or {}).items():
        if not val:
            continue
        if isinstance(val[0], list):
            merged[eid_str] = [list(v) for v in val]
        else:
            merged[eid_str] = [list(val)]
    for tup in all_time:
        eid = eid_fn(tup)
        t = list(tup)
        if eid not in merged:
            merged[eid] = [t]
        else:
            cur_best = merged[eid][0][0]
            if t[0] > cur_best:
                merged[eid] = [t]
            elif t[0] == cur_best:
                if (t[1], t[2]) not in {(e[1], e[2]) for e in merged[eid]}:
                    merged[eid].append(t)
    return merged


def _load_streak_cache(cache_path):
    if cache_path is None:
        return None
    try:
        with open(cache_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def _save_streak_cache(cache_path, data):
    if cache_path is None:
        return
    with open(cache_path, 'w') as f:
        json.dump(data, f, cls=_NumpyEncoder)


def _expand_cached_frs(frs_serialized):
    """Convert JSON franchise_schedule {sn_str: {fr: [sessions]}} to {(sn,fr): [sessions]}."""
    result = {}
    for sn_str, fsd in (frs_serialized or {}).items():
        sn = int(sn_str)
        for fr, sessions in fsd.items():
            result[(sn, fr)] = sessions
    return result


def _serialize_frs(franchise_schedule):
    """Convert {(sn,fr): [sessions]} to JSON-serializable {sn_str: {fr: [sessions]}}."""
    result = {}
    for (sn, fr), sessions in franchise_schedule.items():
        sn_str = str(sn)
        if sn_str not in result:
            result[sn_str] = {}
        result[sn_str][fr] = sorted(sessions)
    return result


# PA types that are NOT real plate appearances (steals, Manfred runners, trailing multisteals).
# Everything else (1=regular, 2=variant, 3=bunt, 8=IBB, 9=AUTO K, 10=AUTO BB) counts as a real PA.
_NON_PA_TYPES = frozenset([0, 4, 5, 6, 15])


def _prep_pa_df(gamelog_df):
    """Filter to real PAs, add inning sort key, sort chronologically."""
    df = gamelog_df[~gamelog_df['PA Type'].isin(_NON_PA_TYPES)].copy()
    df['_ik'] = df['Inning'].apply(_inning_sort_key)
    return df.sort_values(['Season', 'Session', '_ik'])


def _prep_steal_df(gamelog_df):
    """Filter to steal-attempt rows (SB or CS events), sort chronologically."""
    df = gamelog_df[gamelog_df['PA Type'].isin(_STEAL_PA_TYPES)].copy()
    df = df[df['Exact Result'].isin(SB_RESULTS | CS_RESULTS)]
    df['_ik'] = df['Inning'].apply(_inning_sort_key)
    return df.sort_values(['Season', 'Session', '_ik'])


def _prep_diff_df(gamelog_df):
    """
    Filter to all rows where a real number was guessed (Diff is not NaN).
    Includes swings, bunts, infield-in, steals, and multisteals.
    Excludes IBB, Auto K, Auto BB, and ghost-runner placements (all have NaN Diff).
    Adds a '_diff_passes' column so callers can threshold check without re-reading Diff.
    """
    df = gamelog_df[gamelog_df['Diff'].notna()].copy()
    df['_ik'] = df['Inning'].apply(_inning_sort_key)
    return df.sort_values(['Season', 'Session', '_ik'])


# ---------------------------------------------------------------------------
# Consecutive games played
# ---------------------------------------------------------------------------

def _build_player_game_appearances(gamelog_df, hitting_game_stats):
    """
    Combined batter + pitcher appearances per (player, season, session),
    with the Franchise column needed by get_consecutive_games_played.
    """
    cols = ['ID', 'Season', 'Display Season', 'Session', 'Franchise']
    batter_apps = hitting_game_stats[cols].drop_duplicates()

    # Build (Team, Season) -> Franchise lookup from hitting_game_stats.
    team_franchise = (
        hitting_game_stats[['Team', 'Season', 'Franchise']]
        .drop_duplicates()
        .set_index(['Team', 'Season'])['Franchise']
        .to_dict()
    )

    real_pa = gamelog_df[~gamelog_df['PA Type'].isin(_NON_PA_TYPES)]
    pitch_raw = (
        real_pa[real_pa['Pitcher ID'].notna()]
        [['Pitcher ID', 'Season', 'Display Season', 'Session', 'Pitcher Team']]
        .drop_duplicates(subset=['Pitcher ID', 'Season', 'Session'])
        .copy()
    )
    pitch_raw['ID'] = pitch_raw['Pitcher ID'].astype(int)
    pitch_raw['Franchise'] = pitch_raw.apply(
        lambda r: team_franchise.get((r['Pitcher Team'], r['Season']), r['Pitcher Team']), axis=1
    )
    pitcher_apps = pitch_raw[cols]

    combined = pd.concat([batter_apps, pitcher_apps], ignore_index=True)
    combined = combined.drop_duplicates(subset=['ID', 'Season', 'Session'])
    return combined


def get_consecutive_games_played(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None,
                                  prior_bests=None, resume_state=None, cache_output=None,
                                  franchise_schedule_override=None):
    """Longest streak of consecutive team games in which a player appeared."""
    # Full schedule (including current session) for gap-detection during traversal
    if franchise_schedule_override is not None:
        franchise_schedule = franchise_schedule_override
    else:
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
    new_resume = {}

    for pid, grp in df.groupby('ID'):
        rs = (resume_state or {}).get(str(pid))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs[:6]
            prev_franchise = rs[6] if len(rs) > 6 else None
            prev_season = last_sn
            prev_session = last_sess
            best_len = cur_len
            best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
            best_end_ds, best_end_sess, best_end_sn = last_ds, last_sess, last_sn
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            best_start_ds = best_start_sess = best_end_ds = best_end_sess = None
            best_end_sn = -1
            last_ds = last_sess = last_sn = None
            prev_season = prev_session = prev_franchise = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        season_snap_prev_franchise = None
        had_cur_season = False

        for _, row in grp.iterrows():
            season   = row['Season']
            session  = row['Session']
            ds       = row['Display Season']
            franchise = row['Franchise']

            if cur_season is not None and season == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                season_snap_prev_franchise = prev_franchise
                had_cur_season = True

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
                    # any games between the player's last game (prev_session) and
                    # their first game for the new team (session).
                    curr_team = franchise_schedule.get((season, franchise), [])
                    consecutive = not any(prev_session < s < session for s in curr_team)

                # season gap > 1: consecutive stays False

                if consecutive:
                    cur_len += 1
                else:
                    cur_len = 1
                    cur_start_ds, cur_start_sess = ds, session

            if cur_len >= best_len:
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

        if season_snap_len is not None:
            re_len, re_sds, re_ss, re_lds, re_ls, re_lsn, re_pf = (
                season_snap_len, season_snap_start_ds, season_snap_start_sess,
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn,
                season_snap_prev_franchise)
        else:
            re_len, re_sds, re_ss, re_lds, re_ls, re_lsn, re_pf = (
                cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn, prev_franchise)
        new_resume[str(pid)] = [re_len, re_sds, re_ss, re_lds, re_ls, re_lsn, re_pf]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(tup[6]))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


# ---------------------------------------------------------------------------
# Game-based hitting / on-base streaks
# ---------------------------------------------------------------------------

def _game_streak(hitting_game_stats, condition_fn, active_ids=None, cur_season=None, cur_session=None,
                  prior_bests=None, resume_state=None, cache_output=None):
    """Generic game-based streak. condition_fn(row) -> bool (True = continues streak)."""
    df = hitting_game_stats.sort_values(['ID', 'Season', 'Session'])

    all_time = []
    active = []
    new_resume = {}

    for pid, grp in df.groupby('ID'):
        rs = (resume_state or {}).get(str(pid))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        # Snapshot of active-streak state just before the current in-progress session.
        # If the current session doesn't continue the streak, we fall back to this.
        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = False
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

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
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, pid))

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

        if season_snap_len is not None:
            new_resume[str(pid)] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                    season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(pid)] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(tup[6]))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


def get_hitting_streak(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None):
    """Longest hitting streak (consecutive games played with at least one hit)."""
    return _game_streak(hitting_game_stats, lambda r: r['H'] > 0, active_ids=active_ids,
                        cur_season=cur_season, cur_session=cur_session)


def get_onbase_streak(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None):
    """Longest on-base streak (consecutive games with H + BB > 0)."""
    return _game_streak(hitting_game_stats, lambda r: r['H'] + r['BB'] > 0, active_ids=active_ids,
                        cur_season=cur_season, cur_session=cur_session)


def get_hr_streak(hitting_game_stats, active_ids=None, cur_season=None, cur_session=None):
    """Longest streak of consecutive games with at least one home run."""
    return _game_streak(hitting_game_stats, lambda r: r['HR'] > 0, active_ids=active_ids,
                        cur_season=cur_season, cur_session=cur_session)


# ---------------------------------------------------------------------------
# Scoreless innings streak
# ---------------------------------------------------------------------------

def get_scoreless_innings_streak(gamelog_df, active_ids=None, cur_season=None, cur_session=None,
                                  prior_bests=None, resume_state=None, cache_output=None):
    """
    Longest scoreless innings streak for pitchers.
    Outs are counted at the inning level: only innings with no run scored contribute
    outs to the streak. Caught stealings count as outs. Any run in an inning
    (including Manfred runners or runs credited to steal rows) discards all outs
    from that inning and resets the streak.
    Record is displayed as an IP string (e.g. '12.1').
    """
    # Runs on non-PA rows (Manfred runners, steal attempts) are filtered out by
    # _prep_pa_df but still break a scoreless streak. Capture their inning IDs first.
    non_pa_run_inning_ids = set(
        gamelog_df.loc[
            gamelog_df['PA Type'].isin(_NON_PA_TYPES) & (gamelog_df['Run'] > 0),
            'Inning ID'
        ]
    )

    # CS outs (caught stealings) are real outs that count toward innings pitched
    # but live on steal rows (PA Type 4/5/6) filtered out by _prep_pa_df.
    cs_df = gamelog_df[
        gamelog_df['PA Type'].isin([4, 5, 6]) &
        gamelog_df['Exact Result'].isin(CS_RESULTS)
    ]
    cs_outs_map = cs_df.groupby(['Pitcher ID', 'Inning ID']).size().to_dict()

    df = _prep_pa_df(gamelog_df)

    all_time = []
    active = []
    new_resume = {}

    for pid, grp in df.groupby('Pitcher ID'):
        rs = (resume_state or {}).get(str(int(pid)))
        if rs:
            cur_outs, cur_start_ds, cur_start_sess, cur_end_ds, cur_end_sess, cur_end_sn = rs
            best_outs = cur_outs
            best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
            best_end_ds, best_end_sess, best_end_sn = cur_end_ds, cur_end_sess, cur_end_sn
        else:
            cur_outs = 0
            cur_start_ds = cur_start_sess = None
            cur_end_ds = cur_end_sess = cur_end_sn = None
            best_outs = 0
            best_start_ds = best_start_sess = None
            best_end_ds = best_end_sess = best_end_sn = None

        season_snap_outs = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_end_ds = season_snap_end_sess = season_snap_end_sn = None
        had_cur_season = False

        snap_outs = 0
        snap_start_ds = snap_start_sess = None
        snap_end_ds = snap_end_sess = snap_end_sn = None
        had_current = False
        current_had_runs = False

        for (game_id, inning_id), inning_df in grp.groupby(['Game ID', 'Inning ID'], sort=False):
            ds   = inning_df['Display Season'].iat[0]
            sess = inning_df['Session'].iat[0]
            sn   = inning_df['Season'].iat[0]
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_outs = cur_outs
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_end_ds, season_snap_end_sess, season_snap_end_sn = cur_end_ds, cur_end_sess, cur_end_sn
                had_cur_season = True

            if is_current and not had_current:
                snap_outs = cur_outs
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_end_ds, snap_end_sess, snap_end_sn = cur_end_ds, cur_end_sess, cur_end_sn
                had_current = True

            inning_has_run = (
                inning_id in non_pa_run_inning_ids
                or bool((inning_df['Run'] > 0).any())
            )
            inning_outs = sum(
                _pa_outs(_s(row['Exact Result']), _s(row['Old Result']))
                for _, row in inning_df.iterrows()
            ) + cs_outs_map.get((pid, inning_id), 0)

            if inning_has_run:
                if is_current:
                    current_had_runs = True
                cur_outs = 0
                cur_start_ds = cur_start_sess = None
                cur_end_ds = cur_end_sess = cur_end_sn = None
            else:
                if inning_outs > 0:
                    if cur_outs == 0:
                        cur_start_ds, cur_start_sess = ds, sess
                    cur_outs += inning_outs
                    cur_end_ds, cur_end_sess, cur_end_sn = ds, sess, sn
                    if cur_outs >= best_outs:
                        best_outs = cur_outs
                        best_start_ds, best_start_sess = cur_start_ds, cur_start_sess
                        best_end_ds, best_end_sess, best_end_sn = ds, sess, sn

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

        if season_snap_outs is not None:
            new_resume[str(int(pid))] = [season_snap_outs, season_snap_start_ds, season_snap_start_sess,
                                         season_snap_end_ds, season_snap_end_sess, season_snap_end_sn]
        else:
            new_resume[str(int(pid))] = [cur_outs, cur_start_ds, cur_start_sess,
                                         cur_end_ds, cur_end_sess, cur_end_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(int(tup[6])))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_ip_result(final_all_time), 'active': _build_ip_result(active, active_ids=active_ids)}


# ---------------------------------------------------------------------------
# PA-level batting streaks (items 5–8)
# ---------------------------------------------------------------------------

def _pa_batter_streak(pa_df, condition_fn, active_ids=None, cur_season=None, cur_session=None,
                       prior_bests=None, resume_state=None, cache_output=None):
    """Generic per-batter PA-level streak. condition_fn(exact_result: str) -> bool."""
    all_time = []
    active = []
    new_resume = {}

    for pid, grp in pa_df.groupby('Hitter ID'):
        rs = (resume_state or {}).get(str(pid))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True  # cleared if any current-session PA breaks the streak
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)
            exact = _s(row.get('Exact Result'))

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

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
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, pid))

        act_len = cur_len
        act_start_ds, act_start_sess = cur_start_ds, cur_start_sess
        act_end_ds, act_end_sess, act_end_sn = last_ds, last_sess, last_sn

        if act_len > 0 and act_end_ds is not None:
            active.append((act_len, act_start_ds, act_start_sess,
                           act_end_ds, act_end_sess, act_end_sn, pid))

        if season_snap_len is not None:
            new_resume[str(pid)] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                    season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(pid)] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(tup[6]))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


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

def _pa_pitcher_streak(pa_df, condition_fn, active_ids=None, cur_season=None, cur_session=None,
                        prior_bests=None, resume_state=None, cache_output=None):
    """Generic per-pitcher consecutive-batters-faced streak. condition_fn(exact) -> bool."""
    all_time = []
    active = []
    new_resume = {}

    for pid, grp in pa_df.groupby('Pitcher ID'):
        rs = (resume_state or {}).get(str(int(pid)))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)
            exact = _s(row.get('Exact Result'))

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

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
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, pid))

        act_len = cur_len
        act_start_ds, act_start_sess = cur_start_ds, cur_start_sess
        act_end_ds, act_end_sess, act_end_sn = last_ds, last_sess, last_sn

        if act_len > 0 and act_end_ds is not None:
            active.append((act_len, act_start_ds, act_start_sess,
                           act_end_ds, act_end_sess, act_end_sn, pid))

        if season_snap_len is not None:
            new_resume[str(int(pid))] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                         season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(int(pid))] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(int(tup[6])))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


def get_bf_no_hit_streak(gamelog_df):
    """Consecutive batters faced without allowing a hit."""
    return _pa_pitcher_streak(_prep_pa_df(gamelog_df), lambda e: e not in HIT_RESULTS)


def get_bf_no_baserunner_streak(gamelog_df):
    """Consecutive batters faced without allowing a baserunner (no hit or walk)."""
    return _pa_pitcher_streak(_prep_pa_df(gamelog_df), lambda e: e not in REACH_RESULTS)


# ---------------------------------------------------------------------------
# Diff-based PA streaks
# ---------------------------------------------------------------------------

def _diff_batter_streak(diff_df, condition_fn, active_ids=None, cur_season=None, cur_session=None,
                         prior_bests=None, resume_state=None, cache_output=None):
    """Generic per-batter Diff-based streak. condition_fn(diff: float) -> bool.
    diff_df must come from _prep_diff_df (rows where Diff is not NaN)."""
    all_time = []
    active = []
    new_resume = {}

    for pid, grp in diff_df.groupby('Hitter ID'):
        rs = (resume_state or {}).get(str(pid))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(row['Diff']):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
            else:
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, pid))

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

        if season_snap_len is not None:
            new_resume[str(pid)] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                    season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(pid)] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(tup[6]))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


def _diff_pitcher_streak(diff_df, condition_fn, active_ids=None, cur_season=None, cur_session=None,
                          prior_bests=None, resume_state=None, cache_output=None):
    """Generic per-pitcher Diff-based streak. condition_fn(diff: float) -> bool.
    diff_df must come from _prep_diff_df (rows where Diff is not NaN)."""
    all_time = []
    active = []
    new_resume = {}

    for pid, grp in diff_df.groupby('Pitcher ID'):
        rs = (resume_state or {}).get(str(int(pid)))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(row['Diff']):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
            else:
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, pid))

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

        if season_snap_len is not None:
            new_resume[str(int(pid))] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                         season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(int(pid))] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(int(tup[6])))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


# ---------------------------------------------------------------------------
# Team game streak helpers
# ---------------------------------------------------------------------------

def _build_team_wl_df(hitting_team_game_stats):
    """Build per-team per-game Win/Lost flags by joining each team's R with opponent's R."""
    cols = ['Team', 'Opponent', 'Game ID', 'Season', 'Display Season', 'Session', 'R']
    df = hitting_team_game_stats[cols].copy()
    opp = df[['Game ID', 'Team', 'R']].rename(columns={'Team': 'OppTeam', 'R': 'OppR'})
    df = df.merge(opp, left_on=['Game ID', 'Opponent'], right_on=['Game ID', 'OppTeam'], how='left')
    df['Won']  = df['R'] > df['OppR']
    df['Lost'] = df['R'] < df['OppR']
    return df


def _build_team_auto_df(gamelog_df, hitting_team_game_stats):
    """One row per (Team, Game) with auto_free=True if no Auto K or Auto BB that game."""
    team_games = (
        hitting_team_game_stats[['Team', 'Game ID', 'Season', 'Display Season', 'Session']]
        .drop_duplicates(subset=['Team', 'Game ID'])
    )
    auto_k = (
        gamelog_df[gamelog_df['PA Type'] == 9]
        [['Game ID', 'Batter Franchise']].rename(columns={'Batter Franchise': 'Team'})
        .drop_duplicates()
    )
    auto_k['had_auto'] = True
    auto_bb = (
        gamelog_df[gamelog_df['PA Type'] == 10]
        [['Game ID', 'Pitcher Franchise']].rename(columns={'Pitcher Franchise': 'Team'})
        .drop_duplicates()
    )
    auto_bb['had_auto'] = True
    auto_events = pd.concat([auto_k, auto_bb]).drop_duplicates(subset=['Team', 'Game ID'])
    result = team_games.merge(auto_events, on=['Team', 'Game ID'], how='left')
    result['auto_free'] = ~result['had_auto'].fillna(False).astype(bool)
    return result[['Team', 'Game ID', 'Season', 'Display Season', 'Session', 'auto_free']]


def _team_game_streak(team_wl_df, condition_fn, active_teams=None, cur_season=None, cur_session=None,
                       prior_bests=None, resume_state=None, cache_output=None):
    """Generic game-based team streak. condition_fn(row) -> bool (True = continues streak)."""
    df = team_wl_df.sort_values(['Team', 'Season', 'Session', 'Game ID'])
    all_time = []
    active   = []
    new_resume = {}

    for team, grp in df.groupby('Team'):
        rs = (resume_state or {}).get(str(team))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(row):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
            else:
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, team))

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
                           act_end_ds, act_end_sess, act_end_sn, team))

        if season_snap_len is not None:
            new_resume[str(team)] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                     season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(team)] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for team_str, rs in (resume_state or {}).items():
        if team_str not in new_resume:
            new_resume[team_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], team_str))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(tup[6]))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_team_result(final_all_time), 'active': _build_team_result(active, active_teams=active_teams)}


# ---------------------------------------------------------------------------
# Pitcher game-appearance decision streaks
# ---------------------------------------------------------------------------

def _build_pitcher_app_df(gamelog_df, wls_df):
    """One row per (pitcher, game) appearance, annotated with got_W / got_L flags."""
    real_pa = gamelog_df[~gamelog_df['PA Type'].isin(_NON_PA_TYPES)]
    apps = (
        real_pa[real_pa['Pitcher ID'].notna()]
        [['Pitcher ID', 'Game ID', 'Season', 'Display Season', 'Session']]
        .drop_duplicates(subset=['Pitcher ID', 'Game ID'])
    )
    dec = wls_df[['Game ID', 'W', 'L']]
    apps = apps.merge(dec, on='Game ID', how='left')
    apps['got_W'] = apps['Pitcher ID'] == apps['W']
    apps['got_L'] = apps['Pitcher ID'] == apps['L']
    return apps


def _build_pitcher_save_opp_df(gamelog_df, wls_df):
    """One row per (pitcher, game) save opportunity with got_SV / got_BS flags."""
    real_pa = gamelog_df[~gamelog_df['PA Type'].isin(_NON_PA_TYPES)]
    apps = (
        real_pa[real_pa['Pitcher ID'].notna()]
        [['Pitcher ID', 'Game ID', 'Season', 'Display Season', 'Session']]
        .drop_duplicates(subset=['Pitcher ID', 'Game ID'])
    )
    rows = []
    for _, game_row in wls_df.iterrows():
        game_id = game_row['Game ID']
        sv_pid = game_row.get('SV')
        sv_set = {int(sv_pid)} if sv_pid and pd.notna(sv_pid) else set()
        bs_set = set()
        for col in ('BSH', 'BSA'):
            val = game_row.get(col) or []
            for pid in (val if isinstance(val, list) else [val]):
                if pid is not None and pd.notna(pid):
                    bs_set.add(int(pid))
        for pid in sv_set | bs_set:
            rows.append({'Pitcher ID': pid, 'Game ID': game_id,
                         'got_SV': pid in sv_set, 'got_BS': pid in bs_set})
    if not rows:
        return pd.DataFrame(columns=['Pitcher ID', 'Game ID', 'Season',
                                     'Display Season', 'Session', 'got_SV', 'got_BS'])
    sv_opp = pd.DataFrame(rows)
    sv_opp['Pitcher ID'] = sv_opp['Pitcher ID'].astype(apps['Pitcher ID'].dtype)
    return sv_opp.merge(
        apps[['Pitcher ID', 'Game ID', 'Season', 'Display Season', 'Session']],
        on=['Pitcher ID', 'Game ID'], how='inner'
    )


def _pitcher_game_streak(pitcher_app_df, condition_fn, active_ids=None, cur_season=None, cur_session=None,
                          prior_bests=None, resume_state=None, cache_output=None):
    """Generic per-pitcher game-appearance streak. condition_fn(row) -> bool."""
    df = pitcher_app_df.sort_values(['Pitcher ID', 'Season', 'Session', 'Game ID'])
    all_time = []
    active   = []
    new_resume = {}

    for pid, grp in df.groupby('Pitcher ID'):
        rs = (resume_state or {}).get(str(int(pid)))
        if rs:
            cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn = rs
            best_len = cur_len
        else:
            cur_len = 0
            cur_start_ds = cur_start_sess = None
            best_len = 0
            last_ds = last_sess = last_sn = None

        season_snap_len = None
        season_snap_start_ds = season_snap_start_sess = None
        season_snap_last_ds = season_snap_last_sess = season_snap_last_sn = None
        had_cur_season = False

        snap_len = 0
        snap_start_ds = snap_start_sess = None
        snap_last_ds = snap_last_sess = snap_last_sn = None
        had_current = False
        current_continued = True
        pid_all_time = []

        for _, row in grp.iterrows():
            ds, sess, sn = row['Display Season'], row['Session'], row['Season']
            is_current = (cur_season is not None and sn == cur_season and sess == cur_session)

            if cur_season is not None and sn == cur_season and not had_cur_season:
                season_snap_len = cur_len
                season_snap_start_ds, season_snap_start_sess = cur_start_ds, cur_start_sess
                season_snap_last_ds, season_snap_last_sess, season_snap_last_sn = last_ds, last_sess, last_sn
                had_cur_season = True

            if is_current and not had_current:
                snap_len = cur_len
                snap_start_ds, snap_start_sess = cur_start_ds, cur_start_sess
                snap_last_ds, snap_last_sess, snap_last_sn = last_ds, last_sess, last_sn
                had_current = True

            if condition_fn(row):
                if cur_len == 0:
                    cur_start_ds, cur_start_sess = ds, sess
                cur_len += 1
            else:
                if cur_len > 0:
                    if cur_len > best_len:
                        best_len = cur_len
                        pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
                    elif cur_len == best_len:
                        pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
                if is_current:
                    current_continued = False
                cur_len = 0
                cur_start_ds = cur_start_sess = None

            last_ds, last_sess, last_sn = ds, sess, sn

        if cur_len > 0:
            if cur_len > best_len:
                best_len = cur_len
                pid_all_time = [(cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn)]
            elif cur_len == best_len:
                pid_all_time.append((cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn))
        for inst in pid_all_time:
            all_time.append((*inst, pid))

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

        if season_snap_len is not None:
            new_resume[str(int(pid))] = [season_snap_len, season_snap_start_ds, season_snap_start_sess,
                                         season_snap_last_ds, season_snap_last_sess, season_snap_last_sn]
        else:
            new_resume[str(int(pid))] = [cur_len, cur_start_ds, cur_start_sess, last_ds, last_sess, last_sn]

    for pid_str, rs in (resume_state or {}).items():
        if pid_str not in new_resume:
            new_resume[pid_str] = list(rs)
            if rs[0] > 0:
                active.append((rs[0], rs[1], rs[2], rs[3], rs[4], rs[5], int(pid_str)))

    merged_bests = _merge_streak_bests(prior_bests, all_time, lambda tup: str(int(tup[6])))
    final_all_time = [t for entries in merged_bests.values() for t in entries]
    if cache_output is not None:
        cache_output['raw_all_time'] = merged_bests
        cache_output['new_resume'] = new_resume

    return {'all_time': _build_result(final_all_time), 'active': _build_result(active, active_ids=active_ids)}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_streak_records(gamelog_df, hitting_game_stats, hitting_team_game_stats=None, cache_path=None):
    """
    Compute all streak records, optionally using/updating a JSON cache.

    Returns a dict with keys:
      consecutive_games_played, hitting_streak, onbase_streak, hr_streak,
      scoreless_innings, pa_hit_streak, pa_onbase_streak,
      pa_hitless_streak, pa_baseless_streak,
      bf_no_hit_streak, bf_no_baserunner_streak,
      consecutive_sb_streak, bf_strikeout_streak,
      pitcher_no_win_streak, pitcher_no_loss_streak,
      pitcher_win_streak, pitcher_loss_streak,
      batter_diff_lt100, batter_diff_lt200,
      pitcher_diff_gt300, pitcher_diff_gt400,
      team_win_streak, team_loss_streak  (only when hitting_team_game_stats is provided)

    Each value: {'all_time': {entries, tie_at_boundary}, 'active': {entries, tie_at_boundary}}.
    Active entries are limited to players/teams who appeared in the most recent season.
    The current in-progress session is included only if the streak was already extended there.
    """
    cur_season = gamelog_df['Season'].max()
    cur_session = gamelog_df[gamelog_df['Season'] == cur_season]['Session'].max()

    cache = _load_streak_cache(cache_path)
    use_cache = (cache is not None and cache.get('cached_through_season') == cur_season - 1)

    _ALL_STREAK_KEYS = [
        'consecutive_games_played', 'hitting_streak', 'onbase_streak', 'hr_streak',
        'scoreless_innings', 'pa_hit_streak', 'pa_onbase_streak', 'pa_hitless_streak',
        'pa_baseless_streak', 'bf_no_hit_streak', 'bf_no_baserunner_streak',
        'consecutive_sb_streak', 'bf_strikeout_streak',
        'pitcher_no_win_streak', 'pitcher_no_loss_streak',
        'pitcher_win_streak', 'pitcher_loss_streak',
        'batter_diff_lt100', 'batter_diff_lt200',
        'pitcher_diff_gt300', 'pitcher_diff_gt400',
        'team_win_streak', 'team_loss_streak',
        'pa_no_hr_streak', 'bf_no_hr_streak', 'pitcher_save_streak', 'team_no_auto_streak',
    ]

    if use_cache:
        # Fast path: process only cur_season rows
        hgs_use = hitting_game_stats[hitting_game_stats['Season'] == cur_season]
        gl_use  = gamelog_df[gamelog_df['Season'] == cur_season]
    else:
        hgs_use = hitting_game_stats
        gl_use  = gamelog_df

    # Active player/team ID computation
    hgs_excl = hgs_use[~((hgs_use['Season'] == cur_season) & (hgs_use['Session'] == cur_session))]
    gl_excl  = gl_use[~((gl_use['Season'] == cur_season) & (gl_use['Session'] == cur_session))]
    max_season_active = hgs_excl['Season'].max() if not hgs_excl.empty else cur_season
    active_batter_ids = set(hgs_excl[hgs_excl['Season'] == max_season_active]['ID'].unique())
    pa_recent = gl_excl[(gl_excl['Season'] == max_season_active) & (~gl_excl['PA Type'].isin(_NON_PA_TYPES))]
    active_pitcher_ids = set(int(p) for p in pa_recent['Pitcher ID'].dropna().unique())

    pa_df    = _prep_pa_df(gl_use)
    steal_df = _prep_steal_df(gl_use)
    diff_df  = _prep_diff_df(gl_use)

    player_appearances = _build_player_game_appearances(gl_use, hgs_use)

    wls_df = get_game_level_decisions(gl_use, cur_season, cur_session)
    pitcher_app_df = _build_pitcher_app_df(gl_use, wls_df)
    pitcher_app_df_no_cur = pitcher_app_df[
        ~((pitcher_app_df['Season'] == cur_season) & (pitcher_app_df['Session'] == cur_session))
    ]

    pitcher_save_opp_df = _build_pitcher_save_opp_df(gl_use, wls_df)
    pitcher_save_opp_df_no_cur = pitcher_save_opp_df[
        ~((pitcher_save_opp_df['Season'] == cur_season) &
          (pitcher_save_opp_df['Session'] == cur_session))
    ]

    kw = dict(cur_season=cur_season, cur_session=cur_session)
    cos = {k: {} for k in _ALL_STREAK_KEYS}

    cs = (cache or {}).get('streaks', {}) if use_cache else {}

    def _pb(key):
        return cs.get(key, {}).get('prior_bests') if use_cache else None

    def _rs(key):
        return cs.get(key, {}).get('resume') if use_cache else None

    # For consecutive_games_played: merge cached franchise schedule with cur_season schedule
    if use_cache:
        cur_frs = _get_franchise_schedule(player_appearances)
        full_frs = {**_expand_cached_frs(cache.get('franchise_schedule', {})), **cur_frs}
        frs_override = full_frs
    else:
        frs_override = None

    result = {
        'consecutive_games_played': get_consecutive_games_played(
            player_appearances, active_ids=active_batter_ids | active_pitcher_ids,
            prior_bests=_pb('consecutive_games_played'), resume_state=_rs('consecutive_games_played'),
            cache_output=cos['consecutive_games_played'], franchise_schedule_override=frs_override, **kw),
        'hitting_streak': _game_streak(
            hgs_use, lambda r: r['H'] > 0, active_ids=active_batter_ids,
            prior_bests=_pb('hitting_streak'), resume_state=_rs('hitting_streak'),
            cache_output=cos['hitting_streak'], **kw),
        'onbase_streak': _game_streak(
            hgs_use, lambda r: r['H'] + r['BB'] > 0, active_ids=active_batter_ids,
            prior_bests=_pb('onbase_streak'), resume_state=_rs('onbase_streak'),
            cache_output=cos['onbase_streak'], **kw),
        'hr_streak': _game_streak(
            hgs_use, lambda r: r['HR'] > 0, active_ids=active_batter_ids,
            prior_bests=_pb('hr_streak'), resume_state=_rs('hr_streak'),
            cache_output=cos['hr_streak'], **kw),
        'scoreless_innings': get_scoreless_innings_streak(
            gl_use, active_ids=active_pitcher_ids,
            prior_bests=_pb('scoreless_innings'), resume_state=_rs('scoreless_innings'),
            cache_output=cos['scoreless_innings'], **kw),
        'pa_hit_streak': _pa_batter_streak(
            pa_df, lambda e: e in HIT_RESULTS, active_ids=active_batter_ids,
            prior_bests=_pb('pa_hit_streak'), resume_state=_rs('pa_hit_streak'),
            cache_output=cos['pa_hit_streak'], **kw),
        'pa_onbase_streak': _pa_batter_streak(
            pa_df, lambda e: e in REACH_RESULTS, active_ids=active_batter_ids,
            prior_bests=_pb('pa_onbase_streak'), resume_state=_rs('pa_onbase_streak'),
            cache_output=cos['pa_onbase_streak'], **kw),
        'pa_hitless_streak': _pa_batter_streak(
            pa_df, lambda e: e not in HIT_RESULTS, active_ids=active_batter_ids,
            prior_bests=_pb('pa_hitless_streak'), resume_state=_rs('pa_hitless_streak'),
            cache_output=cos['pa_hitless_streak'], **kw),
        'pa_baseless_streak': _pa_batter_streak(
            pa_df, lambda e: e not in REACH_RESULTS, active_ids=active_batter_ids,
            prior_bests=_pb('pa_baseless_streak'), resume_state=_rs('pa_baseless_streak'),
            cache_output=cos['pa_baseless_streak'], **kw),
        'bf_no_hit_streak': _pa_pitcher_streak(
            pa_df, lambda e: e not in HIT_RESULTS, active_ids=active_pitcher_ids,
            prior_bests=_pb('bf_no_hit_streak'), resume_state=_rs('bf_no_hit_streak'),
            cache_output=cos['bf_no_hit_streak'], **kw),
        'bf_no_baserunner_streak': _pa_pitcher_streak(
            pa_df, lambda e: e not in REACH_RESULTS, active_ids=active_pitcher_ids,
            prior_bests=_pb('bf_no_baserunner_streak'), resume_state=_rs('bf_no_baserunner_streak'),
            cache_output=cos['bf_no_baserunner_streak'], **kw),
        'consecutive_sb_streak': _pa_batter_streak(
            steal_df, lambda e: e in SB_RESULTS, active_ids=active_batter_ids,
            prior_bests=_pb('consecutive_sb_streak'), resume_state=_rs('consecutive_sb_streak'),
            cache_output=cos['consecutive_sb_streak'], **kw),
        'bf_strikeout_streak': _pa_pitcher_streak(
            pa_df, lambda e: e in K_RESULTS, active_ids=active_pitcher_ids,
            prior_bests=_pb('bf_strikeout_streak'), resume_state=_rs('bf_strikeout_streak'),
            cache_output=cos['bf_strikeout_streak'], **kw),
        'pitcher_no_win_streak': _pitcher_game_streak(
            pitcher_app_df_no_cur, lambda r: not r['got_W'], active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_no_win_streak'), resume_state=_rs('pitcher_no_win_streak'),
            cache_output=cos['pitcher_no_win_streak'], **kw),
        'pitcher_no_loss_streak': _pitcher_game_streak(
            pitcher_app_df_no_cur, lambda r: not r['got_L'], active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_no_loss_streak'), resume_state=_rs('pitcher_no_loss_streak'),
            cache_output=cos['pitcher_no_loss_streak'], **kw),
        'pitcher_win_streak': _pitcher_game_streak(
            pitcher_app_df_no_cur[pitcher_app_df_no_cur['got_W'] | pitcher_app_df_no_cur['got_L']],
            lambda r: r['got_W'], active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_win_streak'), resume_state=_rs('pitcher_win_streak'),
            cache_output=cos['pitcher_win_streak'], **kw),
        'pitcher_loss_streak': _pitcher_game_streak(
            pitcher_app_df_no_cur[pitcher_app_df_no_cur['got_W'] | pitcher_app_df_no_cur['got_L']],
            lambda r: r['got_L'], active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_loss_streak'), resume_state=_rs('pitcher_loss_streak'),
            cache_output=cos['pitcher_loss_streak'], **kw),
        'batter_diff_lt100': _diff_batter_streak(
            diff_df, lambda d: d < 100, active_ids=active_batter_ids,
            prior_bests=_pb('batter_diff_lt100'), resume_state=_rs('batter_diff_lt100'),
            cache_output=cos['batter_diff_lt100'], **kw),
        'batter_diff_lt200': _diff_batter_streak(
            diff_df, lambda d: d < 200, active_ids=active_batter_ids,
            prior_bests=_pb('batter_diff_lt200'), resume_state=_rs('batter_diff_lt200'),
            cache_output=cos['batter_diff_lt200'], **kw),
        'pitcher_diff_gt300': _diff_pitcher_streak(
            diff_df, lambda d: d > 300, active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_diff_gt300'), resume_state=_rs('pitcher_diff_gt300'),
            cache_output=cos['pitcher_diff_gt300'], **kw),
        'pitcher_diff_gt400': _diff_pitcher_streak(
            diff_df, lambda d: d > 400, active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_diff_gt400'), resume_state=_rs('pitcher_diff_gt400'),
            cache_output=cos['pitcher_diff_gt400'], **kw),
        'pa_no_hr_streak': _pa_batter_streak(
            pa_df, lambda e: e != 'HR', active_ids=active_batter_ids,
            prior_bests=_pb('pa_no_hr_streak'), resume_state=_rs('pa_no_hr_streak'),
            cache_output=cos['pa_no_hr_streak'], **kw),
        'bf_no_hr_streak': _pa_pitcher_streak(
            pa_df, lambda e: e != 'HR', active_ids=active_pitcher_ids,
            prior_bests=_pb('bf_no_hr_streak'), resume_state=_rs('bf_no_hr_streak'),
            cache_output=cos['bf_no_hr_streak'], **kw),
        'pitcher_save_streak': _pitcher_game_streak(
            pitcher_save_opp_df_no_cur, lambda r: r['got_SV'], active_ids=active_pitcher_ids,
            prior_bests=_pb('pitcher_save_streak'), resume_state=_rs('pitcher_save_streak'),
            cache_output=cos['pitcher_save_streak'], **kw),
    }

    if hitting_team_game_stats is not None:
        if use_cache:
            htgs_use = hitting_team_game_stats[hitting_team_game_stats['Season'] == cur_season]
        else:
            htgs_use = hitting_team_game_stats
        htgs_excl = htgs_use[~((htgs_use['Season'] == cur_season) & (htgs_use['Session'] == cur_session))]
        max_team_season = htgs_excl['Season'].max() if not htgs_excl.empty else None
        active_teams = (set(htgs_excl[htgs_excl['Season'] == max_team_season]['Team'].unique())
                        if max_team_season is not None else set())
        team_wl_df = _build_team_wl_df(htgs_excl)
        result['team_win_streak'] = _team_game_streak(
            team_wl_df, lambda r: r['Won'], active_teams=active_teams,
            prior_bests=_pb('team_win_streak'), resume_state=_rs('team_win_streak'),
            cache_output=cos['team_win_streak'], **kw)
        result['team_loss_streak'] = _team_game_streak(
            team_wl_df, lambda r: r['Lost'], active_teams=active_teams,
            prior_bests=_pb('team_loss_streak'), resume_state=_rs('team_loss_streak'),
            cache_output=cos['team_loss_streak'], **kw)
        team_auto_df = _build_team_auto_df(gl_excl, htgs_excl)
        result['team_no_auto_streak'] = _team_game_streak(
            team_auto_df, lambda r: r['auto_free'], active_teams=active_teams,
            prior_bests=_pb('team_no_auto_streak'), resume_state=_rs('team_no_auto_streak'),
            cache_output=cos['team_no_auto_streak'], **kw)

    # Build and save updated cache
    if use_cache:
        save_frs = full_frs
    else:
        all_frs = _get_franchise_schedule(player_appearances)
        save_frs = {k: v for k, v in all_frs.items() if k[0] < cur_season}

    new_cache = {
        'cached_through_season': cur_season - 1,
        'franchise_schedule': _serialize_frs(save_frs),
        'streaks': {k: {'prior_bests': cos[k].get('raw_all_time', {}),
                        'resume':      cos[k].get('new_resume', {})}
                    for k in _ALL_STREAK_KEYS},
    }
    _save_streak_cache(cache_path, new_cache)
    return result
