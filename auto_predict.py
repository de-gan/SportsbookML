import argparse
import requests
import pandas as pd
import re
import time
from datetime import date, datetime
from bs4 import BeautifulSoup, Comment
import requests_cache

from src.feature_engineering import full_to_abbrev
from src.pitchers import get_player_stats
from src.lgbm_model import load_clf_model, FEATURES

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

def get_last_game_features_for_team(processed_df: pd.DataFrame, team: str, as_of: date) -> pd.Series:
    """
    Return the feature row for the last game team played strictly before as_of.
    Assumes processed_df has Date (datetime64[ns]).
    """
    as_ts = pd.to_datetime(as_of)
    mask = (
        (processed_df['Tm'] == team) &
        (processed_df['Date'] < as_ts)
    )
    subset = processed_df.loc[mask].sort_values('Date')
    if subset.empty:
        raise ValueError(f"No prior games for {team} before {as_of}")
    return subset.iloc[-1]

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

def build_features_for_event(event: dict, processed_df: pd.DataFrame, target: date) -> pd.Series:
    """
    Given one event dict with keys 'Tm','Opp','url', builds the FEATURES row.
    If target < today, pulls directly from processed_df; else scrapes SPs.
    """
    today = date.today()
    tm, opp = event['Tm'], event['Opp']
    # historical
    if target < today:
        row = processed_df[
            (processed_df['Date'].dt.date == target) &
            (processed_df['Tm'] == tm)
        ]
        if row.empty:
            raise ValueError(f"Processed features missing for {tm} on {target}")
        return row.iloc[0][FEATURES]

    # today’s games
    url = event['url']
    tm_sp = get_starting_pitcher_from_preview(url, tm)
    opp_sp = get_starting_pitcher_from_preview(url, opp)
    tm_sp_data = get_player_stats(tm_sp["name"], target, target.year)
    tm_sp_data['SP_ERA'] = tm_sp["ERA"]
    opp_sp_data = get_player_stats(opp_sp["name"], target, target.year)
    opp_sp_data['Opp_SP_ERA'] = opp_sp["ERA"]
    tm_feats = get_last_game_features_for_team(processed_df, tm, target)
    opp_feats = get_last_game_features_for_team(processed_df, opp, target)
    data = {}
    
    for f in FEATURES:
        if f.startswith('SP_'):
            data[f] = tm_sp_data.get(f, float('nan'))
        elif f.startswith('Opp_SP_'):
            data[f] = opp_sp_data.get(f, float('nan'))
        elif f.startswith('Opp_'):
            data[f] = opp_feats[f]
        else:
            data[f] = tm_feats[f]
    
    data['D/N'] = event['D/N']
    
    return pd.Series(data)[FEATURES]


def predict_for_date(date_str: str):
    try:
        target = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        raise SystemExit(f"Error: date must be YYYY-MM-DD, got '{date_str}'")

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
        feats.append(build_features_for_event(ev, proc, target))
    X = pd.DataFrame(feats, columns=FEATURES)
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