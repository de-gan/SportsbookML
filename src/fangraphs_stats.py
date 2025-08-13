import requests
import pandas as pd
import numpy as np
from functools import lru_cache
from bs4 import BeautifulSoup
from joblib import Memory

memory = Memory(location=".fangraphs_cache", verbose=0)

def strip_link(html):
    return BeautifulSoup(html, "html.parser").get_text()

def _prefix_all(df, key='Tm', prefix='B_'):
    df = df.rename(columns={'Team': key})
    df = df.rename(columns={c: f"{prefix}{c}" for c in df.columns if c != key})
    return df

@lru_cache()
def fg_team_batting_snapshot(season: int, as_of: str) -> pd.DataFrame:
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
    
    #df.to_csv("data/fangraphs_batting_data.csv", index=False)

    important_batting_stats = [
        'Team', 'HR', 'RBI', 'H', 'wRC+', 'wOBA', 'SLG+', 'OBP+', 'AVG+', 'ISO+',
        'HRFB%+', 'BB%+', 'K%+', 'Spd', 'EV', 'LA', 'Barrel%', 'HardHit%',
        'Pull%+', 'Oppo%+', 'Cent%+', 'WPA', 'pLI', 'Clutch', 'WAR', 'RAR',
        'BaseRunning', 'Offense', 'Defense', 'Fielding', 'wBsR', 'Batting', 'Positional', 'wLeague',
    ]

    if df.empty:
        df = pd.DataFrame(columns=important_batting_stats)
        df = _prefix_all(df, key='Tm', prefix='B_')
        return df

    df[important_batting_stats] = df[important_batting_stats].round(3)
    df = df[important_batting_stats]
    df['Team'] = df['Team'].apply(strip_link)
    bat_df = _prefix_all(df, key='Tm', prefix='B_')
    return bat_df

@lru_cache()
def fg_team_bullpen_snapshot(season: int, as_of: str) -> pd.DataFrame:
    url = 'https://www.fangraphs.com/api/leaders/major-league/data'
    params = {
        'pos':       'all',             # include all positions
        'stats':     'rel',             # RP stats
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

    important_pitching_stats = [
        'Team', 'WPA', 'pLI', 'Clutch', 'MD', 'WAR', 'FIP', 'ERA', 'RAR', 
    ]

    if df.empty:
        df = pd.DataFrame(columns=important_pitching_stats)
        df = _prefix_all(df, key='Tm', prefix='RP_')
        return df

    df[important_pitching_stats] = df[important_pitching_stats].round(3)
    df = df[important_pitching_stats]
    df['Team'] = df['Team'].apply(strip_link)
    rp_df = _prefix_all(df, key='Tm', prefix='RP_')
    return rp_df

def fg_team_snapshot(season: int, as_of: str) -> pd.DataFrame:
    bat_df = fg_team_batting_snapshot(season, as_of)
    bp_df = fg_team_bullpen_snapshot(season, as_of)
    
    #bp_df.to_csv("data/fangraphs_pitching_data.csv", index=False)
    #bat_df.to_csv("data/fangraphs_batting_data.csv", index=False)
    
    df = bat_df.merge(bp_df, on=["Tm"], how="left")
    #df.to_csv("data/merged_fangraphs_data.csv", index=False)
    return df