import pandas as pd

VALID_TOP_BOT = {1, 2}
VALID_OBC = set(range(8))
VALID_OUTS = {0, 1, 2}
DIFF_COLUMNS = ['-10+'] + [str(d) for d in range(-9, 10)] + ['10+']
EXTRA_INNING_BUCKET = 7 # innings 7+ share identical win probabilities in the source matrix


def _parse_wp_cell(value):
    '''
    Function for parsing a single Win Expectancy matrix cell.
        value - raw cell value, either a percent string (e.g. '61.33%') or the literal 'SS'

    Output: float win probability, or None if the cell is 'SS' (small sample, no data)
    '''

    if value is None:
        return None
    value = str(value).strip()
    if value == '' or value.upper() == 'SS':
        return None
    return float(value.strip('%')) / 100


def _load_we_matrix(path = '../data/we_matrices/we_matrix_6inn.csv'):
    '''
    Function for loading the Win Expectancy matrix used for 6-inning standard length games.
        path - path to the WE matrix csv (2 header rows; row 2 has the real column names)

    Output:
        we_matrix - dict keyed by (inning_bucket, top_bot, obc, outs), where inning_bucket is
            min(inning, 7) since innings 7+ share identical win probabilities. Each value is a
            dict {diff: win_probability} for diff in -10..10 (win probability for the batting
            team). win_probability is None for cells marked 'SS' (insufficient sample) in the
            source matrix.
    '''

    raw = pd.read_csv(path, skiprows = 1)

    # keep only well-formed state rows; drops trailing blank rows and any garbage sentinel rows
    inning_numeric = pd.to_numeric(raw['Inning'], errors = 'coerce')
    valid_mask = (
        inning_numeric.notna() &
        pd.to_numeric(raw['Top/Bot'], errors = 'coerce').isin(VALID_TOP_BOT) &
        pd.to_numeric(raw['OBC'], errors = 'coerce').isin(VALID_OBC) &
        pd.to_numeric(raw['Outs'], errors = 'coerce').isin(VALID_OUTS)
    )
    raw = raw[valid_mask].copy()

    raw['Inning'] = inning_numeric[valid_mask].astype(int)
    raw['Top/Bot'] = raw['Top/Bot'].astype(int)
    raw['OBC'] = raw['OBC'].astype(int)
    raw['Outs'] = raw['Outs'].astype(int)

    we_matrix = {}
    for _, row in raw.iterrows():
        inning_bucket = min(row['Inning'], EXTRA_INNING_BUCKET)
        key = (inning_bucket, row['Top/Bot'], row['OBC'], row['Outs'])

        diffs = {}
        for col in DIFF_COLUMNS:
            diff_value = -10 if col == '-10+' else (10 if col == '10+' else int(col))
            diffs[diff_value] = _parse_wp_cell(row[col])

        if key in we_matrix:
            # innings 7-11 are expected to collapse onto identical values; verify that holds
            # rather than silently trusting it, in case a future matrix export changes this
            if we_matrix[key] != diffs:
                raise ValueError(f'WE matrix state {key} has conflicting values across extra innings')
        else:
            we_matrix[key] = diffs

    # sanity check: expect exactly 48 states (2 top/bot x 8 obc x 3 outs) per inning bucket
    buckets = {k[0] for k in we_matrix}
    for bucket in buckets:
        count = sum(1 for k in we_matrix if k[0] == bucket)
        if count != 48:
            raise ValueError(f'Expected 48 states for inning bucket {bucket}, found {count}')

    return we_matrix


def _we_lookup(we_matrix, inning, top_bot, obc, outs, diff):
    '''
    Function for looking up win probability (for the batting team) from the WE matrix.
        we_matrix - dict from _load_we_matrix()
        inning - actual inning number (int, 1+)
        top_bot - 1 for top (away team batting), 2 for bottom (home team batting)
        obc - on-base code, 0-7
        outs - outs before the play, 0-2
        diff - batting team's score minus fielding team's score, before the play

    Output:
        (win_probability, was_clamped) - win_probability is a float in [0, 1]. was_clamped is
            True if diff had to be clamped to +/-10, or moved off of an 'SS' cell.
    '''

    inning_bucket = min(inning, EXTRA_INNING_BUCKET)
    key = (inning_bucket, top_bot, obc, outs)
    if key not in we_matrix:
        raise KeyError(f'No WE matrix entry for state {key}')

    diffs = we_matrix[key]

    clamped_diff = max(-10, min(10, diff))
    was_clamped = clamped_diff != diff

    wp = diffs[clamped_diff]
    if wp is None: # 'SS' cell; move toward diff=0 until a real value is found
        was_clamped = True
        step = 1 if clamped_diff < 0 else -1
        probe = clamped_diff
        while diffs[probe] is None:
            probe += step
        wp = diffs[probe]

    return wp, was_clamped
