import pandas as pd
import numpy as np
from determine_pitcher_decisions import get_pitcher_decisions
from calculate_fip_constant import _get_fip_constants
from calculate_pitching_neutrals import _calculate_pitching_neutrals
from get_hitting_stats import _weighted_average, _create_agg_dict

def get_pitching_stats(df, players, league, against = False):
    '''
    Function for creating a pitching stats table
        df - gamelog dataframe
        players - dataframe containing a list of all players with their player types, handedness, and primary position
        aggregation_level - how the data should be aggregated. Options: ['season', 'team', 'career']
        league - fake baseball league. Options: ['mlr', 'mlr_playoff', 'milr', 'fcb', 'gib', 'eco', 'npr', 'wbc']
        against - if True, aggregate by the opponent's (batter's) team/franchise instead of the pitcher's own team/franchise

    Output:
        pitching_stats - df of pitching stats
    '''

    wls = get_pitcher_decisions(df, league, against) # determine pitcher decisions from gamelogs
    neutrals = _calculate_pitching_neutrals(df, league, against) # determine neutral ER and neutral IP for each pitcher
    fip_constants = _get_fip_constants(league) # retrieve FIP constants for the league

    pitching_stats = _pitching_stats_table(df, wls, neutrals, fip_constants, against) # calculate most stats
    pitching_stats = pitching_stats.merge(players, on = ['Season', 'ID'], how = 'left') # merge with player types
    pitching_stats['Pitching Type (Main)'] = pitching_stats['Pitching Type'].str.split('-', n = 1).str[0] # get main pitching type

    pitching_stats = _calculate_era_minus(pitching_stats) # calculate ERA-

    pitching_stats = _apply_pitcher_decision_adjustments(pitching_stats, league, against)

    return pitching_stats


def get_aggregated_pitching_stats(pitching_stats, aggregation_level):
    '''
    Function for aggregating pitching stats
        pitching_stats - pitching stats by player aggregated by season and team
        aggregation_level - what to aggregate by, options: 'team', 'type', 'team-type', 'career', 'full-team', 'full-franchise'
    '''
    
    # counting stat columns
    cols = ['HR', '3B', '2B', '1B', 'BB', 'IBB', 'Auto BB', 'FO', 'SO', 'PO', 'RGO', 'LGO', 'LO',
            'SF', 'SH', 'GO', 'DP', 'TP', 'SB', 'CS', 'H', 'IP', 'BF', 'AB', 'TB', 'G', 'ER', 
            'Total Diff', 'Total Plays', 'RE24', 'WAR', 'WPA', '0 Diffs', '500 Diffs', '300+ Pitches', '400+ Pitches', 
            'W', 'L', 'SV', 'HLD', 'BS', 'GS', 'GF', 'CG', 'SHO', 'OPP', 'nER', 'nIP']
    sets = ['G_list'] # set columns

    if aggregation_level == 'team': # aggregate by player and team
        pitching_stats = _aggregate_by_team(pitching_stats, cols, sets)

    elif aggregation_level == 'type': # aggregate by player and type
        pitching_stats = _aggregate_by_type(pitching_stats, cols, sets)

    elif aggregation_level == 'team-type': # aggregate by player and type
        pitching_stats = _aggregate_by_team_and_type(pitching_stats, cols, sets)

    elif aggregation_level == 'career': # aggregate by player
        pitching_stats = _aggregate_by_career(pitching_stats, cols, sets)

    elif aggregation_level == 'full-team': # aggregate by season and franchise
        pitching_stats = _aggregate_by_full_team(pitching_stats, cols, sets)

    elif aggregation_level == 'full-franchise': # aggregate by franchise history
        pitching_stats = _aggregate_by_full_franchise(pitching_stats, cols, sets)

    else:
        print(f"Invalid aggregation level '{aggregation_level}'. Valid aggregation levels are 'team', 'type', 'team-type', 'career', 'full-team', 'full-franchise")
        return None

    return pitching_stats


