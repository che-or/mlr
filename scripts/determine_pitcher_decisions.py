import pandas as pd
import numpy as np
from functools import reduce
from simulate_runners import _simulate_runners

def _get_pitcher_df(game_df):
    '''
    Function for getting a list of pitchers for each game.
        game_df - dataframe of a gamelog of an individual game

    Output:
        df - dataframe containing pitcher information. Columns are player ID, the number of outs the player recorded, and whether the player is elgible for the win
    '''
    
    pitchers = game_df['Pitcher ID'].unique() # get all pitchers for the game

    df = pd.DataFrame(columns = ['ID', 'Outs', 'WinElg'])

    for pitcher in pitchers: # loop through each pitcher
        pitcher_df = game_df[game_df['Pitcher ID'] == pitcher] # get only the plays for the current pitcher

        # determine how many outs the pitcher got
        outs = (len(pitcher_df[pitcher_df['Exact Result'].str.upper().isin(['FO', 'K', 'PO', 'RGO', 'LGO', 'AUTO K', 'BUNT SAC', 'BUNT K', 'BUNT GO', 'CS 2B', 'CS 3B', 'CS HOME', 'CMS 3B', 'CMS HOME', 'BUNT GO'])]) 
                + 2 * len(pitcher_df[pitcher_df['Exact Result'].str.upper() == 'BUNT DP']) 
                + len(pitcher_df[pitcher_df['Old Result'].str.upper().isin(['DP', 'LO'])]) 
                + 2 * len(pitcher_df[pitcher_df['Old Result'].str.upper() == 'TP']))

        if pitcher == pitchers[0]:
            if outs < 10 and len(pitchers) > 1: # starter is only elgible for the win if they pitch 3.1+ innings
                win_elgibility = False
            else:
                win_elgibility = True
        elif outs == 0: # pitcher must record at least one out to get a win
            win_elgibility = False
        else:
            win_elgibility = True

        pitcher_row = pd.DataFrame([{'ID': pitcher, 'Outs': outs, 'WinElg': win_elgibility}])
        df = pd.concat([df, pitcher_row], ignore_index = True)

    return df


def _get_home_away_pitcher_dfs(game_df):
    '''
    Function for getting pitcher dataframe for each team.
        game_df - dataframe of a gamelog of an individual game

    Outputs:
        home_pitcher_df - dataframe of home team pitchers
        away_pitcher_df - dataframe of away team pitchers
    '''
    home_df = game_df[game_df['Inning'].str.startswith('T')]
    away_df = game_df[game_df['Inning'].str.startswith('B')]

    home_pitcher_df = _get_pitcher_df(home_df)
    away_pitcher_df = _get_pitcher_df(away_df)

    return home_pitcher_df, away_pitcher_df


def _determine_loss(game_df):
    '''
    Function for determining the losing pitcher. The losing pitcher is the pitcher responsible for the runner that scores the go ahead run.
        game_df - dataframe of a gamelog of an individual game

    Outputs:
        loss - ID of losing pitcher
        go_ahead - the go ahead play. This is not where the runner actually scores, it is where the go ahead runner reaches base.
    '''
    # Divide run column into home and away teams
    game_df['Run_Home'] = game_df['Run'].where(game_df['Inning'].str.startswith('B'), 0)
    game_df['Run_Away'] = game_df['Run'].where(game_df['Inning'].str.startswith('T'), 0)

    # Calculate the cumulative runs scored
    game_df['Score_Home'] = game_df['Run_Home'].shift(fill_value = 0).cumsum()
    game_df['Score_Away'] = game_df['Run_Away'].shift(fill_value = 0).cumsum()
    
    # Handle games that end in ties (includes games that are decided in a home run derby)
    final_play = game_df.iloc[-1]
    obc = final_play['OBC']
    runners_before_play = [None, None, None]
    if obc in [1, 4, 5, 7]:
        runners_before_play[0] = 'i'
    if obc in [2, 4, 6, 7]:
        runners_before_play[1] = 'i'
    if obc in [3, 5, 6, 7]:
        runners_before_play[2] = 'i'
    
    final_play_result = _simulate_runners(runners_before_play, final_play['Outs'], final_play['Exact Result'], 
                                          final_play['Diff'], final_play['Season'], final_play['PA Type'], 'i') # simulate final play

    runs_scored = len(final_play_result['runs'])

    home_score = final_play['Home Score']
    away_score = final_play['Away Score']

    if final_play['Inning'].startswith('B'):
        home_score = home_score + runs_scored
    else:
        away_score = away_score + runs_scored

    if home_score == away_score: # tie game
        loss = None
        go_ahead = None

        return loss, go_ahead

    # find the play where the go ahead run reaches base
    go_ahead_idx = game_df[game_df['Score_Home'] == game_df['Score_Away']].index[-1]
    go_ahead = game_df.loc[go_ahead_idx]

    # assign the loss to the pitcher responsible for the runner
    loss = go_ahead['Pitcher ID']

    if not loss: # handle the case where a Manfred runner scores the winning run. The pitcher that starts the Manfred inning is credited with the loss
        loss = game_df[(game_df.index > go_ahead.name) & (game_df['Pitcher ID'].notna())]['Pitcher ID'].iloc[0]

    return loss, go_ahead


