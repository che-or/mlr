import pandas as pd
from game_processing import Game
from data_loader import load_all_seasons
from gamelog_corrections import apply_gamelog_corrections

def print_scores_for_season(season_name):
    """
    Processes all games for a given season and prints the final score for each.
    """
    print(f"Loading all season data to print scores for {season_name}...")
    all_season_data, _ = load_all_seasons()
    if not all_season_data:
        print("No data found.")
        return

    season_df = all_season_data.get(season_name)
    if season_df is None:
        print(f"Season {season_name} not found.")
        return

    game_ids = season_df['Game ID'].unique()
    print(f"Found {len(game_ids)} games in {season_name}.")

    for game_id in game_ids:
        game_df = season_df[season_df['Game ID'] == game_id].copy()
        if game_df.empty:
            continue

        group_name = (season_name, game_id)
        game_df = apply_gamelog_corrections(game_df, group_name)

        game = Game(game_df, season_name)
        game.process_game()

        winner = game.home_team if game.home_score > game.away_score else game.away_team
        
        print(f"Game {game_id}: {game.away_team} at {game.home_team}")
        print(f"  Final Score: {game.away_score} - {game.home_score}")
        print(f"  Winner: {winner}\n")

if __name__ == "__main__":
    import sys
    season_to_process = 'S2'  # Default season

    if len(sys.argv) > 1:
        season_to_process = sys.argv[1]

    print_scores_for_season(season_to_process)
