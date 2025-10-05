from data_loader import load_all_seasons
from game_processing import get_pitching_decisions
import pandas as pd
import sys
import json

def _read_cache_manifest(cache_dir):
    manifest_path = os.path.join(cache_dir, 'cache_info.json')
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            return data.get('last_run_most_recent')
    except (json.JSONDecodeError, IOError):
        return None

def _write_cache_manifest(cache_dir, most_recent_season):
    manifest_path = os.path.join(cache_dir, 'cache_info.json')
    try:
        with open(manifest_path, 'w') as f:
            json.dump({'last_run_most_recent': most_recent_season}, f)
    except IOError:
        print("Warning: Could not write to cache manifest file.")


# --- Global Helper Functions ---
def calculate_ops_plus_for_row(row, league_stats_by_season):
    """Calculates OPS+ for a given player row, handling different season data structures."""
    if row['PA'] == 0:
        return pd.NA

    # Determine season from the row's data structure. One call site passes a DF row (which has a 'Season' column),
    # the other passes a Series from a different structure where the season is the name.
    if 'Season' in row.index:
        season_name = row['Season']
    else:
        season_name = f"S{row.name}"

    season_stats = league_stats_by_season.get(season_name)
    if not season_stats or season_stats['lg_nOBP'] == 0 or season_stats['lg_nSLG'] == 0:
        return 100

    player_nobp = row['nOBP']
    player_nslg = row['nSLG']

    if pd.isna(player_nobp) or pd.isna(player_nslg):
        return 100

    ops_plus = 100 * ((player_nobp / season_stats['lg_nOBP']) + (player_nslg / season_stats['lg_nSLG']) - 1)

    if pd.isna(ops_plus):
        return 100

    return int(round(ops_plus))


# --- Formatting and Stat Calculation Functions ---
def format_ip(ip_float):
    whole_innings = int(ip_float)
    outs = round((ip_float - whole_innings) * 3)
    if outs == 3:
        whole_innings += 1
        outs = 0
    return f"{whole_innings}.{outs}"

