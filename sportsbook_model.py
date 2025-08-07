import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import pandas as pd
from src.load_process import load_all_teams_data, update_season_data, get_teams_schedules
from src.lgbm_model import train_run_diff_model, train_run_total_model, train_lgbm_classification_model
from auto_predict import predict_for_date
from src.fangraphs_batting import fg_team_snapshot_api
from src.odds import get_game_odds_today

\
def create_models():
    schedules_2025 = load_all_teams_data(2025)
    print(schedules_2025.columns)
    train_lgbm_classification_model(schedules_2025)
    train_run_diff_model(schedules_2025)
    train_run_total_model(schedules_2025)


#create_models()
#get_teams_schedules(2025)
#load_all_teams_data(2025)
#update_season_data()
pred_df = predict_for_date("2025-08-06")
odds_df = get_game_odds_today()

merged = pred_df.merge(odds_df, on=["Team"], how="left")
merged.drop(columns=["home_team", "away_team"], inplace=True)

merged["Implied_Odds"] = (1 / merged["Odds"]).round(3)
merged["Edge"] = (merged["Model_Prob"] - merged["Implied_Odds"]).round(3)
merged["EV"] = (merged["Model_Prob"] * merged["Odds"] - 1).round(3)
value_bets = (
    merged
    .query("Edge >= 0.05 and EV > 0")
    .sort_values("EV", ascending=False)
)
print(value_bets)

merged.to_csv("data/processed/games_today.csv", index=False)