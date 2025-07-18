import requests
import json
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup, Comment
from pybaseball import playerid_lookup, statcast_pitcher

def get_all_boxscores(year: int) -> pd.DataFrame:
    url = f"https://www.baseball-reference.com/leagues/majors/{year}-schedule.shtml"
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", {"type": "application/ld+json"})
    payload = script.string.strip()

    events = json.loads(payload)

    rows = []
    for ev in events:
        if ev.get("@type") != "SportsEvent":
            continue
        # The 'name' field is "Away Team @ Home Team"
        away, home = ev["name"].split(" @ ")
        rows.append({
            "Date"     : ev["startDate"],
            "Opp"     : away,
            "Tm"     : home,
            "Boxscore" : ev["url"],
        })

    schedule_df = pd.DataFrame(rows)
    return schedule_df


def get_starting_pitcher(box_url: str, team_name: str, game_date, year: int = 2024) -> dict:
    resp = requests.get(box_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    clean = re.sub(r'[^A-Za-z]', '', team_name)
    table_id = f"{clean}pitching"
    comments = soup.find_all(string=lambda t: isinstance(t, Comment))
    comment = next(c for c in comments if table_id in c)

    inner = BeautifulSoup(comment, "html.parser")
    table = inner.find("table", id=table_id)

    row = table.tbody.find("tr")
    
    data = {}
    data['pitcher'] = row.find("th", {"data-stat": "player"}).find("a").get_text(strip=True)
    data['ERA'] = float(row.find("td", {"data-stat": "earned_run_avg"}).get_text(strip=True))
    data['WPA'] = float(row.find("td", {"data-stat": "wpa_def"}).get_text(strip=True))
    
    player_stats = get_player_stats(data['pitcher'], game_date, year)
    data.update(player_stats)
    
    return data

def get_player_stats(player_name: str, game_date, year: int = 2024) -> dict:
    last, first = player_name.split()[-1], player_name.split()[0]
    player_id = playerid_lookup(last, first).iloc[0]['key_mlbam']
    
    end_dt = pd.to_datetime(game_date).strftime("%Y-%m-%d")
    start_dt = f"{year}-03-01"
    df = statcast_pitcher(start_dt, end_dt, player_id)
    if df.empty:
        return dict(ERA=np.nan, K9=np.nan, BB9=np.nan, WHIP=np.nan, IP=np.nan)
    
    innings = df['outs_when_up'].sum() / 3
    
    ks = (df['events']=='strikeout').sum()
    k9 = (ks * 9 / innings) if innings>0 else np.nan
    bb = (df['events']=='walk').sum()
    bb9 = (bb * 9 / innings) if innings>0 else np.nan
    
    contact = df[df.launch_speed.notna()]
    hard_hit_pct = (contact.launch_speed>95).mean()
    
    # hits + walks allowed
    wh  = df['events'].isin(['single','double','triple','home_run']).sum() + bb
    whip = (wh / innings) if innings>0 else np.nan
    
    return {
        'K9': round(k9, 2),
        'BB9': round(bb9, 2),
        'WHIP': round(whip,2),
        'HardHit%': round(hard_hit_pct, 2),
        'IP': round(innings,2)
    }
    
#print(get_player_stats("Clarke Schmidt", "2024-05-04", 2024))
print(get_starting_pitcher("https://www.baseball-reference.com/boxes/NYA/NYA202405040.shtml", "New York Yankees", "2024-05-04", 2024))