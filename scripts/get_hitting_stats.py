import pandas as pd
import numpy as np

def get_hitting_stats(df, players, against = False):
    '''
    Function for creating a hitting stats table
        df - gamelog dataframe
        players - dataframe containing a list of all players with their player types, handedness, and primary position
        against - if True, aggregate by the opponent's team/franchise instead of the batter's own team/franchise

    Output:
        hitting_stats - df of hitting stats
    '''

    hitting_stats = _hitting_stats_table(df, against) # calculate most stats
    hitting_stats = hitting_stats.merge(players, on = ['Season', 'ID'], how = 'left') # merge with player types
    hitting_stats = _calculate_ops_plus(hitting_stats) # calculate OPS+

    return hitting_stats
    

def get_aggregated_hitting_stats(hitting_stats, aggregation_level):
    '''
    Function for aggregating hitting stats
        hitting_stats - hitting stats by player aggregated by season and team
        aggregation_level - what to aggregate by, options: 'team', 'type', 'team-type', 'career', 'full-team', 'full-franchise'
    '''

    # counting stat columns
    cols = ['HR', '3B', '2B', '1B', 'BB', 'IBB', 'FO', 'SO', 'Auto K', 'PO', 'RGO', 'LGO', 'LO',
            'SF', 'SH', 'GO', 'GIDP', 'GITP', 'SB', 'CS', 'H', 'PA', 'AB', 'TB', 'G', 'R', 'RBI',
            '1RHR', '2RHR', '3RHR', '4RHR', 'TB+', 'H_RISP', 'AB_RISP',
            'SB 2B', 'SB 3B', 'SB Home', 'CS 2B', 'CS 3B', 'CS Home',
            'Total Diff', 'Total Plays', 'RE24', 'WPA', 'WAR', '0 Diffs', '500 Diffs',
            'nH', 'nTB', 'nBB', 'nFO', 'nSH', 'nPA', 'nAB', 'nSF']
    sets = ['G_list'] # set columns
        
    if aggregation_level == 'team': # aggregate by player and team
        hitting_stats = _aggregate_by_team(hitting_stats, cols, sets)  

    elif aggregation_level == 'type': # aggregate by player and player type
        hitting_stats = _aggregate_by_type(hitting_stats, cols, sets)

    elif aggregation_level == 'team-type': # aggregate by player, team, and player type
        hitting_stats = _aggregate_by_team_and_type(hitting_stats, cols, sets)

    elif aggregation_level == 'career': # aggregate by player
        hitting_stats = _aggregate_by_career(hitting_stats, cols, sets)

    elif aggregation_level == 'full-team': # aggregate by season and franchise
        hitting_stats = _aggregate_by_full_team(hitting_stats, cols, sets)

    elif aggregation_level == 'full-franchise': # aggregate by franchise history
        hitting_stats = _aggregate_by_full_franchise(hitting_stats, cols, sets)

    else:
        print(f"Invalid aggregation level '{aggregation_level}'. Valid aggregation levels are 'team', 'type', 'team-type', 'career', 'full-team', 'full-franchise'")
        return None

    return hitting_stats
    
    
