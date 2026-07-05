import glob
import re
import pandas as pd
from we_matrix import _load_we_matrix
from calculate_wpa import _calculate_wpa
from backfill_wpa import _load_hrd_tie_games, _preflight_checks


def _regulation_innings(league, season_num):
    if league == 'gib':
        return 4
    if league == 'fcb' and season_num == 3:
        return 3
    if league == 'fcb' and season_num in (4, 5, 6, 7):
        return 4
    return 6


def main():
    we_matrix = _load_we_matrix('../data/we_matrices/we_matrix_6inn.csv')
    files = sorted(glob.glob('../data/raw_gamelogs/*_raw_gamelog_S*.csv'))

    summary = []

    for path in files:
        m = re.match(r'.*[\\/](\w+?)_raw_gamelog_S(\d+)(A|B)?\.csv$', path)
        if not m:
            continue
        league, season_str, ab_suffix = m.groups()
        season_num = int(season_str)
        season_display = f'{season_num}{ab_suffix or ""}'
        season_float = season_num + (0.1 if ab_suffix == 'A' else 0.2 if ab_suffix == 'B' else 0)
        regulation_innings = _regulation_innings(league, season_num)

        try:
            df = pd.read_csv(path)
        except Exception as e:
            summary.append({'file': path, 'status': f'READ ERROR: {e}'})
            continue

        if len(df) == 0 or 'Batter WPA' not in df.columns:
            summary.append({'file': path, 'status': 'skipped (empty/no WPA column)'})
            continue

        try:
            _preflight_checks(df)
        except Exception as e:
            summary.append({'file': path, 'status': f'PREFLIGHT FAILED: {e}'})
            continue

        hrd_ties = _load_hrd_tie_games(league, season_num)

        try:
            result = _calculate_wpa(df.copy(), we_matrix, mode='recompute_all',
                                     regulation_innings=regulation_innings,
                                     season=season_float, confirmed_tie_games=hrd_ties)
        except Exception as e:
            summary.append({'file': path, 'status': f'CALC ERROR: {e}'})
            continue

        out_path = path.replace('.csv', '_wpa_filled.csv')
        try:
            result.to_csv(out_path, index=False)
        except PermissionError:
            summary.append({'file': path.split('\\')[-1].split('/')[-1], 'status': f'WRITE FAILED (file locked/open elsewhere): {out_path}'})
            continue

        note_counts = result['WPA Calc Note'].value_counts().to_dict()
        blanks_remaining = result['Batter WPA'].isna().sum() + (result['Batter WPA'].astype(str).str.strip() == '').sum()

        summary.append({
            'file': path.split('\\')[-1].split('/')[-1],
            'league': league,
            'season': season_display,
            'reg_innings': regulation_innings,
            'rows': len(df),
            'blanks_remaining': blanks_remaining,
            'hrd_ties': len(hrd_ties),
            'game_called_early': sum(v for k, v in note_counts.items() if 'GAME_CALLED_EARLY' in str(k)),
            'confirmed_tie': sum(v for k, v in note_counts.items() if 'CONFIRMED_TIE' in str(k)),
            'last_row_of_game': sum(v for k, v in note_counts.items() if 'LAST_ROW_OF_GAME' in str(k)),
            'status': 'OK',
        })

    summary_df = pd.DataFrame(summary)
    pd.set_option('display.width', 250)
    pd.set_option('display.max_rows', 200)
    print(summary_df.to_string(index=False))

    problems = summary_df[summary_df['status'] != 'OK'] if 'status' in summary_df.columns else pd.DataFrame()
    if len(problems) > 0:
        print('\n\nFILES WITH PROBLEMS:')
        print(problems.to_string(index=False))

    nonzero_blanks = summary_df[summary_df.get('blanks_remaining', 0) > 0] if 'blanks_remaining' in summary_df.columns else pd.DataFrame()
    if len(nonzero_blanks) > 0:
        print('\n\nFILES WITH REMAINING BLANKS (unexpected):')
        print(nonzero_blanks.to_string(index=False))


if __name__ == '__main__':
    main()
