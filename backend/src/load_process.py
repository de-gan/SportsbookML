import os
import pandas as pd
import requests_cache

from pybaseball import schedule_and_record

from src.feature_engineering import create_features, full_to_abbrev
from src.pitchers import get_all_boxscores
from src.supabase_client import ensure_local_file
from src.supabase_client import upload_file_to_bucket

HISTORY = "data/pred_history.csv"

# ATH for 2025, OAK for 2024 and before
MLB_TEAMS = ['NYY', 'BOS', 'TOR', 'BAL', 'TBR',  # AL East
        'CHW', 'CLE', 'DET', 'KCR', 'MIN',  # AL Central
        'HOU', 'LAA', 'ATH', 'SEA', 'TEX',  # AL West
        'ATL', 'MIA', 'NYM', 'PHI', 'WSN',  # NL East
        'CHC', 'CIN', 'MIL', 'PIT', 'STL',  # NL Central
        'ARI', 'COL', 'LAD', 'SDP', 'SFG']  # NL West

# Retrieve the raw team schedules for a given year.
def get_teams_schedules(year: int = 2025) -> pd.DataFrame:
    raw_team_schedules = {}
    rawpath = f"data/raw/mlb_teams_schedules_{year}.csv"
    
    requests_cache.clear()

    for team in MLB_TEAMS:
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
    df = pd.merge(
        raw_df,
        boxLong_df,
        on=['Date', 'Tm', 'Opp', 'Game_Number'],
        how='left',
        suffixes=('', '_p')
    )
    
    df.dropna(subset=['Boxscore'], inplace=True)
    
    df.to_csv(rawpath, index=False)
    
    try:
        upload_file_to_bucket(rawpath, dest_path=f"raw/mlb_teams_schedules_{year}.csv")
    except Exception as exc:
        print(f"Failed to upload history CSV to Supabase storage: {exc}")
    
    return df

#
# Load and process team data for all MLB teams for a given year.
# Returns a DataFrame containing the schedules and records of all teams (Processed).
#
def load_all_teams_data(year: int) -> pd.DataFrame:
    # Load if CSV exists locally or download from Supabase storage
    rawpath = f"data/raw/mlb_teams_schedules_{year}.csv"
    newpath = f"data/processed/mlb_teams_schedules_{year}.csv"
    bucket = os.getenv("SUPABASE_BUCKET")

    if bucket:
        try:
            ensure_local_file(bucket, f"processed/mlb_teams_schedules_{year}.csv", newpath)
        except Exception as exc:
            print(f"Warning: failed to download processed schedule from Supabase: {exc}")
        try:
            ensure_local_file(bucket, f"raw/mlb_teams_schedules_{year}.csv", rawpath)
        except Exception as exc:
            print(f"Warning: failed to download raw schedule from Supabase: {exc}")

    if os.path.exists(newpath):
        print(f"Loading CSV file: {newpath}")
        return pd.read_csv(newpath)

    if os.path.exists(rawpath):
        df = pd.read_csv(rawpath)
    else:
        df = get_teams_schedules(year)

    return process_all_teams_data(year, df)

#
# Process the raw teams data one-by-one with computed features and cleaning the DataFrame.
# Adds opponent features in each row
# Returns a DataFrame containing the processed schedules and records of all teams.
#
def process_all_teams_data(year: int, df: pd.DataFrame) -> pd.DataFrame:
    feats_path = f"data/processed/mlb_teams_schedules_{year}_individual.csv"
    bucket = os.getenv("SUPABASE_BUCKET")

    if bucket:
        try:
            ensure_local_file(
                bucket,
                f"processed/mlb_teams_schedules_{year}_individual.csv",
                feats_path,
            )
        except Exception as exc:
            print(
                f"Warning: failed to download individual processed schedules from Supabase: {exc}"
            )

    if os.path.exists(feats_path):
        done = pd.read_csv(
            feats_path,
            usecols=['Tm'],
            on_bad_lines='skip',
            engine='python'
        )['Tm'].unique().tolist()
    else:
        done = []
    
    for team in MLB_TEAMS:
        if team in done:
            print(f"— Skipping {team} (already done)")
            continue

        print(f"➤ Processing {team}")
        team_df      = df[df['Tm'] == team].copy()
        processed_tm = create_features(year, team_df)

        processed_tm.to_csv(
            feats_path,
            mode   = 'a' if os.path.exists(feats_path) else 'w',
            header = not os.path.exists(feats_path),
            index  = False
        )
        print(f"✔ Finished {team}")
        
    if bucket:
        try:
            ensure_local_file(
                bucket,
                f"processed/mlb_teams_schedules_{year}_individual.csv",
                feats_path,
            )
        except Exception as exc:
            print(
                f"Warning: failed to download individual processed schedules from Supabase: {exc}"
            )
        
    all_feats = pd.read_csv(
        feats_path,
        on_bad_lines='skip',
        engine='python'
    )
    full = get_opponent_features(all_feats)

    outpath = f"data/processed/mlb_teams_schedules_{year}.csv"
    full.to_csv(outpath, index=False)
    try:
        upload_file_to_bucket(outpath, dest_path=f"processed/mlb_teams_schedules_{year}.csv")
    except Exception as exc:
        print(f"Failed to upload history CSV to Supabase storage: {exc}")
    
    return full

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

