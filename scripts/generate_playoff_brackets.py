import json
import pandas as pd
from pathlib import Path
from simulate_runners import _simulate_runners

SCRIPT_DIR = Path(__file__).resolve().parent
GAMELOG_DIR = SCRIPT_DIR.parent / 'data' / 'raw_gamelogs'
META_DIR = SCRIPT_DIR.parent / 'docs' / 'data'
OUT_DIR = SCRIPT_DIR.parent / 'docs' / 'generated'


def _season_num(season_key):
    s = season_key.lstrip('S')
    if s.endswith('A'):
        return int(s[:-1]) + 0.1
    if s.endswith('B'):
        return int(s[:-1]) + 0.2
    return int(s)


def _final_score(game_df):
    fp = game_df.iloc[-1]
    obc = fp['OBC']
    runners = [None, None, None]
    if obc in [1, 4, 5, 7]: runners[0] = 'i'
    if obc in [2, 4, 6, 7]: runners[1] = 'i'
    if obc in [3, 5, 6, 7]: runners[2] = 'i'

    result = _simulate_runners(
        runners, fp['Outs'], fp['Exact Result'],
        fp['Diff'], fp['Season'], fp['PA Type'], 'i'
    )
    runs = len(result['runs'])
    home = int(fp['Home Score'])
    away = int(fp['Away Score'])
    if fp['Inning'].startswith('B'):
        home += runs
    else:
        away += runs
    return home, away


def _process_season(season_key, meta, league_prefix):
    gamelog_path = GAMELOG_DIR / f'{league_prefix}_playoff_raw_gamelog_{season_key}.csv'

    out = {'format': meta['format']}
    if 'reseeded' in meta:
        out['reseeded'] = meta['reseeded']
    if 'leagues' in meta:
        out['leagues'] = meta['leagues']
    if 'seeds' in meta:
        out['seeds'] = meta['seeds']

    league_map = {}
    for lg_key, lg_data in meta.get('leagues', {}).items():
        for team in lg_data['seeds']:
            league_map[team] = lg_key

    if not gamelog_path.exists():
        out['rounds'] = [{'name': r['name'], 'matchups': []} for r in meta['rounds']]
        return out

    df = pd.read_csv(gamelog_path)
    df['Season'] = _season_num(season_key)
    df['Exact Result'] = df['Exact Result'].str.upper()

    session_matchups = {}
    for gid in df['Game ID'].unique():
        game_df = df[df['Game ID'] == gid].copy()
        first = game_df.iloc[0]
        session = int(first['Session'])
        away = first['Batter Team']
        home = first['Pitcher Team']
        home_score, away_score = _final_score(game_df)

        matchup = {
            'game_id': int(gid),
            'home': home,
            'away': away,
            'home_score': home_score,
            'away_score': away_score,
        }
        home_lg = league_map.get(home)
        away_lg = league_map.get(away)
        if home_lg and home_lg == away_lg:
            matchup['league'] = home_lg

        session_matchups.setdefault(session, []).append(matchup)

    rounds_out = []
    for r in meta['rounds']:
        matchups = session_matchups.get(r['session'], [])
        matchups.sort(key=lambda m: (m.get('league', '\xff'), m['game_id']))
        rounds_out.append({'name': r['name'], 'matchups': matchups})

    out['rounds'] = rounds_out
    return out


def generate_brackets(league_prefix):
    meta_path = META_DIR / f'{league_prefix}_playoffs.json'
    out_path = OUT_DIR / f'{league_prefix}_playoff_brackets.json'

    with open(meta_path) as f:
        all_meta = json.load(f)

    result = {}
    for season_key, meta in all_meta.items():
        #print(f'  {league_prefix.upper()} playoffs {season_key}...')
        result[season_key] = _process_season(season_key, meta, league_prefix)

    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    #print(f'Written {out_path}')


if __name__ == '__main__':
    generate_brackets('mlr')
    generate_brackets('milr')
