import time
import pandas as pd
import requests
from calculate_re_matrix import _calculate_re_matrix
from calculate_fip_constant import _calculate_fip_constant

def _fetch_csv(url, description, attempts = 3, backoff_seconds = 5):
    '''
    Function for fetching a CSV export from Google Sheets, with validation and retries.
    Google occasionally serves an HTML error/login page instead of the CSV (e.g. transient
    rate limiting), and that HTML would otherwise get written to disk as if it were valid
    data and silently misparsed downstream. Raises RuntimeError if no attempt succeeds.
        url - URL to fetch
        description - human-readable label for error messages (e.g. "FCB S13 gamelog")
        attempts - number of attempts before giving up
        backoff_seconds - delay between attempts
    '''

    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            r = requests.get(url, timeout = 30)
            r.raise_for_status()
            content = r.content
            stripped = content.lstrip()
            if len(stripped) == 0:
                raise RuntimeError(f'Empty response body for {description}')
            if stripped[:1] in (b'<', b'{'):
                raise RuntimeError(f'Response for {description} does not look like CSV '
                                    f'(starts with {stripped[:30]!r}) - likely an HTML error/login page')
            return content
        except (requests.RequestException, RuntimeError) as e:
            last_error = e
            print(f'  Attempt {attempt}/{attempts} failed for {description}: {e}')
            if attempt < attempts:
                time.sleep(backoff_seconds)

    raise RuntimeError(f'Failed to download {description} after {attempts} attempts: {last_error}')


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
        description = f'{row['League']} S{row['Season']} {item}'
        content = _fetch_csv(url, description)
        with open (rf'../data/raw_{item}s/{row['League'].lower()}_raw_{item}_S{row['Season']}.csv', 'wb') as f:
            f.write(content)


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

            if len(df) == 0:
                print(f'No games logged for {row['League']} S{row['Season']}, skipping RE matrix calculation')
            else:
                print(f'Calculating RE matrix for {row['League']} S{row['Season']}...')
                re_matrix = _calculate_re_matrix(df, season)
                re_matrix.to_csv(rf'../data/re_matrices/{row['League'].lower()}_re_matrix_S{row['Season']}.csv')

        if len(df) > 0:
            fip_constant = _calculate_fip_constant(df)
            fip_row = pd.DataFrame([{'League': row['League'], 'Season': row['Season'], 'FIP Constant': fip_constant}])
            fip_constants = pd.concat([fip_constants, fip_row], ignore_index = True)

    fip_constants.to_csv(r'../data/fip_constants.csv', index = False)

    # Download pitcher decision adjustments
    doc_id = '123WLLrCubzg7V6fKfa1YCg78nJAadrtvwBAo0bKjRdU'
    gid = 0

    url = f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}'
    content = _fetch_csv(url, 'pitcher decision adjustments')
    with open (rf'../data/pitcher_decision_adjustments.csv', 'wb') as f:
        f.write(content)
 