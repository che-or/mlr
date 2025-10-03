import pandas as pd
import re

def _get_outs_from_result(result, old_result):
    if old_result == 'DP':
        return 2
    if old_result == 'TP':
        return 3

    # Using the sets from scouting_tool.py
    single_out_bip_old = {'FO', 'LGO', 'PO', 'RGO', 'Bunt', 'LO'}
    strikeouts_old = {'K', 'Auto K'}
    
    single_out_bip_new = {'FO', 'LGO', 'PO', 'RGO', 'LO', 'BUNT GO', 'Bunt GO', 'BUNT Sac', 'Bunt Sac'}
    strikeouts_new = {'K', 'Auto K', 'Bunt K', 'AUTO K'}

    if result in single_out_bip_new or old_result in single_out_bip_old:
        return 1
    if result in strikeouts_new or old_result in strikeouts_old:
        return 1
        
    # Caught stealing is also an out
    caught_stealing_old = {'CS'}
    caught_stealing_new = {'CS 2B', 'CS 3B', 'CS Home'}
    if result in caught_stealing_new or old_result in caught_stealing_old:
        return 1

    return 0

class Game:
    def __init__(self, game_df):
        self.df = game_df
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

    def _parse_inning(self, inning_str):
        inning_str = str(inning_str)
        top = 'T' in inning_str
        num = int(re.search(r'\d+', inning_str).group())
        return num, top

    def process_game(self):
        # This method will contain the core logic for processing the game play-by-play.
        # It will update the game state as it iterates through the plays.
        
        # Determine home and away teams.
        if 'B' in str(self.df['Inning'].iloc[0]):
            self.home_team = self.df.iloc[0]['Batter Team']
            self.away_team = self.df.iloc[0]['Pitcher Team']
        else:
            self.home_team = self.df.iloc[0]['Pitcher Team']
            self.away_team = self.df.iloc[0]['Batter Team']

        # Sort by inning number and top/bottom
        self.df = self.df.reset_index()
        self.df['inning_num'], self.df['is_top'] = zip(*self.df['Inning'].apply(self._parse_inning))
        self.df = self.df.sort_values(by=['inning_num', 'is_top', 'index'])

        self.home_pitcher = self.df[self.df['Pitcher Team'] == self.home_team]['Pitcher ID'].iloc[0]
        self.away_pitcher = self.df[self.df['Pitcher Team'] == self.away_team]['Pitcher ID'].iloc[0]

        last_inning = 0

        for index, play in self.df.iterrows():
            inning_num, is_top = play['inning_num'], play['is_top']
            self.inning = inning_num
            self.top_of_inning = is_top

            pitching_team = play['Pitcher Team']

            # Update current pitchers
            if pitching_team == self.home_team:
                self.home_pitcher = play['Pitcher ID']
            else:
                self.away_pitcher = play['Pitcher ID']

            if self.inning != last_inning:
                self.outs = 0
                last_inning = self.inning

            # Store the score before the play
            score_before = (self.home_score, self.away_score)

            # Update score
            runs_scored = play['Run'] if pd.notna(play['Run']) and isinstance(play['Run'], (int, float)) else 0
            if self.top_of_inning:
                self.away_score += runs_scored
            else:
                self.home_score += runs_scored

            # Check for lead change
            if (score_before[0] - score_before[1]) * (self.home_score - self.away_score) <= 0 and (self.home_score != self.away_score):
                self.lead_changes.append({
                    'inning': self.inning,
                    'top_of_inning': self.top_of_inning,
                    'home_score': self.home_score,
                    'away_score': self.away_score,
                    'home_pitcher': self.home_pitcher,
                    'away_pitcher': self.away_pitcher
                })

            # Log pitching changes
            if self.home_pitcher and (not self.pitching_log or self.pitching_log[-1]['pitcher_id'] != self.home_pitcher):
                self.pitching_log.append({
                    'pitcher_id': self.home_pitcher,
                    'team': self.home_team,
                    'inning_entered': self.inning,
                    'outs_entered': self.outs,
                    'home_score_entered': score_before[0],
                    'away_score_entered': score_before[1]
                })
            if self.away_pitcher and (not self.pitching_log or self.pitching_log[-1]['pitcher_id'] != self.away_pitcher):
                self.pitching_log.append({
                    'pitcher_id': self.away_pitcher,
                    'team': self.away_team,
                    'inning_entered': self.inning,
                    'outs_entered': self.outs,
                    'home_score_entered': score_before[0],
                    'away_score_entered': score_before[1]
                })

            # Update outs
            result = play['Exact Result']
            old_result = play['Old Result']
            self.outs += _get_outs_from_result(result, old_result)

            # Reset outs at the end of a half-inning
            if self.outs >= 3:
                self.outs = 0


