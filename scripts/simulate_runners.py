def _simulate_runners(runners_before_play, current_outs, result, diff, season, pa_type, current_hitter_id):
    '''
    Function for simulating a play and tracking runners, runs, and outs.
        runners_before_play - list of player IDs for runners on [1st, 2nd, 3rd]
        current_outs - outs before play
        result - exact result from the gamelog
        diff - difference between swing and pitch. Necessary for determining if triple play or lineout logic should be applied
        season - season number. Necessary for determining if lineout logic should be applied
        pa_type - value representing type of swing. Necessary for determining if infield in logic should be applied
        current_hitter_id - player ID of current hitter

        !IMPORTANT! This function can also track pitcher responsibility by using responsible pitcher ID in place of the IDs in runners_before_play and current_hitter_id

    Output:
        play_outcome - dictionary with keys:
            'runners' - list of resulting player IDs for runners on [1st, 2nd, 3rd]
            'outs' - number of outs recorded on the play
            'runs' - list of player IDs that scored on the play
            'obc' - resulting OBC. Useful for cases where the player IDs of the runners doesn't matter
    '''
    
    runs_this_play = []
    runners_after_play = [None, None, None]
    outs_this_play = 0
    
#-----HIT LOGIC-----
    # Home Runs
    if result == 'HR':
        if runners_before_play[2]: 
            runs_this_play.append(runners_before_play[2]) # runner on third scores
        if runners_before_play[1]: 
            runs_this_play.append(runners_before_play[1]) # runner on second scores
        if runners_before_play[0]: 
            runs_this_play.append(runners_before_play[0]) # runner on first scores
        runs_this_play.append(current_hitter_id) # batter scores
        runners_after_play = [None, None, None] # bases are now empty
    
    # Triples
    if result == '3B':
        if runners_before_play[2]: 
            runs_this_play.append(runners_before_play[2]) # runner on third scores
        if runners_before_play[1]: 
            runs_this_play.append(runners_before_play[1]) # runner on second scores
        if runners_before_play[0]: 
            runs_this_play.append(runners_before_play[0]) # runner on first scores
        runners_after_play = [None, None, current_hitter_id] # batter placed on third base
    
    # Doubles
    if result == '2B':
        # 2-out logic
        if current_outs == 2:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            if runners_before_play[1]: 
                runs_this_play.append(runners_before_play[1]) # runner on second scores
            if runners_before_play[0]: 
                runs_this_play.append(runners_before_play[0]) # runner on first scores
            runners_after_play = [None, current_hitter_id, None] # batter placed on second base
        # regular logic    
        else:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            if runners_before_play[1]: 
                runs_this_play.append(runners_before_play[1]) # runner on second scores
            runners_after_play = [None, current_hitter_id, runners_before_play[0]] # batter placed on second, runner moves first to third
    
    # Singles
    if result == '1B':
        # 2-out logic
        if current_outs == 2:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            if runners_before_play[1]: 
                runs_this_play.append(runners_before_play[1]) # runner on second scores
            runners_after_play = [current_hitter_id, None, runners_before_play[0]] # batter placed of first, runner moves first to third
        # regular logic
        else:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]] # batter placed on first, runner moves second to third, runner moves first to second
    
    # Walks (including intentional and auto walks)
    if result.upper() in ['BB', 'AUTO BB', 'IBB']:
        if runners_before_play[2] and runners_before_play[1] and runners_before_play[0]: 
            # bases loaded
            runs_this_play.append(runners_before_play[2]) # runner on third scores
            runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]] # all runners advance one base, batter placed on first
        elif runners_before_play[1] and runners_before_play[0]: 
            # first and second
            runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]] # runners advance one base, batter placed on first
        elif runners_before_play[0]:
            # runner on first (includes first and third scenario)
            runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[2]] # runner on first moves to second, batter placed on first, any runner on third stays
        else:
            # first base empty
            runners_after_play = [current_hitter_id, runners_before_play[1], runners_before_play[2]] # batter placed on first, runners stay
      
    