def _hitting_stats_table(df, against = False):
    '''
    Function for calculating counting stats from gamelogs. Rate stats are added by this function calling _calculate_hitting_rate_stats().
        df - gamelog dataframe
        against - if True, group by the opponent's (pitcher's) team/franchise instead of the batter's own team/franchise

    Output:
        hitting_stats - dataframe of hitting stats
    '''

    team_col = 'Pitcher Team' if against else 'Batter Team'
    franchise_col = 'Pitcher Franchise' if against else 'Batter Franchise'
    cols = ['Hitter ID', 'Season', 'Display Season', team_col, franchise_col]

    hitting_stats_exact = pd.pivot_table(df, index = cols, columns = 'Exact Result', aggfunc = 'size', fill_value = 0)
    hitting_stats_old = pd.pivot_table(df, index = cols, columns = ['Exact Result', 'Old Result'], aggfunc = 'size', fill_value = 0)
    hitting_stats_neutral = pd.pivot_table(df, index = cols, columns = 'Result at Neutral', aggfunc = 'size', fill_value = 0)
    hitting_stats_obc = pd.pivot_table(df, index = cols, columns = ['Exact Result', 'OBC'], aggfunc = 'size', fill_value = 0)
    hitting_stats_patype = pd.pivot_table(df, index = cols, columns = 'PA Type', aggfunc = 'size', fill_value = 0)

    # Plays with a runner in scoring position (runner on 2nd and/or 3rd), used for H_RISP/AB_RISP
    risp_obc = [2, 3, 4, 5, 6, 7]
    df_risp = df[df['OBC'].isin(risp_obc)]
    hitting_stats_exact_risp = pd.pivot_table(df_risp, index = cols, columns = 'Exact Result', aggfunc = 'size', fill_value = 0)
    hitting_stats_old_risp = pd.pivot_table(df_risp, index = cols, columns = ['Exact Result', 'Old Result'], aggfunc = 'size', fill_value = 0)

    hitting_stats = pd.DataFrame(index = hitting_stats_exact.index)

    # Hitting stats that can be directly counted from exact result and/or old result
    hitting_stats['HR'] = hitting_stats_exact.get('HR', 0)
    hitting_stats['3B'] = hitting_stats_exact.get('3B', 0)
    hitting_stats['2B'] = hitting_stats_exact.get('2B', 0)
    hitting_stats['1B'] = hitting_stats_exact.get('1B', 0) + hitting_stats_exact.get('BUNT 1B', 0)
    
    hitting_stats['BB'] = hitting_stats_exact.get('BB', 0) + hitting_stats_exact.get('IBB', 0) + hitting_stats_exact.get('AUTO BB', 0)
    hitting_stats['IBB'] = hitting_stats_exact.get('IBB', 0)
    
    hitting_stats['FO'] = hitting_stats_exact.get('FO', 0)
    hitting_stats['SO'] = hitting_stats_exact.get('K', 0) + hitting_stats_exact.get('AUTO K', 0) + hitting_stats_exact.get('BUNT K', 0)
    hitting_stats['Auto K'] = hitting_stats_exact.get('AUTO K', 0)
    hitting_stats['PO'] = hitting_stats_exact.get('PO', 0)
    hitting_stats['RGO'] = hitting_stats_exact.get('RGO', 0)
    hitting_stats['LGO'] = hitting_stats_exact.get('LGO', 0) - hitting_stats_old.get(('LGO','LO'), 0)
    hitting_stats['LO'] = hitting_stats_old.get(('LGO','LO'), 0)
    
    hitting_stats['SF'] = hitting_stats_old.get(('FO','SAC'), 0)
    hitting_stats['SH'] = hitting_stats_exact.get('BUNT SAC', 0)

    hitting_stats['GO'] = hitting_stats['RGO'] + hitting_stats['LGO'] + hitting_stats_exact.get('BUNT GO', 0) + hitting_stats_exact.get('BUNT DP', 0)
    
    hitting_stats['GIDP'] = hitting_stats_old.get(('RGO','DP'), 0) + hitting_stats_old.get(('LGO','DP'), 0) + hitting_stats_exact.get('BUNT DP', 0)
    hitting_stats['GITP'] = hitting_stats_old.get(('LGO', 'TP'), 0)

    hitting_stats['SB 2B'] = hitting_stats_exact.get('STEAL 2B', 0)
    hitting_stats['SB 3B'] = hitting_stats_exact.get('STEAL 3B', 0) + hitting_stats_exact.get('MSTEAL 3B', 0)
    hitting_stats['SB Home'] = hitting_stats_exact.get('STEAL HOME', 0) + hitting_stats_exact.get('MSTEAL HOME', 0)

    hitting_stats['CS 2B'] = hitting_stats_exact.get('CS 2B', 0)
    hitting_stats['CS 3B'] = hitting_stats_exact.get('CS 3B', 0) + hitting_stats_exact.get('CMS 3B', 0)
    hitting_stats['CS Home'] = hitting_stats_exact.get('CS HOME', 0) + hitting_stats_exact.get('CMS HOME', 0)

    hitting_stats['SB'] = hitting_stats['SB 2B'] + hitting_stats['SB 3B'] + hitting_stats['SB Home']
    hitting_stats['CS'] = hitting_stats['CS 2B'] + hitting_stats['CS 3B'] + hitting_stats['CS Home']

    # Home runs of each type
    hitting_stats['1RHR'] = hitting_stats_obc.get(('HR', 0), 0)
    hitting_stats['2RHR'] = hitting_stats_obc.get(('HR', 1), 0) + hitting_stats_obc.get(('HR', 2), 0) + hitting_stats_obc.get(('HR', 3), 0)
    hitting_stats['3RHR'] = hitting_stats_obc.get(('HR', 4), 0) + hitting_stats_obc.get(('HR', 5), 0) + hitting_stats_obc.get(('HR', 6), 0)
    hitting_stats['4RHR'] = hitting_stats_obc.get(('HR', 7), 0)

    # Hits and at-bats with runners in scoring position
    h_risp = (hitting_stats_exact_risp.get('1B', 0) + hitting_stats_exact_risp.get('BUNT 1B', 0)
              + hitting_stats_exact_risp.get('2B', 0) + hitting_stats_exact_risp.get('3B', 0) + hitting_stats_exact_risp.get('HR', 0))

    bb_risp = hitting_stats_exact_risp.get('BB', 0) + hitting_stats_exact_risp.get('IBB', 0) + hitting_stats_exact_risp.get('AUTO BB', 0)
    so_risp = hitting_stats_exact_risp.get('K', 0) + hitting_stats_exact_risp.get('AUTO K', 0) + hitting_stats_exact_risp.get('BUNT K', 0)
    sh_risp = hitting_stats_exact_risp.get('BUNT SAC', 0)
    sf_risp = hitting_stats_old_risp.get(('FO', 'SAC'), 0)

    pa_risp = (h_risp + bb_risp + hitting_stats_exact_risp.get('FO', 0) + so_risp + hitting_stats_exact_risp.get('PO', 0)
               + hitting_stats_exact_risp.get('RGO', 0) + hitting_stats_exact_risp.get('LGO', 0) + sh_risp
               + hitting_stats_exact_risp.get('BUNT GO', 0) + hitting_stats_exact_risp.get('BUNT DP', 0))

    hitting_stats['H_RISP'] = h_risp
    hitting_stats['AB_RISP'] = pa_risp - (bb_risp + sf_risp + sh_risp)
    hitting_stats['H_RISP'] = hitting_stats['H_RISP'].fillna(0)
    hitting_stats['AB_RISP'] = hitting_stats['AB_RISP'].fillna(0)

    # Hitting stats calculated from raw counts
    hitting_stats['H'] = hitting_stats['1B'] + hitting_stats['2B'] + hitting_stats['3B'] + hitting_stats['HR']
    hitting_stats['PA'] = hitting_stats['H'] + hitting_stats['BB'] + hitting_stats['FO'] + hitting_stats['SO'] + hitting_stats['PO'] + hitting_stats['RGO'] + hitting_stats['LGO'] + hitting_stats['LO'] + hitting_stats['SH'] + hitting_stats_exact.get('BUNT GO', 0) + hitting_stats_exact.get('BUNT DP', 0)
    hitting_stats['AB'] = hitting_stats['PA'] - (hitting_stats['BB'] + hitting_stats['SF'] + hitting_stats['SH'])
    hitting_stats['TB'] = hitting_stats['1B'] + 2 * hitting_stats['2B'] + 3 * hitting_stats['3B'] + 4 * hitting_stats['HR']
    hitting_stats['TB+'] = hitting_stats['TB'] + hitting_stats_exact.get('BB', 0) + hitting_stats['SB'] - hitting_stats_patype.get(15, 0)

    # Stats that need to be taken from other columns
    hitting_stats['G_list'] = df.groupby(cols)['Game ID'].apply(lambda x: set(x))
    hitting_stats['G'] = hitting_stats['G_list'].apply(lambda x: len(x))
    hitting_stats['R'] = df.groupby(cols)['Run'].sum()
    hitting_stats['RBI'] = df.groupby(cols)['RBI'].sum()
    hitting_stats['Total Diff'] = df.groupby(cols)['Diff'].sum()
    hitting_stats['Total Plays'] = df.groupby(cols)['Diff'].count()
    hitting_stats['RE24'] = df.groupby(cols)['RE24'].sum()
    hitting_stats['WPA'] = df.groupby(cols)['Batter WPA'].sum()
    hitting_stats['WAR'] = df.groupby(cols)['Batter WAR'].sum()
    hitting_stats['0 Diffs'] = df.groupby(cols)['Diff'].apply(lambda x: (x == 0).sum())
    hitting_stats['500 Diffs'] = df.groupby(cols)['Diff'].apply(lambda x: (x == 500).sum())

    hitting_stats['Last Team'] = df.groupby(['Hitter ID', 'Season'])['Batter Franchise'].last()
    hitting_stats['Last Session'] = df.groupby(cols)['Session'].max()

    # Neutral hitting stats
    hitting_stats['nH'] = hitting_stats_neutral.get('1B', 0) + hitting_stats_neutral.get('2B', 0) + hitting_stats_neutral.get('3B', 0) + hitting_stats_neutral.get('HR', 0) + hitting_stats_neutral.get('BUNT 1B', 0)
    hitting_stats['nTB'] = hitting_stats_neutral.get('1B', 0) + 2 * hitting_stats_neutral.get('2B', 0) + 3 * hitting_stats_neutral.get('3B', 0) + 4 * hitting_stats_neutral.get('HR', 0) + hitting_stats_neutral.get('BUNT 1B', 0)
    hitting_stats['nBB'] = hitting_stats_neutral.get('BB', 0) + hitting_stats_neutral.get('IBB', 0) + hitting_stats_neutral.get('AUTO BB', 0)
    hitting_stats['nFO'] = hitting_stats_neutral.get('FO', 0)
    hitting_stats['nSH'] = hitting_stats_neutral.get('BUNT SAC', 0)
    
    hitting_stats['nPA'] = hitting_stats['nH'] + hitting_stats['nBB'] + hitting_stats['nFO'] + hitting_stats_neutral.get('K', 0) + hitting_stats_neutral.get('BUNT K', 0) + hitting_stats_neutral.get('AUTO K', 0) + hitting_stats_neutral.get('PO', 0) + hitting_stats_neutral.get('RGO', 0) + hitting_stats_neutral.get('LGO', 0) + hitting_stats['nSH'] + hitting_stats_neutral.get('BUNT GO', 0) + hitting_stats_neutral.get('BUNT DP', 0)
    hitting_stats['nAB'] = hitting_stats['nPA'] - (hitting_stats['nBB'] + hitting_stats['nSH'])

    hitting_stats = hitting_stats.reset_index()
    hitting_stats = hitting_stats.rename(columns = {'Hitter ID': 'ID', team_col: 'Team', franchise_col: 'Franchise'})
    
    # Correct for sacrifice flies
    sfvalue = _get_sacfly_rate(df)
    
    hitting_stats['SF value'] = hitting_stats['Season'].map(sfvalue['SF value'])
    hitting_stats['nSF'] = hitting_stats['nFO'] * hitting_stats['SF value']

    hitting_stats['nAB'] = hitting_stats['nAB'] - hitting_stats['nSF']

    # Calculate league neutrals
    hitting_stats['lgnH'] = hitting_stats.groupby('Season')['nH'].transform('sum')
    hitting_stats['lgnBB'] = hitting_stats.groupby('Season')['nBB'].transform('sum')
    hitting_stats['lgnPA'] = hitting_stats.groupby('Season')['nPA'].transform('sum')
    hitting_stats['lgnAB'] = hitting_stats.groupby('Season')['nAB'].transform('sum')
    hitting_stats['lgnTB'] = hitting_stats.groupby('Season')['nTB'].transform('sum')
    
    hitting_stats['lgnOBP'] = (hitting_stats['lgnH'] + hitting_stats['lgnBB']) / hitting_stats['lgnPA']
    hitting_stats['lgnSLG'] = hitting_stats['lgnTB'] / hitting_stats['lgnAB']

    # Calculate rate stats
    hitting_stats = _calculate_hitting_rate_stats(hitting_stats)

    return hitting_stats


