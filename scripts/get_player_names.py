import pandas as pd
import numpy as np
from load_gamelogs import _load_player_types

def get_player_names():
    '''
    Function for getting a dataframe of all players to have played fake baseball.

    Output:
        player_names - df of all players. Contains player ID, most recent name, player information (type, position, hand), and former names
    '''
    df = pd.DataFrame()
    # priority order for names of equal season
    order = ['mlr', 'mlr_playoff', 'milr', 'milr_playoff', 'fcb', 'gib', 'wbc', 'npr', 'eco']
    
    for league in order:
        season = 9999 # value that will never be reached
        
        players = _load_player_types(season, league) # load player types
        players['League'] = league
        
        df = pd.concat([df, players], axis = 0, ignore_index = True) # concatenate all player types (which includes name) into a single df
    
    df['league_order'] = pd.Categorical(df['League'], categories = order, ordered = True) # create a categorical for sorting
    df = df.sort_values(['ID', 'Season', 'league_order'], ascending = [True, False, True]).reset_index() # sort by ID, season descending, and order

    # get other names used by players. These are names that a player never used at the end of a season and would otherwise be lost.
    doc_id = '1YCx6Q9qVH5Wb7HZy07Jt_nuDJwg6mNIeEFsqKJ1viBo'
    gid = 0
    other_names_url = f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}'
    other_names = pd.read_csv(other_names_url)
    
    df = pd.concat([df, other_names], axis = 0, ignore_index = True)

    # get most recent player information and a list of all names
    player_names = df.groupby('ID').agg(
        Name = ('Name', 'first'),
        bt = ('Batting Type', 'first'),
        pt = ('Pitching Type', 'first'),
        Handedness = ('Handedness', 'first'),
        Position = ('Position', 'first'),
        all_names = ('Name', lambda x: set(x))
    ).reset_index()

    # replace batting type of pitchers and pitching type of batters
    player_names['Batting Type'] = np.where(player_names['Position'] == 'P', 'P', player_names['bt'])
    player_names['Pitching Type'] = np.where(~player_names['Position'].isin(['P', 'PH']), 'POS', player_names['pt'])

    # get list of former names
    player_names['Former Names'] = player_names.apply(lambda row: row['all_names'] - {row['Name']}, axis = 1)
    player_names['Former Names'] = player_names['Former Names'].apply(lambda s: '' if len(s) == 0 else s)
    
    player_names = player_names[['ID', 'Name', 'Batting Type', 'Pitching Type', 'Handedness', 'Position', 'Former Names']]

    return player_names