def _determine_win(game_df, go_ahead_play, pitcher_df):
    '''
    Function for determining the winning pitcher. The winning pitcher is the pitcher on the mound when their team scores the go ahead run, with exceptions. A pitcher must record at least one out to qualify for the win and a starter must go at least 3.1 innings.
        game_df - dataframe of a gamelog of an individual game
        go_ahead_play - play where the go ahead runner reaches base. Output of the _determine_loss function
        pitcher_df - dataframe of pitchers on the winning team. Output of _get_home_away_pitcher_dfs. Whether the home_pitcher_df or the away_pitcher_df is sent to this function depends on which team the losing pitcher is on.

    Output:
        win - ID of winning pitcher
    '''
    if len(pitcher_df) == 1: # only one pitcher for winning team. This pitcher gets the win even if inelgible (e.g. very short game)
        win = pitcher_df.iloc[0]['ID']
    elif len(pitcher_df[pitcher_df['WinElg'] == True]) == 1: # only one pitcher elgible for the win
        win = pitcher_df[pitcher_df['WinElg'] == True].iloc[0]['ID']
    else:
        # determine provisional winner as the pitcher pitching when the go ahead run is scored. This pitcher may or may not be elgible
        if go_ahead_play['Inning'] == 'T1': # handle the case where the final lead change is in the top of the first
            W_prov = pitcher_df['ID'].iloc[0]
        elif go_ahead_play['Inning'].startswith('T'): # lead change is in the top half of any other inning
            prov_win_df = game_df[(game_df['Inning'].str.startswith('B')) & (game_df.index < go_ahead_play.name)]
            W_prov = prov_win_df.iloc[-1]['Pitcher ID']
        else: # lead change is in the bottom half of an inning
            prov_win_df = game_df[(game_df['Inning'].str.startswith('T')) & (game_df.index < go_ahead_play.name)]
            W_prov = prov_win_df.iloc[-1]['Pitcher ID']

        if pitcher_df[pitcher_df['ID'] == W_prov]['WinElg'].iloc[0]: # if provisional W pitcher is elgible, award W to them
            win = W_prov
        else: # otherwise, award W to first elgible pitcher after provisional W
            W_idx = pitcher_df[pitcher_df['ID'] == W_prov].iloc[0].name
            win = pitcher_df[(pitcher_df.index > W_idx) & (pitcher_df['WinElg'] == True)]['ID'].iloc[0]

    return win