def _calculate_hitting_rate_stats(hitting_stats):
    '''
    Function for calculating rate stats. It's useful to have these separate because they need to be recalled when aggregating data.
        hitting_stats - dataframe of hitting stats

    Output:
        hitting_stats - dataframe with rate stat columns added or recalculated
    '''
    hitting_stats['BA'] = hitting_stats['H'] / hitting_stats['AB']
    hitting_stats['BARISP'] = hitting_stats['H_RISP'] / hitting_stats['AB_RISP']
    hitting_stats['OBP'] = (hitting_stats['H'] + hitting_stats['BB']) / (hitting_stats['AB'] + hitting_stats['BB'] + hitting_stats['SF']) # denominator is different than hitting_stats['PA'] if the player has any sacrifice bunts, which are plate appearances but don't count toward OBP
    hitting_stats['SLG'] = hitting_stats['TB'] / hitting_stats['AB']
    hitting_stats['OPS'] = hitting_stats['OBP'] + hitting_stats['SLG']
    hitting_stats['ISO'] = hitting_stats['SLG'] - hitting_stats['BA']
    hitting_stats['BABIP'] = (hitting_stats['H'] - hitting_stats['HR']) / (hitting_stats['AB'] - hitting_stats['SO'] - hitting_stats['HR'] + hitting_stats['SF'])
    
    hitting_stats['SB%'] = hitting_stats['SB'] / (hitting_stats['SB'] + hitting_stats['CS'])
    hitting_stats['HR%'] = hitting_stats['HR'] / hitting_stats['PA']
    hitting_stats['K%'] = hitting_stats['SO'] / hitting_stats['PA']
    hitting_stats['BB%'] = hitting_stats['BB'] / hitting_stats['PA']
    hitting_stats['GB%'] = (hitting_stats['RGO'] + hitting_stats['LGO']) / (hitting_stats['FO'] + hitting_stats['PO'] + hitting_stats['RGO'] + hitting_stats['LGO'])
    hitting_stats['FB%'] = hitting_stats['FO'] / (hitting_stats['FO'] + hitting_stats['PO'] + hitting_stats['RGO'] + hitting_stats['LGO'])
    hitting_stats['GB/FB'] = hitting_stats['GB%'] / hitting_stats['FB%']
    
    # Neutral rate stats
    hitting_stats['nOBP'] = (hitting_stats['nH'] + hitting_stats['nBB']) / (hitting_stats['nAB'] + hitting_stats['nBB'] + hitting_stats['nSF'])
    hitting_stats['nSLG'] = hitting_stats['nTB'] / hitting_stats['nAB']

    hitting_stats['Avg Diff'] = hitting_stats['Total Diff'] / hitting_stats['Total Plays'].replace(0, np.nan)

    return hitting_stats


