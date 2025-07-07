import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from pybaseball import schedule_and_record, team_batting, team_pitching

batting_2023 = team_batting(2024)
pitching_2023 = team_pitching(2024)
batting_nyy = batting_2023[batting_2023['Team'] == 'NYY']
pitching_nyy = pitching_2023[pitching_2023['Team'] == 'NYY']

# Team Schedule and Record
def get_team_schedule_and_record(team):
    schedule = schedule_and_record(2023, team)
    schedule.drop(columns=['Time', 'Attendance', 'Inn', 'Orig. Scheduled', 'Save', 'GB'], inplace=True)
    le = LabelEncoder()
    schedule['Home_Away'] = le.fit_transform(schedule['Home_Away'])
    schedule['W/L'] = le.fit_transform(schedule['W/L'])
    schedule['D/N'] = le.fit_transform(schedule['D/N'])
    schedule['WinDiff'] = schedule['R'] - schedule['RA']
    return schedule

schedule_nyy = get_team_schedule_and_record('NYY')
#print(batting_2023)
print(schedule_nyy.head())

#df = schedule_nyy.drop(columns=['Date', 'Tm', 'W-L', 'GB', 'Win', 'Loss'])
#print(df.head())
#correlation_matrix = df.corr()
#sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm")
#plt.show()

