import pandas as pd
import json
from pathlib import Path
from runner_attribution import _runner_attribution

def _load_gamelogs(current_season, league, all_seasons = True):
    '''
    Function for loading gamelogs into a dataframe. All seasons of a league will be loaded into a single dataframe
        current_season - maximum season number to expect
        league - fake baseball league, options: [mlr, mlr_playoffs, milr, milr_playoffs, fcb, eco, npr, wbc, gib]
        all_seasons - boolean controlling whether to load all gamelogs or only a single season. Default true

    Output:
        gamelog_df - dataframe that includes all gamelogs. Season column has been added. Manfred Runners and trailing runner multisteals are included.
    '''
    
    script_dir = Path(__file__).resolve().parent
    gamelog_dir = script_dir.parent / 'data' / 'raw_gamelogs'

    if all_seasons:
        seasons_range = range(1, current_season + 1)
    else:
        seasons_range = range(current_season, current_season + 1)
    
    gamelog_df = pd.DataFrame()
    for season in seasons_range:
        gamelog = gamelog_dir / f'{league}_raw_gamelog_S{season}.csv'

        try:
            season_df = pd.read_csv(gamelog)
            if season_df.empty:
                # file exists (e.g. a new active season whose sheet has been created but has
                # no games logged yet) but has no rows, so all columns default to object dtype.
                # Concatenating that in would silently poison numeric columns (Run, Diff, etc.)
                # to object dtype for every season, breaking downstream arithmetic. Skip it -
                # there's no data to contribute anyway.
                continue
            season_df['Season'] = season
            season_df['Display Season'] = f'S{season}'
            season_df['Game ID'] = season * 1000 + season_df['Game ID']
            season_df['Inning ID'] = season * 10000 + season_df['Inning ID']
        except FileNotFoundError:
            # this block is necessary for dealing with MiLR seasons 8A and 8B
            gamelogA = gamelog_dir / f'{league}_raw_gamelog_S{season}A.csv'
            gamelogB = gamelog_dir / f'{league}_raw_gamelog_S{season}B.csv'
            if not (gamelogA.exists() and gamelogB.exists()):
                continue # no data for this season yet (not played/downloaded)

            try:
                season_dfA = pd.read_csv(gamelogA)
                season_dfA['Season'] = season + 0.1
                season_dfA['Display Season'] = f'S{season}A'
                season_dfA['Game ID'] = season * 1000 + season_dfA['Game ID']
                season_dfA['Inning ID'] = season * 10000 + season_dfA['Inning ID']

                season_dfB = pd.read_csv(gamelogB)
                season_dfB['Season'] = season + 0.2
                season_dfB['Display Season'] = f'S{season}B'
                season_dfB['Game ID'] = season * 1000 + season_dfB['Game ID'] + 500
                season_dfB['Inning ID'] = season * 10000 + season_dfB['Inning ID'] + 5000
            except Exception as e:
                raise RuntimeError(f'Failed to parse gamelog for {league} S{season}A/B: {e}') from e

            gamelog_df = pd.concat([gamelog_df, season_dfA, season_dfB], ignore_index = True)
            continue
        except Exception as e:
            raise RuntimeError(f'Failed to parse gamelog for {league} S{season} ({gamelog}): {e}') from e

        gamelog_df = pd.concat([gamelog_df, season_df], ignore_index = True)

    # nothing loaded (e.g. all_seasons=False for an active season with no games logged yet):
    # bail before _runner_attribution / the franchise merge, which assume real columns.
    # generate_web_data.py handles an empty return.
    if gamelog_df.empty:
        return gamelog_df

    # convert result columns to all caps
    cols = ['Old Result', 'Exact Result', 'Result at Neutral', 'Result All Neutral']
    for col in cols:
        try:
            gamelog_df[col] = gamelog_df[col].str.upper()
        except:
            continue

    # convert WPA columns to numeric
    cols = ['Batter WPA', 'Pitcher WPA']
    for col in cols:
        try:
            gamelog_df[col] = pd.to_numeric(gamelog_df[col].astype(str).str.strip('%'), errors = 'coerce').fillna(0) / 100
        except:
            continue
    
    gamelog_df = _runner_attribution(gamelog_df)

    if league in ['mlr', 'mlr_playoff']: # handle franchise tracking in MLR
        with open(r'../docs/data/mlr_team_history.json') as f:
            team_history = json.load(f)
            
        rows = []
        for franchise_key, eras in team_history.items():
            for era in eras:
                rows.append({
                    'Franchise': franchise_key,
                    'Team': era['abbr'],
                    'Start': era['start'],
                    'End': era['end']
                })

        lookup = pd.DataFrame(rows)

        for item in ['Batter', 'Pitcher']:
            gamelog_df = gamelog_df.merge(lookup, left_on = f'{item} Team', right_on = 'Team', how = 'left')
            gamelog_df = gamelog_df[(gamelog_df['Season'] >= gamelog_df['Start']) & (gamelog_df['Season'] <= gamelog_df['End'])]
            gamelog_df = gamelog_df.drop(columns = ['Team', 'Start', 'End'])
            gamelog_df = gamelog_df.rename(columns = {'Franchise': f'{item} Franchise'})

    else:
        gamelog_df['Batter Franchise'] = gamelog_df['Batter Team']
        gamelog_df['Pitcher Franchise'] = gamelog_df['Pitcher Team']
    
    return gamelog_df
    

