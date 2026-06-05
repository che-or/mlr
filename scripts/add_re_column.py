import pandas as pd
from simulate_runners import _simulate_runners

def _add_re_column(gamelog_df, league):
    '''
    Function for adding RE24 column to the gamelogs using RE matrices.
        gamelog_df - dataframe with gamelogs
        league - fake baseball league, options: [mlr, mlr_playoffs, milr, milr_playoffs, fcb, npr, wbc, gib]

    Output:
        gamelog_df with added 'RE24' column
    '''
    
    re24 = []
    for season, season_df in gamelog_df.groupby('Season'): # iterate through seasons
        try:
            re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}.csv') # load appropriate run expectancy matrix
        except:
            if (10 * season - 10 * int(season)) / 10 == 0.1:
                re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}A.csv')
            elif (10 * season - 10 * int(season)) / 10 == 0.2:
                re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}B.csv')
            else:
                print(f'RE Matrix not found. {season}')
                return None
    
        for inning, inning_df in season_df.groupby('Inning ID'): # iterate through innings
            for idx, row in inning_df.iterrows():
                pa_type = row['PA Type']
                if pa_type in [0, 15]: # do not credit Manfred runners or trailing runners on multisteals with RE24
                    play_re24 = 0
                else: # simulate play to determine resulting state
                    outs = row['Outs']
                    obc = row['OBC']
                    result = row['Exact Result']
                    diff = row['Diff']
                    season = row['Season']
                    current_hitter_id = 'hitter'

                    # place runners on base. IDs of hitter and runners on base isn't necessary for calculating RE24
                    runners_before_play = [None, None, None]
                    if obc in [1, 4, 5, 7]:
                        runners_before_play[0] = 'inherited'
                    if obc in [2, 4, 6, 7]:
                        runners_before_play[1] = 'inherited'
                    if obc in [3, 5, 6, 7]:
                        runners_before_play[2] = 'inherited'
                        
                    play_outcome = _simulate_runners(runners_before_play, outs, result, diff, season, pa_type, current_hitter_id)
    
                    # calculate RE24 for the play based on starting state, ending state, and runs scored
                    re_before = re_matrix[(re_matrix['Outs'] == outs) & (re_matrix['OBC'] == obc)]['RE'].iloc[0]
                    if outs + play_outcome['outs'] == 3:
                        re_after = 0
                    else:
                        re_after = re_matrix[(re_matrix['Outs'] == outs + play_outcome['outs']) & (re_matrix['OBC'] == play_outcome['obc'])]['RE'].iloc[0]
        
                    play_re24 = re_after - re_before + len(play_outcome['runs'])
                
                re24.append(play_re24)

    # add RE24 column to the gamelogs
    gamelog_df['RE24'] = re24

    return gamelog_df