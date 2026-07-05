import pandas as pd
from we_matrix import _we_lookup
from simulate_runners import _simulate_runners

EXCLUDED_PA_TYPES = [0, 15] # Manfred runners and trailing runners on multisteals get no WPA


def _obc_to_runners(obc):
    '''
    Function for converting an OBC code into a runners-on-base list, matching the mapping used
    throughout the rest of the codebase (e.g. add_re_column.py). Player IDs don't matter here,
    only whether a base is occupied, so occupied bases are filled with a placeholder.
        obc - on-base code, 0-7

    Output: list of 3 values for [1st, 2nd, 3rd], each either 'runner' (occupied) or None
    '''

    return [
        'runner' if obc in [1, 4, 5, 7] else None,
        'runner' if obc in [2, 4, 6, 7] else None,
        'runner' if obc in [3, 5, 6, 7] else None,
    ]


def _find_leadoff_obc(game_ids, top_bots, inning_nums, outs, obcs, game_id, top_bot, inning_num):
    '''
    Function for finding the OBC a half-inning actually started with (its first real PA, Outs=0),
    used to carry a Manfred runner from the top of an extra inning to the bottom of the same inning
    (Manfred runners are placed identically in both halves of the same inning).

    Output: the leadoff OBC if that half-inning's data exists in this game, else None
    '''

    for j in range(len(game_ids)):
        if game_ids[j] == game_id and top_bots[j] == top_bot and inning_nums[j] == inning_num and outs[j] == 0:
            return obcs[j]
    return None


def _parse_inning(inning):
    '''
    Function for parsing a gamelog 'Inning' value (e.g. 'T1', 'B6') into its parts.
        inning - string in the form 'T#' (top, away team batting) or 'B#' (bottom, home team batting)

    Output: (top_bot, inning_number) where top_bot is 1 for top, 2 for bottom
    '''

    inning = str(inning).strip()
    top_bot = 1 if inning[0].upper() == 'T' else 2
    return top_bot, int(inning[1:])


def _format_wpa(value):
    '''Function for formatting a WPA value as a percent string matching the existing gamelog convention.'''
    return f'{value * 100:.2f}%'