def _determine_save(game_df, pitcher_df, win):
    '''
    Function for determining which pitcher (if any) gets the save. The saving pitcher is the final pitcher on the winning team if:
        - the pitcher enters with their team leading by 3 or fewer runs and the pitcher records at least 3 outs
        - or, the pitcher enters with the tying run on base, at bat, or on deck
        - or, the pitcher pitches the final two innings, no matter the score
        
        game_df - dataframe of a gamelog of an individual game
        pitcher_df - dataframe of pitchers on the winning team. Output of _get_home_away_pitchers_dfs. Whether the home_pitcher_df or the away_pitcher_df is sent to this function depends on which team the losing pitcher is on.
        win - ID of winning pitcher. This pitcher cannot be awarded the save even if they entered in a save situation.

    Output:
        save - ID of saving pitcher, if any. Otherwise None
    '''
    
    last_pitcher = pitcher_df.dropna().iloc[-1] # only the last pitcher may qualify for a save
    
    if last_pitcher['ID'] == win:
        save = None # no save when last pitcher gets the win
    elif last_pitcher['Outs'] >= 6:
        save = last_pitcher['ID'] # long relief save, defined as 2+ innings pitched
    else:
        first_play = game_df[game_df['Pitcher ID'] == last_pitcher['ID']].iloc[0] # get game state when final pitcher enters
        score_diff = abs(first_play['Score_Home'] - first_play['Score_Away']) # get score differential
    
        if score_diff <= 3 and last_pitcher['Outs'] >= 3:
            save = last_pitcher['ID'] # standard save, 1+ IP entering game with <=3 run lead
        else:
            obc = first_play['OBC']
    
            # scenarios where the tying run is on base, at bat, or on deck
            if obc == 0 and score_diff <= 2: # bases empty
                save = last_pitcher['ID']
            elif obc in [1, 2, 3] and score_diff <= 3: # one runner on
                save = last_pitcher['ID']
            elif obc in [4, 5, 6] and score_diff <= 4: # two runners on
                save = last_pitcher['ID']
            elif obc == 7 and score_diff <= 5: # bases loaded
                save = last_pitcher['ID']
            else:
                save = None # if no scenarios apply at this point, no save is awarded

    return save


def _determine_holds(game_df, pitcher_df, win, loss, save):
    '''
    Function for determining which pitchers (if any) are credited with holds. This function should be called twice, once for home_pitcher_df and once for away_pitcher_df
        game_df - dataframe of a gamelog of an individual game
        pitcher_df - dataframe of pitchers for one team
        win - ID of winning pitcher. This pitcher cannot get a hold
        loss - ID of losing pitcher. This pitcher cannot get a hold
        save - ID of saving pitcher. This pitcher cannot get a hold

    Output:
        holds - if multiple elgible pitchers, a list of eligble IDs. If one elgible pitcher, the player ID of that pitcher. If no elgible pitchers, None

    Hold is not an official MLB stat and is therefore not well-defined. Some sources (e.g. bbref, fangraphs) have different requirements for a hold. For fake baseball, I have chosen to define a hold as:
    - Pitcher is a relief pitcher. If the pitcher is the first relief pitcher, the starter must be elgible for the W
    - Pitcher has not already been credited with a W, L, or SV
    - Pitcher enters in a save situation, defined as:
        - The pitchers team has a lead of 3 runs or fewer
        - or, the tying run is on base, at bat, or on deck
    - Pitcher records at least one out
    - Pitcher leaves the game with their team still leading, and has not relinquished the lead at any point
    - Any runners the pitcher leaves on base must not score the tying run. *This is where this hold definition may vary from others. Some sources may only require that the pitcher exits with the lead. I have chosen to add this rule to make the rules for a blown save more like those of losses*
    '''
    
    if pitcher_df['Outs'].iloc[0] >= 10: # if the starter is elgible for the win, the second pitcher can get a hold
        potential_holds = pitcher_df[1:-1]
    else: # if the starter is not elgible for the win, the second pitcher CANNOT get a hold
        potential_holds = pitcher_df[2:-1]
    potential_holds = potential_holds[~potential_holds['ID'].isin([win, loss, save])] # a player cannot earn a win, loss, or save when they get a hold

    holds = []
    
    for idx, pitcher in potential_holds.iterrows():
        if pitcher['Outs'] == 0: # holds require pitcher to get at least one out
            continue

        app_df = game_df[game_df['Pitcher ID'] == pitcher['ID']] # all plays involving the pitcher

        # holds require pitcher to enter with the lead, and maintain the lead the whole time
        if app_df['Inning'].iloc[0].startswith('T'):
            app_df['Score_Diff'] = app_df['Score_Home'] - app_df['Score_Away']
        else:
            app_df['Score_Diff'] = app_df['Score_Away'] - app_df['Score_Home']

        if (app_df['Score_Diff'] > 0).all() and app_df['Score_Diff'].iloc[0] <= 3:
            # holds require pitcher to exit with the lead
            last_play = game_df[game_df['Pitcher ID'] == pitcher['ID']].iloc[-1] # last play involving the pitcher
            if last_play['Inning'].startswith('T'):
                final_diff = last_play['Score_Home'] - (last_play['Score_Away'] + last_play['Run'])
            else:
                final_diff = last_play['Score_Away'] - (last_play['Score_Home'] + last_play['Run'])

            if final_diff <= 0:
                continue
            else: # pitcher exits with the lead
                obc = app_df['OBC'].iloc[0]
                score_diff = app_df['Score_Diff'].iloc[0]
                if obc in [0, 1, 2, 3] and score_diff <= 3: # save situation
                    holds.extend([pitcher['ID']])
                elif obc in [4, 5, 6] and score_diff <= 4: # save situation
                    holds.extend([pitcher['ID']])
                elif obc == 7 and score_diff <= 5: # save situation
                    holds.extend([pitcher['ID']])
                else: # do not award a hold if not a save situation
                    continue
        else:
            continue
            
    return holds


