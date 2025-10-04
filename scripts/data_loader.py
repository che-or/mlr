import re
import pandas as pd
import sys

def get_export_url(url):
    """Converts a Google Sheet URL to a CSV export URL, correctly handling the gid."""
    # The gid is often at the end of the URL after #gid=
    match_gid = re.search(r'#gid=(\d+)', url)
    if not match_gid:
        # If not found after #, try to find it as a query parameter
        match_gid = re.search(r'[?&]gid=(\d+)', url)

    gid = match_gid.group(1) if match_gid else None

    # The document ID is between /d/ and /
    match_doc_id = re.search(r'/d/([^/]+)/', url)
    if not match_doc_id:
        return None # Cannot proceed without a document ID
    
    doc_id = match_doc_id.group(1)

    if gid:
        return f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}'
    else:
        # If no GID is found, it will export the first/default sheet.
        print(f"Warning: No GID found for URL {url}. Exporting the default sheet.")
        return f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv'

import numpy as np
import os
import json

# --- Caching Helper Functions ---
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

def load_all_seasons():
    """Loads all seasons' data, adding a 'GameType' column and caching raw downloads."""
    season_data = {}
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gamelogs_path = os.path.join(script_dir, '..', 'data', 'gamelogs.txt')
    cache_dir = os.path.join(script_dir, '..', 'data', 'cache')
    raw_data_cache_dir = os.path.join(cache_dir, 'raw_gamelogs')
    if not os.path.exists(raw_data_cache_dir):
        os.makedirs(raw_data_cache_dir)

    try:
        with open(gamelogs_path, 'r') as f:
            gamelogs = f.readlines()
    except FileNotFoundError:
        print(f"Error: Could not find gamelogs.txt at {gamelogs_path}")
        return None

    # Determine season transition for cache invalidation
    previous_most_recent = _read_cache_manifest(cache_dir)
    season_lines = [line.strip().split('\t') for line in gamelogs if line.strip()]
    all_season_names = [parts[0] for parts in season_lines if len(parts) > 0]
    if all_season_names:
        most_recent_season_num = max([int(s.replace('S', '')) for s in all_season_names])
        most_recent_season = f"S{most_recent_season_num}"
    else:
        most_recent_season = ""

    seasons_to_recalc = []
    if most_recent_season != previous_most_recent and previous_most_recent is not None:
        print(f"New season detected. Invalidating raw data cache for {previous_most_recent}...")
        seasons_to_recalc.append(previous_most_recent)

    for log in gamelogs:
        parts = log.strip().split('\t')
        if len(parts) != 3:
            continue

        season, num_games_str, url = parts
        force_recalc = (season == most_recent_season) or (season in seasons_to_recalc)
        raw_cache_path = os.path.join(raw_data_cache_dir, f'raw_gamelog_{season}.csv')

        df = None
        if os.path.exists(raw_cache_path) and not force_recalc:
            try:
                df = pd.read_csv(raw_cache_path)
                print(f"Loaded {season} data from local cache.")
            except Exception as e:
                print(f"Error loading {season} from cache: {e}. Re-downloading...")
                df = None

        if df is None:
            export_url = get_export_url(url)
            if export_url:
                try:
                    print(f"Downloading data for {season}...")
                    df = pd.read_csv(export_url)
                    df.to_csv(raw_cache_path, index=False)
                except Exception as e:
                    print(f"Error loading data for {season} from URL: {e}")
                    continue
            else:
                print(f"Could not generate export URL for {url}")
                continue
        
        if df is not None:
            try:
                num_games = int(num_games_str)
                if 'Session' in df.columns:
                    df['GameType'] = np.where(df['Session'] <= num_games, 'Regular', 'Playoff')
                    season_data[season] = df
                else:
                    print(f"Warning: 'Session' column not found for {season}.")
            except ValueError:
                print(f"Warning: Invalid number of games for season '{season}'.")

    _write_cache_manifest(cache_dir, most_recent_season)
    return season_data, most_recent_season

if __name__ == '__main__':
    # Example usage:
    try:
        import pandas
    except ImportError:
        print("The 'pandas' library is not installed. Please install it using 'pip install pandas'")
        sys.exit(1)
    else:
        all_data, _ = load_all_seasons()
        if all_data:
            print(f"\nSuccessfully loaded data for {len(all_data)} seasons.")
            # For example, print the first 5 rows of Season 5's data
            if 'S5' in all_data:
                print("\nFirst 5 rows of Season 5 data:")
                print(all_data['S5'].head())
