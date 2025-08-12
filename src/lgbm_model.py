import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, root_mean_squared_error, r2_score

from src.load_process import load_all_teams_data

# Recently removed:
# 'R_MA3', 'R_MA5', 'R_MA10', 
# 'RA_MA3', 'RA_MA5', 'RA_MA10',
# 'Opp_R_MA3', 'Opp_R_MA5', 'Opp_R_MA10',
# 'Opp_RA_MA3', 'Opp_RA_MA5', 'Opp_RA_MA10',
FEATURES = [
    'Home_Away', 'D/N', 'Rank', 'Streak',
    'RunDiff_MA3', 'RunDiff_MA5', 'RunDiff_MA10',
    'RunDiff_EWMA3', 'RunDiff_EWMA5', 'RunDiff_EWMA10',
    'SP_ERA', 'SP_WAR', 'SP_K9', 'SP_BB9', 
    'SP_WHIP', 'SP_IP', 'SP_HardHit%',
    'B_HR', 'B_RBI', 'B_H', 'B_wRC+', 'B_wOBA', 
    'B_SLG+', 'B_OBP+', 'B_AVG+', 'B_ISO+', 
    'B_HRFB%+', 'B_BB%+', 'B_K%+', 'B_Spd', 
    'B_EV', 'B_LA', 'B_Barrel%', 'B_HardHit%', 
    'B_Pull%+', 'B_Oppo%+', 'B_Cent%+', 'B_WPA',
    'B_pLI', 'B_Clutch', 'B_WAR', 'B_RAR',
    'B_BaseRunning', 'B_Offense', 'B_Defense',
    'B_Fielding', 'B_wBsR', 'B_Batting', 
    'B_Positional', 'B_wLeague',
    'RP_WPA', 'RP_pLI', 'RP_Clutch', 'RP_MD',
    'RP_WAR', 'RP_FIP', 'RP_ERA', 'RP_RAR',
    'Opp_Rank', 'Opp_Streak',
    'Opp_RunDiff_MA3', 'Opp_RunDiff_MA5', 
    'Opp_RunDiff_MA10', 'Opp_RunDiff_EWMA3',
    'Opp_RunDiff_EWMA5', 'Opp_RunDiff_EWMA10',
    'Opp_SP_ERA', 'Opp_SP_WAR', 'Opp_SP_K9',
    'Opp_SP_BB9', 'Opp_SP_WHIP', 'Opp_SP_IP', 'Opp_SP_HardHit%',
    'Opp_B_HR', 'Opp_B_RBI', 'Opp_B_H',
    'Opp_B_wRC+', 'Opp_B_wOBA', 'Opp_B_SLG+',
    'Opp_B_OBP+', 'Opp_B_AVG+', 'Opp_B_ISO+',
    'Opp_B_HRFB%+', 'Opp_B_BB%+', 'Opp_B_K%+',
    'Opp_B_Spd', 'Opp_B_EV', 'Opp_B_LA',
    'Opp_B_Barrel%', 'Opp_B_HardHit%', 'Opp_B_Pull%+',
    'Opp_B_Oppo%+', 'Opp_B_Cent%+', 'Opp_B_WPA',
    'Opp_B_pLI', 'Opp_B_Clutch', 'Opp_B_WAR',
    'Opp_B_RAR', 'Opp_B_BaseRunning', 'Opp_B_Offense',
    'Opp_B_Defense', 'Opp_B_Fielding', 'Opp_B_wBsR',
    'Opp_B_Batting', 'Opp_B_Positional', 'Opp_B_wLeague',
    'Opp_RP_WPA', 'Opp_RP_pLI', 'Opp_RP_Clutch',
    'Opp_RP_MD', 'Opp_RP_WAR', 'Opp_RP_FIP',
    'Opp_RP_ERA', 'Opp_RP_RAR',
]

os.makedirs("models", exist_ok=True)