def load_team_data(team: str, year: int) -> pd.DataFrame:
    try:
        df = load_team_schedule_CSV(team, year)
    except FileNotFoundError:
        print(f"File not found for {team} in {year}. Attempting to load raw data.")
        df = load_team_schedule_raw_CSV(team, year)
        processed_df = process_team_data(year, df)
        processed_df.to_csv(f"data/processed/{team}_schedules_{year}.csv", index=False)
        return processed_df
    
    return df

def process_team_data(year: int, df: pd.DataFrame) -> pd.DataFrame:
    processed_df = create_features(year, df)

    return processed_df

#
# Load the schedule for a specific team and year from a cached CSV file.
#
def load_team_schedule_CSV(team: str, year: int) -> pd.DataFrame:
    filepath = f"data/processed/mlb_teams_schedules_{year}.csv"
    bucket = os.getenv("SUPABASE_BUCKET")
    if bucket:
        try:
            ensure_local_file(bucket, f"processed/mlb_teams_schedules_{year}.csv", filepath)
        except Exception as exc:
            print(f"Warning: failed to download processed schedule from Supabase: {exc}")
    print(f"Loading cached file: {filepath}")
    df = pd.read_csv(filepath)
    df = df[df['Tm'] == team]
    df.reset_index(drop=True, inplace=True)
    return df
        
#
# Load the schedule for a specific team and year from a cached CSV file. From raw data.
#
def load_team_schedule_raw_CSV(team: str, year: int) -> pd.DataFrame:
    filepath = f"data/raw/mlb_teams_schedules_{year}.csv"
    bucket = os.getenv("SUPABASE_BUCKET")
    if bucket:
        try:
            ensure_local_file(bucket, f"raw/mlb_teams_schedules_{year}.csv", filepath)
        except Exception as exc:
            print(f"Warning: failed to download raw schedule from Supabase: {exc}")

    if os.path.exists(filepath):
        print(f"Loading cached file: {filepath}")
        df = pd.read_csv(filepath)
        df = df[df['Tm'] == team]
        df.reset_index(drop=True, inplace=True)
        return df
    else:
        print(f"Missing processed file: {filepath}")


def logging_actual_winners(processed_df: pd.DataFrame, pred_csv: str = HISTORY):
    bucket = os.getenv("SUPABASE_BUCKET")
    if bucket:
        try:
            ensure_local_file(bucket, "pred_history.csv", pred_csv)
        except Exception as exc:
            print(f"Warning: failed to download prediction history from Supabase: {exc}")
    if not os.path.exists(pred_csv):
        print("No prediction history file found.")
        return None

    hist = pd.read_csv(pred_csv)

    # normalize dates
    for df, col in ((hist, "Date"), (processed_df, "Date")):
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df[col] = df[col].dt.date

    # get only home games from processed_df
    home_games = processed_df.loc[processed_df["Home_Away"] == 1].copy()
    home_games["Home"] = home_games["Tm"]
    home_games["Away"] = home_games["Opp"]

    # map actual winner from W/L boolean
    home_games["Actual_Winner"] = home_games.apply(
        lambda row: row["Home"] if row["W/L"] == 1 else row["Away"], axis=1
    )

    winners = home_games[["Date", "Home", "Away", "Actual_Winner"]].drop_duplicates()

    # merge into history
    merged = hist.merge(winners, on=["Date", "Home", "Away"], how="left", suffixes=("","_new"))

    # fill only missing
    if "Actual_Winner" not in merged.columns:
        merged["Actual_Winner"] = pd.NA
    fill = merged["Actual_Winner"].isna() & merged["Actual_Winner_new"].notna()
    merged.loc[fill, "Actual_Winner"] = merged.loc[fill, "Actual_Winner_new"]
    merged.drop(columns=["Actual_Winner_new"], inplace=True, errors="ignore")

    # optional correctness tracking
    if {"Pred_Winner","Actual_Winner"}.issubset(merged.columns):
        merged["correct"] = (merged["Pred_Winner"] == merged["Actual_Winner"]).astype("Int64")

    merged.to_csv(pred_csv, index=False)
    return merged

