# Test comment
import pandas as pd
import re


def _simulate_play(runners_before_play, current_outs, result, diff, season, pa_type, current_pitcher_id):
    
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
        runs_this_play.append(current_pitcher_id) # batter scores
        runners_after_play = [None, None, None] # bases are now empty
    
    # Triples
    if result == '3B':
        if runners_before_play[2]: 
            runs_this_play.append(runners_before_play[2]) # runner on third scores
        if runners_before_play[1]: 
            runs_this_play.append(runners_before_play[1]) # runner on second scores
        if runners_before_play[0]: 
            runs_this_play.append(runners_before_play[0]) # runner on first scores
        runners_after_play = [None, None, current_pitcher_id] # batter placed on third base
    
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
            runners_after_play = [None, current_pitcher_id, None] # batter placed on second base
        # regular logic    
        else:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            if runners_before_play[1]: 
                runs_this_play.append(runners_before_play[1]) # runner on second scores
            runners_after_play = [None, current_pitcher_id, runners_before_play[0]] # batter placed on second, runner moves first to third
    
    # Singles
    if result == '1B':
        # 2-out logic
        if current_outs == 2:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            if runners_before_play[1]: 
                runs_this_play.append(runners_before_play[1]) # runner on second scores
            runners_after_play = [current_pitcher_id, None, runners_before_play[0]] # batter placed of first, runner moves first to third
        # regular logic
        else:
            if runners_before_play[2]: 
                runs_this_play.append(runners_before_play[2]) # runner on third scores
            runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]] # batter placed on first, runner moves second to third, runner moves first to second
    
    # Walks (including intentional and auto walks)
    if result.upper() in ['BB', 'AUTO BB', 'IBB']:
        if runners_before_play[2] and runners_before_play[1] and runners_before_play[0]: 
            # bases loaded
            runs_this_play.append(runners_before_play[2]) # runner on third scores
            runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]] # all runners advance one base, batter placed on first
        elif runners_before_play[1] and runners_before_play[0]: 
            # first and second
            runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]] # runners advance one base, batter placed on first
        elif runners_before_play[0]:
            # runner on first (includes first and third scenario)
            runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[2]] # runner on first moves to second, batter placed on first, any runner on third stays
        else:
            # first base empty
            runners_after_play = [current_pitcher_id, runners_before_play[1], runners_before_play[2]] # batter placed on first, runners stay
      
    
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
                runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]]
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
                runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]]
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
        runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]] # runner on second moves to third, runner on first moves to second, batter placed on first
    
    # Sacrifice Bunt
    if result.upper() in ['BUNT SAC', 'SAC']:
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
            runners_after_play = [current_pitcher_id, runners_before_play[0], runners_before_play[1]]
        elif runners_before_play[2] and runners_before_play[1]:
            # second and third - batter is out, runners hold
            outs_this_play = 1 # out out recorded
            runners_after_play = [None, runners_before_play[1], runners_before_play[2]]
        elif runners_before_play[2] and runners_before_play[0]:
            # first and third
            if current_outs == 0:
                outs_this_play = 1 # out out recorded
                runners_after_play = [current_pitcher_id, None, runners_before_play[2]] # runner on first forced out at second, runner on third holds, batter reaches on fielder's choice
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


    return runners_after_play, outs_this_play, runs_this_play


