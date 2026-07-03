import json
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
from get_single_game_stats import (
    get_hitting_game_stats, get_pitching_game_stats,
    get_hitting_team_game_stats, get_pitching_team_game_stats,
    get_hitting_combined_game_stats, get_pitching_combined_game_stats,
    get_single_game_records, get_team_game_records, get_combined_game_records,
)
from get_single_game_achievements import get_no_hitters, get_cycles, get_triangles, get_multi_hr_games
from get_streak_records import get_streak_records, _load_streak_cache

def _drop_unused_columns(df):
    '''
    Function for dropping the df columns that aren't used by MLR Reference
    '''
    cols = ['nAB', 'nBB', 'nFO', 'nH', 'nOBP', 'nPA', 'nSF', 'nSH', 'nSLG', 'nTB',
            'lgnAB', 'lgnBB', 'lgnH', 'lgnOBP', 'lgnPA', 'lgnSLG', 'lgnTB',
            'nER', 'nERA', 'nIP', 'lgnERA', 'lgnIP',
            'FIP Constant', 'SF value', 'Total Diff', 'Total Plays', 'G_list',
            'H_RISP', 'AB_RISP']
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
        p_fhs = Path(f'../docs/generated/{league}_franchise_hitting_stats.json')
        p_fps = Path(f'../docs/generated/{league}_franchise_pitching_stats.json')
        p_sgr = Path(f'../docs/generated/{league}_single_game_records.json')
        p_ach = Path(f'../docs/generated/{league}_achievements.json')

        p_hscache = Path(f'../data/cache/{league}_hitting_stats_cache.csv')
        p_pscache = Path(f'../data/cache/{league}_pitching_stats_cache.csv')
    
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
                if p_sgr.exists() and p_ach.exists():
                    print('All files already generated.')
                    continue
            elif p_chs.exists() and p_cps.exists():
                if league in ['milr', 'milr_playoff', 'fcb', 'gib']:
                    if p_sgr.exists() and p_ach.exists():
                        print('All files already generated.')
                        continue
                elif p_hst.exists() and p_pst.exists() and p_hsty.exists() and p_psty.exists() and p_hstty.exists() and p_pstty.exists():
                    if p_sgr.exists() and p_ach.exists():
                        print('All files already generated.')
                        continue
    
        all_seasons = True # default option. Calculate stats for all seasons
        
        if hitting_stats_cache_ex and pitching_stats_cache_ex:
            all_seasons = False # if cached files already exist, use them
            
        if all_seasons:
            print('Loading gamelogs...')
        else:
            print(f'Loading gamelogs for S{season}...')
        gamelog_df = _load_gamelogs(season, league, all_seasons)

        if gamelog_df.empty:
            print(f'No gamelog data for {league} S{season} yet, skipping.')
            continue

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

        print('Computing single-game records...')
        p_hgcache  = Path(f'../data/cache/{league}_hitting_game_stats_cache.csv')
        p_pgcache  = Path(f'../data/cache/{league}_pitching_game_stats_cache.csv')
        p_htgcache = Path(f'../data/cache/{league}_hitting_team_game_stats_cache.csv')
        p_ptgcache = Path(f'../data/cache/{league}_pitching_team_game_stats_cache.csv')
        p_hcgcache = Path(f'../data/cache/{league}_hitting_combined_game_stats_cache.csv')
        p_pcgcache = Path(f'../data/cache/{league}_pitching_combined_game_stats_cache.csv')

        sg_caches_exist = all(p.exists() for p in [
            p_hgcache, p_pgcache, p_htgcache, p_ptgcache, p_hcgcache, p_pcgcache
        ])

        if sg_caches_exist:
            hg_cache  = pd.read_csv(p_hgcache);  hg_cache  = hg_cache[hg_cache['Season']   != season]
            pg_cache  = pd.read_csv(p_pgcache);  pg_cache  = pg_cache[pg_cache['Season']   != season]
            htg_cache = pd.read_csv(p_htgcache); htg_cache = htg_cache[htg_cache['Season'] != season]
            ptg_cache = pd.read_csv(p_ptgcache); ptg_cache = ptg_cache[ptg_cache['Season'] != season]
            hcg_cache = pd.read_csv(p_hcgcache); hcg_cache = hcg_cache[hcg_cache['Season'] != season]
            pcg_cache = pd.read_csv(p_pcgcache); pcg_cache = pcg_cache[pcg_cache['Season'] != season]

            sg_gamelog = gamelog_df

            hitting_game  = pd.concat([hg_cache,  get_hitting_game_stats(sg_gamelog)],          ignore_index=True)
            pitching_game = pd.concat([pg_cache,  get_pitching_game_stats(sg_gamelog)],         ignore_index=True)
            hitting_team  = pd.concat([htg_cache, get_hitting_team_game_stats(sg_gamelog)],     ignore_index=True)
            pitching_team = pd.concat([ptg_cache, get_pitching_team_game_stats(sg_gamelog)],    ignore_index=True)
            hitting_comb  = pd.concat([hcg_cache, get_hitting_combined_game_stats(sg_gamelog)], ignore_index=True)
            pitching_comb = pd.concat([pcg_cache, get_pitching_combined_game_stats(sg_gamelog)],ignore_index=True)
        else:
            if all_seasons:
                sg_gamelog = gamelog_df
            else:
                print(f'Loading all {league} gamelogs for single-game records...')
                sg_gamelog = _load_gamelogs(season, league, all_seasons=True)
                sg_gamelog = _add_re_column(sg_gamelog, league)
                sg_gamelog = _add_war_columns(sg_gamelog)

            hitting_game  = get_hitting_game_stats(sg_gamelog)
            pitching_game = get_pitching_game_stats(sg_gamelog)
            hitting_team  = get_hitting_team_game_stats(sg_gamelog)
            pitching_team = get_pitching_team_game_stats(sg_gamelog)
            hitting_comb  = get_hitting_combined_game_stats(sg_gamelog)
            pitching_comb = get_pitching_combined_game_stats(sg_gamelog)

        if league in active_leagues:
            hitting_game.to_csv(p_hgcache,   index=False)
            pitching_game.to_csv(p_pgcache,  index=False)
            hitting_team.to_csv(p_htgcache,  index=False)
            pitching_team.to_csv(p_ptgcache, index=False)
            hitting_comb.to_csv(p_hcgcache,  index=False)
            pitching_comb.to_csv(p_pcgcache, index=False)

        is_playoff = league.endswith('_playoff')
        player_rec = get_single_game_records(hitting_game, pitching_game, is_playoff=is_playoff)
        team_rec   = get_team_game_records(hitting_team, pitching_team, is_playoff=is_playoff)
        comb_rec   = get_combined_game_records(hitting_comb, pitching_comb, is_playoff=is_playoff)

        with open(p_sgr, 'w') as f:
            json.dump({'player': player_rec, 'team': team_rec, 'combined': comb_rec}, f, indent=2)
        print(f'Single-game records written to {p_sgr}')

        # Exclude the active (incomplete) session from achievements
        if league in active_leagues:
            active_sess = pitching_game[pitching_game['Season'] == season]['Session'].max()
            ach_pitching = pitching_game[~((pitching_game['Season'] == season) & (pitching_game['Session'] == active_sess))]
            ach_hitting  = hitting_game[~((hitting_game['Season'] == season) & (hitting_game['Session'] == active_sess))]
        else:
            ach_pitching = pitching_game
            ach_hitting  = hitting_game

        achievements = {
            'no_hitters': get_no_hitters(ach_pitching, is_playoff=is_playoff),
            'cycles':     get_cycles(ach_hitting, is_playoff=is_playoff),
            'triangles':  get_triangles(ach_hitting, is_playoff=is_playoff),
            'multi_hr':   get_multi_hr_games(ach_hitting, is_playoff=is_playoff),
        }
        with open(p_ach, 'w') as f:
            json.dump(achievements, f, indent=2)
        print(f'Achievements written to {p_ach}')

        if league == 'mlr':
            print('Computing streak records...')
            p_sr_cache = Path('../data/cache/mlr_streak_records_cache.json')
            if not all_seasons and sg_caches_exist:
                sr_cache = _load_streak_cache(p_sr_cache)
                cache_valid = (sr_cache is not None and
                               sr_cache.get('cached_through_season') == season - 1)
                if not cache_valid:
                    print('Loading all mlr gamelogs for streak records...')
                    streak_gamelog = _load_gamelogs(season, 'mlr', all_seasons=True)
                    streak_gamelog = _add_re_column(streak_gamelog, 'mlr')
                    streak_gamelog = _add_war_columns(streak_gamelog)
                else:
                    streak_gamelog = sg_gamelog
            else:
                streak_gamelog = sg_gamelog
            streak_recs = get_streak_records(streak_gamelog, hitting_game,
                                             hitting_team_game_stats=hitting_team,
                                             cache_path=p_sr_cache)
            p_streaks = Path('../docs/generated/mlr_streak_records.json')
            with open(p_streaks, 'w') as f:
                json.dump(streak_recs, f, indent=2)
            print(f'Streak records written to {p_streaks}')

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
    print('Playoff brackets generated.')

if __name__ == '__main__':
    main()