def _pitching_stats_table(df, wls, neutrals, fip_constants, against = False):
    '''
    Function for calculating counting stats from gamelogs. Rate stats are added by this function calling _calculate_pitching_rate_stats().
        df - gamelog dataframe
        wls - pitcher decision dataframe
        neutrals - neutral IP and neutral ER dataframe
        lgn - league neutral ERA dataframe
        fip_constants - fip constants for the league
        against - if True, group by the opponent's (batter's) team/franchise instead of the pitcher's own team/franchise

    Output:
        pitching_stats - dataframe of pitching stats
    '''

    team_col = 'Batter Team' if against else 'Pitcher Team'
    franchise_col = 'Batter Franchise' if against else 'Pitcher Franchise'
    cols = ['Pitcher ID', 'Season', 'Display Season', team_col, franchise_col]

    pitching_stats_exact = pd.pivot_table(df, index = cols, columns = 'Exact Result', aggfunc = 'size', fill_value = 0)
    pitching_stats_old = pd.pivot_table(df, index = cols, columns = ['Exact Result', 'Old Result'], aggfunc = 'size', fill_value = 0)
    pitching_stats_neutral = pd.pivot_table(df, index = cols, columns = 'Result at Neutral', aggfunc = 'size', fill_value = 0)

    pitching_stats = pd.DataFrame(index = pitching_stats_exact.index)

    # Pitching stats that can be directly counted from exact result and/or old result
    pitching_stats['HR'] = pitching_stats_exact.get('HR', 0)
    pitching_stats['3B'] = pitching_stats_exact.get('3B', 0)
    pitching_stats['2B'] = pitching_stats_exact.get('2B', 0)
    pitching_stats['1B'] = pitching_stats_exact.get('1B', 0) + pitching_stats_exact.get('BUNT 1B', 0)
    
    pitching_stats['BB'] = pitching_stats_exact.get('BB', 0) + pitching_stats_exact.get('IBB', 0) + pitching_stats_exact.get('AUTO BB', 0)
    pitching_stats['IBB'] = pitching_stats_exact.get('IBB', 0)
    pitching_stats['Auto BB'] = pitching_stats_exact.get('AUTO BB', 0)
    
    pitching_stats['FO'] = pitching_stats_exact.get('FO', 0)
    pitching_stats['SO'] = pitching_stats_exact.get('K', 0) + pitching_stats_exact.get('AUTO K', 0) + pitching_stats_exact.get('BUNT K', 0)
    pitching_stats['PO'] = pitching_stats_exact.get('PO', 0)
    pitching_stats['RGO'] = pitching_stats_exact.get('RGO', 0)
    pitching_stats['LGO'] = pitching_stats_exact.get('LGO', 0) - pitching_stats_old.get(('LGO','LO'), 0)
    pitching_stats['LO'] = pitching_stats_old.get(('LGO','LO'), 0)
    
    pitching_stats['SF'] = pitching_stats_old.get(('FO','SAC'), 0)
    pitching_stats['SH'] = pitching_stats_exact.get('BUNT SAC', 0)

    pitching_stats['GO'] = pitching_stats['RGO'] + pitching_stats['LGO'] + pitching_stats_exact.get('BUNT GO', 0) + pitching_stats_exact.get('BUNT DP', 0)
    
    pitching_stats['DP'] = pitching_stats_old.get(('RGO','DP'), 0) + pitching_stats_old.get(('LGO','DP'), 0) + pitching_stats_exact.get('BUNT DP', 0)
    pitching_stats['TP'] = pitching_stats_old.get(('LGO', 'TP'), 0)
    
    pitching_stats['SB'] = pitching_stats_exact.get('STEAL 2B', 0) + pitching_stats_exact.get('STEAL 3B', 0) + pitching_stats_exact.get('STEAL HOME', 0) + pitching_stats_exact.get('MSTEAL 3B', 0) +pitching_stats_exact.get('MSTEAL HOME', 0)
    pitching_stats['CS'] = pitching_stats_exact.get('CS 2B', 0) + pitching_stats_exact.get('CS 3B', 0) + pitching_stats_exact.get('CS HOME', 0) + pitching_stats_exact.get('CMS 3B', 0) + pitching_stats_exact.get('CMS HOME', 0)

    # Pitching stats calculated from raw counts
    pitching_stats['H'] = pitching_stats['1B'] + pitching_stats['2B'] + pitching_stats['3B'] + pitching_stats['HR']
    pitching_stats['IP'] = (pitching_stats['FO'] + pitching_stats['SO'] + pitching_stats['PO'] + pitching_stats['RGO'] + pitching_stats['LGO'] + 2 * pitching_stats['LO'] + pitching_stats['DP'] + 2 * pitching_stats['TP'] + pitching_stats['SH'] + pitching_stats_exact.get('BUNT GO', 0) + 2 * pitching_stats_exact.get('BUNT DP', 0) + pitching_stats['CS']) / 3
    pitching_stats['BF'] = pitching_stats['H'] + pitching_stats['BB'] + pitching_stats['FO'] + pitching_stats['SO'] + pitching_stats['PO'] + pitching_stats['RGO'] + pitching_stats['LGO'] + pitching_stats['LO'] + pitching_stats['SH'] + pitching_stats_exact.get('BUNT GO', 0) + pitching_stats_exact.get('BUNT DP', 0)
    pitching_stats['AB'] = pitching_stats['BF'] - (pitching_stats['BB'] + pitching_stats['SF'] + pitching_stats['SH'])
    pitching_stats['TB'] = pitching_stats['1B'] + 2 * pitching_stats['2B'] + 3 * pitching_stats['3B'] + 4 * pitching_stats['HR']

    # Stats that need to be taken from other columns
    pitching_stats['G_list'] = df.groupby(cols)['Game ID'].apply(lambda x: set(x))
    pitching_stats['G'] = pitching_stats['G_list'].apply(lambda x: len(x))
    pitching_stats['ER'] = df.groupby(cols)['Run'].sum()
    pitching_stats['Total Diff'] = df.groupby(cols)['Diff'].sum()
    pitching_stats['Total Plays'] = df.groupby(cols)['Diff'].count()
    pitching_stats['RE24'] = df.groupby(cols)['RE24'].sum()
    pitching_stats['WAR'] = df.groupby(cols)['Pitcher WAR'].sum()
    pitching_stats['WPA'] = df.groupby(cols)['Pitcher WPA'].sum()
    pitching_stats['0 Diffs'] = df.groupby(cols)['Diff'].apply(lambda x: (x == 0).sum())
    pitching_stats['500 Diffs'] = df.groupby(cols)['Diff'].apply(lambda x: (x == 500).sum())
    pitching_stats['300+ Pitches'] = df.groupby(cols)['Diff'].apply(lambda x: (x >= 300).sum())
    pitching_stats['400+ Pitches'] = df.groupby(cols)['Diff'].apply(lambda x: (x >= 400).sum())

    pitching_stats['Last Team'] = df.groupby(['Pitcher ID', 'Season'])['Pitcher Franchise'].last()
    pitching_stats['Last Session'] = df.groupby(cols)['Session'].max()

    pitching_stats = pitching_stats.reset_index()
    pitching_stats = pitching_stats.rename(columns = {'Pitcher ID': 'ID', team_col: 'Team', franchise_col: 'Franchise'})
    
    pitching_stats = pitching_stats.merge(wls, on = ['ID', 'Season', 'Team'], how = 'outer') # add pitcher decisions to dataframe
    pitching_stats = pitching_stats.merge(neutrals, on = ['ID', 'Season', 'Team'], how = 'outer') # add neutral ER and neutral IP to dataframe

    # add FIP constants to dataframe
    if type(fip_constants['Season'].iloc[0]) != type(pitching_stats['Season'].iloc[0]):
        pitching_stats['Season'] = pitching_stats['Season'].astype(float)
    pitching_stats = pitching_stats.merge(fip_constants, on = 'Season')

    # get cumulative league neutral ER and IP and calculate league neutral ERA
    pitching_stats['lgnER'] = pitching_stats.groupby('Season')['nER'].transform('sum')
    pitching_stats['lgnIP'] = pitching_stats.groupby('Season')['nIP'].transform('sum')
    pitching_stats['lgnERA'] = pitching_stats['lgnER'] / pitching_stats['lgnIP'] * 6

    cols_to_fill = ['W', 'L', 'SV', 'HLD', 'BS', 'OPP', 'GS', 'GF', 'CG', 'SHO']
    pitching_stats[cols_to_fill] = pitching_stats[cols_to_fill].fillna(0)

    pitching_stats = _calculate_pitching_rate_stats(pitching_stats)
    
    return pitching_stats


