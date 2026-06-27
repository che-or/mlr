import pandas as pd
import ast
from pathlib import Path
from download_gamelogs import _download_gamelogs
from load_gamelogs import _load_gamelogs, _load_player_types
from add_re_column import _add_re_column
from add_war_columns import _add_war_columns
from get_hitting_stats import get_hitting_stats, get_aggregated_hitting_stats
from get_pitching_stats import get_pitching_stats, get_aggregated_pitching_stats
from create_subrows import create_hitting_subrows, create_pitching_subrows
from get_player_names import get_player_names
from update_glossary_re_matrix import update_glossary_re_matrix
from generate_playoff_brackets import generate_brackets

def _drop_unused_columns(df):
    '''
    Function for dropping the df columns that aren't used by MLR Reference
    '''
    cols = ['nAB', 'nBB', 'nFO', 'nH', 'nOBP', 'nPA', 'nSF', 'nSH', 'nSLG', 'nTB',
            'lgnAB', 'lgnBB', 'lgnH', 'lgnOBP', 'lgnPA', 'lgnSLG', 'lgnTB',
            'nER', 'nERA', 'nIP', 'lgnERA', 'lgnIP',
            'FIP Constant', 'SF value', 'Total Diff', 'Total Plays', 'G_list']
    df = df.drop(columns = cols, errors = 'ignore') # ignoring errors effectively creates 'drop column if exists'

    return df
    

