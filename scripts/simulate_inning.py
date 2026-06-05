import pandas as pd
from simulate_runners import _simulate_runners

def _simulate_inning(inning_df, simulation_column):
    '''
    Function for simulating a neutral inning and determining how many runs and outs would be recorded.
        inning_df - dataframe containing one half inning of a gamelog
        simulation_column - result column to simulate on. Options: ['Exact Result', 'Result at Neutral', 'Result All Neutral']

    Outputs:
        simulated_runs - number of runs that score in the simulation. Includes inherited and Manfred runners.
        simulated_earned_runs - number of earned runs that score in the simulation. Excludes inherited and Manfred runners.
        simulated_outs - number of outs recorded in the simulation. Cannot be more than 3.
    '''
    
    obc = inning_df.iloc[0]['OBC'] # OBC to begin inning / when pitcher comes in
    outs = inning_df.iloc[0]['Outs'] # Outs when pitcher comes in

    # Place inherited or Manfred runners on base
    runners_before_play = [None, None, None]
    if obc in [1, 4, 5, 7]:
        runners_before_play[0] = 'inherited'
    if obc in [2, 4, 6, 7]:
        runners_before_play[1] = 'inherited'
    if obc in [3, 5, 6, 7]:
        runners_before_play[2] = 'inherited'

    runs = []

    # Simulate each play
    for idx, row in inning_df.iterrows():
        if outs < 3: # Stop simulating plays if 3 outs is reached. All plays afterward are ignored
            result = row[simulation_column]
            diff = row['Diff']
            season = row['Season']
            pa_type = row['PA Type']
            player_id = row['Pitcher ID']
                
            play_outcome = _simulate_runners(runners_before_play, outs, result, diff, season, pa_type, player_id)
        
            runners_before_play = play_outcome['runners']
            outs = outs + play_outcome['outs']
            runs.extend(play_outcome['runs'])
        else:
            continue

    earned_runs = [x for x in runs if x != 'inherited'] # determine runs charged to pitcher or team
    obc = play_outcome['obc']

    runners = play_outcome['runners']
    if runners[0] == player_id:
        if runners[1] == player_id:
            if runners[2] == player_id:
                responsible_obc = 7
            else:
                responsible_obc = 4
        elif runners[2] == player_id:
            responsible_obc = 5
        else:
            responsible_obc = 1
    elif runners[1] == player_id:
        if runners[2] == player_id:
            responsible_obc = 6
        else:
            responsible_obc = 2
    elif runners[2] == player_id:
        responsible_obc = 3
    else:
        responsible_obc = 0

    simulated_runs = len(runs)
    simulated_earned_runs = len(earned_runs)
    simulated_outs = outs - inning_df.iloc[0]['Outs']

    inning_results = {'runs': simulated_runs, 'earned runs': simulated_earned_runs, 'outs': simulated_outs, 'total_outs': outs, 'charged': earned_runs, 'obc': obc, 'responsible_obc': responsible_obc}

    return inning_results   