import glob
import re
import pandas as pd
from we_matrix import _load_we_matrix
from calculate_wpa import _calculate_wpa

REGULATION_MAP = {
    ('gib', None): 4,
    ('fcb', 3): 3,
    ('fcb', 4): 4,
    ('fcb', 5): 4,
    ('fcb', 6): 4,
    ('fcb', 7): 4,
}


def _parse_wpa(v):
    '''Robust WPA parser: handles both "13.15%" and bare "0.1315" formats (mixed within some files).'''
    if pd.isna(v) or str(v).strip() == '':
        return None
    s = str(v).strip()
    if '%' in s:
        return float(s.strip('%')) / 100
    return float(s)


def _regulation_innings(league, season_num):
    if league == 'gib':
        return 4
    if league == 'fcb' and season_num in (3, 4, 5, 6, 7):
        return 3 if season_num == 3 else 4
    return 6


def main():
    we = _load_we_matrix('../data/we_matrices/we_matrix_6inn.csv')
    files = sorted(glob.glob('../data/raw_gamelogs/*_raw_gamelog_S*.csv'))

    all_flagged = []
    summary_rows = []

    for path in files:
        m = re.match(r'.*[\\/](\w+?)_raw_gamelog_S(\d+)(A|B)?\.csv$', path)
        if not m:
            continue
        league, season_str, ab_suffix = m.groups()
        season_num = int(season_str)
        season_float = season_num + (0.1 if ab_suffix == 'A' else 0.2 if ab_suffix == 'B' else 0)
        regulation_innings = _regulation_innings(league, season_num)

        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if len(df) == 0 or 'Batter WPA' not in df.columns:
            continue

        blanks = df['Batter WPA'].isna().sum() + (df['Batter WPA'].astype(str).str.strip() == '').sum()

        actual = df['Batter WPA'].apply(_parse_wpa)
        try:
            result = _calculate_wpa(df.copy(), we, mode='recompute_all', season=season_float, regulation_innings=regulation_innings)
        except Exception as e:
            summary_rows.append({'file': path, 'rows': len(df), 'blanks': blanks, 'error': str(e)})
            continue
        predicted = result['Batter WPA'].apply(_parse_wpa)

        mask = actual.notna() & predicted.notna()
        error = (predicted[mask] - actual[mask])

        inning_num = df['Inning'].str[1:].astype(int)
        top_bot = df['Inning'].str[0]
        next_inning_id = df['Inning ID'].shift(-1)
        is_flip_or_terminal = (next_inning_id != df['Inning ID'])
        # extra-innings-adjacent: this row's inning >= regulation, OR (it's a flip and the NEXT row's inning > regulation)
        next_inning_num = df['Inning'].shift(-1).str[1:].astype(float)
        extra_innings_adjacent = (inning_num >= regulation_innings) & is_flip_or_terminal
        extra_innings_adjacent = extra_innings_adjacent | (inning_num > regulation_innings)

        mid_inning_mask = mask & (~is_flip_or_terminal)
        mid_inning_mae = error[mid_inning_mask.reindex(error.index, fill_value=False)].abs().mean() if mid_inning_mask.sum() > 0 else float('nan')

        # candidate bad rows: not extra-innings-adjacent, error > 10 percentage points
        candidate_mask = mask & (~extra_innings_adjacent) & (error.abs() > 0.10)
        n_candidates = candidate_mask.sum()

        summary_rows.append({
            'file': path.split('\\')[-1].split('/')[-1],
            'rows': len(df),
            'blanks': blanks,
            'mid_inning_mae': round(mid_inning_mae, 5) if mid_inning_mae == mid_inning_mae else None,
            'overall_mae': round(error.abs().mean(), 5),
            'candidates_gt_10pp': int(n_candidates),
        })

        if n_candidates > 0:
            idx = df.index[candidate_mask]
            flagged = df.loc[idx, ['Hitter', 'Game ID', 'Inning', 'Outs', 'OBC', 'Home Score', 'Away Score', 'Exact Result', 'RBI']].copy()
            flagged['file'] = path.split('\\')[-1].split('/')[-1]
            flagged['actual_wpa'] = actual.loc[idx]
            flagged['predicted_wpa'] = predicted.loc[idx]
            flagged['error'] = error.loc[idx]
            all_flagged.append(flagged)

    summary_df = pd.DataFrame(summary_rows)
    pd.set_option('display.width', 250)
    pd.set_option('display.max_rows', 200)
    print(summary_df.to_string(index=False))

    if all_flagged:
        flagged_df = pd.concat(all_flagged, ignore_index=True)
        flagged_df = flagged_df.sort_values('error', key=lambda s: s.abs(), ascending=False)
        flagged_df.to_csv('../data/_wpa_audit_verified.csv', index=False)
        print(f'\n{len(flagged_df)} candidate rows written to data/_wpa_audit_verified.csv')
        print(flagged_df.to_string(index=False))
    else:
        print('\nNo candidate rows found.')


if __name__ == '__main__':
    main()
