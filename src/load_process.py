import os
import pandas as pd

from pybaseball import schedule_and_record

from src.feature_engineering import create_features

"""
Load and process team data for all MLB teams for a given year.
"""
def load_all_team_data(year: int) -> pd.DataFrame:
    mlb_teams = ['NYY', 'BOS', 'TOR', 'BAL', 'TBR',  # AL East
             'CHW', 'CLE', 'DET', 'KCR', 'MIN',  # AL Central
             'HOU', 'LAA', 'OAK', 'SEA', 'TEX',  # AL West
             'ATL', 'MIA', 'NYM', 'PHI', 'WSN',  # NL East
             'CHC', 'CIN', 'MIL', 'PIT', 'STL',  # NL Central
             'ARI', 'COL', 'LAD', 'SDP', 'SFG']  # NL West

    raw_team_schedules = {}

    for team in mlb_teams:
        try:
            df = schedule_and_record(year, team)
            df['Team'] = team
            raw_team_schedules[team] = df
        except Exception as e:
            print(f"Error loading {team}: {e}")

    all_teams_df = pd.concat(raw_team_schedules.values(), ignore_index=True)
    
    # Save raw data as CSV
    all_teams_df.to_csv(f"data/raw/mlb_teams_schedules_{year}.csv", index=False)

    
    return all_teams_df

def process_teams_data(year: int) -> None:
    """
    Process the raw teams data by creating features and cleaning the DataFrame.
    """
    processed_team_schedules = pd.read_csv(f"data/raw/{year}.csv")
    proccessed_team_schedules = create_features(processed_team_schedules)

    proccessed_team_schedules.to_csv("data/processed/mlb_teams_schedules_2024_processed.csv", index=False)

def load_team_schedule(team: str, year: int) -> pd.DataFrame:
    filepath = f"data/processed/mlb_teams_schedules_{year}_processed.csv"

    if os.path.exists(filepath):
        print(f"Loading cached file: {filepath}")
        df = pd.read_csv(filepath)
        df = df[df['Team'] == team]
        df.reset_index(drop=True, inplace=True)
        return df
    else:
        print(f"Missing processed file: {filepath}")
        