def calculate_hitting_stats(df, season=None):
    if df.empty: return None

    if season is None:
        season = df.name # Get season from group name
    use_old_results = season in ['S2', 'S3']

    # Define result sets based on season
    if use_old_results:
        result_col = 'Old Result'
        hits = {'1B', '2B', '3B', 'HR'} # 'Bunt' is ambiguous, treated as non-hit
        walks = {'BB', 'IBB', 'Auto BB'}
        strikeouts = {'K', 'Auto K'}
        stolen_bases = {'SB'}
        caught_stealing = {'CS'}
        pa_events = hits | walks | strikeouts | {'FO', 'PO', 'LGO', 'RGO', 'LO', 'DP', 'TP', 'Sac', 'Bunt'}
    else:
        result_col = 'Exact Result'
        hits = {'1B', '2B', '3B', 'HR', 'BUNT 1B'}
        walks = {'BB', 'IBB', 'Auto BB', 'AUTO BB'}
        strikeouts = {'K', 'Auto K', 'Bunt K', 'AUTO K'}
        stolen_bases = {'STEAL 2B', 'STEAL 3B', 'Steal 2B', 'Steal 3B'}
        caught_stealing = {'CS 2B', 'CS 3B', 'CS Home'}
        pa_events = hits | walks | strikeouts | {'FO', 'PO', 'LGO', 'RGO', 'LO', 'BUNT DP', 'BUNT GO', 'BUNT Sac', 'Bunt Sac'}

    # Filter for events that have a diff and calculate the average
    diff_events = pa_events | stolen_bases | caught_stealing
    diff_df = df[df[result_col].isin(diff_events)]
    numeric_diff = pd.to_numeric(diff_df['Diff'], errors='coerce')
    avg_diff = numeric_diff.mean()

    # First, calculate non-PA stats like SB and CS from the original dataframe
    num_sb = df[df[result_col].isin(stolen_bases)].shape[0]
    num_cs = df[df[result_col].isin(caught_stealing)].shape[0]

    # Now, filter for actual plate appearance events
    pa_df = df[df[result_col].isin(pa_events)]
    pa = len(pa_df)

    re24 = pa_df['RE24'].sum() if 'RE24' in pa_df.columns else 0

    if pa == 0:
        return pd.Series({'G': df['Session'].nunique(), 'PA': 0, 'AB': 0, 'H': 0, 'R': 0, 'RBI': 0, '2B': 0, '3B': 0, 'HR': 0, 'BB': 0, 'K': 0, 'SB': num_sb, 'CS': num_cs, 'AVG': 0, 'OBP': 0, 'SLG': 0, 'OPS': 0, 'Avg Diff': avg_diff, 'RE24': re24})

    games_played = df['Session'].nunique()
    num_walks = pa_df[pa_df[result_col].isin(walks)].shape[0]
    
    # Use 'Old Result' to correctly identify all sacrifices (bunts and flies)
    num_sacrifices = pa_df[pa_df['Old Result'] == 'Sac'].shape[0]
    
    ab = pa - num_walks - num_sacrifices
    num_hits = pa_df[pa_df[result_col].isin(hits)].shape[0]
    num_doubles = pa_df[pa_df[result_col] == '2B'].shape[0]
    num_triples = pa_df[pa_df[result_col] == '3B'].shape[0]
    num_hr = pa_df[pa_df[result_col] == 'HR'].shape[0]
    num_singles = pa_df[pa_df[result_col] == '1B'].shape[0]
    if not use_old_results:
        num_singles += pa_df[pa_df[result_col] == 'BUNT 1B'].shape[0]

    num_strikeouts = pa_df[pa_df[result_col].isin(strikeouts)].shape[0]

    runs_scored = df['Run'].sum()
    rbi = df['RBI'].sum()

    # --- Neutral OBP/SLG Calculation (for OPS+) ---
    nOBP = (num_hits + num_walks) / pa if pa > 0 else 0
    nSLG = (num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0

    if 'Result at Neutral' in df.columns and not df['Result at Neutral'].isnull().all():
        if season == 'S3': # S3 uses old results format
            n_hits_def = {'1B', '2B', '3B', 'HR'}
            n_walks_def = {'BB', 'IBB', 'Auto BB'}
            n_pa_events_def = n_hits_def | n_walks_def | {'FO', 'PO', 'LGO', 'RGO', 'LO', 'DP', 'TP', 'Sac', 'Bunt'}
            
            n_pa_df = df[df['Result at Neutral'].isin(n_pa_events_def)]
            n_pa = len(n_pa_df)
            n_walks = n_pa_df[n_pa_df['Result at Neutral'].isin(n_walks_def)].shape[0]
            n_sacrifices = n_pa_df[n_pa_df['Result at Neutral'] == 'Sac'].shape[0]
            n_ab = n_pa - n_walks - n_sacrifices
            n_hits = n_pa_df[n_pa_df['Result at Neutral'].isin(n_hits_def)].shape[0]
            n_doubles = n_pa_df[n_pa_df['Result at Neutral'] == '2B'].shape[0]
            n_triples = n_pa_df[n_pa_df['Result at Neutral'] == '3B'].shape[0]
            n_hr = n_pa_df[n_pa_df['Result at Neutral'] == 'HR'].shape[0]
            n_singles = n_pa_df[n_pa_df['Result at Neutral'] == '1B'].shape[0]

            if n_ab > 0:
                nSLG = (n_singles + n_doubles * 2 + n_triples * 3 + n_hr * 4) / n_ab
            else:
                nSLG = 0
            if n_pa > 0:
                nOBP = (n_hits + n_walks) / n_pa
            else:
                nOBP = 0

        elif season not in ['S2', 'S3']: # S4+ uses new results format
            n_hits_def = {'1B', '2B', '3B', 'HR', 'BUNT 1B'}
            n_walks_def = {'BB', 'IBB', 'Auto BB', 'AUTO BB'}
            n_pa_events_def = n_hits_def | n_walks_def | {'K', 'Auto K', 'Bunt K', 'AUTO K', 'FO', 'PO', 'LGO', 'RGO', 'LO', 'BUNT DP', 'BUNT GO', 'BUNT Sac', 'Bunt Sac'}

            n_pa_df = df[df['Result at Neutral'].isin(n_pa_events_def)]
            n_pa = len(n_pa_df)
            n_walks = n_pa_df[n_pa_df['Result at Neutral'].isin(n_walks_def)].shape[0]
            # Use 'Old Result' for sacrifices as it is more reliable across versions
            n_sacrifices = df[df['Old Result'] == 'Sac'].shape[0]
            n_ab = n_pa - n_walks - n_sacrifices
            n_hits = n_pa_df[n_pa_df['Result at Neutral'].isin(n_hits_def)].shape[0]
            n_doubles = n_pa_df[n_pa_df['Result at Neutral'] == '2B'].shape[0]
            n_triples = n_pa_df[n_pa_df['Result at Neutral'] == '3B'].shape[0]
            n_hr = n_pa_df[n_pa_df['Result at Neutral'] == 'HR'].shape[0]
            n_singles = n_pa_df[n_pa_df['Result at Neutral'] == '1B'].shape[0] + n_pa_df[n_pa_df['Result at Neutral'] == 'BUNT 1B'].shape[0]

            if n_ab > 0:
                nSLG = (n_singles + n_doubles * 2 + n_triples * 3 + n_hr * 4) / n_ab
            else:
                nSLG = 0
            if n_pa > 0:
                nOBP = (n_hits + n_walks) / n_pa
            else:
                nOBP = 0

    return pd.Series({
        'G': games_played, 'PA': pa, 'AB': ab, 'H': num_hits, 'R': runs_scored, '2B': num_doubles, '3B': num_triples, 'HR': num_hr, 'RBI': rbi,
        'BB': num_walks, 'K': num_strikeouts, 'SB': num_sb, 'CS': num_cs,
        'AVG': num_hits / ab if ab > 0 else 0,
        'OBP': (num_hits + num_walks) / pa if pa > 0 else 0,
        'SLG': (num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0,
        'OPS': ((num_hits + num_walks) / pa if pa > 0 else 0) + ((num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0),
        'Avg Diff': avg_diff,
        'nOBP': nOBP,
        'nSLG': nSLG,
        'RE24': re24
    })

def calculate_pitching_stats(df, season=None):
    """Calculates pitching stats for a given dataframe and returns them as a pandas Series."""
    if df.empty: return None

    if season is None:
        season = df.name # Get season from group name
    use_old_results = season in ['S2', 'S3']

    if use_old_results:
        result_col = 'Old Result'
        hits_allowed = {'1B', '2B', '3B', 'HR'}
        walks_allowed = {'BB', 'IBB', 'Auto BB'}
        ibb_events = {'IBB'}
        strikeouts = {'K', 'Auto K'}
        hr_allowed = {'HR'}
        single_out_bip = {'FO', 'LGO', 'PO', 'RGO', 'Bunt', 'LO'} # 'Bunt' is an out
        caught_stealing = {'CS'}
        stolen_bases = {'SB'}
    else:
        result_col = 'Exact Result'
        hits_allowed = {'1B', '2B', '3B', 'HR', 'BUNT 1B'}
        walks_allowed = {'BB', 'IBB', 'Auto BB', 'AUTO BB'}
        ibb_events = {'IBB'}
        strikeouts = {'K', 'Auto K', 'Bunt K', 'AUTO K'}
        hr_allowed = {'HR'}
        single_out_bip = {'FO', 'LGO', 'PO', 'RGO', 'LO', 'BUNT GO', 'Bunt GO', 'BUNT Sac', 'Bunt Sac'}
        caught_stealing = {'CS 2B', 'CS 3B', 'CS Home'}
        stolen_bases = {'STEAL 2B', 'STEAL 3B', 'Steal 2B', 'Steal 3B'}

    # Filter for events that have a diff and calculate the average
    if use_old_results:
        pitching_pa_events = hits_allowed | walks_allowed | strikeouts | single_out_bip | {'DP', 'TP', 'Sac'}
        diff_events = pitching_pa_events | stolen_bases | caught_stealing
        diff_df = df[df[result_col].isin(diff_events)]
    else:
        # For new seasons, PA outcomes are split between Exact and Old results
        pa_events_exact = hits_allowed | walks_allowed | strikeouts | single_out_bip | {'BUNT DP'}
        diff_events_exact = pa_events_exact | stolen_bases | caught_stealing
        
        exact_df = df[df['Exact Result'].isin(diff_events_exact)]
        old_df = df[df['Old Result'].isin(['DP', 'TP'])]
        
        diff_df = pd.concat([exact_df, old_df]).drop_duplicates()

    numeric_diff = pd.to_numeric(diff_df['Diff'], errors='coerce')
    avg_diff = numeric_diff.mean()

    # Calculate Batters Faced (BF)
    if use_old_results:
        pitching_pa_events = hits_allowed | walks_allowed | strikeouts | single_out_bip | {'DP', 'TP', 'Sac'}
        bf_df = df[df[result_col].isin(pitching_pa_events)]
        num_bf = bf_df.shape[0]
    else:
        pa_events_exact = hits_allowed | walks_allowed | strikeouts | single_out_bip | {'BUNT DP'}
        exact_pa_df = df[df['Exact Result'].isin(pa_events_exact)]
        old_pa_df = df[df['Old Result'].isin(['DP', 'TP'])]
        bf_df = pd.concat([exact_pa_df, old_pa_df]).drop_duplicates()
        num_bf = bf_df.shape[0]

    re24 = bf_df['RE24'].sum() if 'RE24' in bf_df.columns else 0

    games_played = df['Session'].nunique()
    num_hits_allowed = df[df[result_col].isin(hits_allowed)].shape[0]
    num_walks_allowed = df[df[result_col].isin(walks_allowed)].shape[0]
    num_ibb = df[df[result_col].isin(ibb_events)].shape[0]
    num_strikeouts = df[df[result_col].isin(strikeouts)].shape[0]
    num_hr_allowed = df[df[result_col].isin(hr_allowed)].shape[0]

    # Use 'Old Result' for DPs and TPs as it's more reliable for them
    dp_outs = df[df['Old Result'] == 'DP'].shape[0] * 2
    tp_outs = df[df['Old Result'] == 'TP'].shape[0] * 3

    # For single outs, use the result_col but exclude plays already counted as DPs/TPs
    non_dp_tp_df = df[~df['Old Result'].isin(['DP', 'TP'])]
    k_outs = non_dp_tp_df[non_dp_tp_df[result_col].isin(strikeouts)].shape[0]
    other_single_outs = non_dp_tp_df[non_dp_tp_df[result_col].isin(single_out_bip)].shape[0]
    cs_outs = non_dp_tp_df[non_dp_tp_df[result_col].isin(caught_stealing)].shape[0]

    total_outs = dp_outs + tp_outs + k_outs + other_single_outs + cs_outs
    ip = total_outs / 3

    runs_allowed = df['Run'].sum()
    
    return pd.Series({
        'G': games_played, 'IP': ip, 'BF': num_bf, 'H': num_hits_allowed, 'R': runs_allowed, 'BB': num_walks_allowed, 'IBB': num_ibb, 'K': num_strikeouts, 'HR': num_hr_allowed,
        'ERA': (runs_allowed * 6) / ip if ip > 0 else 0,
        'WHIP': (num_walks_allowed + num_hits_allowed) / ip if ip > 0 else 0,
        'Avg Diff': avg_diff,
        'RE24': re24
    })

import os


def _get_simulated_runs_for_inning(inning_df):
    """Simulates an inning play-by-play based on rulebook logic to determine runs scored."""
    
    # Mapping from OBC code to a list representing [1B, 2B, 3B]
    obc_to_runners = {
        0: [0, 0, 0], 1: [1, 0, 0], 2: [0, 1, 0], 3: [0, 0, 1],
        4: [1, 1, 0], 5: [1, 0, 1], 6: [0, 1, 1], 7: [1, 1, 1]
    }

    sim_runs_on_play = []
    
    # Get initial state from the first play
    initial_obc = inning_df['OBC'].iloc[0]
    initial_outs = inning_df['Outs'].iloc[0]
    
    runners = obc_to_runners.get(initial_obc, [0, 0, 0])
    outs = initial_outs
    
    for _, play in inning_df.iterrows():
        # The state for this play is the one we've been tracking
        runs_this_play = 0
        
        # Determine which result column to use
        use_old_results = play['Season'] in ['S2', 'S3']
        result = play['Old Result'] if use_old_results else play['Exact Result']

        # Two-out hit rule modifier
        advancement_bonus = 1 if outs == 2 and result in ['1B', '2B', '3B'] else 0

        # --- SIMULATE PLAY OUTCOME ---
        if result == 'HR':
            runs_this_play = sum(runners) + 1
            runners = [0, 0, 0]
        elif result == '3B':
            runs_this_play = sum(runners)
            runners = [0, 0, 1]
        elif result == '2B':
            if runners[2]: runs_this_play += 1 # Runner from 3rd scores
            if runners[1]: runs_this_play += 1 # Runner from 2nd scores
            runners = [0, 1, 1] if runners[0] else [0, 1, 0]
        elif result in ['1B', 'BUNT 1B']:
            if runners[2]: runs_this_play += 1
            if runners[1]: runners = [runners[0], 0, 1] # R2 to 3B
            if runners[0]: runners = [0, 1, runners[2] or runners[1]] # R1 to 2B, handle if R2 was there
            runners[0] = 1 # Batter to 1B
            # Apply 2-out bonus
            if advancement_bonus > 0:
                if runners[2]: runs_this_play += 1 # R3 scores (already counted)
                if runners[1]: runs_this_play += 1; runners[1] = 0 # R2 scores
                if runners[0] and runners[1]==0: runners[1]=1; runners[0]=0 # R1 to 2B

        elif result in ['BB', 'IBB', 'Auto BB', 'AUTO BB']:
            if runners[0] and runners[1] and runners[2]: runs_this_play += 1
            if runners[0] and runners[1]: runners[2] = 1
            if runners[0]: runners[1] = 1
            runners[0] = 1
        elif result == 'FO':
            outs += 1
            if outs <= 2 and runners[2]: # Sac Fly
                runs_this_play += 1
                runners[2] = 0
        elif result in ['K', 'Auto K', 'Bunt K', 'AUTO K', 'PO']:
            outs += 1
        elif result in ['LGO', 'RGO', 'BUNT GO']:
            outs += 1
            if outs <= 2 and runners[0]: # DP
                outs += 1
                runners[0] = 0
            # Runner advancement on non-DP groundouts
            if outs <= 2:
                if runners[2]: runs_this_play += 1; runners[2] = 0
                if runners[1]: runners[2] = 1; runners[1] = 0
        elif result == 'DP':
            outs += 2
        elif result == 'TP':
            outs = 3
            runs_this_play = 0 # No runs on TP
            runners = [0,0,0]

        sim_runs_on_play.append(runs_this_play)

        # Stop if inning is over
        if outs >= 3:
            # Fill remaining plays in this inning with 0 runs if any
            sim_runs_on_play.extend([0] * (len(inning_df) - len(sim_runs_on_play)))
            break
            
    return pd.Series(sim_runs_on_play, index=inning_df.index)

def get_run_expectancy_matrix(season, season_df, is_most_recent_season=False):
    """Calculates or loads a run expectancy matrix for a given season using a simulation engine."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data', 'cache')
    cache_path = os.path.join(data_dir, f're_matrix_{season}.csv')

    # Do not use cache for the most recent season, as it may be in progress.
    if os.path.exists(cache_path) and not is_most_recent_season:
        re_df = pd.read_csv(cache_path)
        re_matrix = {}
        for _, row in re_df.iterrows():
            re_matrix[(int(row['OBC']), int(row['Outs']))] = row['RunExpectancy']
        return re_matrix

    # Ensure key columns are numeric
    for col in ['OBC', 'Outs', 'Run']:
        season_df[col] = pd.to_numeric(season_df[col], errors='coerce').fillna(0).astype(int)

    # Get simulated runs for all innings
    simulated_runs = season_df.groupby('Inning ID').apply(_get_simulated_runs_for_inning, include_groups=False)
    season_df['SimulatedRuns'] = simulated_runs.reset_index(level=0, drop=True)

    all_plays = []
    for _, inning_df in season_df.groupby('Inning ID'):
        total_inning_runs = inning_df['SimulatedRuns'].sum()
        runs_scored_previously = inning_df['SimulatedRuns'].cumsum().shift(1).fillna(0)
        runs_after = total_inning_runs - runs_scored_previously

        temp_df = inning_df[['OBC', 'Outs']].copy()
        temp_df['RunsAfter'] = runs_after
        all_plays.append(temp_df)

    if not all_plays:
        return {}

    all_plays_df = pd.concat(all_plays)
    re_matrix_df = all_plays_df.groupby(['OBC', 'Outs'])['RunsAfter'].mean().reset_index()
    re_matrix_df.rename(columns={'RunsAfter': 'RunExpectancy'}, inplace=True)

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    re_matrix_df.to_csv(cache_path, index=False)

    re_matrix = {}
    for _, row in re_matrix_df.iterrows():
        re_matrix[(row['OBC'], row['Outs'])] = row['RunExpectancy']
        
    return re_matrix



def _simulate_neutral_inning(inning_df, re_matrix):
    """Simulates a single inning based on 'Result at Neutral' to find neutral runs and outs."""
    obc_to_runners = {
        0: [0, 0, 0], 1: [1, 0, 0], 2: [0, 1, 0], 3: [0, 0, 1],
        4: [1, 1, 0], 5: [1, 0, 1], 6: [0, 1, 1], 7: [1, 1, 1]
    }
    runners_to_obc = {tuple(v): k for k, v in obc_to_runners.items()}

    # Get initial state from the first play of the actual inning
    runners = obc_to_runners.get(inning_df['OBC'].iloc[0], [0, 0, 0])
    outs = inning_df['Outs'].iloc[0]
    total_n_runs = 0

    for _, play in inning_df.iterrows():
        if outs >= 3:
            break

        runs_on_play = 0
        result = play['Result at Neutral']
        
        if pd.isna(result):
            result = play['Old Result']

        # --- SIMULATE PLAY OUTCOME ---
        if result == 'HR':
            runs_on_play = sum(runners) + 1
            runners = [0, 0, 0]
        elif result == '3B':
            runs_on_play = sum(runners)
            runners = [0, 0, 1]
        elif result == '2B':
            runs_on_play += runners[2] + runners[1]
            runners = [0, 1, 1] if runners[0] else [0, 1, 0]
        elif result in ['1B', 'BUNT 1B']:
            if runners[2]: runs_on_play += 1
            new_runners = [0,0,0]
            if runners[1]: new_runners[2] = 1
            if runners[0]: new_runners[1] = 1
            new_runners[0] = 1
            runners = new_runners
        elif result in ['BB', 'IBB', 'Auto BB', 'AUTO BB']:
            if runners[0] and runners[1] and runners[2]: runs_on_play += 1
            if runners[0] and runners[1]: runners[2] = 1
            if runners[0]: runners[1] = 1
            runners[0] = 1
        elif result == 'FO':
            outs += 1
            if outs < 3 and runners[2]:
                runs_on_play += 1
                runners[2] = 0
        elif result in ['K', 'Auto K', 'Bunt K', 'AUTO K', 'PO']:
            outs += 1
        elif result in ['LGO', 'RGO', 'BUNT GO', 'Sac']:
            if outs < 2 and runners[0]:
                outs += 2
                runners[0] = 0
            else:
                outs += 1
            if outs < 3:
                if runners[2]: runs_on_play += 1; runners[2] = 0
                if runners[1]: runners[2] = 1; runners[1] = 0
        elif result == 'DP':
            outs += 2
        elif result == 'TP':
            outs = 3

        total_n_runs += runs_on_play

    if outs < 3:
        final_obc = runners_to_obc.get(tuple(runners), 0)
        final_state = (final_obc, outs)
        total_n_runs += re_matrix.get(final_state, 0)

    return pd.Series({'nRuns': total_n_runs, 'nOuts': outs if outs <= 3 else 3})

def calculate_neutral_pitching_stats(df, re_matrix):
    """Calculates total neutral runs and outs for a pitcher's season."""
    if df.empty or not re_matrix:
        return pd.Series({'nRuns': 0, 'nOuts': 0})
    
    # This will be slow, but it's the only way to do it correctly row-by-row
    inning_stats = df.groupby('Inning ID').apply(lambda x: _simulate_neutral_inning(x, re_matrix), include_groups=False)
    return inning_stats.sum()

# --- New Scouting Report Function ---
def _display_pitch_histogram(pitch_series, bin_size, title):
    """Helper to calculate and display a pitch histogram."""
    print(f"\n--- {title} (Bin Size: {bin_size}) ---")
    
    # Drop non-numeric pitches before processing and convert to int
    pitch_series = pitch_series.dropna().astype(int)

    if pitch_series.empty:
        print("No pitches to display.")
        return

    # Handle 1000 -> 0 for binning
    pitches = pitch_series.apply(lambda p: 0 if p == 1000 else p)
    bin_ids = pitches // bin_size
    histogram_data = bin_ids.value_counts()

    # Create all possible bin IDs to show empty bins
    max_pitch = 1000
    # Ensure we handle cases where bin_size isn't a perfect divisor
    num_bins = (max_pitch + bin_size - 1) // bin_size
    all_bin_ids = range(num_bins)

    # Reindex the histogram data to include all possible bins, filling missing ones with 0
    histogram_data = histogram_data.reindex(all_bin_ids, fill_value=0)
    histogram_data.sort_index(inplace=True)

    if histogram_data.sum() > 0:
        max_count = histogram_data.max()
        scale = 50 / max_count if max_count > 0 else 0
        
        if scale > 0:
            # Represent how many pitches each '#' stands for
            print(f"Each '#' represents up to {1/scale:.1f} pitches.")

        for bin_id, count in histogram_data.items():
            lower_bound = bin_id * bin_size
            upper_bound = lower_bound + bin_size - 1
            if lower_bound == 0: lower_bound = 1
            label = f"{lower_bound}-{upper_bound}"
            bar = '#' * int(count * scale)
            print(f"{label.rjust(9)} | {bar} ({count})")
    else:
        print("No pitches available to generate a histogram.")

def generate_scouting_report(player_id, combined_df, player_id_map, bin_size=100):
    if player_id not in player_id_map:
        print("Player not found.")
        return

    player_name = player_id_map[player_id]
    print(f"\nScouting Report for Pitcher: {player_name} (ID: {player_id})")
    pitcher_df = combined_df[combined_df['Pitcher ID'] == player_id].copy()

    if pitcher_df.empty:
        print("No pitching data found for this player.")
        return
        
    # Ensure 'Pitch' column is numeric, coercing invalid values to NaN
    pitcher_df['Pitch'] = pd.to_numeric(pitcher_df['Pitch'], errors='coerce')
    
    # Sort dataframe to easily find first pitches
    pitcher_df.sort_values(by=['Season', 'Session', 'Inning'], inplace=True)

    print("\n--- Top 5 Most Common Pitches ---")
    # Drop NaN values for this calculation and ensure index is integer for display
    valid_pitches = pitcher_df['Pitch'].dropna()
    top_5_pitches = valid_pitches.value_counts().nlargest(5)
    if not top_5_pitches.empty:
        top_5_pitches.index = top_5_pitches.index.astype(int)
    print(top_5_pitches.to_string())

    # --- Histograms ---
    _display_pitch_histogram(pitcher_df['Pitch'], bin_size, "Overall Pitch Distribution")
    
    # First pitch of game
    first_pitches_game = pitcher_df.groupby(['Season', 'Game ID']).first()['Pitch']
    _display_pitch_histogram(first_pitches_game, bin_size, "First Pitch of Game Distribution")

    # First pitch of inning
    first_pitches_inning = pitcher_df.groupby(['Season', 'Game ID', 'Inning']).first()['Pitch']
    _display_pitch_histogram(first_pitches_inning, bin_size, "First Pitch of Inning Distribution")

    # Pitches with runners in scoring position (RISP)
    risp_df = pitcher_df[pd.to_numeric(pitcher_df['OBC'], errors='coerce').fillna(0) > 1]
    _display_pitch_histogram(risp_df['Pitch'], bin_size, "Pitches with RISP Distribution")

    # Pitches after a pitch in the same "hundred" as the most recent pitch
    if len(pitcher_df) > 1:
        last_pitch = pitcher_df['Pitch'].iloc[-1]
        
        # Determine the bin of the last pitch
        last_pitch_for_binning = 0 if last_pitch == 1000 else last_pitch
        bin_id = last_pitch_for_binning // bin_size
        
        # Get all pitches as a numpy array for efficient processing
        all_pitches = pitcher_df['Pitch'].to_numpy()
        
        # Create a version for binning (1000 -> 0)
        all_pitches_for_binning = all_pitches.copy()
        all_pitches_for_binning[all_pitches_for_binning == 1000] = 0
        
        # Find indices of pitches that are in the same bin as the last pitch
        is_in_block = (all_pitches_for_binning // bin_size) == bin_id
        
        # Get the pitches that immediately follow those pitches
        pitches_after = pd.Series(all_pitches[1:][is_in_block[:-1]])
        
        # Format the title for the histogram
        lower_bound = bin_id * bin_size
        upper_bound = lower_bound + bin_size - 1
        if lower_bound == 0: lower_bound = 1
        title = f"Pitches After a {lower_bound}-{upper_bound} Pitch"
        
        _display_pitch_histogram(pitches_after, bin_size, title)

    # --- Pitch Tendencies ---
    pitches = pitcher_df['Pitch'].to_numpy()
    repeat_count = (pitches[:-1] == pitches[1:]).sum()
    total_opportunities = len(pitches) - 1
    repeat_percentage = (repeat_count / total_opportunities) * 100 if total_opportunities > 0 else 0
    print("\n--- Pitch Tendencies ---")
    print(f"Uses same number twice in a row: {repeat_percentage:.2f}%")

    # Check for triple-ups (same pitch 3 times in a row)
    if len(pitches) > 2:
        has_tripled_up = ((pitches[:-2] == pitches[1:-1]) & (pitches[1:-1] == pitches[2:])).any()
    else:
        has_tripled_up = False
    print(f"Has ever thrown same number three times in a row: {'Yes' if has_tripled_up else 'No'}")

    # Calculate tendencies based on previous batter's actions
    if not pitcher_df.empty:
        # Ensure columns are numeric for comparison, coercing errors
        swing = pd.to_numeric(pitcher_df['Swing'], errors='coerce')
        diff = pd.to_numeric(pitcher_df['Diff'], errors='coerce')
        
        # Get previous event's values using shift()
        prev_swing = swing.shift(1)
        prev_diff = diff.shift(1)
        
        # Calculate match rates using the mean of the boolean comparison
        swing_match_rate = (pitcher_df['Pitch'] == prev_swing).mean() * 100
        diff_match_rate = (pitcher_df['Pitch'] == prev_diff).mean() * 100
        
        print(f"Uses previous swing as number: {swing_match_rate:.2f}%")
        print(f"Uses previous diff as number: {diff_match_rate:.2f}%")

    meme_numbers = {69, 420, 666, 327, 880}
    meme_count = pitcher_df['Pitch'].isin(meme_numbers).sum()
    total_pitches = len(pitcher_df)
    meme_percentage = (meme_count / total_pitches) * 100 if total_pitches > 0 else 0
    print(f"Uses a meme number (69, 420, etc.): {meme_percentage:.2f}%")

# --- Leaderboard Functions ---
def display_leaderboard(series, title, player_id_map, stat_name=None):
    if series.empty:
        return
    print(f"\n--- {title} ---")
    df = series.reset_index(name='Value')
    player_id_col = df.columns[0]
    df['Player'] = df[player_id_col].map(player_id_map)
    # Reorder to put Player first, and handle cases where player name is not found
    df = df[['Player', player_id_col, 'Value']]
    df['Player'] = df['Player'].fillna(df[player_id_col].astype(str))
    df = df[['Player', 'Value']]
    df.index = df.index + 1
    
    # Apply special formatting for IP before using the generic formatter
    if stat_name == 'IP':
        df['Value'] = df['Value'].apply(format_ip)
        # Now print and return, as formatters can't handle the IP string
        print(df.to_string())
        return

    # Generic formatters for other stats
    formatters = {}
    if stat_name in ['AVG', 'OBP', 'SLG', 'OPS', 'W-L%']:
        formatters['Value'] = lambda x: f"{x:.3f}".replace('0.', '.')
    elif stat_name in ['ERA', 'WHIP', 'Avg Diff', 'FIP', 'RE24', 'WAR']:
        formatters['Value'] = '{:.2f}'.format
    elif stat_name == 'OPS+':
        formatters['Value'] = '{:.0f}'.format
    else: # Counting stats
        formatters['Value'] = '{:.0f}'.format

    print(df.to_string(formatters=formatters))

def process_leaderboard(stat, combined_df, all_hitting_stats, all_pitching_stats, player_id_map, season_games_map):
    print(f"\n--- Leaderboards for: {stat.upper()} ---")

    # Define stat categories
    hitting_rate_stats = ['AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'Avg Diff', 'WAR']
    hitting_counting_stats = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS', 'RE24']
    pitching_rate_stats = ['ERA', 'WHIP', 'Avg Diff', 'ERA+', 'W-L%', 'FIP', 'WAR']
    pitching_counting_stats = ['G', 'GS', 'GF', 'CG', 'SHO', 'BF', 'IP', 'H', 'R', 'BB', 'IBB', 'K', 'HR', 'W', 'L', 'SV', 'HLD', 'RE24']
    
    lower_is_better_pitching = ['ERA', 'WHIP', 'FIP', 'RE24']
    lower_is_better_hitting = ['Avg Diff']

    stat_upper = stat.upper()

    # --- Hitting Leaderboard ---
    if stat_upper in hitting_rate_stats or stat_upper in hitting_counting_stats:
        print("\n--- Hitting ---")
        is_rate = stat_upper in hitting_rate_stats
        lower_is_better = stat_upper in lower_is_better_hitting

        # Seasonal
        seasons = all_hitting_stats['Season'].unique()
        sorted_seasons = sorted(seasons, key=lambda s: int(s.replace('S', '')))
        for season in sorted_seasons:
            season_df = all_hitting_stats[all_hitting_stats['Season'] == season]
            if is_rate:
                games = season_games_map.get(season, 0)
                min_pa = games * 2
                qualified_season = season_df[season_df['PA'] >= min_pa]
                title = f"Season {season.replace('S','')} (min. {min_pa} PA)"
            else:
                qualified_season = season_df
                title = f"Season {season.replace('S','')}"
            
            leaderboard_series = qualified_season.set_index('Hitter ID')[stat_upper]
            if leaderboard_series.dtype == 'object':
                leaderboard_series = pd.to_numeric(leaderboard_series, errors='coerce')

            season_top_10 = leaderboard_series.nsmallest(10) if lower_is_better else leaderboard_series.nlargest(10)
            display_leaderboard(season_top_10, title, player_id_map, stat_name=stat_upper)

        # All-Time
        career_hitting_stats = all_hitting_stats.groupby('Hitter ID').sum(numeric_only=True)
        
        if is_rate:
            career_hitting_stats['AVG'] = career_hitting_stats['H'] / career_hitting_stats['AB']
            career_hitting_stats['OBP'] = (career_hitting_stats['H'] + career_hitting_stats['BB']) / career_hitting_stats['PA']
            career_hitting_stats['SLG'] = (career_hitting_stats['H'] - career_hitting_stats['2B'] - career_hitting_stats['3B'] - career_hitting_stats['HR'] + career_hitting_stats['2B']*2 + career_hitting_stats['3B']*3 + career_hitting_stats['HR']*4) / career_hitting_stats['AB']
            career_hitting_stats['OPS'] = career_hitting_stats['OBP'] + career_hitting_stats['SLG']
            
            if 'OPS+' in career_hitting_stats.columns:
                ops_plus_df = all_hitting_stats.copy()
                ops_plus_df = ops_plus_df[ops_plus_df['PA'] > 0].dropna(subset=['OPS+', 'PA'])
                ops_plus_df['OPS+'] = pd.to_numeric(ops_plus_df['OPS+'], errors='coerce')
                ops_plus_df['WeightedOPS+'] = ops_plus_df['OPS+'] * ops_plus_df['PA']
                career_ops_plus_agg = ops_plus_df.groupby('Hitter ID').sum(numeric_only=True)
                valid_career_pa = career_ops_plus_agg[career_ops_plus_agg['PA'] > 0]
                career_ops_plus_agg['OPS+'] = valid_career_pa['WeightedOPS+'] / valid_career_pa['PA']
                career_hitting_stats.loc[:, 'OPS+'] = career_ops_plus_agg['OPS+']

            if stat_upper == 'Avg Diff':
                career_avg_diff = combined_df.groupby('Hitter ID')['Diff'].apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
                career_hitting_stats['Avg Diff'] = career_avg_diff

            career_hitting_stats = career_hitting_stats.fillna(0)
            qualified = career_hitting_stats[career_hitting_stats['PA'] >= 100]
            title = "All-Time (min. 100 PA)"
        else:
            qualified = career_hitting_stats
            title = "All-Time"
        
        leaderboard_series = qualified[stat_upper]
        if leaderboard_series.dtype == 'object':
            leaderboard_series = pd.to_numeric(leaderboard_series, errors='coerce')

        all_time_top_10 = leaderboard_series.nsmallest(10) if lower_is_better else leaderboard_series.nlargest(10)
        display_leaderboard(all_time_top_10, title, player_id_map, stat_name=stat_upper)

    # --- Pitching Leaderboard ---
    if stat_upper in pitching_rate_stats or stat_upper in pitching_counting_stats:
        print("\n--- Pitching ---")
        is_rate = stat_upper in pitching_rate_stats
        lower_is_better = stat_upper in lower_is_better_pitching

        # Seasonal
        seasons = all_pitching_stats['Season'].unique()
        sorted_seasons = sorted(seasons, key=lambda s: int(s.replace('S', '')))
        for season in sorted_seasons:
            season_df = all_pitching_stats[all_pitching_stats['Season'] == season].copy()
            if 'W' in season_df.columns and 'L' in season_df.columns:
                season_df['W-L%'] = season_df['W'] / (season_df['W'] + season_df['L'])
            
            season_df = season_df.fillna(0).replace([float('inf'), float('-inf')], 0)

            if is_rate:
                if stat_upper == 'W-L%':
                    min_decisions = 3
                    qualified_season = season_df[(season_df['W'] + season_df['L']) >= min_decisions]
                    title = f"Season {season.replace('S','')} (min. {min_decisions} decisions)"
                else:
                    games = season_games_map.get(season, 0)
                    min_ip = games * 1
                    qualified_season = season_df[season_df['IP'] >= min_ip]
                    title = f"Season {season.replace('S','')} (min. {min_ip} IP)"
            else:
                qualified_season = season_df
                title = f"Season {season.replace('S','')}"
            
            leaderboard_series = qualified_season.set_index('Pitcher ID')[stat_upper]
            season_top_10 = leaderboard_series.nsmallest(10) if lower_is_better else leaderboard_series.nlargest(10)
            display_leaderboard(season_top_10, title, player_id_map, stat_name=stat_upper)

        # All-Time
        career_pitching_stats = all_pitching_stats.groupby('Pitcher ID').sum(numeric_only=True)

        if is_rate:
            # Recalculate all career rate stats
            career_pitching_stats['ERA'] = (career_pitching_stats['R'] * 6) / career_pitching_stats['IP']
            career_pitching_stats['WHIP'] = (career_pitching_stats['BB'] + career_pitching_stats['H']) / career_pitching_stats['IP']
            career_pitching_stats['W-L%'] = career_pitching_stats['W'] / (career_pitching_stats['W'] + career_pitching_stats['L'])

            if 'FIP' in career_pitching_stats.columns:
                fip_df = all_pitching_stats[all_pitching_stats['IP'] > 0].copy()
                fip_df['WeightedFIP'] = fip_df['FIP'] * fip_df['IP']
                career_fip_agg = fip_df.groupby('Pitcher ID').sum(numeric_only=True)
                if 'WeightedFIP' in career_fip_agg.columns and 'IP' in career_fip_agg.columns:
                    valid_career_ip = career_fip_agg[career_fip_agg['IP'] > 0]
                    career_pitching_stats['FIP'] = valid_career_ip['WeightedFIP'] / valid_career_ip['IP']

            if 'ERA+' in career_pitching_stats.columns:
                era_plus_df = all_pitching_stats[all_pitching_stats['nIP'] > 0].copy()
                era_plus_df['WeightedERA+'] = era_plus_df['ERA+'] * era_plus_df['nIP']
                career_era_plus_agg = era_plus_df.groupby('Pitcher ID').sum(numeric_only=True)
                if 'WeightedERA+' in career_era_plus_agg.columns and 'nIP' in career_era_plus_agg.columns:
                    valid_career_nip = career_era_plus_agg[career_era_plus_agg['nIP'] > 0]
                    career_pitching_stats['ERA+'] = valid_career_nip['WeightedERA+'] / valid_career_nip['nIP']

            if stat_upper == 'Avg Diff':
                career_avg_diff = combined_df.groupby('Pitcher ID')['Diff'].apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
                career_pitching_stats['Avg Diff'] = career_avg_diff

            career_pitching_stats = career_pitching_stats.fillna(0).replace([float('inf'), float('-inf')], 0)
            
            if stat_upper == 'W-L%':
                min_decisions = 10
                qualified = career_pitching_stats[(career_pitching_stats['W'] + career_pitching_stats['L']) >= min_decisions]
                title = f"All-Time (min. {min_decisions} decisions)"
            else:
                qualified = career_pitching_stats[career_pitching_stats['IP'] >= 50]
                title = "All-Time (min. 50 IP)"
        else:
            qualified = career_pitching_stats
            title = "All-Time"

        all_time_top_10 = qualified[stat_upper].nsmallest(10) if lower_is_better else qualified[stat_upper].nlargest(10)
        display_leaderboard(all_time_top_10, title, player_id_map, stat_name=stat_upper)

    # --- Fallback to event search ---
    if (stat_upper not in hitting_rate_stats + hitting_counting_stats) and \
       (stat_upper not in pitching_rate_stats + pitching_counting_stats):
        print("\nNote: This is not a calculated stat. Searching for event occurrences...")
        old_seasons_df = combined_df[combined_df['Season'].isin(['S2', 'S3'])]
        new_seasons_df = combined_df[~combined_df['Season'].isin(['S2', 'S3'])]

        old_events = old_seasons_df[old_seasons_df['Old Result'].str.contains(stat, case=False, na=False)]
        new_events = new_seasons_df[new_seasons_df['Exact Result'].str.contains(stat, case=False, na=False)]
        all_events = pd.concat([old_events, new_events])

        if not all_events.empty:
            seasons = all_events['Season'].unique()
            sorted_seasons = sorted(seasons, key=lambda s: int(s.replace('S', '')))
            
            # Hitting
            print("\n--- Hitting (Most Events) ---")
            for season in sorted_seasons:
                season_events = all_events[all_events['Season'] == season]
                season_hitters = season_events.groupby('Hitter ID').size().nlargest(10)
                display_leaderboard(season_hitters, f"Season {season.replace('S','')}", player_id_map)
            all_time_hitters = all_events.groupby('Hitter ID').size().nlargest(10)
            display_leaderboard(all_time_hitters, "All-Time", player_id_map)

            # Pitching
            print("\n--- Pitching (Most Events Allowed/Induced) ---")
            for season in sorted_seasons:
                season_events = all_events[all_events['Season'] == season]
                season_pitchers = season_events.groupby('Pitcher ID').size().nlargest(10)
                display_leaderboard(season_pitchers, f"Season {season.replace('S','')}", player_id_map)
            all_time_pitchers = all_events.groupby('Pitcher ID').size().nlargest(10)
            display_leaderboard(all_time_pitchers, "All-Time", player_id_map)
        else:
            print(f"\nNo events found matching '{stat}'.")

# --- Player Stats Display Functions ---
def display_stats_table(stats_df, is_pitching=False):
    int_cols = ['G', 'PA', 'AB', 'H', 'R', 'RBI', '2B', '3B', 'HR', 'BB', 'IBB', 'K', 'SB', 'CS', 'W', 'L', 'SV', 'HLD', 'GS', 'BF', 'GF', 'CG', 'SHO']
    # The 'R' column is used for both hitting and pitching, so we don't add it here again.
    if 'RBI' not in int_cols:
        int_cols.append('RBI')

    for col in int_cols:
        if col in stats_df.columns:
            stats_df[col] = stats_df[col].fillna(0).astype(int)
    
    if is_pitching:
        col_order = ['Team', 'G', 'GS', 'GF', 'CG', 'SHO', 'W', 'L', 'W-L%', 'SV', 'HLD', 'IP', 'BF', 'H', 'R', 'BB', 'IBB', 'K', 'HR', 'ERA', 'FIP', 'WHIP', 'ERA+', 'RE24', 'WAR', 'Avg Diff']
        if 'IP' in stats_df.columns: stats_df['IP'] = stats_df['IP'].apply(format_ip)
        formatters = {
            'ERA': '{:.2f}'.format, 'FIP': '{:.2f}'.format, 'WHIP': '{:.2f}'.format, 'Avg Diff': '{:.2f}'.format, 'RE24': '{:.2f}'.format, 'WAR': '{:.2f}'.format,
            'W-L%': lambda x: f"{x:.3f}".replace('0.', '.')
        }
    else:
        col_order = ['Team', 'G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS', 'AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'RE24', 'WAR', 'Avg Diff']
        formatters = {
            'AVG': lambda x: f"{x:.3f}".replace('0.', '.'), 'OBP': lambda x: f"{x:.3f}".replace('0.', '.'),
            'SLG': lambda x: f"{x:.3f}".replace('0.', '.'), 'OPS': lambda x: f"{x:.3f}".replace('0.', '.'),
            'Avg Diff': '{:.2f}'.format, 'RE24': '{:.2f}'.format, 'WAR': '{:.2f}'.format
        }
    
    # Use a copy to avoid SettingWithCopyWarning
    stats_df_copy = stats_df.copy()

    # Manually format OPS+ to handle NA values correctly before printing
    if 'OPS+' in stats_df_copy.columns:
        stats_df_copy['OPS+'] = stats_df_copy['OPS+'].apply(lambda x: '' if pd.isna(x) else f'{x:.0f}')

    if 'ERA+' in stats_df_copy.columns:
        stats_df_copy['ERA+'] = stats_df_copy['ERA+'].apply(lambda x: '' if pd.isna(x) else f'{x:.0f}')

    if 'Team' not in stats_df_copy:
        stats_df_copy['Team'] = ''
    else:
        # Ensure career row doesn't show aggregated team list and fill NaNs
        stats_df_copy['Team'] = stats_df_copy['Team'].fillna('')
        if 'Career' in stats_df_copy.index:
            stats_df_copy.loc['Career', 'Team'] = ''

    stats_df_copy = stats_df_copy.reindex(columns=col_order)
    print(stats_df_copy.to_string(formatters=formatters, na_rep=''))

def display_stat_block(df, is_pitching, title, precalculated_stats):
    """Displays a block of pre-calculated stats."""
    if precalculated_stats.empty:
        return

    print(title)
    season_stats = precalculated_stats.copy()

    # The precalculated stats don't have the Team column, so we calculate it from the raw df and merge it in.
    team_col = 'Pitcher Team' if is_pitching else 'Batter Team'
    if not df.empty and team_col in df.columns:
        teams_df = df.dropna(subset=[team_col]).groupby('Season')[team_col].unique().apply(lambda teams: '/'.join(sorted(teams))).rename('Team').reset_index()
        season_stats = season_stats.merge(teams_df, on='Season', how='left')

    # Set index to integer season for sorting and display
    if 'Season' in season_stats.columns:
        season_stats.rename(columns={'Season': 'Season_str'}, inplace=True)
        season_stats['Season'] = season_stats['Season_str'].str.replace('S', '').astype(int)
        season_stats.set_index('Season', inplace=True)
        season_stats.sort_index(inplace=True)

    # Calculate seasonal W-L% for pitching
    if is_pitching:
        if 'W' in season_stats.columns and 'L' in season_stats.columns:
            season_stats['W-L%'] = season_stats['W'] / (season_stats['W'] + season_stats['L'])
            season_stats['W-L%'] = season_stats['W-L%'].fillna(0)

    # --- Career Stat Calculation ---
    career_stats = season_stats.sum(numeric_only=True)
    
    if is_pitching:
        if career_stats['IP'] > 0:
            career_stats['ERA'] = (career_stats['R'] * 6) / career_stats['IP']
            career_stats['WHIP'] = (career_stats['BB'] + career_stats['H']) / career_stats['IP']
            career_stats['FIP'] = (season_stats['FIP'] * season_stats['IP']).sum() / season_stats['IP'].sum()
        else:
            career_stats['ERA'], career_stats['WHIP'], career_stats['FIP'] = 0, 0, 0
        if (career_stats.get('W', 0) + career_stats.get('L', 0)) > 0:
            career_stats['W-L%'] = career_stats['W'] / (career_stats['W'] + career_stats['L'])
        else:
            career_stats['W-L%'] = 0
        if season_stats['nIP'].sum() > 0:
             career_stats['ERA+'] = (season_stats['ERA+'] * season_stats['nIP']).sum() / season_stats['nIP'].sum()
        if not df.empty: career_stats['Avg Diff'] = pd.to_numeric(df['Diff'], errors='coerce').mean()

    else: # Hitting
        if career_stats['AB'] > 0:
            career_stats['AVG'] = career_stats['H'] / career_stats['AB']
            career_stats['SLG'] = (career_stats['H'] - career_stats['2B'] - career_stats['3B'] - career_stats['HR'] + career_stats['2B']*2 + career_stats['3B']*3 + career_stats['HR']*4) / career_stats['AB']
        else:
            career_stats['AVG'], career_stats['SLG'] = 0, 0
        if career_stats['PA'] > 0:
            career_stats['OBP'] = (career_stats['H'] + career_stats['BB']) / career_stats['PA']
            if season_stats['PA'].sum() > 0:
                career_stats['OPS+'] = (season_stats['OPS+'] * season_stats['PA']).sum() / season_stats['PA'].sum()
        else:
            career_stats['OBP'] = 0
        career_stats['OPS'] = career_stats['OBP'] + career_stats['SLG']
        if not df.empty: career_stats['Avg Diff'] = pd.to_numeric(df['Diff'], errors='coerce').mean()

    career_stats_df = pd.DataFrame(career_stats).T
    career_stats_df.index = ['Career']
    
    # Combine and display
    display_df = pd.concat([season_stats, career_stats_df])
    display_stats_table(display_df, is_pitching=is_pitching)
def process_player_stats(player_id, combined_df, player_id_map, all_hitting_stats, all_pitching_stats):
    if player_id not in player_id_map:
        print("Player not found.")
        return

    player_name = player_id_map[player_id]
    print(f"\nStats for: {player_name} (ID: {player_id})")

    # Filter raw data for the player to get team info and other raw details
    hitter_df = combined_df[combined_df['Hitter ID'] == player_id]
    pitcher_df = combined_df[combined_df['Pitcher ID'] == player_id]

    # Filter pre-calculated stats for the player
    player_hitting_stats = all_hitting_stats[all_hitting_stats['Hitter ID'] == player_id]
    player_pitching_stats = all_pitching_stats[all_pitching_stats['Pitcher ID'] == player_id]

    if player_hitting_stats.empty and player_pitching_stats.empty:
        print("No stats found for this player.")
        return

    # Display all stat blocks
    display_stat_block(hitter_df, is_pitching=False, title="\n--- Hitting Stats ---", precalculated_stats=player_hitting_stats)
    display_stat_block(pitcher_df, is_pitching=True, title="\n--- Pitching Stats ---", precalculated_stats=player_pitching_stats)

def calculate_game_achievements(df):
    """Calculates game-level pitching achievements like CG, SHO, GF, and GS."""
    achievements = []

    # Group by each individual game
    for (season, game_id), game_df in df.groupby(['Season', 'Game ID']):
        
        # Find the two teams in the game from the data
        teams_in_game = game_df['Batter Team'].unique()
        if len(teams_in_game) != 2:
            continue # Skip if it's not a standard 2-team game

        team_A, team_B = teams_in_game[0], teams_in_game[1]

        # Calculate total runs for each team
        runs_A = game_df[game_df['Batter Team'] == team_A]['Run'].sum()
        runs_B = game_df[game_df['Batter Team'] == team_B]['Run'].sum()

        # Get all unique pitchers for each team
        pitchers_A = game_df[game_df['Pitcher Team'] == team_A]['Pitcher ID'].unique().tolist()
        pitchers_B = game_df[game_df['Pitcher Team'] == team_B]['Pitcher ID'].unique().tolist()

        # --- Team A Pitchers ---
        if pitchers_A:
            # Game Started: First pitcher to appear for the team
            starter_id_A = game_df[game_df['Pitcher Team'] == team_A]['Pitcher ID'].iloc[0]
            achievements.append({'Season': season, 'Pitcher ID': starter_id_A, 'Stat': 'GS'})

            # Game Finished: Last pitcher to appear for the team
            finisher_id_A = game_df[game_df['Pitcher Team'] == team_A]['Pitcher ID'].iloc[-1]
            achievements.append({'Season': season, 'Pitcher ID': finisher_id_A, 'Stat': 'GF'})

            # Complete Game
            if len(pitchers_A) == 1:
                pitcher_id = pitchers_A[0]
                achievements.append({'Season': season, 'Pitcher ID': pitcher_id, 'Stat': 'CG'})
                
                # Shutout: CG and opponent (Team B) scored 0 runs
                if runs_B == 0:
                    achievements.append({'Season': season, 'Pitcher ID': pitcher_id, 'Stat': 'SHO'})

        # --- Team B Pitchers ---
        if pitchers_B:
            # Game Started
            starter_id_B = game_df[game_df['Pitcher Team'] == team_B]['Pitcher ID'].iloc[0]
            achievements.append({'Season': season, 'Pitcher ID': starter_id_B, 'Stat': 'GS'})

            # Game Finished
            finisher_id_B = game_df[game_df['Pitcher Team'] == team_B]['Pitcher ID'].iloc[-1]
            achievements.append({'Season': season, 'Pitcher ID': finisher_id_B, 'Stat': 'GF'})

            # Complete Game
            if len(pitchers_B) == 1:
                pitcher_id = pitchers_B[0]
                achievements.append({'Season': season, 'Pitcher ID': pitcher_id, 'Stat': 'CG'})

                # Shutout: CG and opponent (Team A) scored 0 runs
                if runs_A == 0:
                    achievements.append({'Season': season, 'Pitcher ID': pitcher_id, 'Stat': 'SHO'})

    if not achievements:
        return pd.DataFrame(columns=['Season', 'Pitcher ID', 'GS', 'GF', 'CG', 'SHO'])

    # Convert list of dicts to DataFrame and aggregate
    achievements_df = pd.DataFrame(achievements)
    
    # Pivot and sum the stats
    agg_df = achievements_df.groupby(['Season', 'Pitcher ID', 'Stat']).size().unstack(fill_value=0).reset_index()

    # Ensure all columns exist in case none of a certain type occurred
    for col in ['GS', 'GF', 'CG', 'SHO']:
        if col not in agg_df.columns:
            agg_df[col] = 0
            
    return agg_df[['Season', 'Pitcher ID', 'GS', 'GF', 'CG', 'SHO']]


def main():
    print("Loading all season data... (this may take a moment)")
    all_season_data, most_recent_season = load_all_seasons()
    if not all_season_data: return
    combined_df = pd.concat([df.assign(Season=season) for season, df in all_season_data.items()], ignore_index=True)

    # Disambiguate Line Outs (LO) from Left Ground Outs (LGO) in modern seasons.
    is_modern_season = ~combined_df['Season'].isin(['S2', 'S3'])
    lo_mask = (combined_df['Exact Result'] == 'LGO') & (combined_df['Old Result'] == 'LO')
    combined_df.loc[is_modern_season & lo_mask, 'Exact Result'] = 'LO'

    # Ensure key numeric columns are treated as numbers, filling non-numeric with 0
    combined_df['RBI'] = pd.to_numeric(combined_df['RBI'], errors='coerce').fillna(0)
    combined_df['Run'] = pd.to_numeric(combined_df['Run'], errors='coerce').fillna(0)
    no_id_mask = combined_df['Pitcher ID'].isna()
    if no_id_mask.any():
        unique_names = combined_df.loc[no_id_mask, 'Pitcher'].unique()
        name_to_id_map = {name: -i for i, name in enumerate(unique_names, 1)}
        combined_df.loc[no_id_mask, 'Pitcher ID'] = combined_df.loc[no_id_mask, 'Pitcher'].map(name_to_id_map)

    no_id_mask_hitter = combined_df['Hitter ID'].isna()
    if no_id_mask_hitter.any():
        unique_names = combined_df.loc[no_id_mask_hitter, 'Hitter'].unique()
        name_to_id_map = {name: -i for i, name in enumerate(unique_names, 1)}
        combined_df.loc[no_id_mask_hitter, 'Hitter ID'] = combined_df.loc[no_id_mask_hitter, 'Hitter'].map(name_to_id_map)

    combined_df['Pitcher ID'] = pd.to_numeric(combined_df['Pitcher ID'], errors='coerce').fillna(0).astype(int)
    combined_df['Hitter ID'] = pd.to_numeric(combined_df['Hitter ID'], errors='coerce').fillna(0).astype(int)
    
    print("Processing Run Expectancy Matrices...")
    run_expectancy_by_season = {}
    all_season_names = combined_df['Season'].unique()
    if all_season_names.size > 0:
        most_recent_season_num = max([int(s.replace('S', '')) for s in all_season_names])
        most_recent_season = f"S{most_recent_season_num}"
    else:
        most_recent_season = ""

    sorted_seasons = sorted(all_season_names, key=lambda s: int(s.replace('S', '')))
    for season in sorted_seasons:
        season_df = combined_df[combined_df['Season'] == season]
        is_current = (season == most_recent_season)
        if is_current: print(f"Calculating matrix for current season {season} (will not use cache)...")
        run_expectancy_by_season[season] = get_run_expectancy_matrix(season, season_df.copy(), is_most_recent_season=is_current)
    print("Run Expectancy Matrices are ready.")

    print("Calculating RE24 for all plays...")
    re24_values = []
    # Use sorted_seasons to ensure order
    for season in sorted_seasons:
        season_df = combined_df[combined_df['Season'] == season].copy()
        re_matrix = run_expectancy_by_season.get(season, {})
        if not re_matrix:
            re24_values.append(pd.Series(0, index=season_df.index))
            continue

        season_df['OBC'] = pd.to_numeric(season_df['OBC'], errors='coerce').fillna(0).astype(int)
        season_df['Outs'] = pd.to_numeric(season_df['Outs'], errors='coerce').fillna(0).astype(int)

        re_before = season_df.apply(lambda row: re_matrix.get((row['OBC'], row['Outs']), 0), axis=1)

        inning_groups = season_df.groupby('Inning ID')
        obc_after = inning_groups['OBC'].shift(-1)
        outs_after = inning_groups['Outs'].shift(-1)

        obc_after.fillna(0, inplace=True)
        outs_after.fillna(3, inplace=True)
        
        after_df = pd.DataFrame({'OBC': obc_after.astype(int), 'Outs': outs_after.astype(int)})
        re_after = after_df.apply(lambda row: re_matrix.get((row['OBC'], row['Outs']), 0), axis=1)
        
        re_after.index = season_df.index

        runs_on_play = pd.to_numeric(season_df['Run'], errors='coerce').fillna(0)

        season_re24 = re_after - re_before + runs_on_play
        re24_values.append(season_re24)

    if re24_values:
        combined_df['RE24'] = pd.concat(re24_values)
    else:
        combined_df['RE24'] = 0
    print("RE24 calculation complete.")

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gamelogs_path = os.path.join(script_dir, '..', 'data', 'gamelogs.txt')
        with open(gamelogs_path, 'r') as f: gamelogs_content = f.read()
        season_games_map = {parts[0]: int(parts[1]) for line in gamelogs_content.splitlines() if len(parts := line.strip().split('\t')) >= 2}
    except FileNotFoundError:
        print("Warning: gamelogs.txt not found. Cannot apply qualifying minimums for leaderboards.")
        season_games_map = {}

    print("\nData loaded successfully! Welcome to the MLR Scouting Tool.")

    player_name_map = {**combined_df.groupby('Hitter')['Hitter ID'].first().to_dict(), **combined_df.groupby('Pitcher')['Pitcher ID'].first().to_dict()}
    player_id_map = {**combined_df.groupby('Hitter ID')['Hitter'].first().to_dict(), **combined_df.groupby('Pitcher ID')['Pitcher'].first().to_dict()}

    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cache')
    previous_most_recent = _read_cache_manifest(cache_dir)
    seasons_to_recalc = []
    if most_recent_season != previous_most_recent and previous_most_recent is not None:
        print(f"New season detected. Finalizing stats cache for {previous_most_recent}...")
        seasons_to_recalc.append(previous_most_recent)

    print("Calculating all player stats and decisions (using cache for past seasons)...")

    season_games_series = combined_df['Season'].map(season_games_map)
    leaderboard_df = combined_df[combined_df['Session'] <= season_games_series]

    # --- Pre-calculate all stats that need to be merged before caching ---
    print("Calculating FIP constants...")
    fip_constants_by_season = {}
    league_pitching_totals = leaderboard_df.groupby('Season').apply(lambda df: calculate_pitching_stats(df, season=df.name), include_groups=False).reset_index()
    if not league_pitching_totals.empty:
        league_pitching_totals['lg_ERA'] = (league_pitching_totals['R'] * 6) / league_pitching_totals['IP']
        league_pitching_totals['lg_FIP_unscaled'] = ((13 * league_pitching_totals['HR']) + (3 * league_pitching_totals['BB']) - (2 * league_pitching_totals['K'])) / league_pitching_totals['IP']
        league_pitching_totals['FIP_Constant'] = league_pitching_totals['lg_ERA'] - league_pitching_totals['lg_FIP_unscaled']
        fip_constants_by_season = league_pitching_totals.set_index('Season')['FIP_Constant'].to_dict()

    print("Calculating Neutral ERA and ERA+...")
    neutral_pitching_stats = []
    for season in sorted_seasons:
        season_df = leaderboard_df[leaderboard_df['Season'] == season]
        re_matrix = run_expectancy_by_season.get(season, {})
        if not re_matrix: continue
        lg_neutral_stats = calculate_neutral_pitching_stats(season_df, re_matrix)
        lg_n_ip = lg_neutral_stats['nOuts'] / 3
        lg_n_era = (lg_neutral_stats['nRuns'] * 6) / lg_n_ip if lg_n_ip > 0 else 0
        for pitcher_id, player_df in season_df.groupby('Pitcher ID'):
            player_neutral_stats = calculate_neutral_pitching_stats(player_df, re_matrix)
            player_n_ip = player_neutral_stats['nOuts'] / 3
            player_n_era = (player_neutral_stats['nRuns'] * 6) / player_n_ip if player_n_ip > 0 else 0
            era_plus = round(100 * (lg_n_era / player_n_era)) if player_n_era > 0 else 0
            neutral_pitching_stats.append({'Season': season, 'Pitcher ID': pitcher_id, 'nIP': player_n_ip, 'ERA+': era_plus})
    neutral_stats_df = pd.DataFrame(neutral_pitching_stats) if neutral_pitching_stats else pd.DataFrame()

    print("Calculating pitching decisions (W, L, SV, HLD)...")
    pitching_decisions = []
    for (season, game_id), game_df in combined_df.groupby(['Season', 'Game ID']):
        decisions = get_pitching_decisions(game_df)
        if decisions:
            decisions['Season'] = season
            decisions['Game ID'] = game_id
            pitching_decisions.append(decisions)
    pitching_decisions_df = pd.DataFrame(pitching_decisions)
    game_types = combined_df[['Season', 'Game ID', 'GameType']].drop_duplicates()
    pitching_decisions_df = pitching_decisions_df.merge(game_types, on=['Season', 'Game ID'], how='left')
    regular_season_decisions = pitching_decisions_df[pitching_decisions_df['GameType'] == 'Regular']
    playoff_decisions = pitching_decisions_df[pitching_decisions_df['GameType'] == 'Playoff']

    def aggregate_decisions(df, games_df):
        if df.empty: return pd.DataFrame(columns=['Season', 'Pitcher ID', 'W', 'L', 'SV', 'HLD'])
        all_pitchers = games_df['Pitcher ID'].unique()
        all_seasons = df['Season'].unique()
        base_df = pd.DataFrame([(s, p) for s in all_seasons for p in all_pitchers], columns=['Season', 'Pitcher ID'])
        wins_df = df[df['win'].notna()].groupby(['Season', 'win']).size().reset_index(name='W').rename(columns={'win': 'Pitcher ID'})
        losses_df = df[df['loss'].notna()].groupby(['Season', 'loss']).size().reset_index(name='L').rename(columns={'loss': 'Pitcher ID'})
        saves_df = df[df['save'].notna()].groupby(['Season', 'save']).size().reset_index(name='SV').rename(columns={'save': 'Pitcher ID'})
        if 'holds' in df.columns:
            holds_exploded = df.explode('holds').dropna(subset=['holds'])
            holds_exploded['holds'] = pd.to_numeric(holds_exploded['holds'], errors='coerce').dropna()
            holds_df = holds_exploded.groupby(['Season', 'holds']).size().reset_index(name='HLD').rename(columns={'holds': 'Pitcher ID'})
        else: holds_df = pd.DataFrame(columns=['Season', 'Pitcher ID', 'HLD'])
        for df_stat in [wins_df, losses_df, saves_df, holds_df]:
            if not df_stat.empty: df_stat['Pitcher ID'] = df_stat['Pitcher ID'].astype(int)
        agg_df = base_df.merge(wins_df, on=['Season', 'Pitcher ID'], how='left').merge(losses_df, on=['Season', 'Pitcher ID'], how='left').merge(saves_df, on=['Season', 'Pitcher ID'], how='left').merge(holds_df, on=['Season', 'Pitcher ID'], how='left').fillna(0)
        for col in ['W', 'L', 'SV', 'HLD']: agg_df[col] = agg_df[col].astype(int)
        return agg_df

    regular_pitcher_stats_agg = aggregate_decisions(regular_season_decisions, leaderboard_df)
    playoff_pitcher_stats_agg = aggregate_decisions(playoff_decisions, combined_df[combined_df['GameType'] == 'Playoff'])

    print("Calculating pitching achievements (GS, CG, SHO, GF)...")
    game_achievements_df = calculate_game_achievements(leaderboard_df)

    # --- Main Processing Loop ---
    all_seasons_hitting_stats = []
    all_seasons_pitching_stats = []
    for season in sorted_seasons:
        force_recalc = (season == most_recent_season) or (season in seasons_to_recalc)
        season_leaderboard_df = leaderboard_df[leaderboard_df['Season'] == season]

        hitting_cache_path = os.path.join(cache_dir, f'hitting_stats_{season}.csv')
        pitching_cache_path = os.path.join(cache_dir, f'pitching_stats_{season}.csv')

        # Determine if we can use cache for both, including checking for WAR column
        can_use_cache = False
        if os.path.exists(hitting_cache_path) and os.path.exists(pitching_cache_path) and not force_recalc:
            # Check if WAR is in the cached files
            try:
                hitting_cols = pd.read_csv(hitting_cache_path, nrows=0).columns
                pitching_cols = pd.read_csv(pitching_cache_path, nrows=0).columns
                if 'WAR' in hitting_cols and 'WAR' in pitching_cols:
                    can_use_cache = True
            except Exception:
                can_use_cache = False # File might be empty or corrupt

        if can_use_cache:
            season_hitting_stats = pd.read_csv(hitting_cache_path)
            season_pitching_stats = pd.read_csv(pitching_cache_path)
        else:
            # --- Hitting Stats Calculation ---
            hitter_records = []
            for (hitter_id), group_df in season_leaderboard_df.groupby('Hitter ID'):
                stats_series = calculate_hitting_stats(group_df, season=season)
                if stats_series is not None:
                    stats_series['Season'] = season
                    stats_series['Hitter ID'] = hitter_id
                    hitter_records.append(stats_series)
            season_hitting_stats = pd.DataFrame(hitter_records)

            # --- Pitching Stats Calculation ---
            pitcher_records = []
            for (pitcher_id), group_df in season_leaderboard_df.groupby('Pitcher ID'):
                stats_series = calculate_pitching_stats(group_df, season=season)
                if stats_series is not None:
                    stats_series['Season'] = season
                    stats_series['Pitcher ID'] = pitcher_id
                    pitcher_records.append(stats_series)
            season_pitching_stats = pd.DataFrame(pitcher_records)

            # --- Merge additional pitching stats ---
            if not season_pitching_stats.empty:
                fip_constant = fip_constants_by_season.get(season, 3.10)
                season_pitching_stats['FIP'] = ((13 * season_pitching_stats['HR']) + (3 * season_pitching_stats['BB']) - (2 * season_pitching_stats['K'])) / season_pitching_stats['IP'] + fip_constant
                season_neutral_stats = neutral_stats_df[neutral_stats_df['Season'] == season] if not neutral_stats_df.empty else pd.DataFrame()
                season_achievements = game_achievements_df[game_achievements_df['Season'] == season]
                season_decisions = regular_pitcher_stats_agg[regular_pitcher_stats_agg['Season'] == season]
                if not season_neutral_stats.empty: season_pitching_stats = season_pitching_stats.merge(season_neutral_stats, on=['Season', 'Pitcher ID'], how='left')
                if not season_achievements.empty: season_pitching_stats = season_pitching_stats.merge(season_achievements, on=['Season', 'Pitcher ID'], how='left')
                if not season_decisions.empty: season_pitching_stats = season_pitching_stats.merge(season_decisions, on=['Season', 'Pitcher ID'], how='left')

            # --- WAR Calculation ---
            if not season_hitting_stats.empty and not season_pitching_stats.empty:
                num_games = season_games_map.get(season, 0)
                if num_games > 0:
                    total_war_season = num_games * 6.17
                    runs_per_win = 10
                    total_rar_season = total_war_season * runs_per_win

                    # Hitting WAR
                    total_pa_season = season_hitting_stats['PA'].sum()
                    if total_pa_season > 0:
                        total_rar_h = total_rar_season / 2
                        runs_per_pa_replacement_h = total_rar_h / total_pa_season
                        season_hitting_stats['WAR'] = (season_hitting_stats['RE24'] + runs_per_pa_replacement_h * season_hitting_stats['PA']) / runs_per_win
                    else:
                        season_hitting_stats['WAR'] = 0

                    # Pitching WAR
                    total_bf_season = season_pitching_stats['BF'].sum()
                    if total_bf_season > 0:
                        total_rar_p = total_rar_season / 2
                        runs_per_bf_replacement_p = total_rar_p / total_bf_season
                        season_pitching_stats['WAR'] = (-season_pitching_stats['RE24'] + runs_per_bf_replacement_p * season_pitching_stats['BF']) / runs_per_win
                    else:
                        season_pitching_stats['WAR'] = 0
                else:
                    season_hitting_stats['WAR'] = 0
                    season_pitching_stats['WAR'] = 0
            
            # --- Cache Results ---
            if not season_hitting_stats.empty:
                season_hitting_stats.to_csv(hitting_cache_path, index=False)
            if not season_pitching_stats.empty:
                season_pitching_stats.to_csv(pitching_cache_path, index=False)

        all_seasons_hitting_stats.append(season_hitting_stats)
        all_seasons_pitching_stats.append(season_pitching_stats)

    # --- Final Assembly ---
    all_hitting_stats = pd.concat(all_seasons_hitting_stats, ignore_index=True)
    all_pitching_stats = pd.concat(all_seasons_pitching_stats, ignore_index=True).fillna(0)

    # --- Calculate league-wide neutral stats for OPS+ ---
    league_stats_by_season = {}
    for season in leaderboard_df['Season'].unique():
        season_df = leaderboard_df[leaderboard_df['Season'] == season]
        if not season_df.empty:
            league_totals = calculate_hitting_stats(season_df, season=season)
            league_stats_by_season[season] = {'lg_nOBP': league_totals['nOBP'], 'lg_nSLG': league_totals['nSLG']}

    if not all_hitting_stats.empty:
        all_hitting_stats['OPS+'] = all_hitting_stats.apply(calculate_ops_plus_for_row, axis=1, league_stats_by_season=league_stats_by_season)

    _write_cache_manifest(cache_dir, most_recent_season)
    print("Calculations complete.")

    while True:
        user_input = input("\nEnter command (e.g., 'stats 1759', 'leaderboard HR', or 'exit'): ").strip()
        if user_input.lower() == 'exit':
            print("Exiting scouting tool. Goodbye!")
            break

        parts = user_input.split()
        if not parts:
            continue
            
        command = parts[0].lower()

        if command == 'leaderboard':
            if len(parts) < 2:
                print("Invalid format. Please use 'leaderboard <stat>'.")
                continue
            stat = " ".join(parts[1:])
            process_leaderboard(stat, leaderboard_df, all_hitting_stats, all_pitching_stats, player_id_map, season_games_map)
        elif command in ['stats', 'scout']:
            if len(parts) < 2:
                print(f"Invalid format. Please use '{command} <Player Name or ID>'.")
                continue
            
            identifier = " ".join(parts[1:])
            player_id = None

            if identifier.isdigit():
                player_id = int(identifier)
            else: # It's a name
                matching_players = [name for name in player_name_map.keys() if name and name.lower() == identifier.lower()]
                if len(matching_players) == 1:
                    player_id = player_name_map[matching_players[0]]
                elif len(matching_players) > 1:
                    print(f"Multiple players found with the name '{identifier}'. Please use a unique Player ID.")
                    continue
            
            if player_id:
                if command == 'stats':
                    process_player_stats(player_id, combined_df, player_id_map, all_hitting_stats, all_pitching_stats)
                elif command == 'scout':
                    generate_scouting_report(player_id, combined_df, player_id_map)
            else:
                print(f"Player '{identifier}' not found.")
        else:
            print(f"Invalid command. Use 'stats', 'scout', or 'leaderboard'.")

if __name__ == '__main__':
    main()
