from sklearn.preprocessing import LabelEncoder
import pandas as pd
import time
from tqdm import tqdm
import random

from src.pitchers import get_starting_pitcher
from src.fangraphs_stats import fg_team_snapshot

# Arizona D'Backs when creating raw data (for collecting boxscores) or making prediction
# Arizona Diamondbacks when creating processed data 
# 2025 season uses Athletics: 'ATH'
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
#   'Oakland Athletics':      'OAK',
    'Athletics':              'ATH',
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

full_to_abbrev_proc = full_to_abbrev.copy()
full_to_abbrev_proc['Arizona Diamondbacks'] = full_to_abbrev_proc.pop('Arizona D\'Backs')

abbrev_to_full = {abbrev: full for full, abbrev in full_to_abbrev_proc.items()}

_snapshot_cache = {}

def get_snapshot_for_date(season: int, as_of: str):
    if as_of not in _snapshot_cache:
        _snapshot_cache[as_of] = fg_team_snapshot(season, as_of)
    return _snapshot_cache[as_of]

# Create features for team dataframe
def create_features(year: int, df: pd.DataFrame, rolling_windows=[3, 5, 10]) -> pd.DataFrame:
    df = df.copy()
    # Drop unwanted columns
    df.drop(columns=['Time', 'Attendance', 'Inn', 'Orig. Scheduled', 'Save', 'GB', 'Win', 'Loss', 'Game_Number'], inplace=True)
    df.loc[:, 'Run_Diff'] = df['R'] - df['RA']

    df['Tm'] = df['Tm'].map(abbrev_to_full)

    # Get starting pitcher stats
    def _scrape_sp(row):
        stats = get_starting_pitcher(
            row['Boxscore'],
            row['Tm'],
            row['Date'],
            year
        )
        time.sleep(random.uniform(1,2))  # Random sleep to avoid hitting the server too hard
        return stats
    
    records = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Fetching SP stats"):
        stats = _scrape_sp(row)
        records.append(stats)

    sp_stats = pd.DataFrame(records)
    
    df = pd.concat([df.reset_index(drop=True), sp_stats], axis=1)
    
    df['Tm'] = df['Tm'].map(full_to_abbrev_proc)
    
    # Adjust date format
    if df['Date'].dtype == object or not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = df['Date'].str.replace(r'\s+\(\d\)', '', regex=True)
        df['Date'] = pd.to_datetime(df['Date'].astype(str) + f' {year}', format='%A, %b %d %Y')
    df.insert(1, 'Month', df['Date'].dt.month)
    df.insert(2, 'DayofWeek', df['Date'].dt.dayofweek)
    
    df.loc[:, 'cLI'] = pd.to_numeric(df['cLI'], errors='coerce')
    df['cLI'].fillna(0, inplace=True)
    
    # Shift the streak column
    df['Streak'] = (
        df
        .groupby('Tm')['Streak']
        .shift(1)
        .fillna(0)
        .astype(int)
    )
    
    # Rolling stats over various windows (Simple rolling and EWM)
    for window in rolling_windows:
        df[f'R_MA{window}'] = (
            df['R']
            .shift(1)
            .rolling(window=window, min_periods=1)
            .mean()
            .round(3)
        )
        df[f'RA_MA{window}'] = (
            df['RA']
            .shift(1)
            .rolling(window=window, min_periods=1)
            .mean()
            .round(3)
        )
        df[f'RunDiff_MA{window}'] = (
            df['Run_Diff']
            .shift(1)
            .rolling(window=window, min_periods=1)
            .mean()
            .round(3)
        )
        
        df[f'R_EWMA{window}'] = (
            df['R']
            .shift(1)
            .ewm(span=window, adjust=False)
            .mean()
            .round(3)
        )
        
        df[f'RA_EWMA{window}'] = (
            df['RA']
            .shift(1)
            .ewm(span=window, adjust=False)
            .mean()
            .round(3)
        )
        
        df[f'RunDiff_EWMA{window}'] = (
            df['Run_Diff']
            .shift(1)
            .ewm(span=window, adjust=False)
            .mean()
            .round(3)
        )
    
    # Encode categorical variables
    df['Home_Away'] = df['Home_Away'].map({'Home': 1, '@': 0})
    df['W/L'] = df['W/L'].replace({'W-wo':'W','L-wo':'L'}).map({'W': 1,'L': 0})
    df['D/N'] = df['D/N'].map({'D': 0, 'N': 1}) # Day = 0, Night = 1
    
    # Add Fangraphs stats
    df['Date'] = pd.to_datetime(df['Date'])
    df['as_of'] = (df['Date'] - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")

    # Pull out the Tm rows for each game
    batting_rows = []
    for _, row in df.iterrows():
        snap = get_snapshot_for_date(year, row['as_of'])
        print("Fetching Fangraphs stats for date:", row['as_of'])
        team_slice = snap[snap['Tm'] == row['Tm']]
        if team_slice.empty:
            # build a dict of NaNs for every stat except 'Tm'
            tm_pref = {c: float('nan') for c in snap.columns if c != 'Tm'}
        else:
            tm_vals = team_slice.iloc[0]
            tm_pref = {
                c: tm_vals[c] 
                for c in tm_vals.index
                if c != 'Tm'
            }
            
        batting_rows.append({**tm_pref})

    batting_df = pd.DataFrame(batting_rows)
    df = pd.concat([df.reset_index(drop=True), batting_df], axis=1)
    df.drop(columns=['as_of'], inplace=True)
    
    return df