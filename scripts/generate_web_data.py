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
    if row['PA'] == 0: return pd.NA
    if 'Season' in row.index: season_name = row['Season']
    else: season_name = f"S{row.name}"
    season_stats = league_stats_by_season.get(season_name)
    if not season_stats or season_stats['lg_nOBP'] == 0 or season_stats['lg_nSLG'] == 0: return 100
    player_nobp, player_nslg = row['nOBP'], row['nSLG']
    if pd.isna(player_nobp) or pd.isna(player_nslg): return 100
    ops_plus = 100 * ((player_nobp / season_stats['lg_nOBP']) + (player_nslg / season_stats['lg_nSLG']) - 1)
    if pd.isna(ops_plus): return 100
    return int(round(ops_plus))

# --- Stat Calculation Functions (similar to scouting_tool.py) ---
def calculate_hitting_stats(df, season=None):
    if df.empty: return None
    if season is None: season = df.name
    use_old_results = season in ['S2', 'S3']
    result_col = 'Old Result' if use_old_results else 'Exact Result'
    hits = {'1B', '2B', '3B', 'HR'} if use_old_results else {'1B', '2B', '3B', 'HR', 'BUNT 1B'}
    walks = {'BB', 'IBB', 'Auto BB'} if use_old_results else {'BB', 'IBB', 'Auto BB', 'AUTO BB'}
    strikeouts = {'K', 'Auto K'} if use_old_results else {'K', 'Auto K', 'Bunt K', 'AUTO K'}
    stolen_bases = {'SB'} if use_old_results else {'STEAL 2B', 'STEAL 3B', 'Steal 2B', 'Steal 3B'}
    caught_stealing = {'CS'} if use_old_results else {'CS 2B', 'CS 3B', 'CS Home'}
    pa_events = hits | walks | strikeouts | ({'FO', 'PO', 'LGO', 'RGO', 'LO', 'DP', 'TP', 'Sac', 'Bunt'} if use_old_results else {'FO', 'PO', 'LGO', 'RGO', 'LO', 'BUNT DP', 'BUNT GO', 'BUNT Sac', 'Bunt Sac'})
    
    diff_events = pa_events | stolen_bases | caught_stealing
    diff_df = df[df[result_col].isin(diff_events)]
    numeric_diff = pd.to_numeric(diff_df['Diff'], errors='coerce')
    avg_diff = numeric_diff.mean()
    num_sb = df[df[result_col].isin(stolen_bases)].shape[0]
    num_cs = df[df[result_col].isin(caught_stealing)].shape[0]
    pa_df = df[df[result_col].isin(pa_events)]
    pa = len(pa_df)
    if pa == 0: return pd.Series({'G': df['Session'].nunique(), 'PA': 0, 'AB': 0, 'H': 0, 'R': 0, 'RBI': 0, '2B': 0, '3B': 0, 'HR': 0, 'BB': 0, 'K': 0, 'SB': num_sb, 'CS': num_cs, 'AVG': 0, 'OBP': 0, 'SLG': 0, 'OPS': 0, 'Avg Diff': avg_diff, 'nOBP': 0, 'nSLG': 0})
    
    games_played = df['Session'].nunique()
    num_walks = pa_df[pa_df[result_col].isin(walks)].shape[0]
    num_sacrifices = pa_df[pa_df['Old Result'] == 'Sac'].shape[0]
    ab = pa - num_walks - num_sacrifices
    num_hits = pa_df[pa_df[result_col].isin(hits)].shape[0]
    num_doubles = pa_df[pa_df[result_col] == '2B'].shape[0]
    num_triples = pa_df[pa_df[result_col] == '3B'].shape[0]
    num_hr = pa_df[pa_df[result_col] == 'HR'].shape[0]
    num_singles = pa_df[pa_df[result_col] == '1B'].shape[0]
    if not use_old_results: num_singles += pa_df[pa_df[result_col] == 'BUNT 1B'].shape[0]
    num_strikeouts = pa_df[pa_df[result_col].isin(strikeouts)].shape[0]
    runs_scored = df['Run'].sum()
    rbi = df['RBI'].sum()
    nOBP = (num_hits + num_walks) / pa if pa > 0 else 0
    nSLG = (num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0
    
    # Simplified nOBP/nSLG calculation for brevity
    return pd.Series({'G': games_played, 'PA': pa, 'AB': ab, 'H': num_hits, 'R': runs_scored, '2B': num_doubles, '3B': num_triples, 'HR': num_hr, 'RBI': rbi, 'BB': num_walks, 'K': num_strikeouts, 'SB': num_sb, 'CS': num_cs, 'AVG': num_hits / ab if ab > 0 else 0, 'OBP': (num_hits + num_walks) / pa if pa > 0 else 0, 'SLG': (num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0, 'OPS': ((num_hits + num_walks) / pa if pa > 0 else 0) + ((num_singles + num_doubles * 2 + num_triples * 3 + num_hr * 4) / ab if ab > 0 else 0), 'Avg Diff': avg_diff, 'nOBP': nOBP, 'nSLG': nSLG})

def calculate_pitching_stats(df, season=None):
    if df.empty: return None
    if season is None: season = df.name
    use_old_results = season in ['S2', 'S3']
    result_col = 'Old Result' if use_old_results else 'Exact Result'
    hits_allowed = {'1B', '2B', '3B', 'HR'} if use_old_results else {'1B', '2B', '3B', 'HR', 'BUNT 1B'}
    walks_allowed = {'BB', 'IBB', 'Auto BB'} if use_old_results else {'BB', 'IBB', 'Auto BB', 'AUTO BB'}
    ibb_events = {'IBB'}
    strikeouts = {'K', 'Auto K'} if use_old_results else {'K', 'Auto K', 'Bunt K', 'AUTO K'}
    hr_allowed = {'HR'}
    single_out_bip = {'FO', 'LGO', 'PO', 'RGO', 'Bunt', 'LO'} if use_old_results else {'FO', 'LGO', 'PO', 'RGO', 'LO', 'BUNT GO', 'Bunt GO', 'BUNT Sac', 'Bunt Sac'}
    caught_stealing = {'CS'} if use_old_results else {'CS 2B', 'CS 3B', 'CS Home'}
    stolen_bases = {'SB'} if use_old_results else {'STEAL 2B', 'STEAL 3B', 'Steal 2B', 'Steal 3B'}
    
    pitching_pa_events = hits_allowed | walks_allowed | strikeouts | single_out_bip | {'DP', 'TP', 'Sac'}
    diff_events = pitching_pa_events | stolen_bases | caught_stealing
    diff_df = df[df[result_col].isin(diff_events)] if use_old_results else pd.concat([df[df['Exact Result'].isin(hits_allowed | walks_allowed | strikeouts | single_out_bip | {'BUNT DP'} | stolen_bases | caught_stealing)], df[df['Old Result'].isin(['DP', 'TP'])]]).drop_duplicates()
    avg_diff = pd.to_numeric(diff_df['Diff'], errors='coerce').mean()
    
    num_bf = df[df[result_col].isin(pitching_pa_events)].shape[0] if use_old_results else pd.concat([df[df['Exact Result'].isin(hits_allowed | walks_allowed | strikeouts | single_out_bip | {'BUNT DP'})], df[df['Old Result'].isin(['DP', 'TP'])]]).drop_duplicates().shape[0]
    
    games_played = df['Session'].nunique()
    num_hits_allowed = df[df[result_col].isin(hits_allowed)].shape[0]
    num_walks_allowed = df[df[result_col].isin(walks_allowed)].shape[0]
    num_ibb = df[df[result_col].isin(ibb_events)].shape[0]
    num_strikeouts = df[df[result_col].isin(strikeouts)].shape[0]
    num_hr_allowed = df[df[result_col].isin(hr_allowed)].shape[0]
    
    dp_outs = df[df['Old Result'] == 'DP'].shape[0] * 2
    tp_outs = df[df['Old Result'] == 'TP'].shape[0] * 3
    non_dp_tp_df = df[~df['Old Result'].isin(['DP', 'TP'])]
    k_outs = non_dp_tp_df[non_dp_tp_df[result_col].isin(strikeouts)].shape[0]
    other_single_outs = non_dp_tp_df[non_dp_tp_df[result_col].isin(single_out_bip)].shape[0]
    cs_outs = non_dp_tp_df[non_dp_tp_df[result_col].isin(caught_stealing)].shape[0]
    total_outs = dp_outs + tp_outs + k_outs + other_single_outs + cs_outs
    ip = total_outs / 3
    runs_allowed = df['Run'].sum()
    
    return pd.Series({'G': games_played, 'IP': ip, 'BF': num_bf, 'H': num_hits_allowed, 'R': runs_allowed, 'BB': num_walks_allowed, 'IBB': num_ibb, 'K': num_strikeouts, 'HR': num_hr_allowed, 'ERA': (runs_allowed * 6) / ip if ip > 0 else 0, 'WHIP': (num_walks_allowed + num_hits_allowed) / ip if ip > 0 else 0, 'Avg Diff': avg_diff})

def calculate_game_achievements(df):
    achievements = []
    for (season, game_id), game_df in df.groupby(['Season', 'Game ID']):
        teams_in_game = game_df['Batter Team'].unique()
        if len(teams_in_game) != 2: continue
        team_A, team_B = teams_in_game[0], teams_in_game[1]
        runs_A = game_df[game_df['Batter Team'] == team_A]['Run'].sum()
        runs_B = game_df[game_df['Batter Team'] == team_B]['Run'].sum()
        pitchers_A = game_df[game_df['Pitcher Team'] == team_A]['Pitcher ID'].unique().tolist()
        pitchers_B = game_df[game_df['Pitcher Team'] == team_B]['Pitcher ID'].unique().tolist()
        
        if pitchers_A:
            starter_id_A = game_df[game_df['Pitcher Team'] == team_A]['Pitcher ID'].iloc[0]
            achievements.append({'Season': season, 'Pitcher ID': starter_id_A, 'Stat': 'GS'})
            finisher_id_A = game_df[game_df['Pitcher Team'] == team_A]['Pitcher ID'].iloc[-1]
            achievements.append({'Season': season, 'Pitcher ID': finisher_id_A, 'Stat': 'GF'})
            if len(pitchers_A) == 1:
                achievements.append({'Season': season, 'Pitcher ID': pitchers_A[0], 'Stat': 'CG'})
                if runs_B == 0: achievements.append({'Season': season, 'Pitcher ID': pitchers_A[0], 'Stat': 'SHO'})
        if pitchers_B:
            starter_id_B = game_df[game_df['Pitcher Team'] == team_B]['Pitcher ID'].iloc[0]
            achievements.append({'Season': season, 'Pitcher ID': starter_id_B, 'Stat': 'GS'})
            finisher_id_B = game_df[game_df['Pitcher Team'] == team_B]['Pitcher ID'].iloc[-1]
            achievements.append({'Season': season, 'Pitcher ID': finisher_id_B, 'Stat': 'GF'})
            if len(pitchers_B) == 1:
                achievements.append({'Season': season, 'Pitcher ID': pitchers_B[0], 'Stat': 'CG'})
                if runs_A == 0: achievements.append({'Season': season, 'Pitcher ID': pitchers_B[0], 'Stat': 'SHO'})
    
    if not achievements: return pd.DataFrame(columns=['Season', 'Pitcher ID', 'GS', 'GF', 'CG', 'SHO'])
    agg_df = pd.DataFrame(achievements).groupby(['Season', 'Pitcher ID', 'Stat']).size().unstack(fill_value=0).reset_index()
    for col in ['GS', 'GF', 'CG', 'SHO']:
        if col not in agg_df.columns: agg_df[col] = 0
    return agg_df[['Season', 'Pitcher ID', 'GS', 'GF', 'CG', 'SHO']]

# --- Scouting Report Data Generation ---
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

# Main data processing and export function
def main():
    print("Loading all season data...")
    all_season_data, most_recent_season = load_all_seasons()
    if not all_season_data: return
    combined_df = pd.concat([df.assign(Season=season) for season, df in all_season_data.items()], ignore_index=True)

    # --- Data Cleaning & Prep ---
    is_modern_season = ~combined_df['Season'].isin(['S2', 'S3'])
    lo_mask = (combined_df['Exact Result'] == 'LGO') & (combined_df['Old Result'] == 'LO')
    combined_df.loc[is_modern_season & lo_mask, 'Exact Result'] = 'LO'
    for col in ['RBI', 'Run', 'Pitcher ID', 'Hitter ID']:
        combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').fillna(0).astype(int)

    # --- Mappings & Game Info ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gamelogs_path = os.path.join(script_dir, '..', 'data', 'gamelogs.txt')
        with open(gamelogs_path, 'r') as f: gamelogs_content = f.read()
        season_games_map = {parts[0]: int(parts[1]) for line in gamelogs_content.splitlines() if len(parts := line.strip().split('	')) >= 2}
    except FileNotFoundError:
        season_games_map = {}
    player_id_map = {**combined_df.groupby('Hitter ID')['Hitter'].first().to_dict(), **combined_df.groupby('Pitcher ID')['Pitcher'].first().to_dict()}
    
    # --- Caching & Recalculation Logic ---
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'cache')
    previous_most_recent = _read_cache_manifest(cache_dir)
    seasons_to_recalc = []
    if most_recent_season != previous_most_recent and previous_most_recent is not None:
        seasons_to_recalc.append(previous_most_recent)
    
    print("Calculating all player stats...")
    season_games_series = combined_df['Season'].map(season_games_map)
    leaderboard_df = combined_df[combined_df['Session'] <= season_games_series]
    sorted_seasons = sorted(leaderboard_df['Season'].unique(), key=lambda s: int(s.replace('S', '')))

    # --- Pre-calculation for Pitching ---
    pitching_decisions = [d for _, game_df in combined_df.groupby(['Season', 'Game ID']) if (d := get_pitching_decisions(game_df)) is not None]
    pitching_decisions_df = pd.DataFrame(pitching_decisions)
    # Simplified decision aggregation
    regular_pitcher_stats_agg = pd.DataFrame() # Placeholder
    game_achievements_df = calculate_game_achievements(leaderboard_df)

    # --- Main Processing Loop ---
    all_seasons_hitting_stats = []
    all_seasons_pitching_stats = []
    for season in sorted_seasons:
        force_recalc = (season == most_recent_season) or (season in seasons_to_recalc)
        season_leaderboard_df = leaderboard_df[leaderboard_df['Season'] == season]

        # --- Hitting Stats ---
        hitting_cache_path = os.path.join(cache_dir, f'hitting_stats_{season}.csv')
        if os.path.exists(hitting_cache_path) and not force_recalc:
            season_hitting_stats = pd.read_csv(hitting_cache_path)
        else:
            hitter_records = []
            for (hitter_id), group_df in season_leaderboard_df.groupby('Hitter ID'):
                stats_series = calculate_hitting_stats(group_df, season=season)
                if stats_series is not None:
                    stats_series['Season'] = season
                    stats_series['Hitter ID'] = hitter_id
                    hitter_records.append(stats_series)
            season_hitting_stats = pd.DataFrame(hitter_records)
            if not season_hitting_stats.empty: season_hitting_stats.to_csv(hitting_cache_path, index=False)
        all_seasons_hitting_stats.append(season_hitting_stats)

        # --- Pitching Stats ---
        pitching_cache_path = os.path.join(cache_dir, f'pitching_stats_{season}.csv')
        if os.path.exists(pitching_cache_path) and not force_recalc:
            season_pitching_stats = pd.read_csv(pitching_cache_path)
        else:
            pitcher_records = []
            for (pitcher_id), group_df in season_leaderboard_df.groupby('Pitcher ID'):
                stats_series = calculate_pitching_stats(group_df, season=season)
                if stats_series is not None:
                    stats_series['Season'] = season
                    stats_series['Pitcher ID'] = pitcher_id
                    pitcher_records.append(stats_series)
            season_pitching_stats = pd.DataFrame(pitcher_records)

            if not season_pitching_stats.empty:
                # Merge all additional stats for the season before caching
                season_achievements = game_achievements_df[game_achievements_df['Season'] == season]
                if not season_achievements.empty: season_pitching_stats = season_pitching_stats.merge(season_achievements, on=['Season', 'Pitcher ID'], how='left')
                season_pitching_stats.to_csv(pitching_cache_path, index=False)
        all_seasons_pitching_stats.append(season_pitching_stats)

    # --- Final Assembly & Calculations ---
    all_hitting_stats = pd.concat(all_seasons_hitting_stats, ignore_index=True).fillna(0)
    all_pitching_stats = pd.concat(all_seasons_pitching_stats, ignore_index=True).fillna(0)
    
    league_stats_by_season = {season: {'lg_nOBP': totals['nOBP'], 'lg_nSLG': totals['nSLG']} for season in leaderboard_df['Season'].unique() if not (season_df := leaderboard_df[leaderboard_df['Season'] == season]).empty and (totals := calculate_hitting_stats(season_df, season=season)) is not None}
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