def train_run_diff_model(df: pd.DataFrame) -> lgb.Booster:
    """
    Train a LightGBM regression model to predict the run differential (R - RA).
    """
    # 1) Load processed features
    df['Run_Diff'] = df['R'] - df['RA']

    # 2) Drop missing
    df = df.dropna(subset=FEATURES + ['Run_Diff'])
    X = df[FEATURES]
    y = df['Run_Diff']

    # 3) Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4) Create LightGBM datasets
    dtrain = lgb.Dataset(X_train, label=y_train)
    dvalid = lgb.Dataset(X_test, label=y_test, reference=dtrain)

    # 5) Model parameters
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'learning_rate': 0.01,
        'num_leaves': 31,
        'min_data_in_leaf': 20,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'verbose': -1
    }

    # 6) Train with early stopping
    model = lgb.train(
        params,
        dtrain,
        num_boost_round=2000,
        valid_sets=[dtrain, dvalid],
        callbacks=[
            lgb.callback.early_stopping(stopping_rounds=50),
            lgb.callback.log_evaluation(period=100)
        ]
    )

    # 7) Evaluate
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)
    print(f"RunDiff RMSE: {rmse:.3f}, R2: {r2:.3f}")

    # 8) Save the model
    model.save_model(f"models/run_diff_lgbm.txt")
    return model


def train_run_total_model(df: pd.DataFrame) -> lgb.Booster:
    """
    Train a LightGBM regression model to predict the total runs (R + RA).
    """
    # 1) Load processed features
    df['Run_Total'] = df['R'] + df['RA']

    # 2) Drop missing
    df = df.dropna(subset=FEATURES + ['Run_Total'])
    X = df[FEATURES]
    y = df['Run_Total']

    # 3) Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4) Create LightGBM datasets
    dtrain = lgb.Dataset(X_train, label=y_train)
    dvalid = lgb.Dataset(X_test, label=y_test, reference=dtrain)

    # 5) Model parameters (same as RunDiff)
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'learning_rate': 0.01,
        'num_leaves': 31,
        'min_data_in_leaf': 20,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'verbose': -1
    }

    # 6) Train with early stopping
    model = lgb.train(
        params,
        dtrain,
        num_boost_round=2000,
        valid_sets=[dtrain, dvalid],
        callbacks=[
            lgb.callback.early_stopping(stopping_rounds=50),
            lgb.callback.log_evaluation(period=100)
        ]
    )

    # 7) Evaluate
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)
    print(f"RunTotal RMSE: {rmse:.3f}, R2: {r2:.3f}")

    # 8) Save the model
    model.save_model(f"models/run_total_lgbm.txt")
    return model

    
def train_lgbm_classification_model(df: pd.DataFrame) -> lgb.Booster:    
    target = 'W/L'
    
    df = df.dropna(subset=FEATURES + [target])
    X = df[FEATURES]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    params = {
        'objective': 'binary',
        'metric':    ['binary_logloss','auc'],
        'boosting_type':  'gbdt',
        'learning_rate':  0.01,
        'num_leaves':     31,
        'max_depth':      6,
        'min_data_in_leaf': 20,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq':      5,
        'lambda_l1':         0.1,
        'lambda_l2':         0.1,
        'verbose':          -1
    }
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=2000,
        valid_sets=[train_data, valid_data],
        callbacks=[
            # stop if validation loss hasn’t improved in 50 rounds
            lgb.callback.early_stopping(stopping_rounds=50),
            # print eval results every 100 rounds
            lgb.callback.log_evaluation(period=100)
        ],
    )
    
    y_pred = model.predict(X_test)
    y_pred_binary = (y_pred >= 0.5).astype(int)
    
    accuracy = accuracy_score(y_test, y_pred_binary)
    roc_auc = roc_auc_score(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.3f}")
    print(f"ROC AUC: {roc_auc:.3f}")
    print(classification_report(y_test, y_pred_binary))
    
    print("Feature importances:")
    feature_importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importance()
    }).sort_values(by='Importance', ascending=False)
    
    print(feature_importances.to_string())
    
    model.save_model("models/wl_lgbm.txt")
    
    return model

def load_reg_model(model_path: str) -> lgb.Booster:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Regression model file not found: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    return model

def load_clf_model(model_path: str) -> lgb.Booster:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Classification model file not found: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    return model

def create_models():
    #schedules_2025 = load_all_teams_data(2025)
    df = load_all_teams_data(2024)
    #df = pd.concat([schedules_2024, schedules_2025], ignore_index=True)
    #print(df.columns)
    train_lgbm_classification_model(df)
    train_run_diff_model(df)
    train_run_total_model(df)