class Game:
    def __init__(self, game_df, season_name):
        self.df = game_df
        self.season = int(season_name.replace("S", ""))
        self.home_team = None
        self.away_team = None
        self.home_score = 0
        self.away_score = 0
        self.inning = 1
        self.top_of_inning = True
        self.outs = 0
        self.home_pitcher = None
        self.away_pitcher = None
        self.lead_changes = []
        self.pitching_log = []
        self.runners_on_base = [None, None, None]
        self.obc_to_runners = {
            0: [False, False, False],
            1: [True, False, False],
            2: [False, True, False],
            3: [False, False, True],
            4: [True, True, False],
            5: [True, False, True],
            6: [False, True, True],
            7: [True, True, True],
        }
        self.runners_to_obc = {tuple(v): k for k, v in self.obc_to_runners.items()}

    def _runners_to_obc(self, runners):
        return self.runners_to_obc.get(tuple(runners))
    def _parse_inning(self, inning_str):
        inning_str = str(inning_str)
        top = "T" in inning_str
        num = int(re.search(r"\d+", inning_str).group())
        return num, top

    def process_game(self):
        if "B" in str(self.df["Inning"].iloc[0]):
            self.home_team = self.df.iloc[0]["Batter Team"]
            self.away_team = self.df.iloc[0]["Pitcher Team"]
        else:
            self.home_team = self.df.iloc[0]["Pitcher Team"]
            self.away_team = self.df.iloc[0]["Batter Team"]

        self.df = self.df.reset_index()
        self.df["calculated_outs"] = 0
        self.df["inning_num"], self.df["is_top"] = zip(
            *self.df["Inning"].apply(self._parse_inning)
        )
        self.df = self.df.sort_values(
            by=["inning_num", "is_top", "index"], ascending=[True, False, True]
        )

        self.home_pitcher = self.df[self.df["Pitcher Team"] == self.home_team][
            "Pitcher ID"
        ].iloc[0]
        self.away_pitcher = self.df[self.df["Pitcher Team"] == self.away_team][
            "Pitcher ID"
        ].iloc[0]

        self.pitching_log.append(
            {
                "pitcher_id": self.home_pitcher,
                "team": self.home_team,
                "home_score_entered": self.home_score,
                "away_score_entered": self.away_score,
                "inning_entered": 1,
                "top_of_inning_entered": True,
                "outs_entered": 0,
                "runners_entered": [None, None, None],
            }
        )
        self.pitching_log.append(
            {
                "pitcher_id": self.away_pitcher,
                "team": self.away_team,
                "home_score_entered": self.home_score,
                "away_score_entered": self.away_score,
                "inning_entered": 1,
                "top_of_inning_entered": False,
                "outs_entered": 0,
                "runners_entered": [None, None, None],
            }
        )

        for index, play in self.df.iterrows():
            inning_num, is_top = play["inning_num"], play["is_top"]

            if self.inning != inning_num or self.top_of_inning != is_top:
                self.outs = 0
                self.runners_on_base = [None, None, None]

                # Handle runners on base at the start of an inning (e.g., Manfred runner)
                initial_obc = play.get("OBC", 0)
                if initial_obc != 0:
                    pitcher_for_runner = play["Pitcher ID"]
                    new_runners = [None, None, None]
                    if initial_obc & 1:
                        new_runners[0] = pitcher_for_runner
                    if initial_obc & 2:
                        new_runners[1] = pitcher_for_runner
                    if initial_obc & 4:
                        new_runners[2] = pitcher_for_runner
                    self.runners_on_base = new_runners

            self.inning = inning_num
            self.top_of_inning = is_top

            current_pitcher_id = play["Pitcher ID"]
            current_pitcher_team = play["Pitcher Team"]

            if (
                current_pitcher_team == self.home_team
                and current_pitcher_id != self.home_pitcher
            ):
                self.home_pitcher = current_pitcher_id
                self.pitching_log.append(
                    {
                        "pitcher_id": self.home_pitcher,
                        "team": self.home_team,
                        "home_score_entered": self.home_score,
                        "away_score_entered": self.away_score,
                        "inning_entered": self.inning,
                        "top_of_inning_entered": self.top_of_inning,
                        "outs_entered": self.outs,
                        "runners_entered": self.runners_on_base,
                    }
                )
            elif (
                current_pitcher_team == self.away_team
                and current_pitcher_id != self.away_pitcher
            ):
                self.away_pitcher = current_pitcher_id
                self.pitching_log.append(
                    {
                        "pitcher_id": self.away_pitcher,
                        "team": self.away_team,
                        "home_score_entered": self.home_score,
                        "away_score_entered": self.away_score,
                        "inning_entered": self.inning,
                        "top_of_inning_entered": self.top_of_inning,
                        "outs_entered": self.outs,
                        "runners_entered": self.runners_on_base,
                    }
                )

            score_before = (self.home_score, self.away_score)

            current_outs = self.outs
            runners_before_play = self.runners_on_base

            result = str(play["Exact Result"])
            diff_val = play.get("Diff")
            if pd.isna(diff_val):
                diff = 0
            else:
                numeric_diff = pd.to_numeric(diff_val, errors="coerce")
                if pd.isna(numeric_diff):
                    diff = 0
                else:
                    diff = int(numeric_diff)
            season = self.season

            pa_type_val = play.get("PA Type")
            if pd.isna(pa_type_val):
                pa_type = 0
            else:
                numeric_pa_type = pd.to_numeric(pa_type_val, errors="coerce")
                if pd.isna(numeric_pa_type):
                    pa_type = 0
                else:
                    pa_type = int(numeric_pa_type)

            (
                new_runners_on_base,
                outs_for_play,
                runs_scored_details,
            ) = _simulate_play(
                runners_before_play,
                current_outs,
                result,
                diff,
                season,
                pa_type,
                current_pitcher_id,
            )

            if isinstance(new_runners_on_base, str) and new_runners_on_base == "Invalid Result":
                self.df.loc[index, "calculated_outs"] = 0
                continue 

            self.df.loc[index, "calculated_outs"] = outs_for_play
            self.runners_on_base = new_runners_on_base

            runs_this_play = len(runs_scored_details)
            if is_top:
                self.away_score += runs_this_play
            else:
                self.home_score += runs_this_play

            self.outs += outs_for_play

            if self.outs >= 3:
                self.runners_on_base = [None, None, None]

            if (score_before[0] - score_before[1]) * (
                self.home_score - self.away_score
            ) <= 0 and (self.home_score != self.away_score):
                self.lead_changes.append(
                    {
                        "inning": self.inning,
                        "top_of_inning": self.top_of_inning,
                        "home_score": self.home_score,
                        "away_score": self.away_score,
                        "home_pitcher": self.home_pitcher,
                        "away_pitcher": self.away_pitcher,
                        "runs_scored_details": runs_scored_details,
                    }
                )


