from data_loader import load_all_seasons
from game_processing import get_pitching_decisions
import pandas as pd
import sys
import json
import os

# --- Cache Manifest Functions ---
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
    wpa = pa_df['Batter WPA'].sum() if 'Batter WPA' in pa_df.columns else 0

    if pa == 0:
        return pd.Series({'G': df['Session'].nunique(), 'PA': 0, 'AB': 0, 'H': 0, 'R': 0, 'RBI': 0, '2B': 0, '3B': 0, 'HR': 0, 'TB': 0, 'BB': 0, 'IBB': 0, 'Auto K': 0, 'K': 0, 'SB': num_sb, 'CS': num_cs, 'SH': 0, 'SF': 0, 'GIDP': 0, 'AVG': 0, 'OBP': 0, 'SLG': 0, 'OPS': 0, 'Avg Diff': avg_diff, 'RE24': re24, 'WPA': 0, 'ISO': 0, 'BABIP': 0, 'SB%': 0, 'HR%': 0, 'SO%': 0, 'BB%': 0, 'GB%': 0, 'FB%': 0, 'GB/FB': 0, 'GB_outs': 0, 'FB_outs': 0})

    games_played = df['Session'].nunique()
    num_walks = pa_df[pa_df[result_col].isin(walks)].shape[0]
    num_ibb = pa_df[pa_df[result_col] == 'IBB'].shape[0]
    
    # Ground into Double/Triple Plays
    num_gidp = pa_df[(pa_df['Old Result'].isin(['DP', 'TP'])) | (pa_df['Exact Result'] == 'BUNT DP')].shape[0]

    # Sacrifices (SH and SF)
    sac_events_df = pa_df[pa_df['Old Result'] == 'Sac']
    # An SF is a sac event that results in an RBI
    num_sf = sac_events_df[pd.to_numeric(sac_events_df['RBI'], errors='coerce').fillna(0) > 0].shape[0]
    num_sh = len(sac_events_df) - num_sf
    num_sacrifices = len(sac_events_df)
    
    ab = pa - num_walks - num_sacrifices
    num_hits = pa_df[pa_df[result_col].isin(hits)].shape[0]
    num_doubles = pa_df[pa_df[result_col] == '2B'].shape[0]
    num_triples = pa_df[pa_df[result_col] == '3B'].shape[0]
    num_hr = pa_df[pa_df[result_col] == 'HR'].shape[0]
    num_singles = pa_df[pa_df[result_col] == '1B'].shape[0]
    if not use_old_results:
        num_singles += pa_df[pa_df[result_col] == 'BUNT 1B'].shape[0]

    num_tb = num_singles + (num_doubles * 2) + (num_triples * 3) + (num_hr * 4)
    num_strikeouts = pa_df[pa_df[result_col].isin(strikeouts)].shape[0]
    num_auto_k = pa_df[pa_df[result_col].isin(['Auto K', 'AUTO K'])].shape[0]

    runs_scored = df['Run'].sum()
    rbi = df['RBI'].sum()

    # --- Standard Rate Stats ---
    avg = num_hits / ab if ab > 0 else 0
    obp = (num_hits + num_walks) / pa if pa > 0 else 0
    slg = (num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0
    ops = obp + slg

    # --- Advanced Stat Calculations ---
    iso = slg - avg
    
    # Percentages
    hr_pct = num_hr / pa if pa > 0 else 0
    so_pct = num_strikeouts / pa if pa > 0 else 0
    bb_pct = num_walks / pa if pa > 0 else 0

    # Stolen Base Percentage
    total_sb_attempts = num_sb + num_cs
    sb_pct = num_sb / total_sb_attempts if total_sb_attempts > 0 else 0

    # Batted Ball Calculations (based on outs)
    fly_ball_events = {'FO', 'PO'}
    ground_ball_events = {'LGO', 'RGO', 'BUNT GO'}
    num_fb_outs = pa_df[pa_df[result_col].isin(fly_ball_events)].shape[0]
    num_gb_outs = pa_df[pa_df[result_col].isin(ground_ball_events)].shape[0] + num_gidp
    
    total_fb_gb = num_fb_outs + num_gb_outs
    gb_pct = num_gb_outs / total_fb_gb if total_fb_gb > 0 else 0
    fb_pct = num_fb_outs / total_fb_gb if total_fb_gb > 0 else 0
    gb_fb_ratio = num_gb_outs / num_fb_outs if num_fb_outs > 0 else 0

    # BABIP
    babip_denominator = ab - num_strikeouts - num_hr + num_sf
    babip = (num_hits - num_hr) / babip_denominator if babip_denominator > 0 else 0

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
        'G': games_played, 'PA': pa, 'AB': ab, 'H': num_hits, 'R': runs_scored, '2B': num_doubles, '3B': num_triples, 'HR': num_hr, 'TB': num_tb, 'RBI': rbi,
        'BB': num_walks, 'IBB': num_ibb, 'K': num_strikeouts, 'Auto K': num_auto_k, 'SB': num_sb, 'CS': num_cs, 'SH': num_sh, 'SF': num_sf, 'GIDP': num_gidp,
        'AVG': avg, 'OBP': obp, 'SLG': slg, 'OPS': ops, 'ISO': iso, 'BABIP': babip,
        'SB%': sb_pct, 'HR%': hr_pct, 'SO%': so_pct, 'BB%': bb_pct,
        'GB%': gb_pct, 'FB%': fb_pct, 'GB/FB': gb_fb_ratio,
        'Avg Diff': avg_diff,
        'nOBP': nOBP, 'nSLG': nSLG, 'RE24': re24, 'WPA': wpa,
        'GB_outs': num_gb_outs, 'FB_outs': num_fb_outs
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
    wpa = bf_df['Pitcher WPA'].sum() if 'Pitcher WPA' in bf_df.columns else 0

    games_played = df['Session'].nunique()
    num_hits_allowed = bf_df[bf_df[result_col].isin(hits_allowed)].shape[0]
    num_walks_allowed = bf_df[bf_df[result_col].isin(walks_allowed)].shape[0]
    num_auto_bb_allowed = bf_df[bf_df[result_col].isin(['Auto BB', 'AUTO BB'])].shape[0]
    num_ibb = bf_df[bf_df[result_col].isin(ibb_events)].shape[0]
    num_strikeouts = bf_df[bf_df[result_col].isin(strikeouts)].shape[0]
    num_hr_allowed = bf_df[bf_df[result_col].isin(hr_allowed)].shape[0]

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

    # --- Opponent Stats Calculations ---
    sac_events_df = bf_df[bf_df['Old Result'] == 'Sac']
    num_sf_allowed = sac_events_df[pd.to_numeric(sac_events_df['RBI'], errors='coerce').fillna(0) > 0].shape[0]
    num_sh_allowed = len(sac_events_df) - num_sf_allowed
    
    ab_against = num_bf - num_walks_allowed - num_sh_allowed - num_sf_allowed

    num_doubles_allowed = bf_df[bf_df[result_col] == '2B'].shape[0]
    num_triples_allowed = bf_df[bf_df[result_col] == '3B'].shape[0]
    num_singles_allowed = num_hits_allowed - num_doubles_allowed - num_triples_allowed - num_hr_allowed

    baa = num_hits_allowed / ab_against if ab_against > 0 else 0
    obpa = (num_hits_allowed + num_walks_allowed) / num_bf if num_bf > 0 else 0
    slga = (num_singles_allowed + 2*num_doubles_allowed + 3*num_triples_allowed + 4*num_hr_allowed) / ab_against if ab_against > 0 else 0
    opsa = obpa + slga

    babip_denom = ab_against - num_strikeouts - num_hr_allowed + num_sf_allowed
    babip_against = (num_hits_allowed - num_hr_allowed) / babip_denom if babip_denom > 0 else 0

    hr_pct_against = num_hr_allowed / num_bf if num_bf > 0 else 0
    k_pct_against = num_strikeouts / num_bf if num_bf > 0 else 0
    bb_pct_against = num_walks_allowed / num_bf if num_bf > 0 else 0

    fly_ball_events = {'FO', 'PO'}
    ground_ball_events = {'LGO', 'RGO', 'BUNT GO'}
    num_fb_outs_allowed = bf_df[bf_df[result_col].isin(fly_ball_events)].shape[0]
    num_gidp_allowed = bf_df[(bf_df['Old Result'].isin(['DP', 'TP'])) | (bf_df['Exact Result'] == 'BUNT DP')].shape[0]
    num_gb_outs_allowed = bf_df[bf_df[result_col].isin(ground_ball_events)].shape[0] + num_gidp_allowed
    
    total_fb_gb_allowed = num_fb_outs_allowed + num_gb_outs_allowed
    gb_pct_against = num_gb_outs_allowed / total_fb_gb_allowed if total_fb_gb_allowed > 0 else 0
    fb_pct_against = num_fb_outs_allowed / total_fb_gb_allowed if total_fb_gb_allowed > 0 else 0
    gb_fb_ratio_against = num_gb_outs_allowed / num_fb_outs_allowed if num_fb_outs_allowed > 0 else 0

    # Rate stats per 6 innings
    h6 = (num_hits_allowed / ip) * 6 if ip > 0 else 0
    hr6 = (num_hr_allowed / ip) * 6 if ip > 0 else 0
    bb6 = (num_walks_allowed / ip) * 6 if ip > 0 else 0
    k6 = (num_strikeouts / ip) * 6 if ip > 0 else 0
    k_bb = num_strikeouts / num_walks_allowed if num_walks_allowed > 0 else 0
    
    return pd.Series({
        'G': games_played, 'IP': ip, 'BF': num_bf, 'H': num_hits_allowed, 'R': runs_allowed, 'BB': num_walks_allowed, 'IBB': num_ibb, 'Auto BB': num_auto_bb_allowed, 'K': num_strikeouts, 'HR': num_hr_allowed,
        'ERA': (runs_allowed * 6) / ip if ip > 0 else 0,
        'WHIP': (num_walks_allowed + num_hits_allowed) / ip if ip > 0 else 0,
        'H/6': h6, 'HR/6': hr6, 'BB/6': bb6, 'K/6': k6, 'K/BB': k_bb,
        'BAA': baa, 'OBPA': obpa, 'SLGA': slga, 'OPSA': opsa, 'BABIP_A': babip_against,
        'HR%_A': hr_pct_against, 'K%_A': k_pct_against, 'BB%_A': bb_pct_against,
        'GB%_A': gb_pct_against, 'FB%_A': fb_pct_against, 'GB/FB_A': gb_fb_ratio_against,
        'Avg Diff': avg_diff,
        'RE24': re24,
        'WPA': wpa,
        'AB_A': ab_against, 'SF_A': num_sf_allowed, 'SH_A': num_sh_allowed,
        '2B_A': num_doubles_allowed, '3B_A': num_triples_allowed,
        'GB_outs_A': num_gb_outs_allowed, 'FB_outs_A': num_fb_outs_allowed
    })

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
    
    # This will be slow, but it's the only way to do it row-by-row
    inning_stats = df.groupby('Inning ID').apply(lambda x: _simulate_neutral_inning(x, re_matrix), include_groups=False)
    return inning_stats.sum()

def _get_pitch_histogram_data(pitch_series, bin_size):
    pitch_series = pitch_series.dropna().astype(int)
    if pitch_series.empty: return []
    pitches = pitch_series.apply(lambda p: 0 if p == 1000 else p)
    bin_ids = pitches // bin_size
    histogram_data = bin_ids.value_counts()
    num_bins = (1000 + bin_size - 1) // bin_size
    all_bin_ids = range(num_bins)
    histogram_data = histogram_data.reindex(all_bin_ids, fill_value=0).sort_index()
    
    output = []
    for bin_id, count in histogram_data.items():
        lower_bound = bin_id * bin_size
        upper_bound = lower_bound + bin_size - 1
        if lower_bound == 0: lower_bound = 1
        label = f"{lower_bound}-{upper_bound}"
        output.append({'label': label, 'count': int(count)})
    return output

def get_scouting_report_data(player_id, pitcher_df, bin_size=100):
    if pitcher_df.empty: return None
    pitcher_df['Pitch'] = pd.to_numeric(pitcher_df['Pitch'], errors='coerce')
    pitcher_df.sort_values(by=['Season', 'Session', 'Inning'], inplace=True)
    
    valid_pitches = pitcher_df['Pitch'].dropna()
    top_5_pitches = valid_pitches.value_counts().nlargest(5)
    
    # Tendencies
    pitches = pitcher_df['Pitch'].to_numpy()
    repeat_count = (pitches[:-1] == pitches[1:]).sum()
    total_opportunities = len(pitches) - 1
    repeat_percentage = (repeat_count / total_opportunities) * 100 if total_opportunities > 0 else 0
    has_tripled_up = ((pitches[:-2] == pitches[1:-1]) & (pitches[1:-1] == pitches[2:])).any() if len(pitches) > 2 else False
    swing = pd.to_numeric(pitcher_df['Swing'], errors='coerce')
    diff = pd.to_numeric(pitcher_df['Diff'], errors='coerce')
    swing_match_rate = (pitcher_df['Pitch'] == swing.shift(1)).mean() * 100
    diff_match_rate = (pitcher_df['Pitch'] == diff.shift(1)).mean() * 100
    meme_numbers = {69, 420, 666, 327, 880}
    meme_percentage = pitcher_df['Pitch'].isin(meme_numbers).sum() / len(pitcher_df) * 100 if len(pitcher_df) > 0 else 0

    # Histograms
    histograms = {
        "overall": _get_pitch_histogram_data(pitcher_df['Pitch'], bin_size),
        "first_of_game": _get_pitch_histogram_data(pitcher_df.groupby(['Season', 'Game ID']).first()['Pitch'], bin_size),
        "first_of_inning": _get_pitch_histogram_data(pitcher_df.groupby(['Season', 'Game ID', 'Inning']).first()['Pitch'], bin_size),
        "risp": _get_pitch_histogram_data(pitcher_df[pd.to_numeric(pitcher_df['OBC'], errors='coerce').fillna(0) > 1]['Pitch'], bin_size)
    }

    return {
        "top_5_pitches": {int(k): int(v) for k, v in top_5_pitches.to_dict().items()},
        "histograms": histograms,
        "tendencies": {
            "repeat_percentage": round(repeat_percentage, 2),
            "has_tripled_up": bool(has_tripled_up),
            "swing_match_rate": round(swing_match_rate, 2),
            "diff_match_rate": round(diff_match_rate, 2),
            "meme_percentage": round(meme_percentage, 2)
        }
    }

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

    if not achievements: return pd.DataFrame(columns=['Season', 'Pitcher ID', 'GS', 'GF', 'CG', 'SHO'])

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
    if 'Batter WPA' in combined_df.columns:
        combined_df['Batter WPA'] = pd.to_numeric(combined_df['Batter WPA'].astype(str).str.strip('%'), errors='coerce').fillna(0) / 100
    if 'Pitcher WPA' in combined_df.columns:
        combined_df['Pitcher WPA'] = pd.to_numeric(combined_df['Pitcher WPA'].astype(str).str.strip('%'), errors='coerce').fillna(0) / 100
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
                if 'WPA' in hitting_cols and 'BAA' in pitching_cols:
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
                    teams = group_df['Batter Team'].unique()
                    stats_series['Team'] = '/'.join(sorted(teams))
                    hitter_records.append(stats_series)
            season_hitting_stats = pd.DataFrame(hitter_records)

            # --- Pitching Stats Calculation ---
            pitcher_records = []
            for (pitcher_id), group_df in season_leaderboard_df.groupby('Pitcher ID'):
                stats_series = calculate_pitching_stats(group_df, season=season)
                if stats_series is not None:
                    stats_series['Season'] = season
                    stats_series['Pitcher ID'] = pitcher_id
                    teams = group_df['Pitcher Team'].unique()
                    stats_series['Team'] = '/'.join(sorted(teams))
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
                if not season_decisions.empty: 
                    season_pitching_stats = season_pitching_stats.merge(season_decisions, on=['Season', 'Pitcher ID'], how='left')
                    if 'W' in season_pitching_stats.columns and 'L' in season_pitching_stats.columns:
                        season_pitching_stats['W-L%'] = season_pitching_stats['W'] / (season_pitching_stats['W'] + season_pitching_stats['L'])
                        season_pitching_stats['W-L%'].fillna(0, inplace=True)

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
    all_hitting_stats = pd.concat(all_seasons_hitting_stats, ignore_index=True).fillna(0)
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

    # --- EXPORTING DATA ---
    print("Exporting data for web app...")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'data')
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    # Save main stats
    all_hitting_stats.to_json(os.path.join(output_dir, 'hitting_stats.json'), orient='records', indent=2)
    all_pitching_stats.to_json(os.path.join(output_dir, 'pitching_stats.json'), orient='records', indent=2)

    # Save maps
    with open(os.path.join(output_dir, 'player_id_map.json'), 'w') as f: json.dump({int(k): v for k, v in player_id_map.items()}, f, indent=2)
    with open(os.path.join(output_dir, 'season_games_map.json'), 'w') as f: json.dump(season_games_map, f, indent=2)

    # Generate and save scouting reports
    print("Generating and exporting scouting reports...")
    all_scouting_reports = {}
    pitcher_ids = leaderboard_df['Pitcher ID'].unique()
    for player_id in pitcher_ids:
        pitcher_df = combined_df[combined_df['Pitcher ID'] == player_id]
        report_data = get_scouting_report_data(player_id, pitcher_df)
        if report_data:
            all_scouting_reports[int(player_id)] = report_data
    with open(os.path.join(output_dir, 'scouting_reports.json'), 'w') as f: json.dump(all_scouting_reports, f, indent=2)
    
    # Save a smaller df for career avg diff calculations on front-end
    diff_data = combined_df[['Hitter ID', 'Pitcher ID', 'Diff']].copy()
    diff_data['Diff'] = pd.to_numeric(diff_data['Diff'], errors='coerce')
    diff_data.dropna(subset=['Diff'], inplace=True)
    diff_data.to_json(os.path.join(output_dir, 'diff_data.json'), orient='records', indent=2)

    print(f"Web data exported successfully to {output_dir}")

if __name__ == '__main__':
    main()