def _get_sacfly_rate(df):
    '''
    Function for getting the ratio of plays where a sacrifice fly is possible.
    Sac flies at neutral is necessary for calculating nSLG, but cannot be inferred from the PA logs. nSF is estimated as the expected number of flyouts
    that would have been sac flies at neutral based on the rate of plays where a runner is on third with less than two outs
        df - gamelog dataframe

    Output:
        sf_df - dataframe of sac fly ratio, indexed by season
    '''
    
    sf = []
    for season in df['Season'].unique().tolist(): # iterate through seasons
        total_pa = len(df[df['Season'] == season]) # total plays in a season
        sf_chances = len(df[(df['Season'] == season) & (df['Outs'] < 2) & (df['OBC'].isin([3, 5, 6, 7]))]) # total plays where a sac fly is possible
        sf_rate = sf_chances / total_pa # ratio of plays where sac fly is possible
    
        sf_season = {'Season': season, 'SF value': sf_rate}
        sf.extend([sf_season])

    # convert to df
    sf_df = pd.DataFrame(sf).set_index('Season')

    return sf_df


def _weighted_average(df, col, weight):
    '''
    Function for calculating weighted averages of a column of a dataframe weighted by another column
        df - dataframe
        col - column of df to average
        weight - weight column

    Output:
        series of weighted averages
    '''
    w = df[weight]
    d = df[col]

    return (d * w).sum() / w.sum() if w.sum() != 0 else np.nan


