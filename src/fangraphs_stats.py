import requests
import pandas as pd
import numpy as np
from functools import lru_cache
from bs4 import BeautifulSoup
from joblib import Memory

memory = Memory(location=".fangraphs_cache", verbose=0)

def strip_link(html):
    return BeautifulSoup(html, "html.parser").get_text()

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
        df.rename(columns={'Team': 'Tm'}, inplace=True)
        return df

    df[important_batting_stats] = df[important_batting_stats].round(3)
    df = df[important_batting_stats]
    df['Team'] = df['Team'].apply(strip_link)
    df.rename(columns={'Team': 'Tm'}, inplace=True)
    print(df.columns)
    bat_df = df.rename(columns={col: f"B_{col}" for col in df.columns if col != "Tm"})
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

    df.to_csv("data/fangraphs_pitching_data.csv", index=False)

    important_pitching_stats = [
        'Team', 'WPA', 'pLI', 'Clutch', 'MD', 'WAR', 'FIP', 'ERA', 'RAR', 
    ]

    if df.empty:
        df = pd.DataFrame(columns=important_pitching_stats)
        df.rename(columns={'Team': 'Tm'}, inplace=True)
        return df

    df[important_pitching_stats] = df[important_pitching_stats].round(3)
    df = df[important_pitching_stats]
    df['Team'] = df['Team'].apply(strip_link)
    df.rename(columns={'Team': 'Tm'}, inplace=True)
    print(df.columns)
    bp_df = df.rename(columns={col: f"RP_{col}" for col in df.columns if col != "Tm"})
    return bp_df

def fg_team_snapshot(season: int, as_of: str) -> pd.DataFrame:
    bat_df = fg_team_batting_snapshot(season, as_of)
    bp_df = fg_team_bullpen_snapshot(season, as_of)
    
    df = bat_df.merge(bp_df, on=["Tm"], how="left")
    return df