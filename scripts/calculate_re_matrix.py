import pandas as pd
from simulate_inning import _simulate_inning

def _calculate_re_matrix(gamelog_df, season):
    '''
    This function calculates the run expectancy matrix for a season gamelog and saves it to a .csv
        gamelog_df - dataframe containing a season gamelog
    '''

    gamelog_df['Season'] = season
    
    all_plays = []
    for inning, inning_df in gamelog_df.groupby('Inning ID'): # iterate through innings, determining the number of runs scored after each play
        for idx, row in inning_df.iterrows():
            outs = row['Outs']
            obc = row['OBC']
            remaining_inning_df = inning_df[inning_df.index >= idx]
            remaining_inning_results = _simulate_inning(remaining_inning_df, 'Exact Result')

            play = {'Inning ID': inning, 'Outs': outs, 'OBC': obc, 'Runs': remaining_inning_results['runs']}
            all_plays.append(play)

    runs_df = pd.DataFrame(all_plays)

    # calculate run expectancy for each base out state
    re_matrix = pd.pivot_table(runs_df, index = ['Outs', 'OBC'], values = 'Runs', aggfunc = ['count', 'sum'], fill_value = 0)
    re_matrix.columns = ['_'.join(col).strip() for col in re_matrix.columns]

    re_matrix['RE'] = re_matrix['sum_Runs'] / re_matrix['count_Runs']
    re_matrix = re_matrix[['RE']]

    return re_matrix