def get_pitching_decisions(game_df):
    """
    Determines wins, losses, saves, and holds for a single game.
    """
    if game_df.empty:
        return {}

    game = Game(game_df)
    game.process_game()

    # Determine winner and loser
    if game.home_score > game.away_score:
        winning_team = game.home_team
        losing_team = game.away_team
    elif game.away_score > game.home_score:
        winning_team = game.away_team
        losing_team = game.home_team
    else: # Tie game
        return {}

    # Find the go-ahead lead change
    go_ahead_lead_change = None
    for lead_change in reversed(game.lead_changes):
        if (winning_team == game.home_team and lead_change['home_score'] > lead_change['away_score']) or \
           (winning_team == game.away_team and lead_change['away_score'] > lead_change['home_score']):
            go_ahead_lead_change = lead_change
            break

    # Calculate innings pitched for each pitcher
    outs_per_pitcher = game.df.groupby('Pitcher ID').apply(lambda x: x.apply(lambda row: _get_outs_from_result(row['Exact Result'], row['Old Result']), axis=1).sum(), include_groups=False)
    ip = outs_per_pitcher / 3.0

    starting_pitcher_home = game.df[game.df['Pitcher Team'] == game.home_team]['Pitcher ID'].iloc[0]
    starting_pitcher_away = game.df[game.df['Pitcher Team'] == game.away_team]['Pitcher ID'].iloc[0]

    if not go_ahead_lead_change:
        # Winning team led from the start
        winning_pitcher_of_record = starting_pitcher_home if winning_team == game.home_team else starting_pitcher_away
        losing_pitcher = starting_pitcher_away if winning_team == game.home_team else starting_pitcher_home
    else:
        # Determine losing pitcher
        losing_pitcher = go_ahead_lead_change['away_pitcher'] if winning_team == game.home_team else go_ahead_lead_change['home_pitcher']
        # Determine winning pitcher of record
        winning_pitcher_of_record = go_ahead_lead_change['home_pitcher'] if winning_team == game.home_team else go_ahead_lead_change['away_pitcher']

    win_awarded = False
    winning_pitcher = None

    starting_pitcher_for_winning_team = starting_pitcher_home if winning_team == game.home_team else starting_pitcher_away

    winning_team_pitchers = game.df[game.df['Pitcher Team'] == winning_team]['Pitcher ID'].unique()
    starting_pitcher_for_winning_team = winning_team_pitchers[0]

    if winning_pitcher_of_record == starting_pitcher_for_winning_team:
        if ip.get(starting_pitcher_for_winning_team, 0) >= 3.333 or len(winning_team_pitchers) == 1:
            winning_pitcher = starting_pitcher_for_winning_team
        else:
            # Starter did not qualify, find first reliever with at least one out
            for pitcher in winning_team_pitchers:
                if pitcher != starting_pitcher_for_winning_team and ip.get(pitcher, 0) > 0:
                    winning_pitcher = pitcher
                    break
    else: # Pitcher of record is a reliever
        winning_pitcher = winning_pitcher_of_record

    # Save and Hold Logic
    save_pitcher = None
    holds = []
    winning_team_pitchers = game.df[game.df['Pitcher Team'] == winning_team]['Pitcher ID'].unique()

    if len(winning_team_pitchers) > 1: # Must have at least one reliever
        last_pitcher = winning_team_pitchers[-1]
        if last_pitcher != winning_pitcher:
            # Find when the last pitcher entered the game
            last_pitcher_entry = next((p for p in reversed(game.pitching_log) if p['pitcher_id'] == last_pitcher), None)

            if last_pitcher_entry:
                lead = abs(last_pitcher_entry['home_score_entered'] - last_pitcher_entry['away_score_entered'])
                # Condition 1: Entered with lead of 3 or less and pitched 1+ inning
                if lead <= 3 and ip.get(last_pitcher, 0) >= 1:
                    save_pitcher = last_pitcher
                # Condition 3: Pitched 3+ innings
                elif ip.get(last_pitcher, 0) >= 3:
                    save_pitcher = last_pitcher

        # Holds
        for i in range(1, len(winning_team_pitchers) - 1):
            pitcher = winning_team_pitchers[i]
            pitcher_entry = next((p for p in reversed(game.pitching_log) if p['pitcher_id'] == pitcher), None)
            if pitcher_entry:
                lead = abs(pitcher_entry['home_score_entered'] - pitcher_entry['away_score_entered'])
                if lead <= 3 and ip.get(pitcher, 0) > 0:
                    # Check if they left with the lead intact
                    # This is simplified: we assume if they are not the losing pitcher, they left with the lead
                    if pitcher != losing_pitcher:
                        holds.append(pitcher)

    return {
        'win': winning_pitcher,
        'loss': losing_pitcher,
        'save': save_pitcher,
        'holds': holds
    }