def main():
    _download_gamelogs()

    print('Retrieving basic player info...')
    player_names = get_player_names()
    pn = Path('../docs/generated/all_players.json')
    player_names.to_json(pn, orient = 'records', indent = 2)
    
    all_fbb_seasons = pd.read_csv(r'../data/gamelog_links.csv')
    active_leagues = [l.lower() for l in all_fbb_seasons[all_fbb_seasons['Active']]['League'].unique()]
    
    for league in all_fbb_seasons['League'].unique():
        print(f'----- Processing {league} -----')
        league = league.lower()
        hitting_stats_cache_ex = False
        pitching_stats_cache_ex = False
    
        try:
            season = int(all_fbb_seasons[all_fbb_seasons['League'].str.lower() == league]['Season'].iloc[-1])
        except:
            season = int(all_fbb_seasons[all_fbb_seasons['League'].str.lower() == league]['Season'].iloc[-1][:-1])
    
        p_hs = Path(f'../docs/generated/{league}_hitting_stats.json')
        p_ps = Path(f'../docs/generated/{league}_pitching_stats.json')
        p_ths = Path(f'../docs/generated/{league}_team_hitting_stats.json')
        p_tps = Path(f'../docs/generated/{league}_team_pitching_stats.json')
        p_chs = Path(f'../docs/generated/{league}_career_hitting_stats.json')
        p_cps = Path(f'../docs/generated/{league}_career_pitching_stats.json')
        p_hst = Path(f'../docs/generated/{league}_hitting_stats_by_team.json')
        p_pst = Path(f'../docs/generated/{league}_pitching_stats_by_team.json')
        p_hsty = Path(f'../docs/generated/{league}_hitting_stats_by_type.json')
        p_psty = Path(f'../docs/generated/{league}_pitching_stats_by_type.json')
        p_hstty = Path(f'../docs/generated/{league}_hitting_stats_by_team_type.json')
        p_pstty = Path(f'../docs/generated/{league}_pitching_stats_by_team_type.json')
    
        p_hscache = Path(f'../data/{league}_hitting_stats_cache.csv')
        p_pscache = Path(f'../data/{league}_pitching_stats_cache.csv')
    
        # check for cached stats for active leagues
        if league in active_leagues:
            if p_hscache.exists():
                print('Loading cached hitting stats...')
                hitting_stats_cache = pd.read_csv(p_hscache)
                hitting_stats_cache['G_list'] = hitting_stats_cache['G_list'].apply(ast.literal_eval)
                hitting_stats_cache = hitting_stats_cache[hitting_stats_cache['Season'] != season]
                hitting_stats_cache_ex = True
            else:
                hitting_stats_cache_ex = False
                
            if p_pscache.exists():
                print('Loading cached pitching stats...')
                pitching_stats_cache = pd.read_csv(p_pscache)
                pitching_stats_cache['G_list'] = pitching_stats_cache['G_list'].apply(ast.literal_eval)
                pitching_stats_cache = pitching_stats_cache[pitching_stats_cache['Season'] != season]
                pitching_stats_cache_ex = True
            else:
                pitching_stats_cache_ex = False
    
        # check for generated files for inactive leagues
        elif p_hs.exists() and p_ps.exists() and p_ths.exists() and p_tps.exists():
            if league in ['eco', 'npr', 'wbc']:
                print('All files already generated.')
                continue
            elif p_chs.exists() and p_cps.exists():
                if league in ['milr', 'milr_playoff', 'fcb', 'gib']:
                    print('All files already generated.')
                    continue
                elif p_hst.exists() and p_pst.exists() and p_hsty.exists() and p_psty.exists() and p_hstty.exists() and p_pstty.exists():
                    print('All files already generated.')
                    continue
                else:
                    pass
            else:
                pass
    
        all_seasons = True # default option. Calculate stats for all seasons
        
        if hitting_stats_cache_ex and pitching_stats_cache_ex:
            all_seasons = False # if cached files already exist, use them
            
        if all_seasons:
            print('Loading gamelogs...')
        else:
            print(f'Loading gamelogs for S{season}...')
        gamelog_df = _load_gamelogs(season, league, all_seasons)
        gamelog_df = _add_re_column(gamelog_df, league)
        gamelog_df = _add_war_columns(gamelog_df)
    
        if all_seasons:
            print('Loading players...')
        else:
            print(f'Loading players for S{season}...')
        players_df = _load_player_types(season, league, all_seasons)
    
        print('Calculating hitting stats...')
        hitting_stats = get_hitting_stats(gamelog_df, players_df)
    
        if hitting_stats_cache_ex:
            print('Concatenating cached hitting stats...')
            hitting_stats = pd.concat([hitting_stats_cache, hitting_stats], ignore_index = True)
        if league in active_leagues:
            print('Caching hitting stats...')
            hitting_stats.to_csv(p_hscache, index = False)
    
        print('Calculating pitching stats...')
        pitching_stats = get_pitching_stats(gamelog_df, players_df, league)
    
        if pitching_stats_cache_ex:
            print('Concatenating cached pitching stats...')
            pitching_stats = pd.concat([pitching_stats_cache, pitching_stats], ignore_index = True)
        if league in active_leagues:
            print('Caching pitching stats...')
            pitching_stats.to_csv(p_pscache, index = False)
    
        print('Calculating team hitting stats...')
        team_hitting_stats = get_aggregated_hitting_stats(hitting_stats, 'full-team')
        team_hitting_stats = _drop_unused_columns(team_hitting_stats)
        team_hitting_stats.to_json(p_ths, orient = 'records', indent = 2)
    
        print('Calculating team pitching stats...')
        team_pitching_stats = get_aggregated_pitching_stats(pitching_stats, 'full-team')
        team_pitching_stats = _drop_unused_columns(team_pitching_stats)
        team_pitching_stats.to_json(p_tps, orient = 'records', indent = 2)
    
        if league in ['mlr', 'mlr_playoff', 'milr', 'milr_playoff', 'fcb', 'gib']:
            print('Calculating career hitting stats...')
            career_hitting_stats = get_aggregated_hitting_stats(hitting_stats, 'career')
            career_hitting_stats = _drop_unused_columns(career_hitting_stats)
            career_hitting_stats.to_json(p_chs, orient = 'records', indent = 2)
    
            print('Calculating career pitching stats...')
            career_pitching_stats = get_aggregated_pitching_stats(pitching_stats, 'career')
            career_pitching_stats = _drop_unused_columns(career_pitching_stats)
            career_pitching_stats.to_json(p_cps, orient = 'records', indent = 2)
    
            if league in ['mlr', 'mlr_playoff']:
                print('Calculating hitting stats by team...')
                hitting_stats_by_team = get_aggregated_hitting_stats(hitting_stats, 'team')
                hitting_stats_by_team = _drop_unused_columns(hitting_stats_by_team)
                hitting_stats_by_team.to_json(p_hst, orient = 'records', indent = 2)
    
                print('Calculating pitching stats by team...')
                pitching_stats_by_team = get_aggregated_pitching_stats(pitching_stats, 'team')
                pitching_stats_by_team = _drop_unused_columns(pitching_stats_by_team)
                pitching_stats_by_team.to_json(p_pst, orient = 'records', indent = 2)
    
                print('Calculating hitting stats by type...')
                hitting_stats_by_type = get_aggregated_hitting_stats(hitting_stats, 'type')
                hitting_stats_by_type = _drop_unused_columns(hitting_stats_by_type)
                hitting_stats_by_type.to_json(p_hsty, orient = 'records', indent = 2)
    
                print('Calculating pitching stats by type...')
                pitching_stats_by_type = get_aggregated_pitching_stats(pitching_stats, 'type')
                pitching_stats_by_type = _drop_unused_columns(pitching_stats_by_type)
                pitching_stats_by_type.to_json(p_psty, orient = 'records', indent = 2)
    
                print('Calculating hitting stats by team/type...')
                hitting_stats_by_team_type = get_aggregated_hitting_stats(hitting_stats, 'team-type')
                hitting_stats_by_team_type = _drop_unused_columns(hitting_stats_by_team_type)
                hitting_stats_by_team_type.to_json(p_hstty, orient = 'records', indent = 2)
    
                print('Calculating pitching stats by team/type...')
                pitching_stats_by_team_type = get_aggregated_pitching_stats(pitching_stats, 'team-type')
                pitching_stats_by_team_type = _drop_unused_columns(pitching_stats_by_team_type)
                pitching_stats_by_team_type.to_json(p_pstty, orient = 'records', indent = 2)

                print('Calculating franchise history hitting stats...')
                franchise_hitting_stats = get_aggregated_hitting_stats(hitting_stats, 'full-franchise')
                franchise_hitting_stats = _drop_unused_columns(franchise_hitting_stats)
                franchise_hitting_stats.to_json(p_fhs, orient = 'records', indent = 2)

                print('Calculating franchise history pitching stats...')
                franchise_pitching_stats = get_aggregated_pitching_stats(pitching_stats, 'full-franchise')
                franchise_pitching_stats = _drop_unused_columns(franchise_pitching_stats)
                franchise_pitching_stats.to_json(p_fps, orient = 'records', indent = 2)

        # subrows are added after all aggregations so that things aren't counted twice
        hitting_stats = create_hitting_subrows(hitting_stats)
        hitting_stats = _drop_unused_columns(hitting_stats)
        hitting_stats.to_json(p_hs, orient = 'records', indent = 2)

        pitching_stats = create_pitching_subrows(pitching_stats)
        pitching_stats = _drop_unused_columns(pitching_stats)
        pitching_stats.to_json(p_ps, orient = 'records', indent = 2)
        
        print('Processing complete.')

    mlr_rows = all_fbb_seasons[all_fbb_seasons['League'].str.lower() == 'mlr']['Season']
    most_recent_mlr = int(str(mlr_rows.iloc[-1]).rstrip('AB'))
    print('Updating glossary RE Matrix...')
    update_glossary_re_matrix(most_recent_mlr)

    print('Generating playoff brackets...')
    generate_brackets('mlr')
    generate_brackets('milr')

if __name__ == '__main__':
    main()