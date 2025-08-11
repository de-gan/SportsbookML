import warnings
import pandas as pd
from urllib3.exceptions import NotOpenSSLWarning
import requests, io

from src.load_process import load_all_teams_data, process_all_teams_data

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

#load_all_teams_data(2024)

path = "data/processed/mlb_teams_schedules_2024_individual.csv"
#df = pd.read_csv(path)
#df = df.sort_values(["Tm", "Date"]).reset_index(drop=True)
rolling_windows=[3, 5, 10]

'''for window in rolling_windows:
    df[f"Avg_R_MA{window}"] = (
        df
        .groupby("Tm")["R"]
        .transform(lambda x: x.shift(1)
            .rolling(window, min_periods=1)
            .mean()
        )
        .round(3)
    )
    df[f"Avg_Ra_MA{window}"] = (
        df
        .groupby("Tm")["RA"]
        .transform(lambda x: x.shift(1)
            .rolling(window, min_periods=1)
            .mean()
        )
        .round(3)
    )
    df[f"RunDiff_MA{window}"] = (
        df
        .groupby("Tm")["Run_Diff"]
        .transform(lambda x: x.shift(1)
            .rolling(window, min_periods=1)
            .mean()
        )
        .round(3)
    )

df.to_csv(path, index=False)'''

load_all_teams_data(2023)
