import pandas as pd

def _calculate_fip_constant(gamelog_df):
    '''
    Function for calculating the FIP constant for a season gamelog.
        gaemlog_df - season gamelog

    Output:
        fip_constant - FIP constant for that season
    '''

    df = gamelog_df[gamelog_df['PA Type'] != 0] #remove Manfred Runners

    league_hr = len(df[df['Exact Result'].str.upper() == 'HR']) # total season home runs
    league_bb = len(df[df['Exact Result'].str.upper().isin(['BB', 'IBB', 'AUTO BB'])]) # total season walks
    league_so = len(df[df['Exact Result'].str.upper().isin(['K', 'BUNT K', 'AUTO K'])]) # total season strikeouts

    # total season innings pitched
    league_ip = (len(df[df['Exact Result'].str.upper().isin(['FO', 'K', 'PO', 'RGO', 'LGO', 'AUTO K', 'BUNT SAC', 'BUNT K', 'BUNT GO', 'CS 2B', 'CS 3B', 'CS HOME', 'CMS 3B', 'CMS HOME', 'BUNT GO'])]) 
                 + 2 * len(df[df['Exact Result'].str.upper() == 'BUNT DP']) 
                 + len(df[df['Old Result'].str.upper().isin(['DP', 'LO'])]) 
                 + 2 * len(df[df['Old Result'].str.upper() == 'TP'])) / 3
                 
    league_er = sum(df['Run']) # total season earned runs

    league_era = league_er / league_ip * 6 # league ERA

    fip_constant = league_era - ((13 * league_hr) + (3 * league_bb) - (2 * league_so)) / league_ip # calculate FIP constant
    return fip_constant


def _get_fip_constants(league):
    '''
    Function for loading the FIP constants for a given league.
        league - fake baseball league, options: mlr, mlr_playoff, milr, fcb, gib, wbc, npr, eco

    Output:
        fip_constants - df containing the FIP constant for each season of the league.
    '''
    
    fip_constants = pd.read_csv(r'../data/fip_constants.csv') # load all FIP constants
    fip_constants = fip_constants[fip_constants['League'].str.lower() == league.lower()].drop(columns = 'League') # choose only desired league

    # convert season to numeric. Changes MiLR 8A to 8.1 and 8B to 8.2
    for idx, row in fip_constants.iterrows():
        season = row['Season']
        
        if season.endswith('A'):
            fip_constants.loc[idx, 'Season'] = str(int(season[:-1]) + 0.1)
        elif season.endswith('B'):
            fip_constants.loc[idx, 'Season'] = str(int(season[:-1]) + 0.2)
        else:
            continue
    
    fip_constants['Season'] = pd.to_numeric(fip_constants['Season'])

    return fip_constants