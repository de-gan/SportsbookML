import requests
import io
import zipfile
import pandas as pd
from functools import lru_cache
from datetime import date

@lru_cache(maxsize=None)
def fetch_daily_war_df(game_date) -> pd.DataFrame:
    """
    Download the war_daily_pitch ZIP for a given date (YYYY‑MM‑DD),
    unzip it in memory, read the inner CSV, and return a DataFrame.
    """
    if not isinstance(game_date, date):
        ymd = pd.to_datetime(game_date).strftime("%Y-%m-%d")

    # build the URL
    url = f"https://www.baseball-reference.com/data/war_archive-{ymd}.zip"

    resp = requests.get(url)
    if resp.status_code == 404:
        return pd.DataFrame()
    resp.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        inner_name = next(n for n in zf.namelist() if "war_daily_pitch" in n)
        with zf.open(inner_name) as csvfile:
            df = pd.read_csv(csvfile)
    #print(f"Loaded {len(df)} rows from {inner_name} for {ymd}")
    return df

def get_pitcher_war_on_date(mlb_code: float, game_date: str) -> float:
    """
    Returns the pitcher’s cumulative WAR as of game_date.
    bbref_id should be the 'key_bbref' from pybaseball.playerid_lookup.
    """
    df = fetch_daily_war_df(game_date)
    if df.empty:
        print(f"No WAR data available for {game_date}")
        return float("nan")
    
    #print("mlb_ID dtype:", df['mlb_ID'].dtype)
    df["mlb_ID"] = df["mlb_ID"].astype(float)
    mlb_code = float(mlb_code)

    # 3) boolean mask on mlb_ID, then select the 'WAR' column
    mask = (df["mlb_ID"] == mlb_code) & (df["year_ID"] == pd.to_datetime(game_date).year)
    war_series = df.loc[mask, "WAR"]

    return war_series.iloc[0] if not war_series.empty else float("nan")

