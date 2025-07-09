from sklearn.preprocessing import LabelEncoder
import pandas as pd

# Team Schedule and Record
def create_features(df: pd.DataFrame, rolling_windows=[3, 5, 10]) -> pd.DataFrame:
    # Drop unwanted columns
    df.drop(columns=['Time', 'Attendance', 'Inn', 'Orig. Scheduled', 'Save', 'GB'], inplace=True)
    
    df['Run_Diff'] = df['R'] - df['RA']
    
    df['Date'] = df['Date'].str.replace(r'\s+\(\d\)', '', regex=True)
    df['Date'] = pd.to_datetime(df['Date'] + ' 2024', format='%A, %b %d %Y')
    df.insert(0, 'Month', df['Date'].dt.month)
    df.insert(1, 'DayofWeek', df['Date'].dt.dayofweek)
    #df.insert (2, 'Year', df['Date'].dt.year)

    df.pop('Date')
    
    df['cLI'] = pd.to_numeric(df['cLI'], errors='coerce')
    df['cLI'].fillna(0, inplace=True)
    
    # Rolling stats over various windows
    for window in rolling_windows:
        df[f'Avg_R_MA{window}'] = df['R'].rolling(window=window, min_periods=1).mean().round(3)
        df[f'Avg_Ra_MA{window}'] = df['RA'].rolling(window=window, min_periods=1).mean().round(3)
        #df[f'WinRate_MA{window}'] = df['W/L'].rolling(window=window, min_periods=1).mean()
        df[f'RunDiff_MA{window}'] = df['Run_Diff'].rolling(window=window, min_periods=1).mean().round(3)
    
        # Encode categorical variables
    le = LabelEncoder()
    df['Home_Away'] = le.fit_transform(df['Home_Away']) # Home = 1, Away = 0
    df['W/L'] = df['W/L'].replace({'W-wo': 'W', 'L-wo': 'L'})
    df['W/L'] = le.fit_transform(df['W/L']) # W = 2, L = 0
    df['D/N'] = le.fit_transform(df['D/N']) # Day = 0, Night = 1
    
    return df
