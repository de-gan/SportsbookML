import argparse
import requests
import pandas as pd
import re
import time
from datetime import date, datetime
from bs4 import BeautifulSoup, Comment

from src.feature_engineering import full_to_abbrev
from src.pitchers import get_player_stats
from src.lgbm_model import load_clf_model, FEATURES
from src.fangraphs_batting import fg_team_snapshot

#requests_cache.clear()

def load_processed_data(year: int) -> pd.DataFrame:
    path = f"data/processed/mlb_teams_schedules_{year}.csv"
    df = pd.read_csv(path, dtype={'Tm':str,'Opp':str}, parse_dates=['Date'])
    return df

def get_todays_slate(target: date = date.today()) -> pd.DataFrame:
    url  = f"https://www.baseball-reference.com/leagues/majors/{target.year}-schedule.shtml"
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    today_h3 = soup.find("span", id="today").find_parent("h3")
    
    rows = []
    for sib in today_h3.next_siblings:
        if getattr(sib, "name", None) == "h3":
            break
        if getattr(sib, "name", None) == "p" and "game" in sib.get("class", []):
            team_links = sib.find_all("a")
            if len(team_links) < 3:
                continue
            away_name = team_links[0].get_text(strip=True)
            home_name = team_links[1].get_text(strip=True)

            # find the <em><a>Preview</a></em>
            em = sib.find("em")
            if not em or not em.a:
                continue
            href = em.a["href"]
            full_url = requests.compat.urljoin(url, href)
            
            dt = sib.find("span")
            if not dt or not dt.get_text(strip=True):
                continue
            dt = dt.get_text(strip=True)
            dt = re.sub(r'\s+', '', dt).lower()
            dt = datetime.strptime(dt, "%I:%M%p") 
            if dt.hour >= 19:
                 dn = 1  # Night game
            else:
                 dn = 0

            rows.append({
                "Date": target,
                "D/N": dn,
                "Opp": full_to_abbrev.get(away_name),
                "Tm": full_to_abbrev.get(home_name),
                "url": full_url
            })
            
    slate = pd.DataFrame(rows, columns=["Date", "D/N", "Tm", "Opp", "url"])
    if slate.empty:
        print(f"No games found for {target.isoformat()}")
    return slate

def get_slate_for_date(target: date) -> pd.DataFrame:
    """
    Get the MLB slate for a given date, either from today's games or from
    the processed data if the date is in the past.
    """
    today = date.today()
    
    if target < today:
        df = load_processed_data(target.year)
        mask = ((df["Date"].dt.date == target) &
                (df["Home_Away"] == 1))  # Home games only
        slate = df.loc[mask, ["Tm", "Opp", "Date"]].reset_index(drop=True)
        if slate.empty:
            print(f"No games found on {target}")
        return slate
    
    return get_todays_slate(target)

def get_starting_pitcher_from_preview(url: str, team_name: str) -> dict:
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    heading = soup.find("div", id=f"sp_{team_name}_sh")
    if not heading:
        raise RuntimeError(f"Couldn’t find sp_{team_name}_sh on {team_name}")

    h2 = heading.find("h2")
    if not h2 or not h2.a:
        raise RuntimeError(f"Malformed H2 in sp_{team_name}_sh on {team_name}")
    
    raw_name = h2.a.get_text(strip=True)    
    name = raw_name.encode("latin‑1").decode("utf‑8")
    
    comment = None
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if f'id="sp_{team_name}"' in c:
            comment = c
            break
    if comment is None:
        debut = h2.strong.get_text(strip=True)
        if not debut:
            raise RuntimeError(f"Couldn’t find commented table sp_{team_name} in preview and not MLB debut")
        print(f"Warning: No commented table sp_{team_name} in preview, using MLB debut {debut} for {name}")
        return {"name": name, "ERA": float("nan")}

    inner = BeautifulSoup(comment, "html.parser")

    table = inner.find("table", id=f"sp_{team_name}")
    if not table or not table.tbody:
        raise RuntimeError(f"No <tbody> in table sp_{team_name}")

    first_row = table.tbody.find("tr")
    era_td = first_row.find("td", {"data-stat": "earned_run_avg"})
    era_text = era_td.get_text(strip=True) if era_td else ""
    try:
        era = float(era_text)
    except:
        era = float("nan")

    return {"name": name, "ERA": era}

