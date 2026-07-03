import pandas as pd
from simulate_inning import _simulate_inning

def _calculate_pitching_neutrals(df, league, against = False):
    '''
    Function for calculating neutral earned runs and neutral innings pitched.
        df - gamelog dataframe
        league - fake baseball league. Options mlr, mlr_playoff, milr, fcb, gib, eco, wbc, npr
        against - if True, group by the opponent's (batter's) team instead of the pitcher's own team

    Output:
        neutrals - dataframe with columns [ID, Season, Team, nER, nIP]
    '''

    team_col = 'Batter Team' if against else 'Pitcher Team'

    neutrals = []
    for pitcher, pitcher_df in df.groupby('Pitcher ID'): # iterate through each pitcher
        pitcher_season = {'ID': pitcher}
        for season, season_df in pitcher_df.groupby('Season'): # iterate through each season
            for team, team_df in season_df.groupby(team_col): # iterate through each team
                runs_allowed = 0
                pitcher_outs = 0
                for inning, inning_df in team_df.groupby('Inning ID'): # iterate through each inning
                    inning_results = _simulate_inning(inning_df, 'Result at Neutral') # simulate the inning
                    runs_allowed += inning_results['earned runs'] # record any earned runs
                    pitcher_outs += inning_results['outs'] # record the number of outs the pitcher got
                    
                    if inning_results['total_outs'] < 3: # if the inning wasn't completed, use the relevant RE matrix to determine how many more runs to charge the pitcher with
                        try:
                            re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}.csv') # load appropriate run expectancy matrix
                        except:
                            if (10 * season - 10 * int(season)) / 10 == 0.1:
                                re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}A.csv')
                            elif (10 * season - 10 * int(season)) / 10 == 0.2:
                                re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}B.csv')
                            else:
                                print(f'RE Matrix not found. {season}')
        
                        re = re_matrix[(re_matrix['Outs'] == inning_results['total_outs']) & (re_matrix['OBC'] == inning_results['responsible_obc'])]['RE'].iloc[0] # get appropriate RE
                        runs_allowed += re # add RE to runs allowed

                # create a row for the output dataframe
                pitcher_season['Season'] = season
                pitcher_season['Team'] = team
                pitcher_season['nER'] = runs_allowed
                pitcher_season['nIP'] = pitcher_outs / 3
        
                neutrals.append(pitcher_season.copy())
    
    neutrals = pd.DataFrame(neutrals) # convert to a dataframe

    return neutrals


def _calculate_league_pitching_neutrals(df, league):
    '''
    Function for calculating neutral earned runs and neutral innings pitched.
        df - gamelog dataframe
        league - fake baseball league. Options mlr, mlr_playoff, milr, fcb, gib, eco, wbc, npr

    Output:
        neutrals - dataframe with columns [Season, lgnERA]
    '''
    
    neutrals = []
    for season, season_df in df.groupby('Season'): # iterate through each season
        league_season = {'Season': season}
        runs_allowed = 0
        pitcher_outs = 0
        for inning, inning_df in season_df.groupby('Inning ID'): # iterate through each inning
            inning_results = _simulate_inning(inning_df, 'Result at Neutral') # simulate the inning
            runs_allowed += inning_results['earned runs'] # record any earned runs
            pitcher_outs += inning_results['outs'] # record the number of outs the pitcher got
            
            if inning_results['total_outs'] < 3: # if the inning wasn't completed, use the relevant RE matrix to determine how many more runs to charge the pitcher with
                try:
                    re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}.csv') # load appropriate run expectancy matrix
                except:
                    if (10 * season - 10 * int(season)) / 10 == 0.1:
                        re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}A.csv')
                    elif (10 * season - 10 * int(season)) / 10 == 0.2:
                        re_matrix = pd.read_csv(f'../data/re_matrices/{league}_re_matrix_S{int(season)}B.csv')
                    else:
                        print(f'RE Matrix not found. {season}')
    
                re = re_matrix[(re_matrix['Outs'] == inning_results['total_outs']) & (re_matrix['OBC'] == inning_results['responsible_obc'])]['RE'].iloc[0] # get appropriate RE
                runs_allowed += re # add RE to runs allowed
    
        # create a row for the output dataframe
        league_season['lgnER'] = runs_allowed
        league_season['lgnIP'] = pitcher_outs / 3
    
        neutrals.append(league_season.copy())
    
    neutrals = pd.DataFrame(neutrals) # convert to a dataframe

    neutrals['lgnERA'] = neutrals['lgnER'] / neutrals['lgnIP'] * 6
    neutrals = neutrals.drop(columns = ['lgnER', 'lgnIP'])

    return neutrals