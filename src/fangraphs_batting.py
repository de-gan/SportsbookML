import requests
import pandas as pd
from functools import lru_cache
from bs4 import BeautifulSoup

def strip_link(html):
    return BeautifulSoup(html, "html.parser").get_text()

@lru_cache()
def fg_team_snapshot(season: int, as_of: str) -> pd.DataFrame:
    
    url = 'https://www.fangraphs.com/api/leaders/major-league/data'
    params = {
        'pos':       'all',             # include all positions
        'stats':     'bat',             # batting stats
        'lg':        'all',             # both leagues
        'qual':      '0',               # no qualification filter
        'type':      '8',
        'season':    season,
        'month':     '1000',            # all months
        'season1':   season,
        'ind':       '0',               # include teams, exclude splits
        'team':      '0,ts',            # include all teams
        'rost':      '',                # no roster filter
        'age':       '',                # no age filter
        'filter':    '',                # no additional filter
        'players':   '0',               # no specific players
        'startdate': f"{season}-03-01",
        'enddate':   as_of,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json().get('data', [])
    df = pd.DataFrame(data)

    df.loc[:, 'HR/FB%+'] = df['HR'] / (df['FB%+'] * 100) if 'FB%+' in df.columns else 0

    important_batting_stats = [
        'Team',
        'HR',
        'RBI',
        'H',
        'wRC+',
        'wOBA',
        'SLG+',
        'OBP+',
        'AVG+',
        'ISO+',
        'HR/FB%+',
        'BB%+',
        'K%+',
        'Spd',
        'EV',
        'LA',
        'Barrel%',
        'HardHit%',
        'Pull%+',
        'Oppo%+',
        'Cent%+',
    ]

    df = df[important_batting_stats]
    df['Team'] = df['Team'].apply(strip_link)

    # Each team appears once; no need to drop duplicates
    return df

# Example: get all teams’ batting as of May 1, 2025
snap = fg_team_snapshot(2025, "2025-03-18")
snap.to_csv("data/raw/fangraphs_team_snapshot_2025.csv", index=False)

print(snap)
print(snap.columns.tolist())