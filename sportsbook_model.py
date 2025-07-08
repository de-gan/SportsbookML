import warnings
from urllib3.exceptions import NotOpenSSLWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

import pandas as pd
from src.load_process import load_team_schedule

print(load_team_schedule('LAA', 2023).head())

#df = schedule_nyy.drop(columns=['Date', 'Tm', 'W-L', 'GB', 'Win', 'Loss'])
#print(df.head())
#correlation_matrix = df.corr()
#sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm")
#plt.show()