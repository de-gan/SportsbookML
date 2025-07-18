import os
import pandas as pd

from pybaseball import schedule_and_record

from src.feature_engineering import create_features
from src.pitchers import get_all_boxscores

full_to_abbrev = {
    'Arizona D\'Backs':       'ARI',
    'Atlanta Braves':         'ATL',
    'Baltimore Orioles':      'BAL',
    'Boston Red Sox':         'BOS',
    'Chicago Cubs':           'CHC',
    'Chicago White Sox':      'CHW',
    'Cincinnati Reds':        'CIN',
    'Cleveland Guardians':    'CLE',
    'Colorado Rockies':       'COL',
    'Detroit Tigers':         'DET',
    'Houston Astros':         'HOU',
    'Kansas City Royals':     'KCR',
    'Los Angeles Angels':     'LAA',
    'Los Angeles Dodgers':    'LAD',
    'Miami Marlins':          'MIA',
    'Milwaukee Brewers':      'MIL',
    'Minnesota Twins':        'MIN',
    'New York Mets':          'NYM',
    'New York Yankees':       'NYY',
    'Oakland Athletics':      'OAK',
    'Philadelphia Phillies':  'PHI',
    'Pittsburgh Pirates':     'PIT',
    'San Diego Padres':       'SDP',
    'Seattle Mariners':       'SEA',
    'San Francisco Giants':   'SFG',
    'St. Louis Cardinals':    'STL',
    'Tampa Bay Rays':         'TBR',
    'Texas Rangers':          'TEX',
    'Toronto Blue Jays':      'TOR',
    'Washington Nationals':   'WSN'
}

#
# Load and process team data for all MLB teams for a given year.
# Returns a DataFrame containing the schedules and records of all teams (Processed).
#
def load_all_team_data(year: int) -> pd.DataFrame:
    # Load if CSV exists
    rawpath = f"data/raw/mlb_teams_schedules_{year}.csv"
    newpath = f"data/processed/mlb_teams_schedules_{year}_processed.csv"
    if os.path.exists(rawpath) and os.path.exists(newpath):
        print(f"Loading CSV file: {newpath}")
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
            raw_team_schedules[team] = df
        except Exception as e:
            print(f"Error loading {team}: {e}")

    raw_df = pd.concat(raw_team_schedules.values(), ignore_index=True)
    
    box_df = get_all_boxscores(year)
    raw_df['Game_Number'] = (
    raw_df['Date']
          .str.extract(r'\((\d+)\)$', expand=False)   # pulls out “1” or “2”
          .fillna('1')                               # single game → game 1
          .astype(int)
    )
    raw_df['Date'] = raw_df['Date'].str.replace(r'\s*\(\d+\)$', '', regex=True)

    box_df['Game_Number'] = box_df.groupby(
        ['Date','Tm','Opp']
    ).cumcount() + 1

    box_df['Tm'] = box_df['Tm'].map(full_to_abbrev)
    box_df['Opp'] = box_df['Opp'].map(full_to_abbrev)

    box_df['Date'] = pd.to_datetime(box_df['Date'], format='%B %d, %Y')
    box_df['Date'] = box_df['Date'].dt.strftime('%A, %b %-d')

    boxOpp_df = box_df.copy()
    boxOpp_df.rename(columns={'Tm': 'Opp', 'Opp': 'Tm'}, inplace=True)

    boxLong_df = pd.concat([box_df, boxOpp_df], ignore_index=True)
    merged_df = pd.merge(
        raw_df,
        boxLong_df,
        on=['Date', 'Tm', 'Opp', 'Game_Number'],
        how='left',
        suffixes=('', '_p')
    )
    
    merged_df.to_csv(rawpath, index=False)
    
    return process_all_teams_data(year, merged_df)

#
# Process the raw teams data by creating features and cleaning the DataFrame.
# Adds opponent features in each row
# Returns a DataFrame containing the processed schedules and records of all teams.
#
def process_all_teams_data(year: int, df: pd.DataFrame) -> pd.DataFrame:
    processed_df = create_features(df)
    merged_df = get_opponent_features(processed_df)
    
    outpath = f"data/processed/mlb_teams_schedules_{year}_processed.csv"
    merged_df.to_csv(outpath, index=False)
    return merged_df

def process_team_data(df: pd.DataFrame) -> pd.DataFrame:
    processed_df = create_features(df)

    return processed_df

def get_opponent_features(df: pd.DataFrame) -> pd.DataFrame:
    all_rows = []
    
    # Step 1: Group by each team so we can access each team's schedule
    teams = df['Tm'].unique()
    team_schedules = {team: df[df['Tm'] == team].copy() for team in teams}

    # Step 2: Go row by row, and pull opponent's version of the same game
    for idx, row in df.iterrows():
        team = row['Tm']
        opponent = row['Opp']
        month = row['Month']
        dow = row['DayofWeek']
        
        # Get opponent schedule
        if opponent not in team_schedules:
            continue
        
        opp_schedule = team_schedules[opponent]
        
        # Try to find the matching game (same day, opponent = team)
        opp_game = opp_schedule[
            (opp_schedule['Opp'] == team) &
            (opp_schedule['Month'] == month) &
            (opp_schedule['DayofWeek'] == dow)
        ]
        
        if opp_game.empty:
            continue
        
        # Extract relevant opponent stats (add prefix)
        opp_features = opp_game.iloc[0].drop(['Tm', 'Opp', 'Home_Away', 'W/L', 'R', 'RA', 'W-L', 'D/N', 'Boxscore'])
        opp_features.index = ['Opp_' + col for col in opp_features.index]
        
        # Combine row and opponent features
        combined = pd.concat([row, opp_features])
        all_rows.append(combined)
    
    return pd.DataFrame(all_rows)

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
        
#
# Load the schedule for a specific team and year from a cached CSV file. From raw data.
#
def load_team_schedule_raw_CSV(team: str, year: int) -> pd.DataFrame:
    filepath = f"data/raw/mlb_teams_schedules_{year}.csv"

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