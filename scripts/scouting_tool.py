from data_loader import load_all_seasons
from game_processing import get_pitching_decisions
import pandas as pd

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

    if pa == 0:
        return pd.Series({'G': df['Session'].nunique(), 'PA': 0, 'AB': 0, 'H': 0, 'R': 0, 'RBI': 0, '2B': 0, '3B': 0, 'HR': 0, 'BB': 0, 'K': 0, 'SB': num_sb, 'CS': num_cs, 'AVG': 0, 'OBP': 0, 'SLG': 0, 'OPS': 0, 'Avg Diff': avg_diff})

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
        'nSLG': nSLG
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
        strikeouts = {'K', 'Auto K'}
        hr_allowed = {'HR'}
        single_out_bip = {'FO', 'LGO', 'PO', 'RGO', 'Bunt', 'LO'} # 'Bunt' is an out
        caught_stealing = {'CS'}
        stolen_bases = {'SB'}
    else:
        result_col = 'Exact Result'
        hits_allowed = {'1B', '2B', '3B', 'HR', 'BUNT 1B'}
        walks_allowed = {'BB', 'IBB', 'Auto BB', 'AUTO BB'}
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

    games_played = df['Session'].nunique()
    num_hits_allowed = df[df[result_col].isin(hits_allowed)].shape[0]
    num_walks_allowed = df[df[result_col].isin(walks_allowed)].shape[0]
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
        'G': games_played, 'IP': ip, 'H': num_hits_allowed, 'R': runs_allowed, 'BB': num_walks_allowed, 'K': num_strikeouts, 'HR': num_hr_allowed,
        'ERA': (runs_allowed * 6) / ip if ip > 0 else 0,
        'WHIP': (num_walks_allowed + num_hits_allowed) / ip if ip > 0 else 0,
        'Avg Diff': avg_diff
    })

# --- New Scouting Report Function ---
def generate_scouting_report(player_id, combined_df, player_id_map):
    if player_id not in player_id_map:
        print("Player not found.")
        return

    player_name = player_id_map[player_id]
    print(f"\nScouting Report for Pitcher: {player_name} (ID: {player_id})")
    pitcher_df = combined_df[combined_df['Pitcher ID'] == player_id].copy()

    if pitcher_df.empty:
        print("No pitching data found for this player.")
        return

    print("\n--- Top 5 Most Common Pitches ---")
    top_5_pitches = pitcher_df['Pitch'].value_counts().nlargest(5)
    print(top_5_pitches.to_string())

    pitcher_df.sort_values(by=['Season', 'Session', 'Inning'], inplace=True)
    pitches = pitcher_df['Pitch'].to_numpy()
    repeat_count = (pitches[:-1] == pitches[1:]).sum()
    total_opportunities = len(pitches) - 1
    repeat_percentage = (repeat_count / total_opportunities) * 100 if total_opportunities > 0 else 0
    print("\n--- Pitch Tendencies ---")
    print(f"Uses same number twice in a row: {repeat_percentage:.2f}%")

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
    if stat_name in ['AVG', 'OBP', 'SLG', 'OPS']:
        formatters['Value'] = lambda x: f"{x:.3f}".replace('0.', '.')
    elif stat_name in ['ERA', 'WHIP', 'Avg Diff']:
        formatters['Value'] = '{:.2f}'.format
    elif stat_name == 'OPS+':
        formatters['Value'] = '{:.0f}'.format
    else: # Counting stats
        formatters['Value'] = '{:.0f}'.format

    print(df.to_string(formatters=formatters))

