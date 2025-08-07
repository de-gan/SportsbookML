import requests
import pandas as pd
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
        "apiKey": os.getenv("API_KEY"),
        #"regions": REGIONS,
        "markets": MARKETS,
        #"commenceTimeFrom": "2025-08-05T04:00:00Z",
        "commenceTimeTo": f"{tomorrow}T03:59:59Z",
        "bookmakers": BOOKMAKERS,
    }
    resp = requests.get(url, params=params)
    odds_data = resp.json()
    odds_df = pd.json_normalize(odds_data,
        record_path=["bookmakers", "markets", "outcomes"],
        meta=[
        ["bookmakers","title"],
        ["bookmakers","last_update"],
        "home_team","away_team"
        ]
    ).rename(columns={"price":"Odds","name":"Team","bookmakers.title":"Book"})
    
    odds_df["Team"] = odds_df["Team"].str.replace(
        "Oakland Athletics", "Athletics", regex=False
    )
    odds_df["Team"] = odds_df["Team"].str.replace(
        "Arizona Diamondbacks", "Arizona D\'Backs", regex=False
    )
    
    odds_df['Team'] = odds_df["Team"].map(full_to_abbrev)
    
    #print(odds_df)
    odds_df.to_csv("data/processed/odds.csv", index=False)
    return odds_df
