import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

from datetime import date
from src.load_process import update_season_data, get_teams_schedules, load_all_teams_data
from src.lgbm_model import create_models
from src.auto_predict import predict_for_date
from src.odds import get_game_odds_today, suggest_units

def predict_and_odds(date: str, bankroll: float, kelly: float, min_edge: float, max_bet_frac: float):
    pred_df = predict_for_date(date)
    odds_df = get_game_odds_today()

    merged = pred_df.merge(odds_df, on=["Team"], how="left")
    # Keep home_team and away_team columns so downstream consumers can
    # reconstruct full matchups from the CSV output.

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

    merged.to_csv("data/processed/games_today.csv", index=False)

def full_updated_odds(date: str, bankroll: float = 100.0, kelly: float = 0.50, min_edge: float = 0.05, max_bet_frac: float = 0.02):
    # Retrieve up-to-date raw game data
    get_teams_schedules(2025)

    # Update processed data
    update_season_data()

    # Create LightGBM models
    #create_models()
    
    predict_and_odds(date, bankroll, kelly, min_edge, max_bet_frac)    

if __name__ == '__main__':
    #d = date.today().strftime("%Y-%m-%d")
    #full_updated_odds(d)
    load_all_teams_data(2023)
    