def process_leaderboard(stat, combined_df, all_hitting_stats, all_pitching_stats, player_id_map, season_games_map):
    print(f"\n--- Leaderboards for: {stat.upper()} ---")

    # Define stat categories
    hitting_rate_stats = ['AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'Avg Diff']
    hitting_counting_stats = ['G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS']
    pitching_rate_stats = ['ERA', 'WHIP', 'Avg Diff']
    pitching_counting_stats = ['G', 'IP', 'H', 'R', 'BB', 'K', 'HR', 'W', 'L', 'SV', 'HLD']
    
    lower_is_better_pitching = ['ERA', 'WHIP']
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
        
        if stat_upper == 'OPS+':
            # Calculate the weighted average for career OPS+, don't just sum it.
            ops_plus_df = all_hitting_stats.copy()
            # Filter out any rows that might cause issues in calculation
            ops_plus_df = ops_plus_df[ops_plus_df['PA'] > 0].dropna(subset=['OPS+', 'PA'])
            ops_plus_df['OPS+'] = pd.to_numeric(ops_plus_df['OPS+'], errors='coerce')
            ops_plus_df['WeightedOPS+'] = ops_plus_df['OPS+'] * ops_plus_df['PA']
            
            career_ops_plus_agg = ops_plus_df.groupby('Hitter ID').sum(numeric_only=True)
            
            # Calculate the final weighted average and handle potential division by zero
            valid_career_pa = career_ops_plus_agg[career_ops_plus_agg['PA'] > 0]
            career_ops_plus_agg['OPS+'] = valid_career_pa['WeightedOPS+'] / valid_career_pa['PA']
            
            # Update the main career stats dataframe using .loc to avoid chained assignment issues
            career_hitting_stats.loc[:, 'OPS+'] = career_ops_plus_agg['OPS+']

        if stat_upper == 'Avg Diff':
            career_avg_diff = combined_df.groupby('Hitter ID')['Diff'].apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
            career_hitting_stats['Avg Diff'] = career_avg_diff

        if is_rate:
            # Recalculate career rate stats
            career_hitting_stats['AVG'] = career_hitting_stats['H'] / career_hitting_stats['AB']
            career_hitting_stats['OBP'] = (career_hitting_stats['H'] + career_hitting_stats['BB']) / career_hitting_stats['PA']
            career_hitting_stats['SLG'] = (career_hitting_stats['H'] - career_hitting_stats['2B'] - career_hitting_stats['3B'] - career_hitting_stats['HR'] + career_hitting_stats['2B']*2 + career_hitting_stats['3B']*3 + career_hitting_stats['HR']*4) / career_hitting_stats['AB']
            career_hitting_stats['OPS'] = career_hitting_stats['OBP'] + career_hitting_stats['SLG']
            # Fill NaNs for calculated rate stats, but leave OPS+ alone as it's handled separately
            for col in ['AVG', 'OBP', 'SLG', 'OPS']:
                career_hitting_stats[col] = career_hitting_stats[col].fillna(0)
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
            season_df = all_pitching_stats[all_pitching_stats['Season'] == season]
            if is_rate:
                games = season_games_map.get(season, 0)
                min_ip = games * 1
                qualified_season = season_df[season_df['IP'] >= min_ip]
                title = f"Season {season.replace('S','')} (min. {min_ip} IP)"
            else:
                qualified_season = season_df
                title = f"Season {season.replace('S','')}"
            
            season_top_10 = qualified_season.set_index('Pitcher ID')[stat_upper].nsmallest(10) if lower_is_better else qualified_season.set_index('Pitcher ID')[stat_upper].nlargest(10)
            display_leaderboard(season_top_10, title, player_id_map, stat_name=stat_upper)

        # All-Time
        career_pitching_stats = all_pitching_stats.groupby('Pitcher ID').sum(numeric_only=True)

        if stat_upper == 'Avg Diff':
            career_pitching_avg_diff = combined_df.groupby('Pitcher ID')['Diff'].apply(lambda x: pd.to_numeric(x, errors='coerce').mean())
            career_pitching_stats['Avg Diff'] = career_pitching_avg_diff

        if is_rate:
            career_pitching_stats['ERA'] = (career_pitching_stats['R'] * 6) / career_pitching_stats['IP']
            career_pitching_stats['WHIP'] = (career_pitching_stats['BB'] + career_pitching_stats['H']) / career_pitching_stats['IP']
            career_pitching_stats.replace([pd.NA, pd.NaT, float('inf'), float('-inf')], 0, inplace=True)
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
    int_cols = ['G', 'PA', 'AB', 'H', 'R', 'RBI', '2B', '3B', 'HR', 'BB', 'K', 'SB', 'CS', 'W', 'L', 'SV', 'HLD']
    # The 'R' column is used for both hitting and pitching, so we don't add it here again.
    if 'RBI' not in int_cols:
        int_cols.append('RBI')

    for col in int_cols:
        if col in stats_df.columns:
            stats_df[col] = stats_df[col].fillna(0).astype(int)
    
    if is_pitching:
        col_order = ['Team', 'G', 'W', 'L', 'SV', 'HLD', 'IP', 'H', 'R', 'BB', 'K', 'HR', 'ERA', 'WHIP', 'Avg Diff']
        if 'IP' in stats_df.columns: stats_df['IP'] = stats_df['IP'].apply(format_ip)
        formatters = {'ERA': '{:.2f}'.format, 'WHIP': '{:.2f}'.format, 'Avg Diff': '{:.2f}'.format}
    else:
        col_order = ['Team', 'G', 'PA', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI', 'BB', 'K', 'SB', 'CS', 'AVG', 'OBP', 'SLG', 'OPS', 'OPS+', 'Avg Diff']
        formatters = {
            'AVG': lambda x: f"{x:.3f}".replace('0.', '.'), 'OBP': lambda x: f"{x:.3f}".replace('0.', '.'),
            'SLG': lambda x: f"{x:.3f}".replace('0.', '.'), 'OPS': lambda x: f"{x:.3f}".replace('0.', '.'),
            'Avg Diff': '{:.2f}'.format
        }
    
    # Use a copy to avoid SettingWithCopyWarning
    stats_df_copy = stats_df.copy()

    # Manually format OPS+ to handle NA values correctly before printing
    if 'OPS+' in stats_df_copy.columns:
        stats_df_copy['OPS+'] = stats_df_copy['OPS+'].apply(lambda x: '' if pd.isna(x) else f'{x:.0f}')

    if 'Team' not in stats_df_copy:
        stats_df_copy['Team'] = ''
    else:
        # Ensure career row doesn't show aggregated team list and fill NaNs
        stats_df_copy['Team'] = stats_df_copy['Team'].fillna('')
        if 'Career' in stats_df_copy.index:
            stats_df_copy.loc['Career', 'Team'] = ''

    stats_df_copy = stats_df_copy.reindex(columns=col_order)
    print(stats_df_copy.to_string(formatters=formatters, na_rep=''))

def display_stat_block(df, is_pitching, title, pitcher_stats_agg=None, league_stats_by_season=None):
    """Calculates and displays a block of stats (e.g., regular season hitting)."""
    if df.empty:
        return

    stat_calculator = calculate_pitching_stats if is_pitching else calculate_hitting_stats
    
    # Manually iterate through seasons to avoid groupby().apply() issues
    seasons = df['Season'].unique()
    season_stats_list = []
    for season in seasons:
        season_df = df[df['Season'] == season]
        stats = stat_calculator(season_df, season=season)
        if stats is not None:
            stats['Season'] = season
            season_stats_list.append(stats)

    if not season_stats_list:
        return

    season_stats = pd.DataFrame(season_stats_list).set_index('Season')

    print(title)

    # Aggregate teams for each season
    team_col = 'Pitcher Team' if is_pitching else 'Batter Team'
    if team_col in df.columns:
        teams_df = df.dropna(subset=[team_col]).groupby('Season')[team_col].unique().apply(lambda teams: '/'.join(sorted(teams))).rename('Team').reset_index()
        season_stats = season_stats.reset_index().merge(teams_df, on='Season', how='left').set_index('Season')

    season_stats.index = season_stats.index.str.replace('S', '').astype(int)
    season_stats = season_stats.sort_index()
    season_stats.index.name = 'Season'
    
    if is_pitching and pitcher_stats_agg is not None:
        if not df.empty:
            player_id = df['Pitcher ID'].iloc[0]
            player_stats = pitcher_stats_agg[pitcher_stats_agg['Pitcher ID'] == player_id]
            if not player_stats.empty:
                player_stats = player_stats.drop(columns=['Pitcher ID'])
                season_stats = season_stats.reset_index()
                season_stats['Season'] = 'S' + season_stats['Season'].astype(str)
                season_stats = season_stats.merge(player_stats, on='Season', how='left').fillna(0)
                season_stats = season_stats.set_index('Season')
                if not season_stats.empty:
                    season_stats.index = season_stats.index.str.replace('S', '').astype(int)

    # --- OPS+ Calculation for Hitting ---
    if not is_pitching and league_stats_by_season is not None:
        season_stats['OPS+'] = season_stats.apply(calculate_ops_plus_for_row, axis=1, league_stats_by_season=league_stats_by_season)

    career_stats = season_stats.sum(numeric_only=True)
    
    if is_pitching:
        if career_stats['IP'] > 0:
            career_stats['ERA'] = (career_stats['R'] * 6) / career_stats['IP']
            career_stats['WHIP'] = (career_stats['BB'] + career_stats['H']) / career_stats['IP']
        else:
            career_stats['ERA'], career_stats['WHIP'] = 0, 0
        career_stats['Avg Diff'] = pd.to_numeric(df['Diff'], errors='coerce').mean()
        career_stats_df = pd.DataFrame(career_stats).T
        career_stats_df.index = ['Career']
        display_stats_table(pd.concat([season_stats, career_stats_df]), is_pitching=True)
    else: # Hitting
        if career_stats['AB'] > 0:
            career_stats['AVG'] = career_stats['H'] / career_stats['AB']
            career_stats['SLG'] = (career_stats['H'] - career_stats['2B'] - career_stats['3B'] - career_stats['HR'] + career_stats['2B']*2 + career_stats['3B']*3 + career_stats['HR']*4) / career_stats['AB']
        else:
            career_stats['AVG'], career_stats['SLG'] = 0, 0
        if career_stats['PA'] > 0:
            career_stats['OBP'] = (career_stats['H'] + career_stats['BB']) / career_stats['PA']
            # Weighted Career OPS+
            if 'OPS+' in season_stats.columns and season_stats['PA'].sum() > 0:
                career_stats['OPS+'] = (season_stats['OPS+'] * season_stats['PA']).sum() / season_stats['PA'].sum()
        else:
            career_stats['OBP'] = 0
        career_stats['OPS'] = career_stats['OBP'] + career_stats['SLG']
        career_stats['Avg Diff'] = pd.to_numeric(df['Diff'], errors='coerce').mean()
        career_stats_df = pd.DataFrame(career_stats).T
        career_stats_df.index = ['Career']
        display_stats_table(pd.concat([season_stats, career_stats_df]), is_pitching=False)

def process_player_stats(player_id, combined_df, player_id_map, season_games_map, regular_pitcher_stats_agg, playoff_pitcher_stats_agg, league_stats_by_season):
    if player_id not in player_id_map:
        print("Player not found.")
        return

    player_name = player_id_map[player_id]
    print(f"\nStats for: {player_name} (ID: {player_id})")

    # Create a boolean mask for regular season based on the Session number
    season_games_series = combined_df['Season'].map(season_games_map)
    is_regular_season = combined_df['Session'] <= season_games_series

    hitter_df = combined_df[combined_df['Hitter ID'] == player_id]
    pitcher_df = combined_df[combined_df['Pitcher ID'] == player_id]

    if hitter_df.empty and pitcher_df.empty:
        print("No stats found for this player.")
        return

    # Create regular season and playoff dataframes
    regular_hitter_df = hitter_df[is_regular_season.loc[hitter_df.index]]
    # playoff_hitter_df = hitter_df[~is_regular_season.loc[hitter_df.index]]
    regular_pitcher_df = pitcher_df[is_regular_season.loc[pitcher_df.index]]
    # playoff_pitcher_df = pitcher_df[~is_regular_season.loc[pitcher_df.index]]

    # Display all stat blocks
    display_stat_block(regular_hitter_df, is_pitching=False, title="\n--- Hitting Stats ---", league_stats_by_season=league_stats_by_season)
    # display_stat_block(playoff_hitter_df, is_pitching=False, title="\n--- Hitting Stats (Playoffs) ---", league_stats_by_season=league_stats_by_season)
    display_stat_block(regular_pitcher_df, is_pitching=True, title="\n--- Pitching Stats ---", pitcher_stats_agg=regular_pitcher_stats_agg)
    # display_stat_block(playoff_pitcher_df, is_pitching=True, title="\n--- Pitching Stats (Playoffs) ---", pitcher_stats_agg=playoff_pitcher_stats_agg)

# --- Main Application Logic ---
def main():
    print("Loading all season data... (this may take a moment)")
    all_season_data = load_all_seasons()
    if not all_season_data: return
    combined_df = pd.concat([df.assign(Season=season) for season, df in all_season_data.items()], ignore_index=True)

    # Disambiguate Line Outs (LO) from Left Ground Outs (LGO) in modern seasons.
    # Per user feedback, some LOs are incorrectly marked as LGO in Exact Result.
    # We use Old Result == 'LO' to identify and correct them.
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
    
    # Load regular season game counts from gamelogs.txt
    try:
        # The script is in a subfolder, so we go up one level to find gamelogs.txt
        with open('../data/gamelogs.txt', 'r') as f:
            gamelogs_content = f.read()
        season_games_map = {}
        for line in gamelogs_content.splitlines():
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                season_games_map[parts[0]] = int(parts[1])
    except FileNotFoundError:
        print("Warning: gamelogs.txt not found. Cannot apply qualifying minimums for leaderboards.")
        season_games_map = {}

    print("\nData loaded successfully! Welcome to the MLR Scouting Tool.")

    player_name_map = {**combined_df.groupby('Hitter')['Hitter ID'].first().to_dict(), **combined_df.groupby('Pitcher')['Pitcher ID'].first().to_dict()}
    player_id_map = {**combined_df.groupby('Hitter ID')['Hitter'].first().to_dict(), **combined_df.groupby('Pitcher ID')['Pitcher'].first().to_dict()}

    # Pre-calculate all seasonal stats for all players for leaderboard generation
    print("Calculating all player stats for leaderboards (Regular Season only)...")
    
    # For leaderboards, we only use regular season stats.
    season_games_series = combined_df['Season'].map(season_games_map)
    leaderboard_df = combined_df[combined_df['Session'] <= season_games_series]

    hitter_records = []
    for (season, hitter_id), group_df in leaderboard_df.groupby(['Season', 'Hitter ID']):
        stats_series = calculate_hitting_stats(group_df, season=season)
        if stats_series is not None:
            stats_series['Season'] = season
            stats_series['Hitter ID'] = hitter_id
            hitter_records.append(stats_series)
    all_hitting_stats = pd.DataFrame(hitter_records)

    # --- Calculate league-wide neutral stats for OPS+ ---
    league_stats_by_season = {}
    for season in leaderboard_df['Season'].unique():
        season_df = leaderboard_df[leaderboard_df['Season'] == season]
        if not season_df.empty:
            league_totals = calculate_hitting_stats(season_df, season=season)
            league_stats_by_season[season] = {
                'lg_nOBP': league_totals['nOBP'],
                'lg_nSLG': league_totals['nSLG']
            }

    # --- Calculate OPS+ for all players ---
    if not all_hitting_stats.empty:
        all_hitting_stats['OPS+'] = all_hitting_stats.apply(calculate_ops_plus_for_row, axis=1, league_stats_by_season=league_stats_by_season)


    pitcher_records = []
    for (season, pitcher_id), group_df in leaderboard_df.groupby(['Season', 'Pitcher ID']):
        stats_series = calculate_pitching_stats(group_df, season=season)
        if stats_series is not None:
            stats_series['Season'] = season
            stats_series['Pitcher ID'] = pitcher_id
            pitcher_records.append(stats_series)
    all_pitching_stats = pd.DataFrame(pitcher_records)

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
    pitching_decisions_df = pitching_decisions_df.merge(game_types, on=['Season', 'Game ID'])

    regular_season_decisions = pitching_decisions_df[pitching_decisions_df['GameType'] == 'Regular']
    playoff_decisions = pitching_decisions_df[pitching_decisions_df['GameType'] == 'Playoff']

    def aggregate_decisions(df, games_df):
        if df.empty:
            return pd.DataFrame(columns=['Season', 'Pitcher ID', 'W', 'L', 'SV', 'HLD'])

        all_pitchers = games_df['Pitcher ID'].unique()
        all_seasons = df['Season'].unique()
        base_df = pd.DataFrame([(s, p) for s in all_seasons for p in all_pitchers], columns=['Season', 'Pitcher ID'])

        wins_df = df[df['win'].notna()].groupby(['Season', 'win']).size().reset_index(name='W').rename(columns={'win': 'Pitcher ID'})
        losses_df = df[df['loss'].notna()].groupby(['Season', 'loss']).size().reset_index(name='L').rename(columns={'loss': 'Pitcher ID'})
        saves_df = df[df['save'].notna()].groupby(['Season', 'save']).size().reset_index(name='SV').rename(columns={'save': 'Pitcher ID'})
        holds_df = df.explode('holds').dropna().groupby(['Season', 'holds']).size().reset_index(name='HLD').rename(columns={'holds': 'Pitcher ID'})

        for df_stat in [wins_df, losses_df, saves_df, holds_df]:
            if not df_stat.empty:
                df_stat['Pitcher ID'] = df_stat['Pitcher ID'].astype(int)

        agg_df = base_df.merge(wins_df, on=['Season', 'Pitcher ID'], how='left')
        agg_df = agg_df.merge(losses_df, on=['Season', 'Pitcher ID'], how='left')
        agg_df = agg_df.merge(saves_df, on=['Season', 'Pitcher ID'], how='left')
        agg_df = agg_df.merge(holds_df, on=['Season', 'Pitcher ID'], how='left')

        agg_df = agg_df.fillna(0)

        for col in ['W', 'L', 'SV', 'HLD']:
            if col in agg_df.columns:
                agg_df[col] = agg_df[col].astype(int)
        return agg_df

    regular_season_games = combined_df[combined_df['GameType'] == 'Regular']
    playoff_games = combined_df[combined_df['GameType'] == 'Playoff']

    regular_pitcher_stats_agg = aggregate_decisions(regular_season_decisions, regular_season_games)
    playoff_pitcher_stats_agg = aggregate_decisions(playoff_decisions, playoff_games)

    all_pitching_stats = all_pitching_stats.merge(regular_pitcher_stats_agg, on=['Season', 'Pitcher ID'], how='left').fillna(0)

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
                    process_player_stats(player_id, combined_df, player_id_map, season_games_map, regular_pitcher_stats_agg, playoff_pitcher_stats_agg, league_stats_by_season)
                elif command == 'scout':
                    generate_scouting_report(player_id, combined_df, player_id_map)
            else:
                print(f"Player '{identifier}' not found.")
        else:
            print(f"Invalid command. Use 'stats', 'scout', or 'leaderboard'.")

if __name__ == '__main__':
    main()
