from sportsreference.mlb.schedule import Schedule
from sportsreference.mlb.boxscore import Boxscore
import pandas as pd

def get_starting_pitchers(team_abbr: str, year: int) -> pd.DataFrame:
    """
    Returns one row per game for `team_abbr` in `year` with:
      Date, Tm, Opp, Home_Away (1=home,0=away), SP_name, SP_id
    """
    schedule = Schedule(team_abbr, year)
    rows = []
    for game in schedule:
        # Basic game info
        date       = game.date                 # datetime.date
        opponent   = game.opponent_abbr        # e.g. 'BOS'
        location   = game.location             # 'Home' or 'Away'
        home_away  = 1 if location == 'Home' else 0
        
        # Load the boxscore to get the SP
        box = Boxscore(game.boxscore_index)    # or .boxscore_link
        if location == 'Home':
            sp_name = box.home_starting_pitcher
            # Many Boxscore objects also expose an ID property:
            sp_id   = box.home_starting_pitcher_id  
        else:
            sp_name = box.away_starting_pitcher
            sp_id   = box.away_starting_pitcher_id
        
        rows.append({
            'Date'      : date,
            'Tm'        : team_abbr,
            'Opp'       : opponent,
            'Home_Away' : home_away,
            'SP_name'   : sp_name,
            'SP_id'     : sp_id,
        })
    return pd.DataFrame(rows)


df_sp = get_starting_pitchers('NYY', 2023)
print(df_sp.head())
