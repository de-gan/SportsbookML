import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

from src.load_process import update_season_data, get_teams_schedules
from src.lgbm_model import create_models
from src.auto_predict import predict_for_date
from src.odds import get_game_odds_today, suggest_units


def predict_and_odds(date: str):
    """Return model predictions merged with available odds for a given date.

    Parameters
    ----------
    date: str
        Target date in ``YYYY-MM-DD`` format.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing one row per team with model probability, odds and
        suggested betting units. If odds cannot be retrieved the odds related
        columns will contain ``NaN`` values and units will be ``0``.
    """

    pred_df = predict_for_date(date)

    try:
        odds_df = get_game_odds_today()
    except Exception:
        odds_df = None

    if odds_df is not None and not odds_df.empty:
        merged = pred_df.merge(odds_df, on=["Team"], how="left")
        merged.drop(columns=["home_team", "away_team"], inplace=True)

        merged["Implied_Odds"] = (1 / merged["Odds"]).round(3)
        merged["Edge"] = (merged["Model_Prob"] - merged["Implied_Odds"]).round(3)
        merged["EV"] = (merged["Model_Prob"] * merged["Odds"] - 1).round(3)
        merged["Units"] = suggest_units(
            merged,
            bankroll_units=100.0,
            kelly_frac=0.25,
            min_edge=0.06,
            max_bankroll_frac=0.02,
            round_to_units=0.01,
        )
    else:
        merged = pred_df.copy()
        merged["Odds"] = float("nan")
        merged["Book"] = float("nan")
        merged["Implied_Odds"] = float("nan")
        merged["Edge"] = float("nan")
        merged["EV"] = float("nan")
        merged["Units"] = 0.0

    bets_to_place = merged.loc[merged["Units"] > 0, ["Team", "Model_Prob", "Odds", "Edge", "EV", "Units", "Book"]].copy()
    if not bets_to_place.empty:
        bets_to_place = bets_to_place.sort_values("Edge", ascending=False).reset_index(drop=True)
        print(bets_to_place.to_string(index=False))

    merged.to_csv("data/processed/games_today.csv", index=False)
    return merged

def full_updated_odds(date: str):
    # Retrieve up-to-date raw game data
    get_teams_schedules(2025)

    # Update processed data
    update_season_data()

    # Create LightGBM models
    create_models()
    
    predict_and_odds(date)

#get_teams_schedules(2025)
#load_all_teams_data(2025)

#create_models()

#full_updated_odds()


if __name__ == "__main__":
    from datetime import date
    predict_and_odds(date.today().isoformat())
