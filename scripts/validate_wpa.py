import argparse
import pandas as pd
from we_matrix import _load_we_matrix
from calculate_wpa import _calculate_wpa


def _parse_percent(value):
    '''Function for parsing a gamelog percent-string WPA value (e.g. '13.15%') into a float, or None if blank.'''
    if pd.isna(value) or str(value).strip() == '':
        return None
    return float(str(value).strip().strip('%')) / 100


def main():
    parser = argparse.ArgumentParser(description = 'Validate the WPA calculator against a gamelog that already has real WPA populated.')
    parser.add_argument('--league', required = True)
    parser.add_argument('--season', required = True)
    parser.add_argument('--we-matrix', default = '../data/we_matrices/we_matrix_6inn.csv')
    parser.add_argument('--regulation-innings', type = int, default = 6)
    parser.add_argument('--threshold', type = float, default = 0.01, help = 'abs(error) threshold (in WP units, e.g. 0.01 = 1 percentage point) for flagging rows')
    args = parser.parse_args()

    path = f'../data/raw_gamelogs/{args.league}_raw_gamelog_S{args.season}.csv'
    df = pd.read_csv(path)

    actual = df['Batter WPA'].apply(_parse_percent)

    we_matrix = _load_we_matrix(args.we_matrix)
    result = _calculate_wpa(df.copy(), we_matrix, mode = 'recompute_all', season = float(args.season), regulation_innings = args.regulation_innings)
    predicted = result['Batter WPA'].apply(_parse_percent)

    mask = actual.notna() & predicted.notna()
    error = predicted[mask] - actual[mask]

    print(path)
    print(f'rows compared: {mask.sum()} / {len(df)}')
    if mask.sum() == 0:
        print('No rows with both actual and predicted WPA -- nothing to validate.')
        return

    print(f'mean error: {error.mean():.5f}')
    print(f'mean abs error: {error.abs().mean():.5f}')
    print(f'stddev: {error.std():.5f}')
    print(f'abs error percentiles: p50={error.abs().quantile(.5):.5f} p90={error.abs().quantile(.9):.5f} p99={error.abs().quantile(.99):.5f} max={error.abs().max():.5f}')

    # split by code path: mid-inning continuation, half-inning flip, or terminal (walk-off/final out)
    categories = pd.Series('mid_inning', index = df.index)
    categories[result['WPA Calc Note'].str.contains('LAST_ROW_OF_GAME', na = False)] = 'terminal'
    next_inning_ids = df['Inning ID'].shift(-1)
    flip_mask = (next_inning_ids != df['Inning ID']) & (categories != 'terminal')
    categories[flip_mask] = 'half_inning_flip'

    print('\nBreakdown by code path:')
    for cat in ['mid_inning', 'half_inning_flip', 'terminal']:
        cat_mask = mask & (categories == cat)
        if cat_mask.sum() == 0:
            continue
        cat_error = predicted[cat_mask] - actual[cat_mask]
        print(f'  [{cat}] n={cat_mask.sum()} mean={cat_error.mean():.5f} mae={cat_error.abs().mean():.5f} max={cat_error.abs().max():.5f}')

    flagged_idx = df.index[mask & (error.abs() > args.threshold)]
    if len(flagged_idx) > 0:
        flagged = df.loc[flagged_idx].copy()
        flagged['Actual Batter WPA'] = actual.loc[flagged_idx]
        flagged['Predicted Batter WPA'] = predicted.loc[flagged_idx]
        flagged['Error'] = error.loc[flagged_idx]
        flagged['Category'] = categories.loc[flagged_idx]
        cols = ['Hitter', 'Game ID', 'Inning', 'Outs', 'OBC', 'Home Score', 'Away Score',
                'Exact Result', 'PA Type', 'Category', 'Actual Batter WPA', 'Predicted Batter WPA', 'Error']
        cols = [c for c in cols if c in flagged.columns]
        print(f'\n{len(flagged_idx)} rows with abs(error) > {args.threshold}:')
        pd.set_option('display.width', 200)
        print(flagged[cols].to_string(index = False))
    else:
        print(f'\nNo rows with abs(error) > {args.threshold}')


if __name__ == '__main__':
    main()