def _weighted_league_neutrals(df, cols):
    '''
    Function for calculating weighted league neutral OBP and SLG
        df - hitting stats dataframe with columns lgnOBP, lgnSLG, PA, AB
        cols - columns to group by

    Output:
        lgn - league neutral stats
    '''
    
    lgn = df.groupby(cols).apply(lambda g: pd.Series({'lgnOBP': _weighted_average(g, 'lgnOBP', 'PA'), 
                                                      'lgnSLG': _weighted_average(g, 'lgnSLG', 'AB')})).reset_index()

    return lgn


def _calculate_ops_plus(df):
    '''
    Function for calculating OPS+
        df - hitting stats dataframe with columns nOBP, nSLG, lgnOBP, lgnSLG

    Output:
        df - dataframe with new OPS+ column
    '''

    df['OPS+'] = 100 * (df['nOBP'] / df['lgnOBP'] + df['nSLG'] / df['lgnSLG'] - 1)

    return df


def _constant_or_null(x):
    '''
    Function for determining whether player type, handedness, or position are constant or varying for aggregation
        x - dataframe column

    Output:
        constant value if it's constant, NaN if not
    '''
    return x.iloc[0] if x.nunique() == 1 else np.nan
    

def _create_agg_dict(summed, constants, sets):
    '''
    Function for creating an aggregation dictionary
        summed - columns to sum
        constants - columns to remain constant or turn to null
        sets - columns to create as a union of sets
    '''
    
    agg_dict = {col: 'sum' for col in summed} # sum counting stats
    agg_dict.update({col: _constant_or_null for col in constants}) # dynamically determine whether to take the constant value or make null
    agg_dict.update({col: (lambda s: set.union(*s)) for col in sets}) # union set columns

    return agg_dict


