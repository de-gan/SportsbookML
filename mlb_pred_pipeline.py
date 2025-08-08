import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

from src.load_process import update_season_data, get_teams_schedules
from src.lgbm_model import create_models
from src.auto_predict import predict_for_date
from src.odds import get_game_odds_today

def full_updated_odds():
    # Retrieve up-to-date raw game data
    get_teams_schedules(2025)

    # Update processed data
    update_season_data()

    # Create LightGBM models
    create_models()

    # Make predictions for today's games
    pred_df = predict_for_date("2025-08-07")
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
    
    
create_models()

#full_updated_odds()
