import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import os
import pandas as pd
import numpy as np
from datetime import date
from src.mlb.load_process import update_season_data, get_teams_schedules, load_all_teams_data
from src.mlb.lgbm_model import create_models
from src.mlb.auto_predict import predict_for_date
from src.mlb.odds import get_game_odds_today, suggest_units
from src.mlb.supabase_client import upsert_predictions, upload_file_to_bucket, ensure_local_file

def predict_and_odds(date: str, bankroll: float, kelly: float, min_edge: float, max_bet_frac: float):
    pred_df = predict_for_date(date)
    odds_df = get_game_odds_today()

    merged = pred_df.merge(odds_df, on=["Team"], how="left")

    merged["Implied_Odds"] = (1 / merged["Odds"]).round(3)
    merged["Edge"] = (merged["Model_Prob"] - merged["Implied_Odds"]).round(3)
    merged["EV"] = (merged["Model_Prob"] * merged["Odds"] - 1).round(3)
    merged["Units"] = suggest_units(
        merged,
        bankroll_units=bankroll,
        kelly_frac=kelly,
        min_edge=min_edge,
        max_bankroll_frac=max_bet_frac,
        round_to_units=0.01,
    )
    
    bets_to_place = merged.loc[merged["Units"] > 0, ["Team", "Model_Prob", "Odds", "Edge", "EV", "Units", "Book"]].copy()
    bets_to_place = bets_to_place.sort_values("Edge", ascending=False).reset_index(drop=True)
    print(bets_to_place.to_string(index=False))

    path = "data/games_today.csv"
    merged.to_csv(path, index=False)
    
    try:
        upload_file_to_bucket(path)
    except Exception as exc:
        print(f"Failed to upload games_today CSV to Supabase storage: {exc}")

    try:
        upsert_predictions(merged)
    except Exception as exc:
        print(f"Failed to upload today's predictions (games_today) to Supabase table: {exc}")

def full_updated_odds(date: str, bankroll: float = 100.0, kelly: float = 0.50, min_edge: float = 0.05, max_bet_frac: float = 0.02):
    # Retrieve up-to-date raw game data
    get_teams_schedules(2025)

    # Update processed data
    update_season_data()
    
    path = "data/pred_history.csv"
    bucket = os.getenv("SUPABASE_BUCKET")
    if bucket:
        try:
            ensure_local_file(bucket, "pred_history.csv", path)
        except Exception as exc:
            print(f"Warning: failed to download prediction history from Supabase: {exc}")
    
    predict_and_odds(date, bankroll, kelly, min_edge, max_bet_frac)
    
    df = pd.read_csv(path)
    df = df.replace([np.inf, -np.inf], None).where(pd.notnull(df), None)
    df = df.astype(object).where(pd.notnull(df), None)
    try:
        upsert_predictions(df, table="history")
    except Exception as exc:
        print(f"Failed to upload prediction history to Supabase table: {exc}")

if __name__ == '__main__':
    # Create LightGBM models
    #create_models()
    d = date.today().strftime("%Y-%m-%d")
    full_updated_odds(d)
    