#-----OUT LOGIC-----
    # Flyouts (including sacrifice flies)
    if result == 'FO':
        outs_this_play = 1 # one out recorded
        if current_outs < 2: # inning continues 
            if runners_before_play[2]: # sacrifice fly logic
                runs_this_play.append(runners_before_play[2]) # runner on third scores on sacrifice fly
                runners_after_play = [runners_before_play[0], runners_before_play[1], None] # third base now empty
            else: # no sacrifice fly
                runners_after_play = runners_before_play # runners stay
        else: # inning ends
            runners_after_play = [None, None, None] # bases are cleared
    
    # Strikeouts (including bunt and auto strikeouts) & Popouts
    if result.upper() in ['K', 'AUTO K', 'BUNT K', 'PO']:
        outs_this_play = 1 # one out recorded
        if current_outs < 2: # inning continues
            runners_after_play = runners_before_play # runners stay
        else: # inning ends
            runners_after_play = [None, None, None] # bases are cleared
    
    # Right Groundouts
    if result == 'RGO':
        # 2-out logic
        if current_outs == 2:
            outs_this_play = 1 # one out recorded
            runners_after_play = [None, None, None] # bases are cleared 
            
        # infield in logic
        elif pa_type == 2:
            outs_this_play = 1 # no double plays when infield in
            if runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
                # bases loaded - force out at home, all others safe
                runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]]
            elif runners_before_play[2] and runners_before_play[1]:
                # second and third - batter is out, runners hold
                runners_after_play = runners_before_play
            elif runners_before_play[2] and runners_before_play[0]:
                # first and third - batter is out, runner on third holds, runner on first advances to second
                runners_after_play = [None, runners_before_play[0], runners_before_play[2]]
            elif runners_before_play[2]:
                # runner on third - batter is out, runner holds
                runners_after_play = runners_before_play
            elif runners_before_play[1] and runners_before_play[0]:
                # first and second - batter is out, runners advance
                runners_after_play = [None, runners_before_play[0], runners_before_play[1]]
            elif runners_before_play[1]:
                # runner on second - batter is out, runner advances
                runners_after_play = [None, None, runners_before_play[1]]
            elif runners_before_play[0]:
                # runner on first - batter is out, runner advances
                runners_after_play = [None, runners_before_play[0], None]
            else:
                # bases empty - batter is out
                runners_after_play = [None, None, None] # bases remain empty

        # regular logic
        else:
            if runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
                # bases loaded
                outs_this_play = 2 # double play
                if current_outs == 1: # inning ends
                    runners_after_play = [None, None, None] # bases are cleared
                else: # inning continues
                    runs_this_play.append(runners_before_play[2]) # runner on third scores
                    runners_after_play = [None, None, runners_before_play[1]] # runner moves from second to third
            elif runners_before_play[2] and runners_before_play[1]:
                # second and third
                outs_this_play = 1 # one out recorded
                runs_this_play.append(runners_before_play[2]) # runner on third scores
                runners_after_play = [None, None, runners_before_play[1]] # runner moves from second to third
            elif runners_before_play[2] and runners_before_play[0]:
                # first and third
                outs_this_play = 2 # double play
                if current_outs == 1: # inning ends
                    runners_after_play = [None, None, None] # bases are cleared
                else: # inning continues
                    runs_this_play.append(runners_before_play[2]) # runner on third scores
                    runners_after_play = [None, None, None] # bases are now empty
            elif runners_before_play[2]:
                # runner on third
                outs_this_play = 1 # one out recorded
                runs_this_play.append(runners_before_play[2]) # runner on third scores
                runners_after_play = [None, None, None] # bases are now empty
            elif runners_before_play[1] and runners_before_play[0]:
                # first and second
                outs_this_play = 2 # double play
                if current_outs == 1: # inning ends
                    runners_after_play = [None, None, None] # bases are cleared 
                else: # inning continues
                    runners_after_play = [None, None, runners_before_play[1]] # runner moves from second to third
            elif runners_before_play[1]:
                # runner on second
                outs_this_play = 1 # one out recorded
                runners_after_play = [None, None, runners_before_play[1]] # runner moves from second to third
            elif runners_before_play[0]:
                # runner on first
                outs_this_play = 2 # double play
                runners_after_play = [None, None, None] # bases are now empty
            else:
                # bases empty
                outs_this_play = 1 # one out recorded
                runners_after_play = [None, None, None] # bases remain empty
     
    # Left Groundouts
    if result == 'LGO':
        # 2-out logic
        if current_outs == 2:
            outs_this_play = 1 # one out recorded
            runners_after_play = [None, None, None] # bases are cleared
        
        # infield in logic
        elif pa_type == 2:
            outs_this_play = 1 # no double plays when infield in
            if runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
                # bases loaded - force out at home, all others safe
                runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]]
            elif runners_before_play[2] and runners_before_play[1]:
                # second and third - batter is out, runners hold
                runners_after_play = runners_before_play
            elif runners_before_play[2] and runners_before_play[0]:
                # first and third - batter is out, runner on third holds, runner on first advances to second
                runners_after_play = [None, runners_before_play[0], runners_before_play[2]]
            elif runners_before_play[2]:
                # runner on third - batter is out, runner holds
                runners_after_play = runners_before_play
            elif runners_before_play[1] and runners_before_play[0]:
                # first and second - batter is out, runners advance
                runners_after_play = [None, runners_before_play[0], runners_before_play[1]]
            elif runners_before_play[1]:
                # runner on second - batter is out, runner advances
                runners_after_play = [None, None, runners_before_play[1]]
            elif runners_before_play[0]:
                # runner on first - batter is out, runner advances
                runners_after_play = [None, runners_before_play[0], None]
            else:
                # bases empty - batter is out
                runners_after_play = [None, None, None] # bases remain empty
        
        # regular logic
        else:
            if runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
                # bases loaded
                if diff >= 496 and current_outs == 0: # triple play logic
                    outs_this_play = 3 # triple play, inning ends
                    runners_after_play = [None, None, None] # bases are cleared
                else:
                    outs_this_play = 2 # double play
                    if current_outs == 0: # inning continues
                        runs_this_play.append(runners_before_play[2]) # runner on third scores
                        runners_after_play = [None, None, runners_before_play[1]] # runner on second moves to third
                    else: # inning ends
                        runners_after_play = [None, None, None] # bases are cleared
            elif runners_before_play[2] and runners_before_play[1]:
                #second and third
                if diff >= 496 and season >= 9: # lineout logic
                    outs_this_play = 2 # double play - batter out, runner on second doubled off, runner on third stays
                    if current_outs == 0: # inning continues
                        runners_after_play = [None, None, runners_before_play[2]]
                    else: # inning ends
                        runners_after_play = [None, None, None] # bases are cleared
                else:
                    outs_this_play = 1 # one out recorded
                    runs_this_play.append(runners_before_play[2]) # runner on third scores
                    runners_after_play = [None, runners_before_play[1], None] # batter is out, runner on second stays
            elif runners_before_play[2] and runners_before_play[0]:
                # first and third
                if diff >= 496 and season >= 9: # lineout logic
                    outs_this_play = 2 # double play - batter out, runner on second doubled off, runner on third stays
                    if current_outs == 0: # inning continues
                        runners_after_play = [None, None, runners_before_play[2]]
                    else: # inning ends
                        runners_after_play = [None, None, None] # bases are cleared
                else:
                    outs_this_play = 2 # double play - force out at second, batter out
                    if current_outs == 0: # inning continues
                        runs_this_play.append(runners_before_play[2]) # runner on third scores
                        runners_after_play = [None, None, None] # bases are now empty
                    else: # inning ends
                        runners_after_play = [None, None, None] # bases are cleared
            elif runners_before_play[2]:
                # runner on third
                if diff >= 496 and season >= 9: # lineout logic
                    outs_this_play = 2 # double play - batter out, runner on third doubled off
                    if current_outs == 0: # inning continues
                        runners_after_play = [None, None, None] # bases now empty
                    else: # inning ends
                        runners_after_play = [None, None, None] # bases are cleared
                else:
                    outs_this_play = 1 # one out recorded
                    runs_this_play.append(runners_before_play[2]) # runner on third scores
                    runners_after_play = [None, None, None] # bases now empty
            elif runners_before_play[1] and runners_before_play[0]:
                # first and second
                if diff >= 496 and current_outs == 0: # triple play logic
                    outs_this_play = 3 # triple play, inning ends
                    runners_after_play = [None, None, None] # bases are cleared
                else:
                    outs_this_play = 2 # double play
                    if current_outs == 0: # inning continues
                        runners_after_play = [None, None, runners_before_play[1]] # runner on second moves to third
                    else: # inning ends:
                        runners_after_play = [None, None, None] # bases are cleared
            elif runners_before_play[1]:
                # runner on second
                if diff >= 496 and season >= 9: # lineout logic
                    outs_this_play = 2 # double play - batter out, runner on second doubled off
                    if current_outs == 0: # inning continues
                        runners_after_play = [None, None, None] # bases now empty
                    else: # inning ends
                        runners_after_play = [None, None, None] # bases are cleared
                else:
                    outs_this_play = 1 # one out recorded
                    runners_after_play = [None, runners_before_play[1], None] # runner on second stays
            elif runners_before_play[0]:
                # runner on first
                outs_this_play = 2 # double play
                if current_outs == 0: # inning continues
                    runners_after_play = [None, None, None] # bases now empty
                else: # inning ends
                    runners_after_play = [None, None, None] # bases are cleared
            else:
                # bases empty
                outs_this_play = 1 # one out recorded
                runners_after_play = [None, None, None] # bases remain empty
                
                
