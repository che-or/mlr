"""
Fetch MLR Draft History from Google Sheets and write docs/data/draft_history.json

Output format:
{
  "1": {
    "1": [{ "team": "MIN", "id": 2128 }, ...],
    "2": [...]
  },
  ...
}

id is an integer for numeric player IDs, a string otherwise.
Pick-within-round is derived from position in the array (index + 1).
"""

import csv
import io
import json
import urllib.request
from pathlib import Path

SHEET_ID = '1KJmUR65fSDNdoZyjpoD2FaCAB0hdbuOmBjOFnwky64M'
GID = '0'
URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}'

ROOT = Path(__file__).parent.parent
OUTPUT = ROOT / 'docs' / 'data' / 'draft_history.json'

print(f'Fetching {URL}')
with urllib.request.urlopen(URL) as response:
    content = response.read().decode('utf-8')

draft = {}

reader = csv.DictReader(io.StringIO(content))
for row in reader:
        season = row['Season'].strip()
        round_ = row['Round'].strip()
        team = row['Team'].strip()
        raw_id = row['ID'].strip()

        try:
            player_id = int(raw_id)
        except ValueError:
            player_id = raw_id

        draft.setdefault(season, {}).setdefault(round_, []).append(
            {'team': team, 'id': player_id}
        )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(draft, f, separators=(',', ':'))

print(f'Wrote {OUTPUT}')
seasons = sorted(draft.keys(), key=lambda s: int(s))
for s in seasons:
    rounds = sorted(draft[s].keys(), key=lambda r: int(r))
    total_picks = sum(len(draft[s][r]) for r in rounds)
    print(f'  Season {s}: {len(rounds)} rounds, {total_picks} picks')
