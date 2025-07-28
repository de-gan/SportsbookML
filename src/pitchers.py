import requests
import requests_cache
import json
import re
import pandas as pd
from pandas.errors import ParserError
import numpy as np
import warnings
from datetime import datetime, date
from bs4 import BeautifulSoup, Comment
from pybaseball import playerid_lookup, statcast_pitcher

requests_cache.install_cache('bbref_cache', expire_after=86400)
session = requests_cache.CachedSession()

pid_df = pd.read_csv("data/playerid_list.csv")  

def get_all_boxscores(year: int) -> pd.DataFrame:
    url = f"https://www.baseball-reference.com/leagues/majors/{year}-schedule.shtml"
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    script = soup.find("script", {"type": "application/ld+json"})
    payload = script.string.strip()

    events = json.loads(payload)

    today = date.today()
    rows = []
    for ev in events:
        if ev.get("@type") != "SportsEvent":
            continue
        
        try:
            game_date = datetime.strptime(ev["startDate"], "%B %d, %Y").date()
        except Exception:
            continue
        
        if game_date > today:
            continue
        
        box = ev.get("url", "")
        if not box or "/boxes/" not in box:
            continue
        
        # The 'name' field is "Away Team @ Home Team"
        away, home = ev["name"].split(" @ ")
        rows.append({
            "Date" : game_date,
            "Opp" : away,
            "Tm" : home,
            "Boxscore" : box,
        })

    schedule_df = pd.DataFrame(rows)
    return schedule_df

def get_starting_pitcher(box_url: str, team_name: str, game_date, year: int = 2024) -> dict:
    resp = session.get(box_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    clean = re.sub(r'[^A-Za-z]', '', team_name)
    table_id = f"{clean}pitching"
    comments = soup.find_all(string=lambda t: isinstance(t, Comment))

    try:
        comment = next(c for c in comments if table_id in c)
    except StopIteration:
        warnings.warn(f"No pitching table for {team_name} at {box_url}; returning NaNs")
        return {
            'SP':       np.nan,
            'SP_ERA':   np.nan,
            'SP_WPA':   np.nan,
            'SP_K9':    np.nan,
            'SP_BB9':   np.nan,
            'SP_WHIP':  np.nan,
            'SP_HardHit%': np.nan,
            'SP_IP':    np.nan
        }

    inner = BeautifulSoup(comment, "html.parser")
    table = inner.find("table", id=table_id)

    row = table.tbody.find("tr")
    
    def _parse_float(cell, stat):
        text = cell.get_text(strip=True) if cell is not None else ""
        return float(text) if text else np.nan
    
    data = {}
    name_cell = row.find("th", {"data-stat": "player"})
    raw = name_cell.find("a").get_text(strip=True)
    name = raw.encode("latin-1").decode("utf-8")
    data['SP'] = name
    era_cell = row.find("td", {"data-stat": "earned_run_avg"})
    data['SP_ERA'] = _parse_float(era_cell, 'earned_run_avg')
    # TODO: Use WAR
    
    player_stats = get_player_stats(data['SP'], game_date, year)
    data.update(player_stats)
    
    return data

def get_player_stats(player_name: str, game_date, year: int = 2025) -> dict:
    if not player_name or pd.isna(player_name):
        print(
            f"⚠️ get_player_stats(): no player_name provided (game_date={game_date}); "
            "returning NaNs for SP stats."
        )
        return {'K9':np.nan, 'BB9':np.nan, 'WHIP':np.nan, 'HardHit%':np.nan, 'IP':np.nan}
    
    #player_name = player_name.encode("latin-1").decode("utf-8")
    last, first = player_name.split()[-1], player_name.split()[0]
    
    player_id = pid_df[(pid_df['LASTNAME'] == last) & (pid_df['FIRSTNAME'] == first)]
    if not player_id.empty:
        raw_code = player_id['MLBCODE'].iat[0]
        if pd.notna(raw_code):
            pid = int(raw_code)
        else:
            pid = None
    else:
        pid = None
    
    if pid is None:
        # Fallback to pybaseball lookup (key_mlbam column)
        mlb_df = playerid_lookup(last, first)
        if mlb_df.empty or mlb_df['key_mlbam'].isna().all():
            warnings.warn(f"No PID found for {player_name}; returning NaNs")
            return dict(SP_ERA=np.nan, SP_K9=np.nan, SP_BB9=np.nan, SP_WHIP=np.nan, SP_IP=np.nan)
        pid = int(mlb_df.loc[mlb_df['key_mlbam'].notna(),'key_mlbam'].iat[0])
    
    if game_date is type(str):
        game_date = game_date + f" {year}"
    end_dt = pd.to_datetime(game_date).strftime("%Y-%m-%d")
    start_dt = f"{year}-03-01"
    
    try:
        df = statcast_pitcher(start_dt, end_dt, pid)
    except ParserError as e:
        warnings.warn(
            f"ParserError reading Statcast for {player_name} ({pid}) on {end_dt}: {e}\n"
            "Falling back to NaNs."
        )
        return _make_nan_stats()
    except Exception as e:
        warnings.warn(f"Unexpected error for {player_name} ({pid}) on {end_dt}: {e}")
        return _make_nan_stats()

    if df.empty:
        return _make_nan_stats()
    
    if 'outs_when_up' not in df.columns:
        warnings.warn(f"Statcast output missing 'outs_when_up' for {player_name} on {end_dt}; returning NaNs")
        return _make_nan_stats()
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
        'SP_K9': round(k9, 2),
        'SP_BB9': round(bb9, 2),
        'SP_WHIP': round(whip,2),
        'SP_HardHit%': round(hard_hit_pct, 2),
        'SP_IP': round(innings,2)
    }

def _make_nan_stats():
    return {
        'SP_K9':       np.nan,
        'SP_BB9':      np.nan,
        'SP_WHIP':     np.nan,
        'SP_HardHit%': np.nan,
        'SP_IP':       np.nan
    }

#print(get_player_stats("Clarke Schmidt", "2024-05-04", 2024))
#print(get_starting_pitcher("https://www.baseball-reference.com/boxes/NYA/NYA202405040.shtml", "New York Yankees", "2024-05-04", 2024))