def update_season_data(year: int = 2025):
    """
    Incrementally process any games in raw_df that occur
    after the last‐processed date, appending them to your
    per‐team features file and then re‐merging opponents.
    
    raw_df must have at least columns ['Date','Tm','Opp',…]
    with Date as datetime64[ns].
    """
    raw_path = f"data/raw/mlb_teams_schedules_{year}.csv"
    feats_path = f"data/processed/mlb_teams_schedules_{year}_individual.csv"
    final_path = f"data/processed/mlb_teams_schedules_{year}.csv"
    bucket = os.getenv("SUPABASE_BUCKET")

    if bucket:
        try:
            ensure_local_file(bucket, f"raw/mlb_teams_schedules_{year}.csv", raw_path)
        except Exception as exc:
            print(f"Warning: failed to download raw schedule from Supabase: {exc}")
        try:
            ensure_local_file(
                bucket,
                f"processed/mlb_teams_schedules_{year}_individual.csv",
                feats_path,
            )
        except Exception as exc:
            print(
                f"Warning: failed to download individual processed schedules from Supabase: {exc}"
            )

    raw_df = pd.read_csv(raw_path, parse_dates=['Date'])
    
    if raw_df['Date'].dtype == object or not pd.api.types.is_datetime64_any_dtype(raw_df['Date']):
        raw_df['Date'] = pd.to_datetime(raw_df['Date'] + f" {year}", format='%A, %b %d %Y')
    
    if os.path.exists(feats_path):
        feats = pd.read_csv(feats_path, parse_dates=['Date'])
        last_date = feats['Date'].max()
        last_streak = feats.groupby('Tm')['Streak'].last().to_dict()
        last_result = feats.groupby('Tm')['W/L'].last().to_dict()
        #print (f"Last processed streak: {last_streak}, {last_result}")
    else:
        print("No existing feature file")
        return
    
    new_games = raw_df[raw_df['Date'] > last_date]
    if new_games.empty:
        print(f"No new games after {last_date.date()}; nothing to do.")
        return
        
    print(f"Found {len(new_games)} new games since {last_date.date()} → processing…")
    
    for team in MLB_TEAMS:
        team_new = new_games[(new_games['Tm'] == team)].sort_values("Date")
        if team_new.empty:
            continue
        
        print(f"  • Adding {len(team_new)} games for {team}")
        
        tm_feats = create_features(year, team_new)
        tm_feats = tm_feats.drop(columns=["Streak"], errors="ignore")
        
        history = feats[feats['Tm'] == team].sort_values("Date").tail(9)
        combo = pd.concat(
            [history[["R", "RA", "Run_Diff"]], tm_feats[["R", "RA", "Run_Diff"]]],
            ignore_index=True,
        )

        for window in [3, 5, 10]:
            r_ma = (
                combo["R"].shift(1).rolling(window, min_periods=1).mean().round(3)
            )
            ra_ma = (
                combo["RA"].shift(1).rolling(window, min_periods=1).mean().round(3)
            )
            rd_ma = (
                combo["Run_Diff"].shift(1).rolling(window, min_periods=1).mean().round(3)
            )

            r_ewma = (
                combo["R"].shift(1).ewm(span=window, adjust=False).mean().round(3)
            )
            ra_ewma = (
                combo["RA"].shift(1).ewm(span=window, adjust=False).mean().round(3)
            )
            rd_ewma = (
                combo["Run_Diff"].shift(1).ewm(span=window, adjust=False).mean().round(3)
            )

            tm_feats[f"R_MA{window}"] = r_ma.iloc[-len(tm_feats):].values
            tm_feats[f"RA_MA{window}"] = ra_ma.iloc[-len(tm_feats):].values
            tm_feats[f"RunDiff_MA{window}"] = rd_ma.iloc[-len(tm_feats):].values

            tm_feats[f"R_EWMA{window}"] = r_ewma.iloc[-len(tm_feats):].values
            tm_feats[f"RA_EWMA{window}"] = ra_ewma.iloc[-len(tm_feats):].values
            tm_feats[f"RunDiff_EWMA{window}"] = rd_ewma.iloc[-len(tm_feats):].values
        
        streak_before = []
        prev_s = last_streak.get(team, 0)
        prev_r = last_result.get(team, 0)
        #print(f"  • Last streak for {team} was {prev_s}, last result was {prev_r}")
        s = prev_s
        r = prev_r
        for wl in tm_feats['W/L'].astype(int):
            if r == 1:
                s = s + 1 if s > 0 else 1
            else:
                s = s - 1 if s < 0 else -1
            
            r = 1 if wl == 1 else 0
            streak_before.append(s)

        tm_feats['Streak'] = streak_before
        st = tm_feats.pop("Streak")
        tm_feats.insert(13, "Streak", st)
        tm_feats.to_csv(feats_path, mode='a', header=False, index=False)
    
    if bucket:
        try:
            ensure_local_file(
                bucket,
                f"processed/mlb_teams_schedules_{year}_individual.csv",
                feats_path,
            )
        except Exception as exc:
            print(
                f"Warning: failed to download individual processed schedules from Supabase: {exc}"
            )
    
    all_feats = pd.read_csv(feats_path)
    full = get_opponent_features(all_feats)
    full.to_csv(final_path, index=False)
    logging_actual_winners(full)
    print("✅ Updated processed file written to", final_path)
    try:
        upload_file_to_bucket(final_path, dest_path=f"processed/mlb_teams_schedules_{year}.csv")
    except Exception as exc:
        print(f"Failed to upload history CSV to Supabase storage: {exc}")
    try:
        upload_file_to_bucket(feats_path, dest_path=f"processed/mlb_teams_schedules_{year}_individual.csv")
    except Exception as exc:
        print(f"Failed to upload history CSV to Supabase storage: {exc}")
    
    return full