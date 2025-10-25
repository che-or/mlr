import pandas as pd

def apply_gamelog_corrections(df, group_name):
    """
    Applies manual corrections to the gamelog data for known errors in the raw data.
    
    Args:
        df (pd.DataFrame): The raw gamelog DataFrame for a single game.
        group_name (tuple): A tuple containing the group identifiers, e.g., (season, game_id).
        
    Returns:
        pd.DataFrame: The corrected gamelog DataFrame.
    """
    
    season, game_id = group_name

    # S2, Game 164: Hitter 382 HR in T1
    if season == 'S2' and game_id == 164:
        correction_mask = (
            (df['Hitter ID'] == 382) &
            (df['Inning'] == 'T1') &
            (df['Old Result'] == 'HR')
        )
        df.loc[correction_mask, 'OBC'] = 2
        df.loc[correction_mask, 'RBI'] = 2

    # S3, Game 90: Hitter 192 FO in T5
    elif season == 'S3' and game_id == 90:
        correction_mask = (
            (df['Hitter ID'] == 192) &
            (df['Inning'] == 'T5') &
            (df['Old Result'] == 'FO')
        )
        df.loc[correction_mask, 'OBC'] = 6

    # S3, Game 188: Hitter 299 LGO in T2
    elif season == 'S3' and game_id == 188:
        correction_mask = (
            (df['Hitter ID'] == 299) &
            (df['Inning'] == 'T2') &
            (df['Old Result'] == 'LGO')
        )
        df.loc[correction_mask, 'OBC'] = 6

    # S5, Game 228: Add missing final play and correct a run
    elif season == 'S5' and game_id == 228:
        # Hitter 1733's 3B should have resulted in a run
        run_correction_mask = (
            (df['Hitter ID'] == 1733) &
            (df['Inning'] == 'B6') &
            (df['Exact Result'] == '3B')
        )
        df.loc[run_correction_mask, 'Run'] = 1

        # Add missing final play
        new_play_data = {
            'Hitter': 'Hudson Hildebrandt',
            'Hitter ID': 284,
            'Swing': 447,
            'Pitcher': 'Ryan Gastings',
            'Pitcher ID': 394,
            'Pitch': 633,
            'Old Result': 'Sac',
            'Diff': 186,
            'Inning': 'B6',
            'Outs': 1,
            'OBC': 3,
            'Home Score': 2,
            'Away Score': 2,
            'Batter WPA': 17.99,
            'Pitcher WPA': 17.99,
            'RBI': 1,
            'Run': 0,
            'Scores': 0,
            'Inning ID': 2702,
            'Session': 16,
            'Batter Team': 'TBR',
            'Pitcher Team': 'TOR',
            'Exact Result': 'FO',
            'Result at Neutral': 'Sac',
            'Result All Neutral': 'Sac'
        }
        new_play_df = pd.DataFrame([new_play_data])
        df = pd.concat([df, new_play_df], ignore_index=True)
        
    return df