def _determine_blown_saves(game_df, pitcher_df, save):
    '''
    Function for determining which pitchers (if any) are charged with blown saves. This function should be called twice, once for home_pitcher_df and once for away_pitcher_df
        game_df - dataframe of a gamelog of an individual game
        pitcher_df - dataframes of pitchers for one team
        save - ID of saving pitcher. This pitcher cannot get a BS

    Output:
        blown_saves - if multiple elgible pitchers, a list of eligble IDs. If one elgible pitcher, the player ID of that pitcher. If no elgible pitchers, None

    Blown Save is not an official MLB stat and is therefore not well-defined. Some sources (e.g. bbref, fangraphs) have different requirements for a blown save. For fake baseball, I have chosen to define a blown save as:
    - Pitcher is a relief pitcher. If the pitcher is the first relief pitcher, the starter must be elgible for the W
    - Pitcher has not already been credited with a SV or HLD
    - Pitcher enters in a save situation, defined as:
        - The pitchers team has a lead of 3 runs or fewer
        - or, the tying run is on base, at bat, or on deck
    - At some point during the pitcher's outing, the team relinquishes the lead. This includes the case where the pitcher leaves runners on base and the next pitcher allows those runners to score. *This is where this blown save definition may vary from others. Some sources will charge the next pitcher with the blown save, even though they are not responsible for the runners. I have chosen to add this rule to make the rules for a blown save more like those losses.*
    - A player charged with a blown save may also be given a W or L
    '''
    
    if pitcher_df['Outs'].iloc[0] >= 10: # if the starter is elgible for the win, the second pitcher can get a blown save
        potential_bs = pitcher_df[1:]
    else: # if the starter is not elgible for the win, the second pitcher CANNOT get a blown save
        potential_bs = pitcher_df[2:]
    potential_bs = potential_bs[(~potential_bs['ID'].isin(['Save'])) & (potential_bs['ID'].notna())] # a pitcher receiving a save cannot get a blown save

    blown_saves = []

    for idx, pitcher in potential_bs.iterrows():
        app_df = game_df[game_df['Pitcher ID'] == pitcher['ID']] # all plays involving the pitcher

        # pitcher must enter with the lead, and give up that lead
        if app_df['Inning'].iloc[0].startswith('T'):
            app_df['Score_Diff'] = app_df['Score_Home'] - app_df['Score_Away']
        else:
            app_df['Score_Diff'] = app_df['Score_Away'] - app_df['Score_Home']

        start_diff = app_df['Score_Diff'].iloc[0]
        if (start_diff > 0): # pitcher enters with the lead
            obc = app_df['OBC'].iloc[0]
            
            if (obc in [0, 1, 2, 3] and start_diff <= 3) or (obc in [4, 5, 6] and start_diff <= 4) or (obc == 7 and start_diff <= 5): # save situation
                last_play = game_df[game_df['Pitcher ID'] == pitcher['ID']].iloc[-1] # last play involving the pitcher
                if last_play['Inning'].startswith('T'):
                    final_diff = last_play['Score_Home'] - (last_play['Score_Away'] + last_play['Run'])
                else:
                    final_diff = last_play['Score_Away'] - (last_play['Score_Home'] + last_play['Run'])
    
                if final_diff <= 0: # pitcher exits having lost the lead
                    blown_saves.extend([pitcher['ID']])
                elif (app_df['Score_Diff'] <= 0).any(): # pitcher exits with the lead, but lost it along the way. Pitcher is now in line for the W
                    blown_saves.extend([pitcher['ID']])
                else: # pitcher exits with the lead, having never given it up. Pitcher will be credited with a SV or HLD
                    continue 
            else: # not a save situation
                continue
        else: # pitcher enters tied or trailing
            continue

    return blown_saves


