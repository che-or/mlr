import glob
import os
import re
import pandas as pd


def parse_wpa(v):
    if pd.isna(v) or str(v).strip() == '':
        return None
    s = str(v).strip()
    if '%' in s:
        return round(float(s.strip('%')) / 100, 4)
    return round(float(s), 4)


def main():
    files = sorted(glob.glob('../data/raw_gamelogs/*_raw_gamelog_S*.csv'))
    results = []
    for path in files:
        m = re.match(r'.*[\\/](\w+?)_raw_gamelog_S(\d+)(A|B)?\.csv$', path)
        if not m:
            continue
        filled_path = path.replace('.csv', '_wpa_filled.csv')
        if not os.path.exists(filled_path):
            continue
        current = pd.read_csv(path)
        fresh = pd.read_csv(filled_path)
        name = path.split('\\')[-1].split('/')[-1]
        if len(current) != len(fresh):
            results.append((name, 'ROW COUNT MISMATCH', len(current), None))
            continue
        cur_vals = current['Batter WPA'].apply(parse_wpa)
        fresh_vals = fresh['Batter WPA'].apply(parse_wpa)
        diff_mask = (cur_vals != fresh_vals) & ~(cur_vals.isna() & fresh_vals.isna())
        n_diff = diff_mask.sum()
        pct = round(100 * n_diff / len(current), 1) if len(current) else 0
        results.append((name, n_diff, len(current), pct))

    for name, n_diff, total, pct in results:
        print(f'{name}: {n_diff}/{total} rows differ ({pct}%)')


if __name__ == '__main__':
    main()