def _calculate_pitching_rate_stats(pitching_stats):
    '''
    Function for calculating rate stats. It's useful to have these separate because they need to be recalled when aggregating data.
        pitching_stats - dataframe of pitching stats

    Output:
        pitching_stats - dataframe with rate stat columns added or recalculated
    '''
    pitching_stats['ERA'] = pitching_stats['ER'] / pitching_stats['IP'] * 6
    pitching_stats['WHIP'] = (pitching_stats['BB'] + pitching_stats['H']) / pitching_stats['IP']
    pitching_stats['FIP'] = (13 * pitching_stats['HR'] + 3 * pitching_stats['BB'] - 2 * pitching_stats['SO']) / pitching_stats['IP'] + pitching_stats['FIP Constant']
    pitching_stats['H6'] = pitching_stats['H'] / pitching_stats['IP'] * 6
    pitching_stats['HR6'] = pitching_stats['HR'] / pitching_stats['IP'] * 6
    pitching_stats['BB6'] = pitching_stats['BB'] / pitching_stats['IP'] * 6
    pitching_stats['SO6'] = pitching_stats['SO'] / pitching_stats['IP'] * 6
    pitching_stats['SO/BB'] = pitching_stats['SO'] / pitching_stats['BB']

    # Opponent batting stats
    pitching_stats['BA'] = pitching_stats['H'] / pitching_stats['AB']
    pitching_stats['OBP'] = (pitching_stats['H'] + pitching_stats['BB']) / (pitching_stats['AB'] + pitching_stats['BB'] + pitching_stats['SF']) # denominator is different from pitching_stats['BF'] if the player has allowed any sacrifice bunts, which count as a batter faced (plate appearance) but don't count toward OBP
    pitching_stats['SLG'] = pitching_stats['TB'] / pitching_stats['BF']
    pitching_stats['OPS'] = pitching_stats['OBP'] + pitching_stats['SLG']
    pitching_stats['BABIP'] = (pitching_stats['H'] - pitching_stats['HR']) / (pitching_stats['AB'] - pitching_stats['SO'] - pitching_stats['HR'] + pitching_stats['SF'])

    pitching_stats['SB%'] = pitching_stats['SB'] / (pitching_stats['SB'] + pitching_stats['CS'])
    pitching_stats['HR%'] = pitching_stats['HR'] / pitching_stats['BF']
    pitching_stats['K%'] = pitching_stats['SO'] / pitching_stats['BF']
    pitching_stats['BB%'] = pitching_stats['BB'] / pitching_stats['BF']
    pitching_stats['GB%'] = (pitching_stats['RGO'] + pitching_stats['LGO']) / (pitching_stats['FO'] + pitching_stats['PO'] + pitching_stats['RGO'] + pitching_stats['LGO'])
    pitching_stats['FB%'] = pitching_stats['FO'] / (pitching_stats['FO'] + pitching_stats['PO'] + pitching_stats['RGO'] + pitching_stats['LGO'])
    pitching_stats['GB/FB'] = pitching_stats['GB%'] / pitching_stats['FB%']

    pitching_stats['W-L%'] = pitching_stats['W'] / (pitching_stats['W'] + pitching_stats['L'])
    pitching_stats['SV%'] = pitching_stats['SV'] / pitching_stats['OPP']

    pitching_stats['nERA'] = pitching_stats['nER'] / pitching_stats['nIP'] * 6

    pitching_stats['Avg Diff'] = pitching_stats['Total Diff'] / pitching_stats['Total Plays'].replace(0, np.nan)

    return pitching_stats
    