#-----STOLEN BASE LOGIC-----
    # Steal 2B
    if result.upper() == 'STEAL 2B':
        if runners_before_play[0] and not runners_before_play[1]: # stealing second requires runner on first and empty second
            runners_after_play = [None, runners_before_play[0], runners_before_play[2]] # runner moves from first to second, any runner on third stays
        else:
            runners_after_play = 'Invalid Result' # cannot steal second without runner on first and empty second
    
    # Caught Stealing 2B
    if result == 'CS 2B':
        if runners_before_play[0] and not runners_before_play[1]: # stealing second requires runner on first and empty second
            outs_this_play = 1 # one out recorded
            if current_outs < 2: # inning continues
                runners_after_play = [None, None, runners_before_play[2]] # runner on first removed, any runner on third stays
            else: # inning ends
                runners_after_play = [None, None, None] # bases are cleared
        else:
            runners_after_play = 'Invalid Result' # cannot steal second without runner on first and empty second
          
    # Steal 3B    
    if result.upper() == 'STEAL 3B':
        if runners_before_play[1] and not runners_before_play[2]: # stealing third requires runner on second and empty third
            runners_after_play = [runners_before_play[0], None, runners_before_play[1]] # runner moves from second to third, any runner on first stays
        else:
            runners_after_play = 'Invalid Result' # cannot steal third without runner on second and empty third
            
    # Caught Stealing 3B            
    if result == 'CS 3B':
        if runners_before_play[1] and not runners_before_play[2]: # stealing third requires runner on second and empty third
            outs_this_play = 1 # one out recorded
            if current_outs < 2: # inning continues
                runners_after_play = [runners_before_play[0], None, None] # runner on second removed, any runner on first stays
            else: # inning ends
                runners_after_play = [None, None, None] # bases are cleared
        else:
            runners_after_play = 'Invalid Result' # cannot steal third without runner on second and empty third
    
    # Steal Home
    if result.upper() == 'STEAL HOME':
        if runners_before_play[2]: # stealing home requires runner on third
            runs_this_play.append(runners_before_play[2]) # runner on third scores
            runners_after_play = [runners_before_play[0], runners_before_play[1], None] # runner on third removed, other runners stay
        else:
            runners_after_play = 'Invalid Result' # cannot steal home without runner on third
            
    # Caught Stealing Home        
    if result.upper() == 'CS HOME':
        if runners_before_play[2]: # stealing home requires runner on third
            outs_this_play = 1 # one out recorded
            if current_outs < 2: # inning continues
                runners_after_play = [runners_before_play[0], runners_before_play[1], None] # runner on third removed, other runners stay
            else: # inning ends
                runners_after_play = [None, None, None] # bases are cleared 
        else:
            runners_after_play = 'Invalid Result' # cannot steal home without runner on third
    
    # Multi-steal 3B
    if result.upper() == 'MSTEAL 3B':
        if runners_before_play[1] and runners_before_play[0] and not runners_before_play[2]: # multi-steal of third requires runners on both first and second and empty third
            runners_after_play = [None, runners_before_play[0], runners_before_play[1]] # runner moves from second to third, runner moves from first to second
        else:
            runners_after_play = 'Invalid Result' # cannot multi-steal third without runners on first and second and empty third
    
    # Caught Multi-steal 3B
    if result.upper() == 'CMS 3B':
        if runners_before_play[1] and runners_before_play[0] and not runners_before_play[2]: # multi-steal of third requires runners on both first and second and empty third
            outs_this_play = 1 # one outs recorded
            if current_outs < 2: # inning continues
                runners_after_play = [None, runners_before_play[0], None] # runner from second out at third, runner moves from first to second
            else: # inning ends
                runners_after_play = [None, None, None] # bases are cleared
        else:
            runners_after_play = 'Invalid Result' # cannot multi-steal third without runners on first and second and empty third
    
    # Multi-steal Home
    if result.upper() == 'MSTEAL HOME':
        if runners_before_play[2] and (runners_before_play[0] or runners_before_play[1]): # multi-steal of home requires runner on third and at least one other base
            runs_this_play.append(runners_before_play[2]) # runner on third scores
            runners_after_play = [None, runners_before_play[0], runners_before_play[1]] # any runner on second moves to third, any runner on first moves to second
        else:
            runners_after_play = 'Invalid Result' # cannot multi-steal home without runner on third and at least one other base
    
    # Caught Multi-steal Home
    if result.upper() == 'CMS HOME':
        if runners_before_play[2] and (runners_before_play[0] or runners_before_play[1]): # multi-steal of home requires runner on third and at least one other base
            outs_this_play = 1 # one out recorded
            if current_outs < 2: # inning continues
                runners_after_play = [None, runners_before_play[0], runners_before_play[1]] # any runner on second moves to third, any runner on first moves to second
            else: # inning ends
                runners_after_play = [None, None, None] # bases are cleared
        else:
            runners_after_play = 'Invalid Result' # cannot multi-steal home without runner on third and at least one other base
          
            
