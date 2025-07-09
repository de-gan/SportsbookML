import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import pandas as pd
from src.load_process import load_team_schedule, load_all_team_data, load_team_schedule_CSV
from src.lgbm_model import train_lgbm_regression_model, train_lgbm_classification_model

#
# Load all team data for 2023
#
def get_all_teams_schedule(year: int):
    print(f"Loading all team data for {year}...")
    df = load_all_team_data(year)
    print("All team data loaded.")
    print(df.head())

#
# Load the schedule for a specific team
#
def get_team_schedule(team: str, year: int):
    print(f"Loading schedule for {team} in {year}...")
    df = load_team_schedule(team, year)
    print(f"\nSchedule for {team} in {year} loaded.")
    print(df.columns)
    print(df.head())

#
# Load the schedule for a specific team with known CSV
#
def get_team_scheduleCSV(team: str, year: int):
    print(f"Loading schedule for {team} in {year}...")
    df = load_team_schedule_CSV(team, year)
    print(f"Schedule for {team} in {year} loaded.")
    print(df.head())
    
#get_team_schedule('NYY', 2024)
#get_all_teams_schedule(2024)
schedules_2024 = load_all_team_data(2024)
#train_lgbm_regression_model(2024, schedules_2024)
train_lgbm_classification_model(2024, schedules_2024)

#df = schedule_nyy.drop(columns=['Date', 'Tm', 'W-L', 'GB', 'Win', 'Loss'])
#print(df.head())
#correlation_matrix = df.corr()
#sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm")
#plt.show()