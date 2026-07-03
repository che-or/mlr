import pandas as pd
from simulate_runners import _simulate_runners

def manfred_runner_row(play, prev_play, base, obc_value, pa_value):
    '''
    Function for adding Manfred Runner rows to gamelogs
        play - df row of first real play of inning
        prev_play - df row of Manfred Runner's previous plate appearance (in the inning prior)
        base - base to place the Manfred Runner on
        obc_value - OBC before the Manfred Runner
        pa_value - position in the inning, used for ordering. Because the runners start on base, use negative numbers

    Output: df row for placing a Manfred Runner on base. Result column will be MR1, MR2, or MR3 (depending on which base the runner is placed on)
    '''
    
    new_row = play.copy()
    new_row['Hitter'] = prev_play['Hitter']
    new_row['Hitter ID'] = prev_play['Hitter ID']

    # These columns should be left blank for Manfred Runners
    cols_to_clear = ['Swing', 'Pitcher', 'Pitcher ID', 'Pitch', 
                     'Diff', 'Batter WPA', 'Pitcher WPA']
    for col in cols_to_clear:
        new_row[col] = None

    # Result columns should identify the row as a Manfred Runner (with the base)
    mr_cols = ['Old Result', 'Exact Result', 'Result at Neutral', 'Result All Neutral']
    for col in mr_cols:
        new_row[col] = f'MR{base}'

    new_row['RBI'] = 0 # No RBIs for Manfred Runners
    new_row['Run'] = 0 # Assume Manfred Runner doesn't score. This will be corrected later in the pipeline if necessary.
    new_row['Outs'] = 0 # Manfred Runners place before inning begins
    new_row['PA Type'] = 0 # Use PA Type 0 to identify Manfred Runners
    new_row['OBC'] = obc_value
    new_row['PA of Inning'] = pa_value

    return new_row    


def trailing_multisteal_row(play, runner_id, base, outs, obc_value, pa_value):
    '''
    Function for adding stolen base rows for trailing runners on multisteal attempts to gamelogs.
    This will make it much easier to correctly count stolen bases
        play - df row of multisteal
        runner_id - player ID for trailing runner
        base - base the trailing runner steals
        outs - number of outs before play. This will be the same as in the multisteal row if multisteal was successful, otherwise 1 more
        obc_value - OBC before the trailing runner steals (but after the lead runner(s))
        pa_value - position in the inning, used for ordering. Because multisteals happen mid-inning, assign decimal values to avoid having to reindex inning

    Output: df row for trailing runner stealing on a multisteal. Will either be STEAL 2B or STEAL 3B as trailing runners are always successful on multisteal

    !IMPORTANT! The output of this function has the wrong name in the 'Hitter' column. This must be fixed later on.
    '''
    
    new_row = play.copy()
    new_row['Hitter ID'] = runner_id

    # These columns should be left blank
    cols_to_clear = ['Swing', 'Pitch', 'Diff', 'Batter WPA', 'Pitcher WPA']
    for col in cols_to_clear:
        new_row[col] = None

    # set the Old Result to SB and the other results to specify which base was stolen
    new_row['Old Result'] = 'SB'
    result_cols = ['Exact Result', 'Result at Neutral', 'Result All Neutral']
    for col in result_cols:
        new_row[col] = f'STEAL {base}B'

    new_row['Outs'] = outs
    new_row['PA Type'] = 15 # Define PA Type 15 as trailing runner on multisteal
    new_row['OBC'] = obc_value
    new_row['PA of Inning'] = pa_value

    return new_row


