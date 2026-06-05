import pandas as pd

def _add_war_columns(gamelog_df):
    '''
    Function for adding Batter WAR and Pitcher WAR columns to a gamelog dataframe
        gamelog_df - gamelog dataframe with RE24 column
    '''
    
    batter_war = []
    pitcher_war = []
    for season, season_df in gamelog_df.groupby('Season'): # iterate through seasons
        total_games = len(season_df['Game ID'].unique()) # number of games in the season
        total_pa = len(season_df[~season_df['PA Type'].isin([0, 15])]) # number of plate apperances in the season. PA in this case also includes stolen base attempts
        war_available = 0.41 * total_games / 2 # calculate the total amount of WAR
        rar_available = 10 * war_available # calculate the total runs above replacement
        batting_replacement = (rar_available - sum(season_df['RE24'])) / total_pa # calculate the replacement level RE for a batter
        pitching_replacement = (rar_available + sum(season_df['RE24'])) / total_pa # calculate the replacement level RE for a pitcher
    
        for idx, row in season_df.iterrows(): # iterate through each play
            if row['PA Type'] in [0, 15]: # ignore Manfred runners and trailing runners on multisteals
                batting_rar = 0
                pitching_rar = 0
            else: # calculate RAR and WAR
                batting_rar = row['RE24'] + batting_replacement
                pitching_rar = -row['RE24'] + pitching_replacement
            batter_war.append(batting_rar / 10)
            pitcher_war.append(pitching_rar / 10)

    # add columns to gamelogs
    gamelog_df['Batter WAR'] = batter_war
    gamelog_df['Pitcher WAR'] = pitcher_war

    return gamelog_df