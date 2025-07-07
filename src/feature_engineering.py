from sklearn.preprocessing import LabelEncoder
import pandas as pd

# Team Schedule and Record
def create_features(df: pd.DataFrame, rolling_windows=[3, 5, 10]) -> pd.DataFrame:
    # Drop unwanted columns
    df.drop(columns=['Time', 'Attendance', 'Inn', 'Orig. Scheduled', 'Save', 'GB'], inplace=True)
    
    df['Run_Diff'] = df['R'] - df['RA']
    
    #df['Date'] = pd.to_datetime(df['Date'])
    #df['DayOfWeek'] = df['Date'].dt.dayofweek
    #df['Month'] = df['Date'].dt.month
    
    
    # Rolling stats over various windows
    for window in rolling_windows:
        df[f'Avg_R_MA{window}'] = df['R'].rolling(window=window, min_periods=1).mean()
        df[f'Avg_Ra_MA{window}'] = df['RA'].rolling(window=window, min_periods=1).mean()
        #df[f'WinRate_MA{window}'] = df['W/L'].rolling(window=window, min_periods=1).mean()
        df[f'RunDiff_MA{window}'] = df['Run_Diff'].rolling(window=window, min_periods=1).mean()
    
        # Encode categorical variables
    le = LabelEncoder()
    df['Home_Away'] = le.fit_transform(df['Home_Away']) # Home = 1, Away = 0
    df['W/L'] = le.fit_transform(df['W/L']) # W = 2, L = 0
    df['D/N'] = le.fit_transform(df['D/N']) # Day = 0, Night = 1
    
    return df