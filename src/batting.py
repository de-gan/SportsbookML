from pybaseball import team_batting, batting_stats_range
import pandas as pd
from datetime import date

def load_team_batting_metrics(year: int) -> pd.DataFrame:
    """
    Saves the team batting metrics for a given year to a CSV file.
    """
    df = team_batting(year)
    
    df.loc[:, 'Date'] = date.today()
    df.insert(0, 'Date', df.pop('Date'))
    
    df.to_csv(f"data/raw/all_batting_{year}.csv", index=False)
    
    return df.columns
    

def get_team_batting_metrics(year: int) -> pd.DataFrame:
    """
    Returns a DataFrame with one row per MLB team, containing key batting metrics.
    """
    df = team_batting(year)
    
    df = df.rename(columns={
        'Team': 'Tm',
    })
    
    # Select relevant columns
    df = df[[
        'Tm', 'wRC+', 'wOBA', 'SLG+', 'AVG+', 'OBP+', 'ISO+', 'HR/FB%+', 'BB%+', 'K%+', 'Bat', 'Off', 'Spd', 'BsR',
        'EV', 'LA', 'Barrel%', 'HardHit%', 'Pull%+', 'Oppo%+', 'Cent%+', 'HR', 'RBI', 'H'
    ]]
    
    return df

load_team_batting_metrics(2025)