def build_features_for_event(
    event: dict,
    raw_schedule_df: pd.DataFrame,
    snapshot_cache: dict,
    year: int
) -> pd.Series:
    """
    event: { 'Tm': 'NYY', 'Opp': 'BOS', 'url': '…', 'D/N': 1 }
    raw_schedule_df: your raw "mlb_teams_schedules_YYYY.csv" parsed with Date datetime64
    snapshot_cache: pre-built dict mapping 'YYYY-MM-DD' → fangraphs snapshot df
    year: the season year, e.g. 2025
    """
    tm, opp = event['Tm'], event['Opp']
    target = event['Date']  # a pd.Timestamp or python date
    
    if raw_schedule_df['Date'].dtype == object or not pd.api.types.is_datetime64_any_dtype(raw_schedule_df['Date']):
        raw_schedule_df['Date'] = raw_schedule_df['Date'].str.replace(r'\s+\(\d\)', '', regex=True)
        raw_schedule_df['Date'] = pd.to_datetime(raw_schedule_df['Date'].astype(str) + f' {year}', format='%A, %b %d %Y')
    
    # 1) find that team’s last raw boxscore row (strictly before game date)
    def last_raw_features(team_code):
        df = raw_schedule_df.copy()
        
        # now filter by the date‐only comparison
        mask = (
            (df['Tm'] == team_code)
            & (df['Date'].dt.date < target)
        )
        hist = df.loc[mask].sort_values('Date')
        if hist.empty:
            raise ValueError(f"No prior row for {team_code} before {target}")
        
        R   = hist['R']
        RA  = hist['RA']
        Diff = R - RA
        last = hist.iloc[-1]
        
        last = hist.iloc[-1]
        return {
            'Rank':          last['Rank'],
            'Streak':        last['Streak'],
            'Avg_R_MA3':         R.tail(3).mean().round(3),
            'Avg_R_MA5':         R.tail(5).mean().round(3),
            'Avg_R_MA10':        R.tail(10).mean().round(3),
            'Avg_Ra_MA3':        RA.tail(3).mean().round(3),
            'Avg_Ra_MA5':        RA.tail(5).mean().round(3),
            'Avg_Ra_MA10':       RA.tail(10).mean().round(3),
            'RunDiff_MA3':   Diff.tail(3).mean().round(3),
            'RunDiff_MA5':   Diff.tail(5).mean().round(3),
            'RunDiff_MA10':  Diff.tail(10).mean().round(3),
            'W/L':           last['W/L'],
            'Streak':        last['Streak'],
        }
    
    home_raw = last_raw_features(tm)
    opp_raw  = last_raw_features(opp)
    
    # 2) SP preview + statcast stats
    sp_tm  = get_starting_pitcher_from_preview(event['url'], tm)
    #print(f"Found SP for {tm}: {sp_tm['name']} with ERA {sp_tm['ERA']}")
    time.sleep(0.5)
    sp_opp = get_starting_pitcher_from_preview(event['url'], opp)
    #print(f"Found SP for {opp}: {sp_opp['name']} with ERA {sp_opp['ERA']}")
    sp_tm_stats  = get_player_stats(sp_tm['name'], target, year)
    sp_opp_stats = get_player_stats(sp_opp['name'], target, year)
    # override ERA with the preview ERA
    sp_tm_stats['SP_ERA']   = sp_tm['ERA']
    sp_opp_stats['SP_ERA']  = sp_opp['ERA']
    
    #print(f"SP stats for {tm}: {sp_tm_stats}")
    #print(f"SP stats for {opp}: {sp_opp_stats}")
    
    # 3) Fangraphs batting—use "yesterday" as_of
    as_of = (pd.to_datetime(target) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    if as_of not in snapshot_cache:
        snapshot_cache[as_of] = fg_team_snapshot(year, as_of)
    snap = snapshot_cache[as_of]
    
    def bat_stats(team_code, prefix):
        sl = snap[snap['Tm']==team_code]
        if sl.empty:
            # fill all batting cols with NaN
            return { f"{prefix}_{c}": float('nan') 
                     for c in sl.columns if c!='Tm' }
        row = sl.iloc[0]
        return { f"{prefix}{c}": row[c] for c in row.index if c!='Tm' }
    
    tm_bat  = bat_stats(tm,  '')
    opp_bat = bat_stats(opp, 'Opp_')
    
    # 4) assemble into a single dict
    data = {}
    
    # Handle streak with W/L
    if home_raw['W/L'] == 'W-wo' or home_raw['W/L'] == 'W':
        h_win = True
    else:
        h_win = False
        
    h_streak = home_raw['Streak']
    if h_streak > 0:
        h_streak += 1 if h_win else -1
    elif h_streak < 0:
        h_streak -= 1 if h_win else -1
    else:
        h_streak = 1 if h_win else -1
        
    if opp_raw['W/L'] == 'W-wo' or opp_raw['W/L'] == 'W':
        o_win = True
    else:
        o_win = False
        
    o_streak = home_raw['Streak']
    if o_streak > 0:
        o_streak += 1 if o_win else -1
    elif o_streak < 0:
        o_streak -= 1 if o_win else -1
    else:
        o_streak = 1 if o_win else -1
    
    data['Home_Away'] = 1
    data['Streak']        = h_streak
    data['Opp_Streak']        = o_streak

    base = [
        "Rank",
        "Avg_R_MA3", "Avg_R_MA5", "Avg_R_MA10",
        "Avg_Ra_MA3", "Avg_Ra_MA5", "Avg_Ra_MA10",
        "RunDiff_MA3", "RunDiff_MA5", "RunDiff_MA10"
    ]
    
    for feat in base:
        # home side
        data[feat] = home_raw[feat]
        # away/opponent side: just prefix with "Opp_"
        data["Opp_" + feat] = opp_raw[feat]
    
    # SP fields
    for k,v in sp_tm_stats.items():
        data[k] = v
    for k,v in sp_opp_stats.items():
        data[f"Opp_{k}"] = v
    
    # batting
    data.update(tm_bat)
    data.update(opp_bat)
    
    # D/N
    data['D/N'] = event['D/N']
    
    # now turn into a Series in your FEATURES order
    return pd.Series({ f: data.get(f, float('nan')) for f in FEATURES })


def predict_for_date(date_str: str):
    try:
        target = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise SystemExit(f"Error: date must be YYYY-MM-DD, got '{date_str}'")

    raw = pd.read_csv(f"data/raw/mlb_teams_schedules_{target.year}.csv",
                  parse_dates=['Date'])

    snap_cache = {}

    slate = get_slate_for_date(target)
    records = slate.to_dict('records')
    
    if not records:
        print(f"No matchups found for {target}")
        return
    
    print(f"Found {len(records)} matchups for {target}...")
    if target < date.today():
        print("Using historical data for predictions")
    else:
        print("Using today's data for predictions")
    
    print(slate[["Tm", "Opp", "Date", "D/N"]])

    proc = load_processed_data(target.year)
    if 'Date' not in proc.columns:
        raise RuntimeError("Processed data missing Date column")

    feats = []
    for ev in records:
        feats.append(build_features_for_event(ev, raw, snap_cache, target.year))
    X = pd.DataFrame(feats, columns=FEATURES)
    X.to_csv("data/processed/today.csv", index=False)
    print(X)

    clf = load_clf_model("models/wl_lgbm.txt")
    probs = clf.predict(X)

    for ev, p in zip(records, probs):
        home, away = ev["Tm"], ev["Opp"]
        # if p>=0.5 home is the bet, else away
        winner   = home if p >= 0.5 else away
        win_prob = p    if p >= 0.5 else 1 - p

        # only show the “favorite”
        if win_prob > 0.5:
            print(f"{home} vs {away} → {winner} win probability = {win_prob:.1%}")


def main():
    parser = argparse.ArgumentParser(
        description="Predict MLB outcomes for games on a given date using processed features and BBRef scraping."
    )
    parser.add_argument(
        'date', nargs='?', default=date.today().isoformat(),
        help="Date to predict in YYYY-MM-DD format (defaults to today)"
    )
    args = parser.parse_args()
    predict_for_date(args.date)

if __name__ == '__main__':
    main()