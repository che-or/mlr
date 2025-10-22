import pandas as pd
import os
from data_loader import load_all_seasons
from game_processing import get_pitching_decisions

def find_missing_pitcher_decisions():
    """
    This script loads all season data, calculates pitching decisions for each game,
    and identifies games where pitcher decisions (win, loss) are missing.
    """
    print("Loading all season data...")
    all_season_data, _ = load_all_seasons()
    if not all_season_data:
        print("No data found.")
        return

    print("Processing games to find missing pitcher decisions...")
    combined_df = pd.concat([df.assign(Season=season) for season, df in all_season_data.items()], ignore_index=True)

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gamelogs_path = os.path.join(script_dir, '..', 'data', 'gamelogs.txt')
        with open(gamelogs_path, 'r') as f: gamelogs_content = f.read()
        season_games_map = {parts[0]: int(parts[1]) for line in gamelogs_content.splitlines() if len(parts := line.strip().split('\t')) >= 2}
    except FileNotFoundError:
        print("Warning: gamelogs.txt not found. Cannot filter for regular season games.")
        season_games_map = {}

    if season_games_map:
        season_games_series = combined_df['Season'].map(season_games_map)
        combined_df = combined_df[combined_df['Session'] <= season_games_series].copy()
        print(f"Filtered to {len(combined_df.groupby(['Season', 'Game ID']))} regular season games.")

    missing_decision_games = []

    game_groups = list(combined_df.groupby(['Season', 'Game ID']))
    num_games = len(game_groups)

    for i, ((season, game_id), game_df) in enumerate(game_groups):
        if (i + 1) % 100 == 0:
            print(f"  ... processed {i + 1} / {num_games} games")

        decisions = get_pitching_decisions(game_df)

        # Check if decisions are missing
        if not decisions or decisions.get('win') is None or decisions.get('loss') is None:
            missing_decision_games.append((season, game_id))

    if missing_decision_games:
        print("\nGames with missing pitcher decisions found:")
        for season, game_id in missing_decision_games:
            print(f"  - Season: {season}, Game ID: {game_id}")
    else:
        print("\nNo games with missing pitcher decisions found.")

if __name__ == "__main__":
    find_missing_pitcher_decisions()