def _wls(df, active_season, active_session):
    '''
    Function for creating a dataframe recording wins, losses, saves, holds, and blown saves for each game.
        df - gamelog dataframe for a season or seasons
        active_season - currently ongoing season
        active_session - currently ongoing session

    Output:
        wls - dataframe of pitcher decisions
    '''
    
    wls = pd.DataFrame(columns = ['Season', 'Game ID', 'W', 'L', 'SV', 'HLDH', 'HLDA', 'BSH', 'BSA', 'GSH', 'GSA', 'GFH', 'GFA', 'CGH', 'CGA', 'SHOH', 'SHOA', 'WinTeam', 'LossTeam', 'HomeTeam', 'AwayTeam'])

    for game in df['Game ID'].unique(): # iterate through each game
        game_df = df[df['Game ID'] == game]

        if game_df['Season'].iloc[0] == active_season and game_df['Session'].iloc[0] == active_session: # check if the game is active
            continue
        
        home_pitcher_df, away_pitcher_df = _get_home_away_pitcher_dfs(game_df) # get pitchers for each team

        # determine starting pitchers
        gs_home = home_pitcher_df['ID'].iloc[0]
        gs_away = away_pitcher_df['ID'].iloc[0]

        # determine finishing pitchers
        gf_home = home_pitcher_df[home_pitcher_df['ID'].notna()]['ID'].iloc[-1]
        gf_away = away_pitcher_df[away_pitcher_df['ID'].notna()]['ID'].iloc[-1]

        # determine complete games. Complete games are when a pitcher both starts and finishes the game, no matter the game's length
        if gs_home == gf_home:
            cg_home = gs_home
        else:
            cg_home = None
            
        if gs_away == gf_away:
            cg_away = gs_away
        else:
            cg_away = None

        # determine loss
        loss, go_ahead_play = _determine_loss(game_df)

        # determine shutouts
        sho_home = None
        if cg_home:
            if game_df['Score_Away'].iloc[-1] == 0:
                if game_df['Run'].iloc[-1] == 0 or game_df['Inning'].iloc[-1].startswith('B'): # handles the case of a walk off
                    sho_home = cg_home

        sho_away = None
        if cg_away:
            if game_df['Score_Home'].iloc[-1] == 0:
                if game_df['Run'].iloc[-1] == 0 or game_df['Inning'].iloc[-1].startswith('T'): # handles the case of a walk off
                    sho_away = cg_away

        # determine win and save
        if loss: # some games in leagues outside MLR may end in ties
            if loss in home_pitcher_df['ID'].unique():
                win = _determine_win(game_df, go_ahead_play, away_pitcher_df)
                save = _determine_save(game_df, away_pitcher_df, win)
            else:
                win = _determine_win(game_df, go_ahead_play, home_pitcher_df)
                save = _determine_save(game_df, home_pitcher_df, win)
        else: # no win or save in tie games
            win = None
            save = None
    
        # determine holds
        holds_home = _determine_holds(game_df, home_pitcher_df, win, loss, save)
        holds_away = _determine_holds(game_df, away_pitcher_df, win, loss, save)

        # determine blown saves
        blown_saves_home = _determine_blown_saves(game_df, home_pitcher_df, save)
        blown_saves_away = _determine_blown_saves(game_df, away_pitcher_df, save)

        try:
            win_team = go_ahead_play['Batter Team']
            loss_team = go_ahead_play['Pitcher Team']
        except:
            win_team = None
            loss_team = None

        wls_row = pd.DataFrame([{'Season': game_df['Season'].iloc[0], 'Game ID': game, 'W': win, 'L': loss, 'SV': save, 'HLDH': holds_home, 'HLDA': holds_away, 'BSH': blown_saves_home, 'BSA': blown_saves_away, 'GSH': gs_home, 'GSA': gs_away, 'GFH': gf_home, 'GFA': gf_away, 'CGH': cg_home, 'CGA': cg_away, 'SHOH': sho_home, 'SHOA': sho_away, 'WinTeam': win_team, 'LossTeam': loss_team, 'HomeTeam': game_df['Pitcher Team'].iloc[0], 'AwayTeam': game_df['Batter Team'].iloc[0]}])
        wls = pd.concat([wls, wls_row], ignore_index = True)

    return wls


