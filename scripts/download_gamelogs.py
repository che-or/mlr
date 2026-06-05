import pandas as pd
import requests
from calculate_re_matrix import _calculate_re_matrix
from calculate_fip_constant import _calculate_fip_constant

def _download_data(row):
    '''
    Function for downloading a gamelog from Google Sheets.
        row - dataframe row containing league and url info
    '''
    
    print(f'Downloading data for {row['League']} S{row['Season']}...')
    for item in ['gamelog', 'player_type']:
        doc_id = row[f'{item}_doc_id']
        gid = row[f'{item}_gid']

        url = f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}'
        r = requests.get(url)
        with open (rf'../data/raw_{item}s/{row['League'].lower()}_raw_{item}_S{row['Season']}.csv', 'wb') as f:
            f.write(r.content)


def _download_gamelogs():
    '''
    Function for downloading missing gamelogs and gamelogs for active seasons.
    '''
    
    download_df = pd.read_csv(r'../data/gamelog_links.csv') # read file containing season info

    fip_constants = pd.DataFrame(columns = ['League', 'Season', 'FIP Constant']) # create FIP constant df

    for idx, row in download_df.iterrows(): # iterate through seasons
        active = row['Active']
        season = row['Season']
        try:
            season = int(season)
        except:
            season = int(season[:-1])

        if active == False:
            try: # check if gamelog is already downloaded
                df = pd.read_csv(rf'../data/raw_gamelogs/{row['League'].lower()}_raw_gamelog_S{row['Season']}.csv')
                try: # check if re matrix already exists
                    re_matrix = pd.read_csv(rf'../data/re_matrices/{row['League'].lower()}_re_matrix_S{row['Season']}.csv')
                except: # calculate re matrix
                    print(f'Calculating RE matrix for {row['League']} S{row['Season']}...')
                    re_matrix = _calculate_re_matrix(df, season)
                    re_matrix.to_csv(rf'../data/re_matrices/{row['League'].lower()}_re_matrix_S{row['Season']}.csv')
            except: # download missing gamelogs and calculate re matrix
                _download_data(row)
                df = pd.read_csv(rf'../data/raw_gamelogs/{row['League'].lower()}_raw_gamelog_S{row['Season']}.csv')
    
                print(f'Calculating RE matrix for {row['League']} S{row['Season']}...')
                re_matrix = _calculate_re_matrix(df, season)
                re_matrix.to_csv(rf'../data/re_matrices/{row['League'].lower()}_re_matrix_S{row['Season']}.csv')

        if active == True: # download gamelogs for active seasons and calculate re matrix
            _download_data(row)
            df = pd.read_csv(rf'../data/raw_gamelogs/{row['League'].lower()}_raw_gamelog_S{row['Season']}.csv')

            print(f'Calculating RE matrix for {row['League']} S{row['Season']}...')
            re_matrix = _calculate_re_matrix(df, season)
            re_matrix.to_csv(rf'../data/re_matrices/{row['League'].lower()}_re_matrix_S{row['Season']}.csv')

        fip_constant = _calculate_fip_constant(df)
        fip_row = pd.DataFrame([{'League': row['League'], 'Season': row['Season'], 'FIP Constant': fip_constant}])
        fip_constants = pd.concat([fip_constants, fip_row], ignore_index = True)

    fip_constants.to_csv(r'../data/fip_constants.csv', index = False)

    # Download pitcher decision adjustments
    doc_id = '123WLLrCubzg7V6fKfa1YCg78nJAadrtvwBAo0bKjRdU'
    gid = 0

    url = f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}'
    r = requests.get(url)
    with open (rf'../data/pitcher_decision_adjustments.csv', 'wb') as f:
        f.write(r.content)
 