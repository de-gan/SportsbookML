import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, root_mean_squared_error, r2_score

FEATURES = [
    'Home_Away', 'D/N', 'Rank', 'Streak',
    'SP_ERA', 'SP_WAR', 'SP_K9', 
    'SP_BB9', 'SP_WHIP', 'SP_IP', 'SP_HardHit%',
    'Avg_R_MA3', 'Avg_R_MA5', 'Avg_R_MA10',
    'Avg_Ra_MA3', 'Avg_Ra_MA5', 'Avg_Ra_MA10',
    'RunDiff_MA3', 'RunDiff_MA5', 'RunDiff_MA10',
    'Opp_Rank', 'Opp_Streak',
    'Opp_SP_ERA', 'Opp_SP_WAR', 'Opp_SP_K9', 'Opp_SP_BB9',
    'Opp_SP_WHIP', 'Opp_SP_IP', 'Opp_SP_HardHit%',
    'Opp_Avg_R_MA3', 'Opp_Avg_R_MA5', 'Opp_Avg_R_MA10',
    'Opp_Avg_Ra_MA3', 'Opp_Avg_Ra_MA5', 'Opp_Avg_Ra_MA10',
    'Opp_RunDiff_MA3', 'Opp_RunDiff_MA5', 'Opp_RunDiff_MA10',
    'HR', 'RBI', 'H', 'wRC+', 'wOBA', 'SLG+', 'OBP+', 'AVG+',
    'ISO+', 'HR/FB%+', 'BB%+', 'K%+', 'Spd', 'EV', 'LA',
    'Barrel%', 'HardHit%', 'Pull%+', 'Oppo%+', 'Cent%+',
    'Opp_HR', 'Opp_RBI', 'Opp_H', 'Opp_wRC+', 'Opp_wOBA', 'Opp_SLG+', 'Opp_OBP+', 'Opp_AVG+',
    'Opp_ISO+', 'Opp_HR/FB%+', 'Opp_BB%+', 'Opp_K%+', 'Opp_Spd', 'Opp_EV', 'Opp_LA',
    'Opp_Barrel%', 'Opp_HardHit%', 'Opp_Pull%+', 'Opp_Oppo%+', 'Opp_Cent%+',
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
    
    print(feature_importances)
    
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