def _runner_attribution(gamelog_df):
    '''
    Function that expands gamelogs for easier stat calculations. This function:
        1. Creates rows for Manfred Runners. These rows are given PA Type = 0
        2. Tracks whether Manfred Runners score
        3. Creates rows for trailing runners during multisteals. These rows are given PA Type = 15
        4. Identifies pinch runners and properly reassigns runs scored to them if applicable
    '''
    
    gamelog_df['PA of Inning'] = gamelog_df.groupby(['Game ID', 'Inning ID']).cumcount()

    updated_games = []

    for game_id, game_df in gamelog_df.groupby(['Season', 'Game ID']):
        game_df = game_df.sort_values(by = ['Inning', 'PA of Inning']).copy()
    
    # ----- MANFRED RUNNERS -----
        new_rows_for_game = []
            
        valid_prev_plays_all = game_df[~game_df['PA Type'].isin([4, 5, 6])] # filter out stolen base attempts
    
        # Manfred Runners based on OBC, in form OBC: list of (base, offset, obc_value, pa_value)
        manfred_patterns = {
            2: [(2, -1, 0, -1)],
            6: [(3, -2, 0, -2), (2, -1, 3, -1)],
            7: [(3, -3, 0, -3), (2, -2, 3, -2), (1, -1, 6, -1)]
        }
    
        for inning, inning_df in game_df.groupby('Inning'):
            current_row = inning_df.iloc[0]
            obc = current_row['OBC']
            inning_id = current_row['Inning ID']
        
            # Handle Manfred Runners
            if obc in manfred_patterns:
                # Find valid previous plays from the last two innings
                # It is necessary to do it for the last two innings to account for potential outs on the basepaths
                valid_prev_plays = valid_prev_plays_all[valid_prev_plays_all['Inning ID'].isin([inning_id - 2, inning_id - 4])]
                
                for base, offset, obc_value, pa_value in manfred_patterns[obc]:
                    prev_play = valid_prev_plays.iloc[offset]
                    runner_id = prev_play['Hitter ID']
    
                    new_row = manfred_runner_row(current_row, prev_play, base, obc_value, pa_value)
                    new_rows_for_game.append(new_row)
    
        # Add new rows to dataframe
        if new_rows_for_game:
            new_rows_df = pd.DataFrame(new_rows_for_game)
            game_df = pd.concat([new_rows_df, game_df], ignore_index = True)
    
        game_df = game_df.sort_values(by = ['Inning ID', 'PA of Inning']).reset_index(drop = True)
        
    
    #-----MANFRED RUNNER SCORES-----
    # !CAUTION! This step must be processed before gamelogs are altered for multisteals
        if len(game_df[game_df['PA Type'] == 0]) > 0: # find games with Manfred Runners
            for inning, inning_df in game_df.groupby('Inning'):
                if len(inning_df[inning_df['PA Type'] == 0]) > 0: # find innings with Manfred Runners
                    manfred_idx = inning_df.index[inning_df['PA Type'] == 0].tolist() # indices of Manfred Runners
                    manfred_runners = inning_df.loc[inning_df['PA Type'] == 0, 'Hitter ID'].tolist() # player IDs of Manfred Runners
                    runs_this_inning = []
    
                    # simulate the entire inning
                    runners = [None, None, None]
                    for idx, row in inning_df.iterrows():
                        hitter_id = row['Hitter ID']
                        exact_result = row['Exact Result']
                        outs = row['Outs']
                        pa_type = row['PA Type']
                        diff = row['Diff']
                        season = row['Season']
    
                        play_outcome = _simulate_runners(runners, outs, exact_result, diff, season, pa_type, hitter_id)
                        runners = play_outcome['runners']
                        if play_outcome['runs']: # collect player IDs of all players who scored in the inning
                            runs_this_inning.extend(play_outcome['runs'])
    
                    for i in range(len(manfred_runners)):
                        if manfred_runners[i] in runs_this_inning: # if a Manfred Runner scores, credit them with a run scored
                            run_idx = manfred_idx[i]
                            game_df.loc[run_idx, 'Run'] = 1
                        else:
                            continue
    
    
    # ----- MULTISTEALS -----
        new_rows_for_game = []
        
        if len(game_df[game_df['PA Type'] == 6]) > 0: # find games with multisteals
            for inning, inning_df in game_df.groupby('Inning'):
                if len(inning_df[inning_df['PA Type'] == 6]) > 0: # find innings with multisteals
                    multisteal_idx = inning_df.index[inning_df['PA Type'] == 6].tolist()
                    for idx in multisteal_idx: # find indices of multisteals
                        pre_multisteal = inning_df[inning_df.index < idx]
                        multisteal_play = inning_df.loc[idx]
                            
                        # simulate the inning up until the multisteal
                        runners = [None, None, None]
                        for idx2, row in pre_multisteal.iterrows():
                            hitter_id = row['Hitter ID']
                            exact_result = row['Exact Result']
                            outs = row['Outs']
                            pa_type = row['PA Type']
                            diff = row['Diff']
                            season = row['Season']
    
                            play_outcome = _simulate_runners(runners, outs, exact_result, diff, season, pa_type, hitter_id)
                            runners = play_outcome['runners']
                            
                        # Create a dataframe row for trailing runners
                        obc = multisteal_play['OBC']
                        outs = multisteal_play['Outs'] + play_outcome['outs']
                        pa_of_inning = multisteal_play['PA of Inning']
                        if outs < 3:
                            if obc == 4:
                                new_row = trailing_multisteal_row(multisteal_play, runners[0], 2, outs, 5, pa_of_inning + 0.1)
                            elif obc == 5:
                                new_row = trailing_multisteal_row(multisteal_play, runners[0], 2, outs, 1, pa_of_inning + 0.1)
                            elif obc == 6:
                                new_row = trailing_multisteal_row(multisteal_play, runners[1], 3, outs, 2, pa_of_inning + 0.1)
                            elif obc == 7:
                                new_row = trailing_multisteal_row(multisteal_play, runners[1], 3, outs, 4, pa_of_inning + 0.1)
                                new_row = trailing_multisteal_row(multisteal_play, runners[0], 2, outs, 5, pa_of_inning + 0.2)
    
                            # Correct the hitter name in the new row
                            new_row['Hitter'] = pre_multisteal[pre_multisteal['Hitter ID'] == new_row['Hitter ID']].iloc[0]['Hitter']
                            new_rows_for_game.append(new_row)
    
        # Add new rows to dataframe
        if new_rows_for_game:
            new_rows_df = pd.DataFrame(new_rows_for_game)
            game_df = pd.concat([new_rows_df, game_df], ignore_index = True)
            
        game_df = game_df.sort_values(by = ['Inning ID', 'PA of Inning']).reset_index(drop = True)
    
        
    #-----PINCH RUNNERS-----
        if len(game_df[game_df['PA Type'].isin([4, 5, 6])]) > 0: # find games with steals
            for inning, inning_df in game_df.groupby('Inning'):
                if len(inning_df[inning_df['PA Type'].isin([4, 5, 6])]) > 0: # find innings with steals
                    steal_idx = inning_df.index[inning_df['PA Type'].isin([4, 5, 6])].tolist()
                    for idx in steal_idx: # find indices of steals
                        pre_steal = inning_df[inning_df.index < idx]
                        steal_play = inning_df.loc[idx]
    
                        if steal_play['Hitter ID'] in pre_steal['Hitter ID'].tolist(): # skip if no pinch runner
                            continue
                        else: # pinch runner case
                            # simulate inning up until pinch runner
                            runners = [None, None, None]
                            for idx2, row in pre_steal.iterrows():
                                hitter_id = row['Hitter ID']
                                exact_result = row['Exact Result']
                                outs = row['Outs']
                                pa_type = row['PA Type']
                                diff = row['Diff']
                                season = row['Season']
        
                                play_outcome = _simulate_runners(runners, outs, exact_result, diff, season, pa_type, hitter_id)
                                runners = play_outcome['runners']
                            
                            # determine which player was removed
                            if steal_play['Exact Result'] == 'STEAL 2B':
                                removed_idx = pre_steal[pre_steal['Hitter ID'] == runners[0]].index[-1]
                            elif steal_play['Exact Result'] in (['STEAL 3B', 'MSTEAL 3B']):
                                removed_idx = pre_steal[pre_steal['Hitter ID'] == runners[1]].index[-1]
                            elif steal_play['Exact Result'] in (['STEAL HOME', 'MSTEAL HOME']):
                                removed_idx = pre_steal[pre_steal['Hitter ID'] == runners[2]].index[-1]
                            else:
                                continue
    
                            # reassign run scored if necessary
                            game_df.loc[idx, 'Run'] = game_df.loc[removed_idx, 'Run']
                            game_df.loc[removed_idx, 'Run'] = 0
    
        # Add the updated game to list                        
        updated_games.append(game_df)
    
    # Reconstruct dataframe using the corrected games
    if updated_games:
        gamelog_df = pd.concat(updated_games, ignore_index = True)

    return gamelog_df