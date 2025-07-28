import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import pandas as pd
from src.load_process import load_all_teams_data, load_team_schedule_raw_CSV, process_all_teams_data, process_team_data, update_season_data, get_team_schedules
from src.lgbm_model import train_run_diff_model, train_run_total_model, train_lgbm_classification_model
from auto_predict import get_starting_pitcher_from_preview
from src.pitchers import get_player_stats

def create_models():
    schedules_2025 = load_all_teams_data(2025)
    print(schedules_2025.columns)
    train_lgbm_classification_model(schedules_2025)
    train_run_diff_model(schedules_2025)
    train_run_total_model(schedules_2025)


create_models()
#get_team_schedules(2025)

#update_season_data()
#pitcher = get_starting_pitcher_from_preview("https://www.baseball-reference.com/previews/2025/NYA202507270.shtml", "NYY")
#print(get_player_stats(pitcher, "2025-07-27", 2025))