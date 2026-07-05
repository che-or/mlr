import argparse
import re
import sys
import pandas as pd
from we_matrix import _load_we_matrix
from calculate_wpa import _calculate_wpa, EXCLUDED_PA_TYPES

INNING_PATTERN = re.compile(r'^[TB]\d+$')
HRD_LEAGUE_NAMES = {'mlr': 'MLR', 'milr': 'MiLR', 'fcb': 'FCB', 'npr': 'NPR'}


def _load_hrd_tie_games(league, season, path = '../data/pitcher_decision_adjustments.csv'):
    '''
    Function for finding games decided by a home run derby tiebreaker (Notes == 'HRD') in
    data/pitcher_decision_adjustments.csv. These games end in a genuine tie in the gamelog itself
    (the derby happens outside the simulated plate appearances), so they should be treated like a
    confirmed permanent tie, not a game whose data is merely missing.
        league - league code as passed on the CLI (e.g. 'fcb')
        season - season number (int-valued; split seasons like 8A/8B aren't tracked separately here)

    Output: set of raw (non-offset) Game IDs for this league/season decided by a home run derby
    '''

    league_name = HRD_LEAGUE_NAMES.get(league.lower())
    if league_name is None:
        return set()

    try:
        adjustments = pd.read_csv(path)
    except FileNotFoundError:
        return set()

    matches = adjustments[
        (adjustments['League'] == league_name) &
        (adjustments['Season'] == int(season)) &
        (adjustments['Notes'] == 'HRD')
    ]
    # Game ID in this file is offset by season*1000, matching load_gamelogs.py's convention
    return {int(gid) - int(season) * 1000 for gid in matches['Game ID']}


def _preflight_checks(df):
    '''
    Function for validating a raw gamelog dataframe before computing WPA. Fails loudly with the
    offending row identified rather than letting a malformed row silently produce bad WPA.
    '''

    bad_inning = df.index[~df['Inning'].astype(str).str.match(INNING_PATTERN)]
    if len(bad_inning) > 0:
        raise ValueError(f"Unrecognized 'Inning' format at row(s) {bad_inning.tolist()[:5]}")

    for col, valid_range in [('Outs', range(0, 3)), ('OBC', range(0, 8))]:
        numeric = pd.to_numeric(df[col], errors = 'coerce')
        bad = df.index[numeric.isna() | ~numeric.isin(valid_range)]
        if len(bad) > 0:
            raise ValueError(f"Invalid '{col}' value at row(s) {bad.tolist()[:5]}")

    for col in ['Home Score', 'Away Score']:
        numeric = pd.to_numeric(df[col], errors = 'coerce')
        bad = df.index[numeric.isna()]
        if len(bad) > 0:
            raise ValueError(f"Blank/non-numeric '{col}' at row(s) {bad.tolist()[:5]}")

    # one consistent home/away pairing per Game ID
    for game_id, game_df in df.groupby('Game ID'):
        away_teams = game_df.loc[game_df['Inning'].str[0] == 'T', 'Batter Team'].unique()
        home_teams = game_df.loc[game_df['Inning'].str[0] == 'B', 'Batter Team'].unique()
        if len(away_teams) > 1 or len(home_teams) > 1:
            raise ValueError(f'Game ID {game_id} has inconsistent home/away team assignment: away={away_teams}, home={home_teams}')



def main():
    parser = argparse.ArgumentParser(description = 'Backfill missing WPA in a raw gamelog using a Win Expectancy matrix.')
    parser.add_argument('--league', required = True, help = 'league code, e.g. mlr, milr, milr_playoff, mlr_playoff, fcb, eco, npr, wbc, gib')
    parser.add_argument('--season', required = True, help = "season number, or a string like '8A'/'8B' for milr's split seasons")
    parser.add_argument('--file', default = None, help = 'explicit path override for the input gamelog csv')
    parser.add_argument('--mode', choices = ['fill_blanks', 'recompute_all'], default = 'fill_blanks')
    parser.add_argument('--out', default = None, help = 'output path (default: input path with _wpa_filled suffix)')
    parser.add_argument('--we-matrix', default = '../data/we_matrices/we_matrix_6inn.csv')
    parser.add_argument('--regulation-innings', type = int, default = 6)
    parser.add_argument('--confirmed-ties', default = '', help = 'comma-separated Game IDs known to have genuinely ended in a permanent tie (not a data gap)')
    args = parser.parse_args()

    confirmed_tie_games = {int(g.strip()) for g in args.confirmed_ties.split(',') if g.strip()}

    in_path = args.file or f'../data/raw_gamelogs/{args.league}_raw_gamelog_S{args.season}.csv'
    out_path = args.out or in_path.replace('.csv', '_wpa_filled.csv')

    season_str = str(args.season).upper()
    if season_str.endswith('A'):
        season = float(season_str[:-1]) + 0.1
    elif season_str.endswith('B'):
        season = float(season_str[:-1]) + 0.2
    else:
        season = float(season_str)

    hrd_tie_games = _load_hrd_tie_games(args.league, season)
    if hrd_tie_games:
        print(f'Auto-detected home-run-derby-decided game(s) from pitcher_decision_adjustments.csv: {sorted(hrd_tie_games)}')
        confirmed_tie_games |= hrd_tie_games

    df = pd.read_csv(in_path)
    original_columns = list(df.columns)

    _preflight_checks(df)

    pa_type_zero_fifteen = df['PA Type'].isin(EXCLUDED_PA_TYPES).sum()
    if pa_type_zero_fifteen > 0:
        print(f'WARNING: {pa_type_zero_fifteen} row(s) in this raw file are tagged PA Type 0/15. '
              'These should only ever exist in the expanded (runner_attribution) dataframe, not a raw '
              'gamelog -- double check this is really a raw, unprocessed gamelog file.')

    we_matrix = _load_we_matrix(args.we_matrix)

    blanks_before = df['Batter WPA'].isna().sum()
    result = _calculate_wpa(df.copy(), we_matrix, mode = args.mode, regulation_innings = args.regulation_innings, season = season, confirmed_tie_games = confirmed_tie_games)

    assert list(result.columns[:len(original_columns)]) == original_columns, 'Output column order does not match input'

    result.to_csv(out_path, index = False)

    note_counts = result['WPA Calc Note'].value_counts()
    filled = ((result['WPA Calc Note'] != '') | (args.mode == 'recompute_all')).sum() if args.mode == 'recompute_all' else blanks_before

    print(f'Input: {in_path}')
    print(f'Output: {out_path}')
    print(f'Mode: {args.mode}')
    print(f'Rows processed: {len(df)}')
    print(f'Rows with previously-blank Batter WPA: {blanks_before}')
    print('Diagnostic note counts:')
    for note, count in note_counts.items():
        label = note if note else '(none)'
        print(f'  {label}: {count}')

    for flag in ['GAME_CALLED_EARLY', 'CONFIRMED_TIE', 'LAST_ROW_OF_GAME']:
        flagged = result[result['WPA Calc Note'].str.contains(flag, na = False)]
        if len(flagged) > 0:
            print(f"\n{flag} rows (review manually):")
            print(flagged[['Hitter', 'Game ID', 'Inning', 'Home Score', 'Away Score', 'Exact Result']].to_string(index = False))


if __name__ == '__main__':
    main()
