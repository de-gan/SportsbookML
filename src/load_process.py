import os
import pandas as pd

from pybaseball import schedule_and_record

from src.feature_engineering import create_features

#
# Load and process team data for all MLB teams for a given year.]
# Returns a DataFrame containing the schedules and records of all teams (Processed).
#
def load_all_team_data(year: int) -> pd.DataFrame:
    # Load if CSV exists
    rawpath = f"data/raw/mlb_teams_schedules_{year}.csv"
    newpath = f"data/processed/mlb_teams_schedules_{year}_processed.csv"
    if os.path.exists(rawpath) and os.path.exists(newpath):
        print(f"Loading cached file: {newpath}")
        return pd.read_csv(newpath)
    
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
    all_teams_df.to_csv(rawpath, index=False)
    
    return process_all_teams_data(year, all_teams_df)

#
# Process the raw teams data by creating features and cleaning the DataFrame.
# Returns a DataFrame containing the processed schedules and records of all teams.
#
def process_all_teams_data(year: int, df: pd.DataFrame) -> pd.DataFrame:
    processed_df = create_features(df)
    outpath = f"data/processed/mlb_teams_schedules_{year}_processed.csv"
    processed_df.to_csv(outpath, index=False)
    return processed_df

#
# Load the schedule for a specific team and year from a cached CSV file.
#
def load_team_schedule_CSV(team: str, year: int) -> pd.DataFrame:
    filepath = f"data/processed/mlb_teams_schedules_{year}_processed.csv"

    if os.path.exists(filepath):
        print(f"Loading cached file: {filepath}")
        df = pd.read_csv(filepath)
        df = df[df['Team'] == team]
        df.reset_index(drop=True, inplace=True)
        return df
    else:
        print(f"Missing processed file: {filepath}")

def load_team_schedule(team: str, year: int) -> pd.DataFrame:
    df = schedule_and_record(year, team)
    processed_df = create_features(df)
    return processed_df