import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

from pybaseball import schedule_and_record, team_batting, team_pitching

from src.feature_engineering import create_features

schedule = schedule_and_record(2023, 'NYY')
schedule_nyy = create_features(schedule)

batting_2023 = team_batting(2024)
pitching_2023 = team_pitching(2024)
batting_nyy = batting_2023[batting_2023['Team'] == 'NYY']
pitching_nyy = pitching_2023[pitching_2023['Team'] == 'NYY']

print(schedule_nyy.head())

#df = schedule_nyy.drop(columns=['Date', 'Tm', 'W-L', 'GB', 'Win', 'Loss'])
#print(df.head())
#correlation_matrix = df.corr()
#sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm")
#plt.show()