def _load_player_types(current_season, league, all_seasons = True):
    '''
    Function for loading gamelogs into a dataframe. All seasons of a league will be loaded into a single dataframe
        current_season - maximum season number to expect
        league - fake baseball league, options: [mlr, mlr_playoffs, milr, milr_playoffs, fcb, eco, npr, wbc, gib]
        all_seasons - boolean controlling whether to load all players or only a single season. Default true
    
    Output:
        players_df - dataframe that includes all players and their types. Season column has been added.
    '''
    
    script_dir = Path(__file__).resolve().parent
    players_dir = script_dir.parent / 'data' / 'raw_player_types'

    if all_seasons:
        seasons_range = range(1, current_season + 1)
    else:
        seasons_range = range(current_season, current_season + 1)
    
    players_df = pd.DataFrame()
    for season in seasons_range:
        players = players_dir / f'{league}_raw_player_type_S{season}.csv'

        try:
            season_df = pd.read_csv(players)
        except FileNotFoundError:
            # this block is necessary for dealing with MiLR seasons 8A and 8B
            playersA = players_dir / f'{league}_raw_player_type_S{season}A.csv'
            playersB = players_dir / f'{league}_raw_player_type_S{season}B.csv'
            if not (playersA.exists() and playersB.exists()):
                continue # no data for this season yet (not played/downloaded)

            try:
                season_dfA = pd.read_csv(playersA)
                season_dfA['Season'] = season + 0.1

                season_dfB = pd.read_csv(playersB)
                season_dfB['Season'] = season + 0.2
            except Exception as e:
                raise RuntimeError(f'Failed to parse player types for {league} S{season}A/B: {e}') from e

            players_df = pd.concat([players_df, season_dfA, season_dfB], ignore_index = True)
            continue
        except Exception as e:
            raise RuntimeError(f'Failed to parse player types for {league} S{season} ({players}): {e}') from e

        season_df['Season'] = season
        players_df = pd.concat([players_df, season_df], ignore_index = True)

    players_df['Pitching Type'] = players_df['Pitching Type'] + players_df['Pitching Bonus'].radd('-').fillna('')
    players_df = players_df.rename(columns = {'Primary Position': 'Position', 'Player ID': 'ID'})
    
    players_df = players_df[['Season', 'ID', 'Name', 'Batting Type', 'Pitching Type', 'Handedness', 'Position']]

    return players_df