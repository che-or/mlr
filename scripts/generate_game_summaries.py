import os
import pandas as pd
import sys

# Add scripts directory to sys.path to allow module imports
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from data_loader import load_all_seasons
from game_processing import get_pitching_decisions, Game

def generate_summaries_for_league(gamelog_source, output_prefix):
    """
    Loads all data for a league, calculates game summaries, and saves to a CSV.

    Args:
        gamelog_source (str): Path to the league's gamelog file.
        output_prefix (str): Prefix for the output CSV file (e.g., 'mlr_').
    """
    print(f"--- Generating game summaries for {output_prefix.upper().strip('_')} ---")

    # The data loader uses a cache, which is fine. We can ignore the other return values.
    all_season_data, _, _ = load_all_seasons(
        gamelog_file_path=gamelog_source, cache_prefix=output_prefix
    )

    if not all_season_data:
        print(f"No season data found for {gamelog_source}. Aborting.")
        return

    all_game_summaries = []
    for season, season_df in all_season_data.items():
        if season_df.empty or "Session" not in season_df.columns:
            continue

        print(f"Processing {season}...")
        for game_id, game_df in season_df.groupby("Game ID"):
            try:
                # Use the Game class to simulate the game and get the final score
                game = Game(game_df.copy(), season)
                game.process_game()
                
                # Get pitching decisions
                decisions = get_pitching_decisions(game_df.copy(), season)

                all_game_summaries.append(
                    {
                        "season": season,
                        "game_id": game_id,
                        "home_team": game.home_team,
                        "away_team": game.away_team,
                        "home_score": game.home_score,
                        "away_score": game.away_score,
                        "winning_pitcher": decisions.get("win"),
                        "losing_pitcher": decisions.get("loss"),
                        "save_pitcher": decisions.get("save"),
                        "holds": ",".join(map(str, decisions.get("holds", []))),
                    }
                )
            except Exception as e:
                print(f"  - Error processing game {game_id} in {season}: {e}")

    if not all_game_summaries:
        print("No game summaries generated.")
        return

    game_summaries_df = pd.DataFrame(all_game_summaries)
    output_dir = os.path.join(script_dir, "..", "docs", "data")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, f"{output_prefix}game_summaries.csv")
    game_summaries_df.to_csv(output_path, index=False)
    print(f"Game summaries successfully saved to {output_path}")

def main():
    """
    Main function to generate game summaries for all leagues.
    """
    # Generate MLR data
    generate_summaries_for_league(
        gamelog_source="data/mlr_gamelogs.txt",
        output_prefix="mlr_",
    )

    # Generate MiLR data
    generate_summaries_for_league(
        gamelog_source="data/milr_gamelogs.txt",
        output_prefix="milr_",
    )
    
    # Generate FCB data
    generate_summaries_for_league(
        gamelog_source="data/fcb_gamelogs.txt",
        output_prefix="fcb_",
    )

if __name__ == "__main__":
    main()