def get_pitcher_decisions(df, league):
    '''
    Function for getting a dataframe of pitcher decisions, formatted in the same way as stat tables for easy merging.
        df - gamelog dataframe for a season or league
        league - league name. Options mlr, mlr_playoff, milr, fcb, gib, eco, wbc

    Outputs:
        player_decisions - dataframe of pitcher decisions
    '''

    # determine active session
    seasons_df = pd.read_csv(r'../data/gamelog_links.csv') # read file containing season info
    try:
        active_season = seasons_df[(seasons_df['League'].str.upper() == league.upper()) & (seasons_df['Active'])]['Season'].iloc[0]
        try:
            active_season = int(active_season)
        except:
            if active_season[-1] == 'A':
                active_season = int(active_season[:-1]) + 0.1
            elif active_season[-1] == 'B':
                active_season = int(active_season[:-1]) + 0.2
    except:
        active_season = None

    if active_season:
        try:
            active_session = df[df['Season'] == active_season]['Session'].iloc[-1]
        except:
            active_session = None
    else:
        active_session = None

    decisions = _wls(df, active_season, active_session) # get decisions for each game

    # count decisions and reformat
    wins = pd.pivot_table(decisions, index = ['W', 'Season', 'WinTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    wins = wins.rename(columns = {'W': 'ID', 'WinTeam': 'Team', 0: 'Wins'})
    
    losses = pd.pivot_table(decisions, index = ['L', 'Season', 'LossTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    losses = losses.rename(columns = {'L': 'ID', 'LossTeam': 'Team', 0: 'Losses'})
    
    saves = pd.pivot_table(decisions, index = ['SV', 'Season', 'WinTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    saves = saves.rename(columns = {'SV': 'ID', 'WinTeam': 'Team', 0: 'Saves'})
    
    decisions_exploded = decisions.explode('HLDH')
    holds_home = pd.pivot_table(decisions_exploded, index = ['HLDH', 'Season', 'HomeTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    holds_home = holds_home.rename(columns = {'HLDH': 'ID', 'HomeTeam': 'Team', 0: 'Holds_Home'})
    
    decisions_exploded = decisions.explode('HLDA')
    holds_away = pd.pivot_table(decisions_exploded, index = ['HLDA', 'Season', 'AwayTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    holds_away = holds_away.rename(columns = {'HLDA': 'ID', 'AwayTeam': 'Team', 0: 'Holds_Away'})
    
    decisions_exploded = decisions.explode('BSH')
    bs_home = pd.pivot_table(decisions_exploded, index = ['BSH', 'Season', 'HomeTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    bs_home = bs_home.rename(columns = {'BSH': 'ID', 'HomeTeam': 'Team', 0: 'BS_Home'})
    
    decisions_exploded = decisions.explode('BSA')
    bs_away = pd.pivot_table(decisions_exploded, index = ['BSA', 'Season', 'AwayTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    bs_away = bs_away.rename(columns = {'BSA': 'ID', 'AwayTeam': 'Team', 0: 'BS_Away'})

    gs_home = pd.pivot_table(decisions, index = ['GSH', 'Season', 'HomeTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    gs_home = gs_home.rename(columns = {'GSH': 'ID', 'HomeTeam': 'Team', 0: 'GS_Home'})

    gs_away = pd.pivot_table(decisions, index = ['GSA', 'Season', 'AwayTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    gs_away = gs_away.rename(columns = {'GSA': 'ID', 'AwayTeam': 'Team', 0: 'GS_Away'})

    gf_home = pd.pivot_table(decisions, index = ['GFH', 'Season', 'HomeTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    gf_home = gf_home.rename(columns = {'GFH': 'ID', 'HomeTeam': 'Team', 0: 'GF_Home'})

    gf_away = pd.pivot_table(decisions, index = ['GFA', 'Season', 'AwayTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    gf_away = gf_away.rename(columns = {'GFA': 'ID', 'AwayTeam': 'Team', 0: 'GF_Away'})

    cg_home = pd.pivot_table(decisions, index = ['CGH', 'Season', 'HomeTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    cg_home = cg_home.rename(columns = {'CGH': 'ID', 'HomeTeam': 'Team', 0: 'CG_Home'})

    cg_away = pd.pivot_table(decisions, index = ['CGA', 'Season', 'AwayTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    cg_away = cg_away.rename(columns = {'CGA': 'ID', 'AwayTeam': 'Team', 0: 'CG_Away'})

    sho_home = pd.pivot_table(decisions, index = ['SHOH', 'Season', 'HomeTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    sho_home = sho_home.rename(columns = {'SHOH': 'ID', 'HomeTeam': 'Team', 0: 'SHO_Home'})

    sho_away = pd.pivot_table(decisions, index = ['SHOA', 'Season', 'AwayTeam'], aggfunc = 'size', fill_value = 0).reset_index()
    sho_away = sho_away.rename(columns = {'SHOA': 'ID', 'AwayTeam': 'Team', 0: 'SHO_Away'})

    # merge dataframes
    dfs = [wins, losses, saves, holds_home, holds_away, bs_home, bs_away, gs_home, gs_away, gf_home, gf_away, cg_home, cg_away, sho_home, sho_away]
    player_decisions = reduce(lambda l, r: pd.merge(l, r, on = ['ID', 'Season', 'Team'], how = 'outer'), dfs).fillna(0)
    
    player_decisions['HLD'] = player_decisions['Holds_Home'] + player_decisions['Holds_Away']
    player_decisions['BS'] = player_decisions['BS_Home'] + player_decisions['BS_Away']
    player_decisions['GS'] = player_decisions['GS_Home'] + player_decisions['GS_Away']
    player_decisions['GF'] = player_decisions['GF_Home'] + player_decisions['GF_Away']
    player_decisions['CG'] = player_decisions['CG_Home'] + player_decisions['CG_Away']
    player_decisions['SHO'] = player_decisions['SHO_Home'] + player_decisions['SHO_Away']
    
    player_decisions = player_decisions.drop(columns = ['Holds_Home', 'Holds_Away', 'BS_Home', 'BS_Away', 'GS_Home', 'GS_Away', 'GF_Home', 'GF_Away', 'CG_Home', 'CG_Away', 'SHO_Home', 'SHO_Away'])
    player_decisions = player_decisions.rename(columns = {'Wins': 'W', 'Losses': 'L', 'Saves': 'SV'})
    
    player_decisions['OPP'] = player_decisions['SV'] + player_decisions['BS']

    return player_decisions