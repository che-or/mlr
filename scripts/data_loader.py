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

def load_all_seasons():
    """Loads all seasons' data, adding a 'GameType' column to distinguish regular vs. playoff games."""
    season_data = {}
    with open('../data/gamelogs.txt', 'r') as f:
        gamelogs = f.readlines()

    for log in gamelogs:
        parts = log.strip().split('\t')
        if len(parts) != 3:
            if log.strip():
                print(f"Warning: Skipping malformed line in gamelogs.txt: {log.strip()}")
            continue

        season, num_games_str, url = parts
        try:
            num_games = int(num_games_str)
        except ValueError:
            print(f"Warning: Invalid number of games for season '{season}'. Skipping line.")
            continue

        export_url = get_export_url(url)
        if export_url:
            try:
                print(f"Loading data for {season}...")
                df = pd.read_csv(export_url)
                if 'Session' in df.columns:
                    df['GameType'] = np.where(df['Session'] <= num_games, 'Regular', 'Playoff')
                    print(f"Successfully loaded data for {season} ({len(df)} total PAs).")
                    season_data[season] = df
                else:
                    print(f"Warning: 'Session' column not found for {season}. Cannot determine game type. Skipping season.")
            except Exception as e:
                print(f"Error loading data for {season}: {e}")
        else:
            print(f"Could not generate export URL for {url}")
    return season_data

if __name__ == '__main__':
    # Example usage:
    try:
        import pandas
    except ImportError:
        print("The 'pandas' library is not installed. Please install it using 'pip install pandas'")
        sys.exit(1)
    else:
        all_data = load_all_seasons()
        if all_data:
            print(f"\nSuccessfully loaded data for {len(all_data)} seasons.")
            # For example, print the first 5 rows of Season 5's data
            if 'S5' in all_data:
                print("\nFirst 5 rows of Season 5 data:")
                print(all_data['S5'].head())
