import requests
import pandas as pd
import numpy as np
import os
from datetime import date, timedelta

from dotenv import load_dotenv
from src.feature_engineering import full_to_abbrev

load_dotenv()

SPORT = "baseball_mlb"
REGIONS = "us"
MARKETS = "h2h"
BOOKMAKERS = "fanduel,draftkings,betus,betmgm"

def get_game_odds_today() -> pd.DataFrame:
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    today = date.today()
    tomorrow = today + timedelta(days=1)
    tomorrow = str(tomorrow)
    params = {
        "apiKey": os.getenv("ODDS_API_KEY"),
        #"regions": REGIONS,
        "markets": MARKETS,
        #"commenceTimeFrom": "2025-08-05T04:00:00Z",
        "commenceTimeTo": f"{tomorrow}T03:59:59Z",
        "bookmakers": BOOKMAKERS,
    }
    resp = requests.get(url, params=params)
    odds_data = resp.json()
    odds_df = pd.json_normalize(
        odds_data,
        record_path=["bookmakers", "markets", "outcomes"],
        meta=[
            ["bookmakers", "title"],
            ["bookmakers", "last_update"],
            "commence_time",
            "home_team",
            "away_team",
        ],
    ).rename(columns={"price": "Odds", "name": "Team", "bookmakers.title": "Book"})
    
    odds_df["Team"] = odds_df["Team"].str.replace(
        "Oakland Athletics", "Athletics", regex=False
    )
    odds_df["Team"] = odds_df["Team"].str.replace(
        "Arizona Diamondbacks", "Arizona D\'Backs", regex=False
    )
    odds_df["home_team"] = odds_df["home_team"].str.replace(
        "Oakland Athletics", "Athletics", regex=False
    )
    odds_df["away_team"] = odds_df["away_team"].str.replace(
        "Oakland Athletics", "Athletics", regex=False
    )
    odds_df["home_team"] = odds_df["home_team"].str.replace(
        "Arizona Diamondbacks", "Arizona D\'Backs", regex=False
    )
    odds_df["away_team"] = odds_df["away_team"].str.replace(
        "Arizona Diamondbacks", "Arizona D\'Backs", regex=False
    )
    
    odds_df['Team'] = odds_df["Team"].map(full_to_abbrev)
    odds_df["home_team"] = odds_df["home_team"].map(full_to_abbrev)
    odds_df["away_team"] = odds_df["away_team"].map(full_to_abbrev)

    # print(odds_df)
    # odds_df.to_csv("data/processed/odds.csv", index=False)
    return odds_df

def suggest_units(
    df,
    *,
    bankroll_units=100.0,
    kelly_frac=0.5,
    min_edge=0.05,
    min_ev=0.0,
    max_bankroll_frac=0.02,
    round_to_units=0.5,
    odds_col="Odds",
    prob_col="Model_Prob",
    edge_col="Edge",
    ev_col="EV"
):
    p = df[prob_col].astype(float)
    d = df[odds_col].astype(float)

    implied = 1.0 / d
    edge = df[edge_col].astype(float) if edge_col in df else (p - implied)
    ev   = df[ev_col].astype(float)   if ev_col   in df else (p * d - 1.0)

    # Full Kelly fraction for decimal odds
    b = d - 1.0
    f_full = (b * p - (1 - p)) / b
    f_full = np.clip(f_full, 0.0, None)

    # Fractional Kelly + cap
    f_used = np.clip(f_full * kelly_frac, 0.0, max_bankroll_frac)

    # Require edge/EV and positive stake
    mask = (edge >= min_edge) & (ev >= min_ev) & (f_used > 0)

    raw_units = bankroll_units * f_used
    units = np.round(raw_units / round_to_units) * round_to_units
    units = np.where(mask, units, 0.0)

    return units