#-----BUNT LOGIC-----  
    # Bunt Single
    if result.upper() == 'BUNT 1B':
        if runners_before_play[2]: 
            runs_this_play.append(runners_before_play[2]) # runner on third scores
        runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]] # runner on second moves to third, runner on first moves to second, batter placed on first
    
    # Sacrifice Bunt
    if result.upper() == 'BUNT SAC':
        if current_outs == 2:
            runners_after_play = 'Invalid Result' # cannot have sacrifice bunt with 2 outs
        elif runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
            runners_after_play = 'Invalid Result' # cannot have sacrifice bunt with bases loaded
        elif runners_before_play[2] and runners_before_play[1]:
            runners_after_play = 'Invalid Result' # cannot have sacrifice bunt with runners on second and third
        elif runners_before_play[2] and runners_before_play[0]:
            # first and third - batter is out, runner on first moves to second, runner on third holds
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, runners_before_play[0], runners_before_play[2]]
        elif runners_before_play[2]:
            runners_after_play = 'Invalid Result' # cannot have sacrifice bunt with only runner on third
        elif runners_before_play[1] and runners_before_play[0]:
            # first and second - batter is out, runner on first moves to second, runner on second moves to third
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, runners_before_play[0], runners_before_play[1]]
        elif runners_before_play[1]:
            # runner on second - batter is out, runner moves second to third
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, None, runners_before_play[1]]
        elif runners_before_play[0]:
            # runner on first - batter is out, runner moves first to second
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, runners_before_play[0], None]
        else:
            runners_after_play = 'Invalid Result' # cannot have sacrifice bunt with bases empty
    
    # Bunt Strikeouts are handled with regular strikeout logic
    
    # Bunt Groundout
    if result.upper() == 'BUNT GO':
        if current_outs == 2: # inning ends
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, None, None] # bases are cleared
        elif runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
            # bases loaded - force out at home, all others safe
            outs_this_play = 1 # out out recorded
            runners_after_play = [current_hitter_id, runners_before_play[0], runners_before_play[1]]
        elif runners_before_play[2] and runners_before_play[1]:
            # second and third - batter is out, runners hold
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, runners_before_play[1], runners_before_play[2]]
        elif runners_before_play[2] and runners_before_play[0]:
            # first and third
            if current_outs == 0:
                outs_this_play = 1 # out out recorded
                runners_after_play = [current_hitter_id, None, runners_before_play[2]] # runner on first forced out at second, runner on third holds, batter reaches on fielder's choice
            else:
                runners_after_play = 'Invalid Result' # cannot have bunt groundout with only runners on first and third and 1 out
        elif runners_before_play[2]:
            # runner on third - batter is out, runner holds
            outs_this_play = 1 # out out recorded
            runners_after_play = runners_before_play
        elif runners_before_play[1] and runners_before_play[0]:
            runners_after_play = 'Invalid Result' # cannot have bunt groundout with only runners on first and second
        elif runners_before_play[1]:
            # runner on second - batter is out, runner holds
            outs_this_play = 1 # out out recorded
            runners_after_play = runners_before_play
        elif runners_before_play[0]:
            runners_after_play = 'Invalid Result' # cannot have bunt groundout with only runner on first
        else:
            # bases empty - bases remain empty
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, None, None]
    
    # Bunt Double Play
    if result.upper() == 'BUNT DP':
        if current_outs == 2:
            runners_after_play = 'Invalid Result' # cannot have bunt double play with 2 outs
        elif runners_before_play[2] and runners_before_play[1] and runners_before_play[0]:
            # bases loaded - force out at home, batter out at first, runner on second moves to third, runner on first moves to second
            outs_this_play = 2 # double play
            if current_outs == 0: # inning continues
                runners_after_play = [None, runners_before_play[0], runners_before_play[1]]
            else: # inning ends
                runners_after_play = [None, None, None]
        elif runners_before_play[2] and runners_before_play[1]:
            runners_after_play = 'Invalid Result' # cannot have bunt double play with only runners on second and third
        elif runners_before_play[2] and runners_before_play[0]:
            if current_outs == 0:
                runners_after_play = 'Invalid Result' # cannot have bunt double play with only runners on first and third and no outs
            else: # inning ends
                outs_this_play = 2 # double play
                runners_after_play = [None, None, None]
        elif runners_before_play[2]:
            runners_after_play = 'Invalid Result' # cannot have bunt double play with only runner on third
        elif runners_before_play[1] and runners_before_play[0]:
            # first and second - force out at second, batter out at first, runner on second moves to third
            outs_this_play = 2 # double play
            if current_outs == 0: # inning continues
                runners_after_play = [None, None, runners_before_play[1]]
            else: # inning ends
                runners_after_play = [None, None, None]
        elif runners_before_play[1]:
            runners_after_play = 'Invalid Result' # cannot have bunt double play with only runner on second
        elif runners_before_play[0]:
            # runner on first - force out at second, batter out at first
            outs_this_play = 2 # double play
            if current_outs == 0: # inning continues
                runners_after_play = [None, None, None]
            else: # inning ends
                runners_after_play = [None, None, None]
        else:
            runners_after_play = 'Invalid Result' # cannot have bunt double play with bases empty