def get_pitching_decisions(game_df, season_name):
    """
    Determines wins, losses, saves, and holds for a single game.
    """
    if game_df.empty:
        return {}

    game = Game(game_df, season_name)
    game.process_game()

    if game.home_score > game.away_score:
        winning_team = game.home_team
        losing_team = game.away_team
    elif game.away_score > game.home_score:
        winning_team = game.away_team
        losing_team = game.home_team
    else:
        return {}

    go_ahead_lead_change = None
    for lead_change in reversed(game.lead_changes):
        if (
            winning_team == game.home_team
            and lead_change["home_score"] > lead_change["away_score"]
        ) or (
            winning_team == game.away_team
            and lead_change["away_score"] > lead_change["home_score"]
        ):
            go_ahead_lead_change = lead_change
            break

    outs_per_pitcher = game.df.groupby("Pitcher ID")["calculated_outs"].sum()
    ip = outs_per_pitcher / 3.0

    starting_pitcher_home = game.df[game.df["Pitcher Team"] == game.home_team][
        "Pitcher ID"
    ].iloc[0]
    starting_pitcher_away = game.df[game.df["Pitcher Team"] == game.away_team][
        "Pitcher ID"
    ].iloc[0]

    losing_pitcher = None
    winning_pitcher_of_record = None

    if not go_ahead_lead_change:
        winning_pitcher_of_record = (
            starting_pitcher_home
            if winning_team == game.home_team
            else starting_pitcher_away
        )
        losing_pitcher = (
            starting_pitcher_away
            if winning_team == game.home_team
            else starting_pitcher_home
        )
    else:
        runs_on_play = go_ahead_lead_change["runs_scored_details"]
        num_runs = len(runs_on_play)

        if winning_team == game.home_team:
            score_after = (
                go_ahead_lead_change["home_score"],
                go_ahead_lead_change["away_score"],
            )
            score_before = (score_after[0] - num_runs, score_after[1])
            
            current_home_score = score_before[0]
            for run_pitcher_id in runs_on_play:
                current_home_score += 1
                if current_home_score > score_before[1]:
                    losing_pitcher = run_pitcher_id
                    break
        else:
            score_after = (
                go_ahead_lead_change["home_score"],
                go_ahead_lead_change["away_score"],
            )
            score_before = (score_after[0], score_after[1] - num_runs)

            current_away_score = score_before[1]
            for run_pitcher_id in runs_on_play:
                current_away_score += 1
                if current_away_score > score_before[0]:
                    losing_pitcher = run_pitcher_id
                    break
        
        if not losing_pitcher and runs_on_play:
             losing_pitcher = runs_on_play[0]
        elif not losing_pitcher:
            losing_pitcher = go_ahead_lead_change["away_pitcher"] if winning_team == game.home_team else go_ahead_lead_change["home_pitcher"]


        winning_pitcher_of_record = (
            go_ahead_lead_change["home_pitcher"]
            if winning_team == game.home_team
            else go_ahead_lead_change["away_pitcher"]
        )

    winning_pitcher = None
    winning_team_pitchers = game.df[game.df["Pitcher Team"] == winning_team][
        "Pitcher ID"
    ].unique()
    starting_pitcher_for_winning_team = winning_team_pitchers[0]

    if winning_pitcher_of_record == starting_pitcher_for_winning_team:
        # We'll use 3 1/3 IP (3.333) as the qualifier for our 6-inning games.
        if (ip.get(starting_pitcher_for_winning_team, 0) >= 3.333 or len(winning_team_pitchers) == 1):
            winning_pitcher = starting_pitcher_for_winning_team
        else:
            # Starter did not qualify, find first reliever with at least one out
            winning_pitcher = None
            for pitcher in winning_team_pitchers:
                if (
                    pitcher != starting_pitcher_for_winning_team
                    and ip.get(pitcher, 0) > 0
                ):
                    winning_pitcher = pitcher
                    break
    else:  # Pitcher of record is a reliever
        winning_pitcher = winning_pitcher_of_record

    save_pitcher = None
    holds = []
    pitcher_entries = {
        p["pitcher_id"]: p for p in game.pitching_log
    }
    
    if len(winning_team_pitchers) > 1:
        last_pitcher = winning_team_pitchers[-1]

        if last_pitcher != winning_pitcher:
            entry = pitcher_entries.get(last_pitcher)
            if entry:
                if winning_team == game.home_team:
                    lead = entry["home_score_entered"] - entry["away_score_entered"]
                else:
                    lead = entry["away_score_entered"] - entry["home_score_entered"]
                
                runners_on = sum(1 for r in entry["runners_entered"] if r)
                tying_run_on_deck = (lead - runners_on) <= 2
                
                # Save criteria
                if ip.get(last_pitcher, 0) > 0 and lead > 0:
                    if (lead <= 3 and ip.get(last_pitcher, 0) >= 1.0) or \
                       tying_run_on_deck or \
                       (ip.get(last_pitcher, 0) >= 2.0):
                        save_pitcher = last_pitcher

        for i in range(1, len(winning_team_pitchers)):
            p_id = winning_team_pitchers[i]
            if p_id == winning_pitcher or p_id == save_pitcher or ip.get(p_id, 0) == 0:
                continue

            entry = pitcher_entries.get(p_id)
            if not entry or entry['outs_entered'] >= 3:
                continue

            if winning_team == game.home_team:
                lead_entered = entry["home_score_entered"] - entry["away_score_entered"]
            else:
                lead_entered = entry["away_score_entered"] - entry["home_score_entered"]

            runners_on = sum(1 for r in entry["runners_entered"] if r)
            tying_run_on_deck = (lead_entered - runners_on) <= 2

            if lead_entered > 0 and (lead_entered <= 3 or tying_run_on_deck):
                # Find exit data
                exit_pitcher_index = i + 1
                if exit_pitcher_index < len(winning_team_pitchers):
                    next_pitcher_id = winning_team_pitchers[exit_pitcher_index]
                    exit_info = pitcher_entries.get(next_pitcher_id)
                    if exit_info:
                        if winning_team == game.home_team:
                            lead_left = exit_info["home_score_entered"] - exit_info["away_score_entered"]
                        else:
                            lead_left = exit_info["away_score_entered"] - exit_info["home_score_entered"]
                        
                        if lead_left > 0:
                            holds.append(p_id)

    if winning_pitcher:
        if winning_pitcher == losing_pitcher:
            losing_pitcher = None
        if winning_pitcher == save_pitcher:
            save_pitcher = None
        holds = [h for h in holds if h != winning_pitcher]

    if losing_pitcher:
        if losing_pitcher == save_pitcher:
            save_pitcher = None
        holds = [h for h in holds if h != losing_pitcher]
    
    if save_pitcher:
        holds = [h for h in holds if h != save_pitcher]

    return {
        "win": winning_pitcher,
        "loss": losing_pitcher,
        "save": save_pitcher,
        "holds": list(set(holds)),
    }