def _calculate_era_minus(df):
    '''
    Function for calculating ERA-
        df - hitting stats dataframe with columns nERA, lgnERA

    Output:
        df - dataframe with new ERA- column
    '''

    df['ERA-'] = 100 * df['nERA'] / df['lgnERA']

    return df


def _apply_pitcher_decision_adjustments(pitching_stats, league, against = False):
    '''
    Function for adjusting pitcher Wins and Losses. This is necessary for games that end in a home run derby, as they show as ties in the gamelogs. This is also necessary do to WSH forfeiting S2.11 and DET winning S1.1 due to earlier runner advancement rules.
        pitching_stats - dataframe of pitching stats prior to adjustments being applied
        league - fake baseball league
        against - if True, attribute each adjustment to the opponent team (the other team on the same adjustment row) instead of the pitcher's own team

    Output:
        pitching_stats - df with adjustments applied
    '''

    pda = pd.read_csv('../data/pitcher_decision_adjustments.csv') # read decision adjustments file

    league_pda = pda[pda['League'].str.lower() == league] # filter to league

    # each row pairs a Win+/Loss+ (or Win-/Loss-) team together from the same game, so the
    # opponent for one side is simply the team recorded for the other side of the same row
    win_plus_team_col   = 'Loss+Team' if against else 'Win+Team'
    win_minus_team_col  = 'Loss-Team' if against else 'Win-Team'
    loss_plus_team_col  = 'Win+Team'  if against else 'Loss+Team'
    loss_minus_team_col = 'Win-Team'  if against else 'Loss-Team'

    # create a dataframe for each decision adjustment outcome
    add_win = league_pda.groupby(['Season', 'Win+', win_plus_team_col]).size().reset_index(name = '+W').rename(columns = {'Win+': 'ID', win_plus_team_col: 'Team'})
    lose_win = league_pda.groupby(['Season', 'Win-', win_minus_team_col]).size().reset_index(name = '-W').rename(columns = {'Win-': 'ID', win_minus_team_col: 'Team'})
    add_loss = league_pda.groupby(['Season', 'Loss+', loss_plus_team_col]).size().reset_index(name = '+L').rename(columns = {'Loss+': 'ID', loss_plus_team_col: 'Team'})
    lose_loss = league_pda.groupby(['Season', 'Loss-', loss_minus_team_col]).size().reset_index(name = '-L').rename(columns = {'Loss-': 'ID', loss_minus_team_col: 'Team'})

    # merge to a single dataframe
    merge_columns = ['Season', 'ID', 'Team']
    decision_adjust = add_win.merge(lose_win, on = merge_columns, how = 'outer').fillna(0)
    decision_adjust = decision_adjust.merge(add_loss, on = merge_columns, how = 'outer').fillna(0)
    decision_adjust = decision_adjust.merge(lose_loss, on = merge_columns, how = 'outer').fillna(0)

    # combine columns
    decision_adjust['+W'] = (decision_adjust['+W'] - decision_adjust['-W']).astype(int)
    decision_adjust['+L'] = (decision_adjust['+L'] - decision_adjust['-L']).astype(int)
    
    decision_adjust = decision_adjust.drop(columns = ['-W', '-L']) # drop redundant columns

    if len(decision_adjust) > 0:
        if type(decision_adjust['Season'].iloc[0]) != type(pitching_stats['Season'].iloc[0]):
            decision_adjust['Season'] = decision_adjust['Season'].astype(float)
        pitching_stats = pitching_stats.merge(decision_adjust, on = ['Season', 'ID', 'Team'], how = 'left').fillna(0)
        pitching_stats['W'] += pitching_stats['+W']
        pitching_stats['L'] += pitching_stats['+L']
        pitching_stats = pitching_stats.drop(columns = ['+W', '+L'])

    return pitching_stats


