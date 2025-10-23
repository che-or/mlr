import pandas as pd
import itertools
from game_processing import Game, _get_outs_from_result

def generate_play_outcome_markdown():
    markdown_content = "# Baseball Play Outcome Rulebook\n\n"
    markdown_content += "This document details the logic for various baseball play outcomes as implemented in the game simulation engine (`game_processing.py`). For each outcome, it shows how the base-out state changes and how many runs are scored.\n\n"

    obc_to_runners = {
        0: [False, False, False], 1: [True, False, False], 2: [False, True, False], 3: [False, False, True],
        4: [True, True, False], 5: [True, False, True], 6: [False, True, True], 7: [True, True, True]
    }

    play_results = [
        'HR', '3B', '2B', '1B', 'BUNT 1B', 'Bunt 1B',
        'BB', 'IBB', 'Auto BB', 'AUTO BB',
        'STEAL 2B', 'STEAL 3B', 'STEAL HOME', 'MSTEAL 3B', 'MSTEAL HOME',
        'FO', 'Sac', 'BUNT Sac', 'Bunt Sac', 'Bunt',
        'LO', 'LGO (normal diff)', 'LGO (high diff) S9+', 'LGO (high diff) S1-8', 'RGO', 'BUNT GO', 'Bunt GO', 'RGO/LGO (Infield In)',
        'DP', 'TP', # Note: These are now mostly handled by LGO/RGO logic
        'K', 'Auto K', 'Bunt K', 'AUTO K', 'PO',
        'CS 2B', 'CS 3B', 'CS Home', 'CS', 'SB', 'CMS 3B', 'CMS Home', 'Bunt DP'
    ]

    dummy_df = pd.DataFrame([{'Inning': 'T1', 'Batter Team': 'A', 'Pitcher Team': 'H', 'Pitcher ID': 'P1', 'OBC': 0, 'Exact Result': '1B', 'Old Result': ''}])
    game_instance = Game(dummy_df)

    logic_explanations = {
        'HR': "All runners on base score, plus the batter. Bases become empty.",
        '3B': "All runners on base score. Batter is on 3rd.",
        '2B': "Standard double. Runners advance two bases. With 2 outs, all runners advance two bases, and the batter is on 2nd.",
        '1B': "Standard single. Runners advance one base. With 2 outs, all runners advance two bases, and the batter is on 1st.",
        'LGO (normal diff)': "A standard groundout. With a runner on 1st, this becomes a 2-out double play.",
        'LGO (high diff) S9+': "A special high-diff result for Season 9+. Can become a lineout (1 out), lineout double play (2 outs), or triple play (3 outs) depending on base state and outs, as per the table.",
        'LGO (high diff) S1-8': "A special high-diff result for Seasons 1-8. Can become a triple play (3 outs) if runners are on 1st and 2nd or bases loaded, otherwise it behaves like a normal LGO.",
        'RGO': "Groundout. With a runner on 1st, this becomes a 2-out double play.",
        'RGO/LGO (Infield In)': "Special logic for seasons 7+ when the infield is playing in. Applies to both RGO and LGO. The batter is out, and runners advance based on a specific set of rules designed to reflect the infield-in strategy.",
        'DP': "Generic Double Play. Primarily used in seasons before S4. In modern seasons, DPs are typically derived from LGO/RGO results.",
        'TP': "Generic Triple Play. In modern seasons, TPs are typically derived from LGO results with high diff.",
        'SB': "Generic Stolen Base. Only occurs in seasons 2 and 3. Runner successfully advances to the next base.",
        'BUNT 1B': "Batter on 1st. Runners advance one base.",
        'Bunt 1B': "Batter on 1st. Runners advance one base.",
        'BB': "Batter on 1st. All forced runners advance one base.",
        'IBB': "Batter on 1st. All forced runners advance one base.",
        'Auto BB': "Batter on 1st. All forced runners advance one base.",
        'AUTO BB': "Batter on 1st. All forced runners advance one base.",
        'STEAL 2B': "Runner on 1st steals 2nd.",
        'STEAL 3B': "Runner on 2nd steals 3rd.",
        'STEAL HOME': "Runner on 3rd steals home.",
        'MSTEAL 3B': "Runner on 1st advances to 2nd, runner on 2nd advances to 3rd.",
        'MSTEAL HOME': "Runner on 1st advances to 2nd, runner on 2nd advances to 3rd, runner on 3rd scores.",
        'FO': "Flyout. Batter is out. Runners advance if tagging up.",
        'Sac': "Sacrifice fly. Batter is out. Runner on 3rd scores.",
        'BUNT Sac': "Sacrifice bunt. Batter is out. Runners advance one base.",
        'Bunt Sac': "Sacrifice bunt. Batter is out. Runners advance one base.",
        'Bunt': "Bunt. Batter is out. Runners advance one base.",
        'LO': "Lineout. Batter is out. Runners hold their bases.",
        'BUNT GO': "Bunt groundout. Batter is out. Runners advance one base.",
        'Bunt GO': "Bunt groundout. Batter is out. Runners advance one base.",
        'K': "Strikeout. Batter is out. Runners hold their bases.",
        'Auto K': "Automatic strikeout. Batter is out. Runners hold their bases.",
        'Bunt K': "Bunt strikeout. Batter is out. Runners hold their bases.",
        'AUTO K': "Automatic strikeout. Batter is out. Runners hold their bases.",
        'PO': "Popout. Batter is out. Runners hold their bases.",
        'CS 2B': "Caught stealing 2nd. Runner on 1st is out.",
        'CS 3B': "Caught stealing 3rd. Runner on 2nd is out.",
        'CS Home': "Caught stealing home. Runner on 3rd is out.",
        'CS': "Caught stealing. Trailing runner is out.",
        'CMS 3B': "Caught stealing 3rd (multiple runners). Trailing runner is out.",
        'CMS HOME': "Caught stealing home (multiple runners). Trailing runner is out."
    }

    # Store the full table content as a string for comparison
    table_content_to_outcomes = {} # Key: full table markdown string, Value: list of outcomes

    for result in play_results:
        current_table_rows = []
        
        season = 9 # Default for most plays
        diff = 0
        pa_type = 0
        sim_result = result

        if result == 'LGO (normal diff)':
            sim_result = 'LGO'
        elif result == 'LGO (high diff) S9+':
            sim_result = 'LGO'
            diff = 496
            season = 9
        elif result == 'LGO (high diff) S1-8':
            sim_result = 'LGO'
            diff = 496
            season = 1
        elif result == 'RGO/LGO (Infield In)':
            sim_result = 'RGO'
            season = 7
            pa_type = 2
        elif result in ['DP', 'TP', 'CS', 'SB']:
            season = 3

        for initial_outs in range(3):
            for obc_key, initial_runners in obc_to_runners.items():
                initial_bases_str = "".join(["1" if r else "0" for r in initial_runners])

                # Filtering logic (from original generate_rulebook.py)
                if result == 'DP' and not (initial_runners[0] and initial_outs < 2):
                    continue
                if result == 'TP' and not (initial_runners[0] and initial_runners[1] and initial_outs == 0):
                    continue
                if result == 'STEAL 2B' and not (initial_runners[0] and not initial_runners[1]):
                    continue
                if result == 'STEAL 3B' and not (initial_runners[1] and not initial_runners[2]):
                    continue
                if result == 'STEAL HOME' and not initial_runners[2]:
                    continue
                if result == 'MSTEAL 3B' and not (initial_runners[0] and initial_runners[1] and not initial_runners[2]):
                    continue
                if result == 'MSTEAL HOME' and not (initial_runners[2] and (initial_runners[0] or initial_runners[1])):
                    continue
                if result == 'CS 2B' and not (initial_runners[0] and not initial_runners[1]):
                    continue
                if result == 'CS 3B' and not (initial_runners[1] and not initial_runners[2]):
                    continue
                if result == 'CS Home' and not initial_runners[2]:
                    continue
                if result == 'CS' and not any(initial_runners):
                    continue
                if result == 'SB' and not any(initial_runners):
                    continue
                if result == 'CMS 3B' and not (initial_runners[0] and initial_runners[1] and not initial_runners[2]):
                    continue
                if result == 'CMS HOME' and not (initial_runners[2] and (initial_runners[0] or initial_runners[1])):
                    continue
                if result in ['Bunt Sac', 'BUNT Sac', 'Bunt']:
                    if initial_bases_str not in ['100', '010', '110', '101']:
                        continue

                new_runners, runs_scored, outs_this_play = game_instance._simulate_play(
                    initial_runners, initial_outs, sim_result, sim_result, diff, season, pa_type
                )
                
                resulting_outs = initial_outs + outs_this_play
                if resulting_outs > 3: resulting_outs = 3

                resulting_bases_str = "".join(["1" if r else "0" for r in new_runners])

                current_table_rows.append(f"| {initial_outs} | {initial_bases_str} | {resulting_bases_str} | {runs_scored} | {resulting_outs} |")
        
        table_header = "| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |\n|---|---|---|---|---|"
        table_content = table_header + "\n" + "\n".join(current_table_rows)

        if table_content not in table_content_to_outcomes:
            table_content_to_outcomes[table_content] = []
        table_content_to_outcomes[table_content].append(result)

    # Now, iterate through table_content_to_outcomes to produce the final markdown
    for table_content, outcomes in table_content_to_outcomes.items():
        markdown_content += f"## Outcomes: {', '.join(outcomes)}\n\n"
        
        # Use the logic_explanations for the first outcome in the list
        first_outcome = outcomes[0]
        markdown_content += f"**Logic:** {logic_explanations.get(first_outcome, 'No specific logic explanation provided.')}\n\n"

        markdown_content += table_content + "\n\n"

    with open("C:\\Users\\tjjoh\\Documents\\MLR\\mlr\\rulebook.md", "w") as f:
        f.write(markdown_content)

if __name__ == "__main__":
    generate_play_outcome_markdown()