def _calculate_wpa(gamelog_df, we_matrix, mode = 'fill_blanks', regulation_innings = 6, season = None, confirmed_tie_games = None):
    '''
    Function for calculating Batter WPA / Pitcher WPA for a raw gamelog using a Win Expectancy matrix.
    Operates directly on the raw (non-expanded) gamelog: PA Type 0 (Manfred runners) and 15
    (trailing runners on multisteals) are synthetic rows added later by runner_attribution.py and
    should never appear here, but are excluded defensively if present. No play simulation is needed
    for most rows: the before-state and after-state for a normal play are read directly from that
    row's own Outs/OBC/scores and the literal next row's Outs/OBC/scores, since those already
    reflect the true game state at each point (including any Manfred runner placement). The one
    exception is a game whose data was cut off early (called official mid-game) -- there, the last
    recorded row's own play is simulated via simulate_runners.py to determine its true after-state,
    since no next row exists to read it from directly.
        gamelog_df - dataframe loaded from a raw gamelog csv, in original row order
        we_matrix - dict from _load_we_matrix()
        mode - 'fill_blanks' (default: only compute rows where Batter WPA is currently blank) or
            'recompute_all' (overwrite every row's WPA with the calculated value; used for validation)
        regulation_innings - scheduled game length for this league (6 for standard MLR/MiLR/etc.,
            4 for GIB/FCB S4, 3 for FCB S3). Used both to tell a legitimate end-of-game state (a
            lead in the bottom of this inning or later, or the home team already ahead after the
            top of it) apart from a game that was simply called early, and to shift which inning
            of the (always 6-inning-shaped) WE matrix applies: a shorter league's last inning
            should look up the matrix's inning-6 values, so game inning N maps to matrix inning
            N + (6 - regulation_innings). For a standard 6-inning league this offset is 0.
        season - season number for this gamelog (needed by simulate_runners.py for season-specific
            play logic). Only required if the file has a game that was called early.
        confirmed_tie_games - set/list of Game IDs known to have genuinely ended in a permanent tie
            (not just cut off mid-game). A tied final score can't be told apart from an in-progress
            data gap by the data alone, so this must be supplied explicitly. A confirmed tie gets
            50% win probability for whichever team just played, rather than being simulated as an
            ordinary continuing play.

    Output:
        gamelog_df with 'Batter WPA' / 'Pitcher WPA' populated as percent strings, plus an appended
        'WPA Calc Note' column ('' normally, or a flag: PA_TYPE_EXCLUDED, LAST_ROW_OF_GAME,
        GAME_CALLED_EARLY, CONFIRMED_TIE, CLAMPED_SS)
    '''

    confirmed_tie_games = set(confirmed_tie_games) if confirmed_tie_games else set()
    we_inning_offset = 6 - regulation_innings
    gamelog_df = gamelog_df.reset_index(drop = True)
    n_rows = len(gamelog_df)

    top_bots = []
    inning_nums = []
    for inning in gamelog_df['Inning']:
        top_bot, inning_num = _parse_inning(inning)
        top_bots.append(top_bot)
        inning_nums.append(inning_num)

    outs = gamelog_df['Outs'].astype(int).tolist()
    obcs = gamelog_df['OBC'].astype(int).tolist()
    home_scores = gamelog_df['Home Score'].astype(int).tolist()
    away_scores = gamelog_df['Away Score'].astype(int).tolist()
    rbis = gamelog_df['RBI'].fillna(0).astype(int).tolist()
    pa_types = gamelog_df['PA Type'].tolist()
    exact_results = gamelog_df['Exact Result'].astype(str).str.upper().tolist()
    mechanic_diffs = gamelog_df['Diff'].tolist()
    game_ids = gamelog_df['Game ID'].tolist()
    original_batter_wpa = gamelog_df['Batter WPA'].tolist()

    batter_wpa_out = []
    pitcher_wpa_out = []
    notes_out = []

    for i in range(n_rows):
        top_bot = top_bots[i]
        inning_num = inning_nums[i]
        pa_type = pa_types[i]

        is_blank = pd.isna(original_batter_wpa[i]) or str(original_batter_wpa[i]).strip() == ''
        if mode == 'fill_blanks' and not is_blank:
            batter_wpa_out.append(original_batter_wpa[i])
            pitcher_wpa_out.append(gamelog_df['Pitcher WPA'].iloc[i])
            notes_out.append('')
            continue

        if pa_type in EXCLUDED_PA_TYPES:
            batter_wpa_out.append(_format_wpa(0.0))
            pitcher_wpa_out.append(_format_wpa(0.0))
            notes_out.append('PA_TYPE_EXCLUDED')
            continue

        diff_before = (away_scores[i] - home_scores[i]) if top_bot == 1 else (home_scores[i] - away_scores[i])
        wp_before, clamped_before = _we_lookup(we_matrix, inning_num + we_inning_offset, top_bot, obcs[i], outs[i], diff_before)

        is_terminal = (i == n_rows - 1) or (game_ids[i + 1] != game_ids[i])
        clamped_after = False
        note = ''

        if is_terminal:
            is_home_batting = (top_bot == 2)
            final_home = home_scores[i] + (rbis[i] if is_home_batting else 0)
            final_away = away_scores[i] + (rbis[i] if not is_home_batting else 0)

            # A game can only legitimately end here if regulation has been reached, and either
            # the bottom half just ended with a real winner (not tied -- a tie means extra innings
            # follow) or the top half just ended with the home team already ahead (skipping the
            # bottom half entirely). Anything else means this game's data is missing more innings.
            if is_home_batting:
                is_valid_end = inning_num >= regulation_innings and final_home != final_away
            else:
                is_valid_end = inning_num >= regulation_innings and final_home > final_away

            if not is_valid_end and final_home == final_away and game_ids[i] in confirmed_tie_games:
                # confirmed permanent tie: the game is genuinely over with no winner, so both
                # teams' win probability lands at 50%, not a simulated continuing-play value
                wp_after = 0.5
                batter_wpa = wp_after - wp_before
                batter_wpa_out.append(_format_wpa(batter_wpa))
                pitcher_wpa_out.append(_format_wpa(-batter_wpa))
                notes_out.append('CONFIRMED_TIE')
                continue

            if not is_valid_end:
                # game was called official before it actually finished. There's no game-ending
                # state to jump to, but the last known play's own outcome is fully determined --
                # simulate it and treat it as an ordinary continuing play, not a decided win/loss.
                if season is None:
                    raise ValueError('season is required to compute WPA for a game that was called early')

                runners_before = _obc_to_runners(obcs[i])
                play_outcome = _simulate_runners(runners_before, outs[i], exact_results[i], mechanic_diffs[i], season, pa_type, 'hitter')
                outs_after_play = outs[i] + play_outcome['outs']
                diff_after_play = diff_before + len(play_outcome['runs'])

                if outs_after_play >= 3:
                    # this known play ended the half-inning; the following half-inning was never
                    # played (the game was called before it happened), so fall back to the matrix's
                    # own leadoff value for that hypothetical next state
                    next_top_bot = 2 if top_bot == 1 else 1
                    next_inning_num = inning_num if top_bot == 1 else inning_num + 1

                    if top_bot == 1:
                        # moving from top to bottom of the SAME inning: a Manfred runner (if any)
                        # is placed identically in both halves, and we already know what the top
                        # half itself started with, so reuse it rather than assuming empty bases
                        next_obc = _find_leadoff_obc(game_ids, top_bots, inning_nums, outs, obcs, game_ids[i], top_bot, inning_num)
                        note_suffix = ''
                    else:
                        # moving to the top of a NEW inning: no data exists for what that inning's
                        # Manfred pattern would be, so this is a best-effort guess of empty bases
                        next_obc = 0
                        note_suffix = ';ASSUMED_NO_MANFRED' if inning_num + 1 > regulation_innings else ''

                    wp_next_team, clamped_after = _we_lookup(we_matrix, next_inning_num + we_inning_offset, next_top_bot, next_obc, 0, -diff_after_play)
                    wp_after = 1 - wp_next_team
                else:
                    note_suffix = ''
                    wp_after, clamped_after = _we_lookup(we_matrix, inning_num + we_inning_offset, top_bot, play_outcome['obc'], outs_after_play, diff_after_play)

                batter_wpa = wp_after - wp_before
                note = 'GAME_CALLED_EARLY' + note_suffix
                if clamped_after:
                    note += ';CLAMPED_SS'

                batter_wpa_out.append(_format_wpa(batter_wpa))
                pitcher_wpa_out.append(_format_wpa(-batter_wpa))
                notes_out.append(note)
                continue

            batting_team_won = (final_home > final_away) if is_home_batting else (final_away > final_home)
            wp_after = 1.0 if batting_team_won else 0.0
            note = 'LAST_ROW_OF_GAME'
        elif top_bots[i + 1] == top_bot and inning_nums[i + 1] == inning_num:
            # half-inning continues; same batting team, directly comparable win probability.
            # Checked via Inning (top/bot + inning number) rather than Inning ID -- a handful of
            # games have a data-entry glitch where Inning ID increments mid-half-inning without
            # the actual Inning changing, which would otherwise be misread as a half-inning flip.
            next_diff = (away_scores[i + 1] - home_scores[i + 1]) if top_bot == 1 else (home_scores[i + 1] - away_scores[i + 1])
            wp_after, clamped_after = _we_lookup(we_matrix, inning_num + we_inning_offset, top_bot, obcs[i + 1], outs[i + 1], next_diff)
        else:
            # half-inning just ended; next row's leadoff state is for the OTHER team batting
            next_top_bot, next_inning_num = _parse_inning(gamelog_df['Inning'].iloc[i + 1])
            next_diff = (away_scores[i + 1] - home_scores[i + 1]) if next_top_bot == 1 else (home_scores[i + 1] - away_scores[i + 1])
            wp_next_team, clamped_after = _we_lookup(we_matrix, next_inning_num + we_inning_offset, next_top_bot, obcs[i + 1], outs[i + 1], next_diff)
            wp_after = 1 - wp_next_team

        batter_wpa = wp_after - wp_before
        if clamped_before or clamped_after:
            note = (note + ';CLAMPED_SS').strip(';')

        batter_wpa_out.append(_format_wpa(batter_wpa))
        pitcher_wpa_out.append(_format_wpa(-batter_wpa))
        notes_out.append(note)

    gamelog_df['Batter WPA'] = batter_wpa_out
    gamelog_df['Pitcher WPA'] = pitcher_wpa_out
    gamelog_df['WPA Calc Note'] = notes_out

    return gamelog_df