def _aggregate_stats(stats_df, counting_stats, constants, sets, group):
    '''
    Function for aggregating a hitting stats dataframe.
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing
        constants - list of stats that should be nulled if not constant
        group - columns to group by

    Output:
        agg_stats - aggregated dataframe
    '''
    
    agg_dict = _create_agg_dict(counting_stats, constants, sets) # create aggregation dictionary

    agg_stats = stats_df.groupby(group).agg(agg_dict).reset_index() # aggregate
    agg_stats = _calculate_hitting_rate_stats(agg_stats) # recalculate rate stats

    # use a weighted average to determine league neutral values
    lgn = _weighted_league_neutrals(stats_df, group)
    
    agg_stats['lgnOBP'] = lgn['lgnOBP']
    agg_stats['lgnSLG'] = lgn['lgnSLG']

    # calculate OPS+
    agg_stats = _calculate_ops_plus(agg_stats)

    return agg_stats


def _aggregate_by_team(stats_df, counting_stats, sets):
    '''
    Function for aggregating a hitting stats dataframe by franchise (team)
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing

    Output
        stats_by_team - hitting stats dataframe aggregated by franchise (team)
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['ID', 'Franchise']

    stats_by_team = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return stats_by_team


def _aggregate_by_type(stats_df, counting_stats, sets):
    '''
    Function for aggregating a hitting stats dataframe by player type
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing

    Output
        stats_by_type - hitting stats dataframe aggregated by player type
    '''
    
    constants = ['Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['ID', 'Batting Type']
    
    stats_by_type = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return stats_by_type


def _aggregate_by_team_and_type(stats_df, counting_stats, sets):
    '''
    Function for aggregating a hitting stats dataframe by franchise (team) and player type
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing

    Output
        stats_by_teamtype - hitting stats dataframe aggregated by franchise (team) and player type
    '''
    
    constants = ['Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['ID', 'Franchise', 'Batting Type']
    
    stats_by_teamtype = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return stats_by_teamtype


def _aggregate_by_career(stats_df, counting_stats, sets):
    '''
    Function for aggregating a hitting stats dataframe by player ID
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing

    Output
        career_stats - hitting stats dataframe aggregated by player ID
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = 'ID'

    career_stats = _aggregate_stats(stats_df, counting_stats, constants, sets, group)
    
    return career_stats


def _aggregate_by_full_team(stats_df, counting_stats, sets):
    '''
    Function for aggregating a hitting stats dataframe for all players on each team
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing

    Output
        full_team_stats - hitting stats dataframe aggregated to each team
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['Season', 'Display Season', 'Team', 'Franchise']

    full_team_stats = _aggregate_stats(stats_df, counting_stats, constants, sets, group)
    full_team_stats['G'] = full_team_stats['G_list'].apply(lambda x: len(x))
    
    return full_team_stats


def _aggregate_by_full_franchise(stats_df, counting_stats, sets):
    '''
    Function for aggregating a hitting stats dataframe for an entire franchise history
        stats_df - hitting stats dataframe
        counting_stats - list of counting stats for summing

    Output
        full_team_stats - hitting stats dataframe aggregated to each team
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['Franchise']

    full_franchise_stats = _aggregate_stats(stats_df, counting_stats, constants, sets, group)
    full_franchise_stats['G'] = full_franchise_stats['G_list'].apply(lambda x: len(x))
    
    return full_franchise_stats