# Test comment
import pandas as pd
import re


def _get_outs_from_result(result):
    # Ensure result is a string for comparison
    result = str(result) if pd.notna(result) else ""
    # Using the sets from scouting_tool.py
    single_out_bip = {
        "FO",
        "LGO",
        "PO",
        "RGO",
        "LO",
        "BUNT Sac",
        "Bunt Sac",
        "Sac",
    }
    strikeouts = {"K", "Auto K", "Bunt K", "AUTO K"}

    if result in single_out_bip:
        return 1
    if result in strikeouts:
        return 1

    # Caught stealing is also an out
    caught_stealing = {"CS 2B", "CS 3B", "CS Home", "CMS 3B", "CMS Home"}
    if result in caught_stealing:
        return 1

    if result.upper() in ["BUNT GO", "BUNT DP"]:
        return 0

    return 0


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
        self.runners_on_base = [False, False, False]
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

    def _simulate_play(
        self,
        obc_after,
        runners_before_play,
        current_outs,
        result,
        old_result,
        diff,
        season,
        pa_type,
    ):
        runs_this_play = 0
        new_runners = list(runners_before_play)
        outs_for_play = _get_outs_from_result(result)

        # Infield-in logic for S7+
        if pa_type == 2 and result in ["RGO", "LGO"]:
            gamestate_tuple = tuple(runners_before_play)
            infield_in_outcomes = {
                # gamestate: (new_runners, runs, outs)
                (False, False, False): (
                    [False, False, False],
                    0,
                    1,
                ),  # 000 -> 000, 1 out
                (True, False, False): ([False, True, False], 0, 1),  # 100 -> 010, 1 out
                (False, True, False): ([False, False, True], 0, 1),  # 010 -> 001, 1 out
                (False, False, True): ([False, False, True], 0, 1),  # 001 -> 001, 1 out
                (True, True, False): ([False, True, True], 0, 1),  # 110 -> 011, 1 out
                (True, False, True): ([False, True, True], 0, 1),  # 101 -> 011, 1 out
                (False, True, True): ([False, True, True], 0, 1),  # 011 -> 011, 1 out
                (True, True, True): (
                    [True, True, True],
                    0,
                    1,
                ),  # 111 -> 111, 1 out (out at home)
            }
            outcome = infield_in_outcomes.get(gamestate_tuple)
            if outcome:
                new_runners, runs_this_play, outs_for_play = outcome
                return new_runners, runs_this_play, outs_for_play

        # --- ERA-BASED LOGIC ---
        # Handle LGO (high diff) first, as it's a special case
        if result == "LGO" and 496 <= diff <= 500:
            gamestate_tuple = tuple(runners_before_play)
            if season >= 9:
                high_diff_lgo_s9_plus_outcomes = {
                    (0, (False, False, False)): ([False, False, False], 0, 1),
                    (0, (True, False, False)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 1st out
                    (0, (False, True, False)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 2nd out
                    (0, (False, False, True)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 3rd out
                    (0, (True, True, False)): (
                        [False, False, False],
                        0,
                        3,
                    ),  # Triple play: 1st, 2nd out
                    (0, (True, False, True)): (
                        [False, False, True],
                        0,
                        2,
                    ),  # Runner on 1st out, 3rd safe
                    (0, (False, True, True)): (
                        [False, False, True],
                        0,
                        2,
                    ),  # Runner on 2nd out, 3rd safe
                    (0, (True, True, True)): (
                        [False, False, True],
                        0,
                        3,
                    ),  # Triple play: 1st, 2nd out, 3rd safe
                    (1, (False, False, False)): ([False, False, False], 0, 1),
                    (1, (True, False, False)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 1st out
                    (1, (False, True, False)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 2nd out
                    (1, (False, False, True)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 3rd out
                    (1, (True, True, False)): (
                        [False, False, False],
                        0,
                        2,
                    ),  # Runner on 1st out, 2nd out (total 3 outs)
                    (1, (True, False, True)): (
                        [False, False, True],
                        0,
                        2,
                    ),  # Runner on 1st out, 3rd safe (total 3 outs)
                    (1, (False, True, True)): (
                        [False, False, True],
                        0,
                        2,
                    ),  # Runner on 2nd out, 3rd safe (total 3 outs)
                    (1, (True, True, True)): (
                        [False, False, True],
                        0,
                        2,
                    ),  # Runner on 1st out, 2nd out, 3rd safe (total 3 outs)
                    (2, (False, False, False)): ([False, False, False], 0, 1),
                    (2, (True, False, False)): ([False, False, False], 0, 1),
                    (2, (False, True, False)): ([False, False, False], 0, 1),
                    (2, (False, False, True)): ([False, False, False], 0, 1),
                    (2, (True, True, False)): ([False, False, False], 0, 1),
                    (2, (True, False, True)): ([False, False, False], 0, 1),
                    (2, (False, True, True)): ([False, False, False], 0, 1),
                    (2, (True, True, True)): ([False, False, False], 0, 1),
                }
                outcome = high_diff_lgo_s9_plus_outcomes.get(
                    (current_outs, gamestate_tuple)
                )
                if outcome:
                    new_runners, runs_this_play, outs_for_play = outcome
                    return new_runners, runs_this_play, outs_for_play
                else:  # Fallback for unexpected states, though the table should be exhaustive
                    outs_for_play = 1
                    new_runners = list(runners_before_play)
                    runs_this_play = 0
                    return new_runners, runs_this_play, outs_for_play

            elif season >= 1 and season <= 8:
                if (
                    runners_before_play[0] and runners_before_play[1]
                ):  # Runners on 1st and 2nd (110) or Bases loaded (111)
                    outs_for_play = 3
                    new_runners = [False, False, False]
                    runs_this_play = 0
                    return (
                        new_runners,
                        runs_this_play,
                        outs_for_play,
                    )  # Only return if it's a triple play
                # If not a triple play, fall through to normal LGO logic.

        # Normal LGO/RGO double play logic (applies to all seasons)
        if result in ["LGO", "RGO"] and runners_before_play[0]:
            outs_for_play = 2
            new_runners = [False, False, False]
            if (current_outs + outs_for_play) < 3:
                if runners_before_play[2]:
                    runs_this_play += 1
                if runners_before_play[1]:
                    new_runners[2] = True
            return new_runners, runs_this_play, outs_for_play

        # Original logic for other seasons
        if str(result).strip() == "DP":
            outs_for_play = 2
            if runners_before_play[0]:
                new_runners = [False, False, False]
                if (current_outs + outs_for_play) < 3:
                    if runners_before_play[2]:
                        runs_this_play += 1
                    if runners_before_play[1]:
                        new_runners[2] = True
            else:
                # This is a non-force DP. Assume a flyout and a runner is doubled-off.
                # No runners advance. The most advanced runner is out.
                new_runners = list(runners_before_play)
                if new_runners[2]:
                    new_runners[2] = False
                elif new_runners[1]:
                    new_runners[1] = False
                runs_this_play = 0
            return new_runners, runs_this_play, outs_for_play
        if str(result).strip() == "TP":
            outs_for_play = 3
            new_runners = [False, False, False]
            runs_this_play = 0
            return new_runners, runs_this_play, outs_for_play

        # --- DEFAULT LOGIC ---
        if result == "HR":
            runs_this_play = sum(runners_before_play) + 1
            new_runners = [False, False, False]
        elif result == "3B":
            runs_this_play = sum(runners_before_play)
            new_runners = [False, False, True]
        elif result == "2B":
            new_runners = [False, False, False]
            if current_outs == 2:
                new_runners[1] = True
                if runners_before_play[2]:
                    runs_this_play += 1
                if runners_before_play[1]:
                    runs_this_play += 1
                if runners_before_play[0]:
                    runs_this_play += 1
            else:
                if runners_before_play[2]:
                    runs_this_play += 1
                if runners_before_play[1]:
                    runs_this_play += 1
                if runners_before_play[0]:
                    new_runners[2] = True
                new_runners[1] = True
        elif result in ["1B", "BUNT 1B", "Bunt 1B"]:
            new_runners = [False, False, False]
            if result == "1B" and current_outs == 2:
                new_runners[0] = True
                if runners_before_play[2]:
                    runs_this_play += 1
                if runners_before_play[1]:
                    runs_this_play += 1
                if runners_before_play[0]:
                    new_runners[2] = True
            else:
                if runners_before_play[2]:
                    runs_this_play += 1
                if runners_before_play[1]:
                    new_runners[2] = True
                if runners_before_play[0]:
                    new_runners[1] = True
                new_runners[0] = True
        elif result.upper() in ["BB", "IBB", "AUTO BB"]:
            if (
                runners_before_play[0]
                and runners_before_play[1]
                and runners_before_play[2]
            ):
                runs_this_play += 1
            if runners_before_play[0] and runners_before_play[1]:
                new_runners[2] = runners_before_play[1]
            if runners_before_play[0]:
                new_runners[1] = runners_before_play[0]
            new_runners[0] = True
        elif result.upper() == "STEAL 2B":
            if runners_before_play[0]:
                new_runners[0] = False
                new_runners[1] = True
        elif result.upper() == "STEAL 3B":
            if runners_before_play[1]:
                new_runners[1] = False
                new_runners[2] = True
        elif result.upper() == "STEAL HOME":
            if runners_before_play[2]:
                new_runners[2] = False
                runs_this_play += 1
        elif result.upper() == "MSTEAL 3B":
            new_runners[2] = runners_before_play[1] or runners_before_play[2]
            new_runners[1] = runners_before_play[0]
            new_runners[0] = False
        elif result.upper() == "MSTEAL HOME":
            if runners_before_play[2]:
                runs_this_play += 1
            new_runners[2] = runners_before_play[1]
            new_runners[1] = runners_before_play[0]
            new_runners[0] = False
        elif result.upper() == "CS 2B":
            if runners_before_play[0]:
                new_runners[0] = False
        elif result.upper() == "CS 3B":
            if runners_before_play[1]:
                new_runners[1] = False
        elif result.upper() == "CS HOME":
            if runners_before_play[2]:
                new_runners[2] = False
        elif result.upper() == "CMS 3B":
            if runners_before_play[1]:
                new_runners[2] = runners_before_play[2]
                new_runners[1] = runners_before_play[0]
                new_runners[0] = False
        elif result.upper() == "CMS HOME":
            if runners_before_play[2]:
                new_runners[2] = runners_before_play[1]
                new_runners[1] = runners_before_play[0]
                new_runners[0] = False
        elif result in ["FO", "Sac"]:
            if current_outs < 2 and runners_before_play[2]:
                runs_this_play += 1
                new_runners[2] = False
        elif result in ["BUNT Sac", "Bunt Sac"]:
            if current_outs < 2:
                if runners_before_play == [False, True, True]:
                    pass
                elif runners_before_play == [True, True, True]:
                    new_runners = [True, True, True]
                else:
                    new_runners = [False, False, False]
                    if runners_before_play[2] or runners_before_play[1]:
                        new_runners[2] = True
                    if runners_before_play[0]:
                        new_runners[1] = True
        elif result.upper() in ["BUNT GO", "BUNT DP"]:
            gamestate_str = "".join(["1" if r else "0" for r in runners_before_play])

            bunt_outcomes = {
                "000": ([False, False, False], 0, 1),
                "100": ([False, False, False], 0, 2),
                "010": ([False, True, False], 0, 1),
                "001": ([False, False, True], 0, 1),
                "110": ([False, False, True], 0, 2),
                "101": ([True, False, True], 0, 1),
                "011": ([False, True, True], 0, 1),
                "111": ([False, True, True], 0, 2),
            }

            outcome = bunt_outcomes.get(gamestate_str)
            if outcome:
                new_runners, runs_this_play, outs_for_play = outcome
                if (current_outs + outs_for_play) > 3:
                    outs_for_play = 3 - current_outs
                    if outs_for_play < 0:
                        outs_for_play = 0
                return new_runners, runs_this_play, outs_for_play
            else:
                outs_for_play = 1
                new_runners = list(runners_before_play)
                runs_this_play = 0
                return new_runners, runs_this_play, outs_for_play
        elif result in ["LGO", "RGO"]:
            if current_outs < 2:
                if result == "RGO":
                    if runners_before_play[2]:
                        runs_this_play += 1
                    new_runners[2] = runners_before_play[1]
                    new_runners[1] = runners_before_play[0]
                    new_runners[0] = False
                elif result == "LGO":
                    if runners_before_play[2]:
                        runs_this_play += 1
                    new_runners[2] = runners_before_play[1] and runners_before_play[0]
                    new_runners[1] = runners_before_play[0] or (
                        runners_before_play[1] and not runners_before_play[0]
                    )
                    new_runners[0] = False
            else:
                new_runners = [False, False, False]

        if (current_outs + outs_for_play) >= 3 and result in [
            "LGO",
            "RGO",
            "BUNT GO",
            "Bunt GO",
            "DP",
            "TP",
        ]:
            runs_this_play = 0

        return new_runners, runs_this_play, outs_for_play

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

        # Pre-calculate the OBC_after for determining ambiguous plays
        self.df["OBC_after"] = (
            pd.to_numeric(
                self.df.groupby(["inning_num", "is_top"])["OBC"].shift(-1),
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
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
                "runners_entered": [False, False, False],
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
                "runners_entered": [False, False, False],
            }
        )

        for index, play in self.df.iterrows():
            inning_num, is_top = play["inning_num"], play["is_top"]

            if self.inning != inning_num or self.top_of_inning != is_top:
                self.outs = 0

            self.inning = inning_num
            self.top_of_inning = is_top

            current_pitcher_id = play["Pitcher ID"]
            current_pitcher_team = play["Pitcher Team"]

            if (
                current_pitcher_team == self.home_team
                and current_pitcher_id != self.home_pitcher
            ):
                self.home_pitcher = current_pitcher_id
                runners_entered = self.obc_to_runners.get(play["OBC"], [False, False, False])
                self.pitching_log.append(
                    {
                        "pitcher_id": self.home_pitcher,
                        "team": self.home_team,
                        "home_score_entered": play["Home Score"],
                        "away_score_entered": play["Away Score"],
                        "inning_entered": self.inning,
                        "top_of_inning_entered": self.top_of_inning,
                        "outs_entered": play["Outs"],
                        "runners_entered": runners_entered,
                    }
                )
            elif (
                current_pitcher_team == self.away_team
                and current_pitcher_id != self.away_pitcher
            ):
                self.away_pitcher = current_pitcher_id
                runners_entered = self.obc_to_runners.get(play["OBC"], [False, False, False])
                self.pitching_log.append(
                    {
                        "pitcher_id": self.away_pitcher,
                        "team": self.away_team,
                        "home_score_entered": play["Home Score"],
                        "away_score_entered": play["Away Score"],
                        "inning_entered": self.inning,
                        "top_of_inning_entered": self.top_of_inning,
                        "outs_entered": play["Outs"],
                        "runners_entered": runners_entered,
                    }
                )

            score_before = (self.home_score, self.away_score)

            current_outs = self.outs
            runners_before_play = self.obc_to_runners.get(
                play["OBC"], [False, False, False]
            )
            obc_after = play["OBC_after"]

            old_result = play["Old Result"]
            if old_result in ["DP", "TP", "Sac"]:
                result = old_result
            else:
                result = play["Exact Result"]

            result = str(result)
            diff_val = play.get("Diff")
            if pd.isna(diff_val):
                diff = 0
            else:
                # Attempt to convert to numeric, coercing errors to NaN
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

            new_runners_on_base, runs_this_play, outs_for_play = self._simulate_play(
                obc_after,
                runners_before_play,
                current_outs,
                result,
                old_result,
                diff,
                season,
                pa_type,
            )
            self.df.loc[index, "calculated_outs"] = outs_for_play
            self.runners_on_base = new_runners_on_base

            if is_top:
                self.away_score += runs_this_play
            else:
                self.home_score += runs_this_play

            self.outs += outs_for_play

            if self.outs >= 3:
                self.runners_on_base = [False, False, False]

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

    # Determine winner and loser
    if game.home_score > game.away_score:
        winning_team = game.home_team
        losing_team = game.away_team
    elif game.away_score > game.home_score:
        winning_team = game.away_team
        losing_team = game.home_team
    else:  # Tie game
        return {}

    # Find the go-ahead lead change
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

    # Calculate innings pitched for each pitcher
    outs_per_pitcher = game.df.groupby("Pitcher ID")["calculated_outs"].sum()
    ip = outs_per_pitcher / 3.0

    starting_pitcher_home = game.df[game.df["Pitcher Team"] == game.home_team][
        "Pitcher ID"
    ].iloc[0]
    starting_pitcher_away = game.df[game.df["Pitcher Team"] == game.away_team][
        "Pitcher ID"
    ].iloc[0]

    if not go_ahead_lead_change:
        # Winning team led from the start
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
        # Determine losing pitcher
        losing_pitcher = (
            go_ahead_lead_change["away_pitcher"]
            if winning_team == game.home_team
            else go_ahead_lead_change["home_pitcher"]
        )
        # Determine winning pitcher of record
        winning_pitcher_of_record = (
            go_ahead_lead_change["home_pitcher"]
            if winning_team == game.home_team
            else go_ahead_lead_change["away_pitcher"]
        )

    win_awarded = False
    winning_pitcher = None

    starting_pitcher_for_winning_team = (
        starting_pitcher_home
        if winning_team == game.home_team
        else starting_pitcher_away
    )

    winning_team_pitchers = game.df[game.df["Pitcher Team"] == winning_team][
        "Pitcher ID"
    ].unique()
    starting_pitcher_for_winning_team = winning_team_pitchers[0]

    if winning_pitcher_of_record == starting_pitcher_for_winning_team:
        if (
            ip.get(starting_pitcher_for_winning_team, 0) >= 3.333
            or len(winning_team_pitchers) == 1
        ):
            winning_pitcher = starting_pitcher_for_winning_team
        else:
            # Starter did not qualify, find first reliever with at least one out
            for pitcher in winning_team_pitchers:
                if (
                    pitcher != starting_pitcher_for_winning_team
                    and ip.get(pitcher, 0) > 0
                ):
                    winning_pitcher = pitcher
                    break
    else:  # Pitcher of record is a reliever
        winning_pitcher = winning_pitcher_of_record

    # Save and Hold Logic
    save_pitcher = None
    holds = []
    winning_team_pitchers = game.df[game.df["Pitcher Team"] == winning_team][
        "Pitcher ID"
    ].unique()

    # Create a dictionary for quick lookup of pitcher entry data
    pitcher_entries = {
        p_id: next((p for p in game.pitching_log if p["pitcher_id"] == p_id), None)
        for p_id in game.df["Pitcher ID"].unique()
    }

    if len(winning_team_pitchers) > 1:  # Must have at least one reliever
        last_pitcher = winning_team_pitchers[-1]

        # Save Logic
        if last_pitcher != winning_pitcher:
            entry = pitcher_entries.get(last_pitcher)
            if entry:
                # Determine lead at time of entry
                if winning_team == game.home_team:
                    lead = entry["home_score_entered"] - entry["away_score_entered"]
                else:
                    lead = entry["away_score_entered"] - entry["home_score_entered"]

                runners_on_entry = sum(1 for r in entry["runners_entered"] if r)
                innings_pitched = ip.get(last_pitcher, 0)

                # Case 1: The "Standard" Save
                cond1 = lead <= 3 and innings_pitched >= 1.0
                # Case 2: The "Tying Run" Save
                cond2 = lead <= runners_on_entry + 2
                # Case 3: The "Long Relief" Save
                cond3 = innings_pitched >= 2.0

                if cond1 or cond2 or cond3:
                    save_pitcher = last_pitcher

        # Hold Logic
        # Iterate through relievers who are not the first or last pitcher
        for i in range(1, len(winning_team_pitchers) - 1):
            pitcher = winning_team_pitchers[i]
            entry = pitcher_entries.get(pitcher)

            if not entry or ip.get(pitcher, 0) == 0:
                continue

            # Check for save situation on entry
            if winning_team == game.home_team:
                lead_entered = (
                    entry["home_score_entered"] - entry["away_score_entered"]
                )
            else:
                lead_entered = (
                    entry["away_score_entered"] - entry["home_score_entered"]
                )
            runners_on_entry = sum(1 for r in entry["runners_entered"] if r)

            is_save_sit = lead_entered <= 3 or lead_entered <= runners_on_entry + 2

            if is_save_sit:
                # Find when the pitcher left and check if lead was intact
                next_pitcher_id = winning_team_pitchers[i + 1]
                exit_info = pitcher_entries.get(next_pitcher_id)
                if exit_info:
                    if winning_team == game.home_team:
                        lead_left = (
                            exit_info["home_score_entered"]
                            - exit_info["away_score_entered"]
                        )
                    else:
                        lead_left = (
                            exit_info["away_score_entered"]
                            - exit_info["home_score_entered"]
                        )

                    if lead_left > 0:
                        holds.append(pitcher)

    # Ensure no pitcher receives multiple decisions
    if winning_pitcher:
        if winning_pitcher == losing_pitcher:  # Should not happen, but for safety
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
        "holds": holds,
    }
