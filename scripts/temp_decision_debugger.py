import pandas as pd
import os
import re
from collections import defaultdict

# Assuming game_processing.py and data_loader.py are in the same directory
from game_processing import Game, get_pitching_decisions, _get_outs_from_result
from data_loader import load_all_seasons

def debug_game_decisions(season_name, game_id_to_debug):
    print(f"Loading all season data for debugging {season_name} Game {game_id_to_debug}...")
    all_season_data, _ = load_all_seasons()
    if not all_season_data:
        print("No data found.")
        return

    season_df = all_season_data.get(season_name)
    if season_df is None:
        print(f"Season {season_name} not found.")
        return

    game_df = season_df[season_df['Game ID'] == game_id_to_debug].copy()

    if game_df.empty:
        print(f"Game {game_id_to_debug} in {season_name} not found.")
        return

    print(f"\nDebugging {season_name} Game {game_id_to_debug} play-by-play:")

    game = Game(game_df)
    
    # Manually process the game play-by-play to print intermediate states
    game.df = game.df.reset_index()
    game.df['inning_num'], game.df['is_top'] = zip(*game.df['Inning'].apply(game._parse_inning))
    game.df = game.df.sort_values(by=['inning_num', 'is_top', 'index'], ascending=[True, False, True])

    # Pre-calculate the OBC_after for determining ambiguous plays
    game.df['OBC_after'] = game.df.groupby(['inning_num', 'is_top'])['OBC'].shift(-1).fillna(0).astype(int)

    # Determine home and away teams
    if 'B' in str(game.df['Inning'].iloc[0]):
        game.home_team = game.df.iloc[0]['Batter Team']
        game.away_team = game.df.iloc[0]['Pitcher Team']
    else:
        game.home_team = game.df.iloc[0]['Pitcher Team']
        game.away_team = game.df.iloc[0]['Batter Team']

    game.home_pitcher = game.df[game.df['Pitcher Team'] == game.home_team]['Pitcher ID'].iloc[0]
    game.away_pitcher = game.df[game.df['Pitcher Team'] == game.away_team]['Pitcher ID'].iloc[0]

    # Log initial pitchers
    game.pitching_log.append({
        'pitcher_id': game.home_pitcher,
        'team': game.home_team,
        'home_score_entered': game.home_score,
        'away_score_entered': game.away_score,
        'inning_entered': 1,
        'top_of_inning_entered': True
    })
    game.pitching_log.append({
        'pitcher_id': game.away_pitcher,
        'team': game.away_team,
        'home_score_entered': game.home_score,
        'away_score_entered': game.away_score,
        'inning_entered': 1,
        'top_of_inning_entered': False
    })

    obc_to_runners = {
        0: [False, False, False], 1: [True, False, False], 2: [False, True, False], 3: [False, False, True],
        4: [True, True, False], 5: [True, False, True], 6: [False, True, True], 7: [True, True, True]
    }
    runners_to_obc = {tuple(v): k for k, v in obc_to_runners.items()}

    for idx, play in game.df.iterrows():
        inning_num, is_top = play['inning_num'], play['is_top']

        if game.inning != inning_num or game.top_of_inning != is_top:
            game.outs = 0
            print(f"\n--- Start of Inning {inning_num} {'Top' if is_top else 'Bottom'} ---")

        game.inning = inning_num
        game.top_of_inning = is_top

        current_pitcher_id = play['Pitcher ID']
        current_pitcher_team = play['Pitcher Team']

        # Check for pitcher change and log it
        if current_pitcher_team == game.home_team and current_pitcher_id != game.home_pitcher:
            game.home_pitcher = current_pitcher_id
            game.pitching_log.append({
                'pitcher_id': game.home_pitcher, 'team': game.home_team, 'home_score_entered': game.home_score,
                'away_score_entered': game.away_score, 'inning_entered': game.inning, 'top_of_inning_entered': game.top_of_inning
            })
            print(f"  Pitcher Change (Home): {game.home_pitcher} entered.")
        elif current_pitcher_team == game.away_team and current_pitcher_id != game.away_pitcher:
            game.away_pitcher = current_pitcher_id
            game.pitching_log.append({
                'pitcher_id': game.away_pitcher, 'team': game.away_team, 'home_score_entered': game.home_score,
                'away_score_entered': game.away_score, 'inning_entered': game.inning, 'top_of_inning_entered': game.top_of_inning
            })
            print(f"  Pitcher Change (Away): {game.away_pitcher} entered.")

        score_before = (game.home_score, game.away_score)
        
        runners_before_play = obc_to_runners.get(play['OBC'], [False, False, False])
        current_outs = game.outs
        obc_after = play['OBC_after']
        result = play['Exact Result'] if pd.notna(play['Exact Result']) else play['Old Result']
        diff_val = play.get('Diff')
        if pd.isna(diff_val):
            diff = 0
        else:
            numeric_diff = pd.to_numeric(diff_val, errors='coerce')
            if pd.isna(numeric_diff):
                diff = 0
            else:
                diff = int(numeric_diff)
        
        season = int(play.get('Season', 'S0').replace('S', ''))

        pa_type_val = play.get('PA Type')
        if pd.isna(pa_type_val):
            pa_type = 0
        else:
            numeric_pa_type = pd.to_numeric(pa_type_val, errors='coerce')
            if pd.isna(numeric_pa_type):
                pa_type = 0
            else:
                pa_type = int(numeric_pa_type)

        new_runners, runs_this_play, outs_this_play = game._simulate_play(
            obc_after, runners_before_play, current_outs, result, play['Old Result'], diff, season, pa_type
        )

        game.runners_on_base = new_runners
        if is_top:
            game.away_score += runs_this_play
        else:
            game.home_score += runs_this_play
        game.outs += outs_this_play

        print(f"  Play: {play['Hitter']} - {result}")
        print(f"    Before -> Runners: {runners_before_play}, Outs: {current_outs}")
        print(f"    After  -> Runners: {game.runners_on_base}, Outs: {game.outs}, Runs: {runs_this_play}")
        print(f"    Score: Home {game.home_score}, Away {game.away_score}")
        
        simulated_obc = runners_to_obc.get(tuple(game.runners_on_base), -1)
        gamelog_obc_after = play['OBC_after']
        
        if game.outs < 3 and simulated_obc != gamelog_obc_after:
            print(f"    !!! WARNING: Simulated OBC ({simulated_obc}) does NOT match gamelog OBC for next play ({gamelog_obc_after}) !!!")
        
        if game.outs >= 3:
            game.runners_on_base = [False, False, False]

        if (score_before[0] - score_before[1]) * (game.home_score - game.away_score) <= 0 and (game.home_score != game.away_score):
            game.lead_changes.append({'inning': game.inning, 'top_of_inning': game.top_of_inning, 'home_score': game.home_score, 'away_score': game.away_score, 'home_pitcher': game.home_pitcher, 'away_pitcher': game.away_pitcher})

    final_decisions = get_pitching_decisions(game_df)
    print("\n--- Final Pitching Decisions ---")
    if not final_decisions or final_decisions.get('win') is None or final_decisions.get('loss') is None:
        print("DECISIONS ARE MISSING OR INCOMPLETE")
    
    if final_decisions:
        for key, value in final_decisions.items():
            print(f"  - {key.replace('_', ' ').title()}: {value}")
    else:
        print("  - No decisions dictionary was returned.")

if __name__ == "__main__":
    import sys
    # Default values
    season_name = 'S2'
    game_id_to_debug = 23

    # Check if arguments are provided
    if len(sys.argv) > 1:
        season_name = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            game_id_to_debug = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid game ID '{sys.argv[2]}'. Using default: {game_id_to_debug}")

    debug_game_decisions(season_name, game_id_to_debug)