#-----MANFRED RUNNER LOGIC-----
    if result.upper() == 'MR1':
        if current_outs == 0 and not runners_before_play[0] and runners_before_play[2] and runners_before_play[1]: # Manfred runner on first can only happen with no outs with runners already placed on second and third
            runners_after_play = [current_hitter_id, runners_before_play[1], runners_before_play[2]]
        else:
            runners_after_play = 'Invalid Result'

    if result.upper() == 'MR2':
        if current_outs == 0 and not runners_before_play[1] and not runners_before_play[0]: # Manfred runner on first can only happen with no outs and will always be filled before first
            runners_after_play = [None, current_hitter_id, runners_before_play[2]]
        else:
            runners_after_play = 'Invalid Result'

    if result.upper() == 'MR3':
        if current_outs == 0 and not runners_before_play[2] and not runners_before_play[1] and not runners_before_play[0]: # Manfred runner on first can only happen with no outs and third will always be filled before any other bases
            runners_after_play = [None, None, current_hitter_id]
        else:
            runners_after_play = 'Invalid Result'

# determine resulting OBC
    if runners_after_play[0]:
        if runners_after_play[1]:
            if runners_after_play[2]:
                resulting_obc = 7
            else:
                resulting_obc = 4
        else:
            if runners_after_play[2]:
                resulting_obc = 5
            else:
                resulting_obc = 1
    elif runners_after_play[1]:
        if runners_after_play[2]:
            resulting_obc = 6
        else:
            resulting_obc = 2
    elif runners_after_play[2]:
        resulting_obc = 3
    else:
        resulting_obc = 0

    # Handle invalid results. These may occur when doing neutral simulation, especially when it comes to stolen bases. If invalid results are found, assume nothing happened and continue the simulation.
    if runners_after_play == 'Invalid Result':
        #print('WARNING: Invalid Result calculation. Assuming nothing happened...')

        #get the OBC from before the play
        if runners_before_play[0]:
            if runners_before_play[1]:
                if runners_before_play[2]:
                    resulting_obc = 7
                else:
                    resulting_obc = 4
            else:
                if runners_before_play[2]:
                    resulting_obc = 5
                else:
                    resulting_obc = 1
        elif runners_before_play[1]:
            if runners_before_play[2]:
                resulting_obc = 6
            else:
                resulting_obc = 2
        elif runners_before_play[2]:
            resulting_obc = 3
        else:
            resulting_obc = 0
            
        play_outcome = {'runners': runners_before_play, 'outs': 0, 'runs': [], 'obc': resulting_obc}
        
    else:
        play_outcome = {'runners': runners_after_play, 'outs': outs_this_play, 'runs': runs_this_play, 'obc': resulting_obc}

    return play_outcome
            