def _aggregate_stats(stats_df, counting_stats, constants, sets, group):
    '''
    Function for aggregating a pitching stats dataframe.
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing
        constants - list of stats that should be nulled if not constant
        group - columns to group by

    Output:
        agg_stats - aggregated dataframe
    '''
    
    agg_dict = _create_agg_dict(counting_stats, constants, sets)
            
    agg_stats = stats_df.groupby(group).agg(agg_dict).reset_index() # aggregate
    
    # use a weighted average to determine league neutral ERA and FIP constant
    weighted_cols = stats_df.groupby(group).apply(lambda g: pd.Series({'FIP Constant': _weighted_average(g, 'FIP Constant', 'IP'), 'lgnERA': _weighted_average(g, 'lgnERA', 'IP')})).reset_index()
    agg_stats['FIP Constant'] = weighted_cols['FIP Constant']
    agg_stats['lgnERA'] = weighted_cols['lgnERA']

    # recalculate rate stats
    agg_stats = _calculate_pitching_rate_stats(agg_stats)

    # calculate ERA-
    agg_stats = _calculate_era_minus(agg_stats)

    return agg_stats


def _aggregate_by_team(stats_df, counting_stats, sets):
    '''
    Function for aggregating a pitching stats dataframe by franchise (team)
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing

    Output
        stats_by_team - pitching stats dataframe aggregated by franchise (team)
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['ID', 'Franchise']

    stats_by_team = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return stats_by_team


def _aggregate_by_type(stats_df, counting_stats, sets):
    '''
    Function for aggregating a pitching stats dataframe by player type
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing

    Output
        stats_by_type - pitching stats dataframe aggregated by player type
    '''
    
    constants = ['Batting Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['ID', 'Pitching Type']

    stats_df = stats_df.copy()
    stats_df['Pitching Type'] = stats_df['Pitching Type'].str.split('-', n = 1).str[0]
    stats_by_type = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return stats_by_type


def _aggregate_by_team_and_type(stats_df, counting_stats, sets):
    '''
    Function for aggregating a pitching stats dataframe by franchise (team) and player type
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing

    Output
        stats_by_teamtype - pitching stats dataframe aggregated by franchise (team) and player type
    '''
    
    constants = ['Batting Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['ID', 'Franchise', 'Pitching Type']

    stats_df = stats_df.copy()
    stats_df['Pitching Type'] = stats_df['Pitching Type'].str.split('-', n = 1).str[0]
    stats_by_teamtype = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return stats_by_teamtype


def _aggregate_by_career(stats_df, counting_stats, sets):
    '''
    Function for aggregating a pitching stats dataframe by player ID
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing

    Output
        career_stats - pitching stats dataframe aggregated by player ID
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = 'ID'

    career_stats = _aggregate_stats(stats_df, counting_stats, constants, sets, group)

    return career_stats


def _aggregate_by_full_team(stats_df, counting_stats, sets):
    '''
    Function for aggregating a pitching stats dataframe for all players on each team
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing

    Output
        full_team_stats - pitching stats dataframe aggregated to each team
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['Season', 'Display Season', 'Team', 'Franchise']

    full_team_stats = _aggregate_stats(stats_df, counting_stats, constants, sets, group)
    full_team_stats['G'] = full_team_stats['G_list'].apply(lambda x: len(x))

    return full_team_stats


def _aggregate_by_full_franchise(stats_df, counting_stats, sets):
    '''
    Function for aggregating a pitching stats dataframe for an entire franchise history
        stats_df - pitching stats dataframe
        counting_stats - list of counting stats for summing

    Output
        full_team_stats - pitching stats dataframe aggregated to each team
    '''
    
    constants = ['Batting Type', 'Pitching Type', 'Handedness', 'Position'] # these attributes are only kept if they're constant
    group = ['Franchise']

    full_franchise_stats = _aggregate_stats(stats_df, counting_stats, constants, sets, group)
    full_franchise_stats['G'] = full_franchise_stats['G_list'].apply(lambda x: len(x))

    return full_franchise_stats