import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, root_mean_squared_error, r2_score

from src.load_process import load_all_teams_data
from src.s3_utils import upload_model

# Recently removed:
# 'R_MA3', 'R_MA5', 'R_MA10', 
# 'RA_MA3', 'RA_MA5', 'RA_MA10',
# 'Opp_R_MA3', 'Opp_R_MA5', 'Opp_R_MA10',
# 'Opp_RA_MA3', 'Opp_RA_MA5', 'Opp_RA_MA10',
FEATURES = [
    'Home_Away', 'Rank', 'Streak', 'D/N',
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

def _prepare_features(df: pd.DataFrame, feature_list: list) -> pd.DataFrame:
    """Return numeric feature matrix with constant columns removed."""
    X = df[feature_list]
    constant_cols = [col for col in X.columns if X[col].nunique() <= 1]
    if constant_cols:
        print(f"Removing constant columns: {constant_cols}")
        X = X.drop(columns=constant_cols)
    return X

os.makedirs("models", exist_ok=True)

def train_run_diff_model(df: pd.DataFrame) -> lgb.Booster:
    """
    Train a LightGBM regression model to predict the run differential (R - RA).
    """
    # 1) Load processed features
    df['Run_Diff'] = df['R'] - df['RA']

    # 2) Drop missing
    df = df.dropna(subset=FEATURES + ['Run_Diff'])
    X = _prepare_features(df, FEATURES)
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
    model_path = "models/run_diff_lgbm.txt"
    model.save_model(model_path)
    upload_model(model_path)
    return model


def train_run_total_model(df: pd.DataFrame) -> lgb.Booster:
    """
    Train a LightGBM regression model to predict the total runs (R + RA).
    """
    # 1) Load processed features
    df['Run_Total'] = df['R'] + df['RA']

    # 2) Drop missing
    df = df.dropna(subset=FEATURES + ['Run_Total'])
    X = _prepare_features(df, FEATURES)
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
    model_path = "models/run_total_lgbm.txt"
    model.save_model(model_path)
    upload_model(model_path)
    return model

    
def train_lgbm_classification_model(df: pd.DataFrame) -> lgb.Booster:
    """Train a LightGBM classifier with cross-validation and hyperparameter search."""

    target = 'W/L'

    # Drop rows with missing values in features or target
    df = df.dropna(subset=FEATURES + [target])
    X = _prepare_features(df, FEATURES)
    y = df[target]

    # Split once to hold out a final test set
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # Base model for hyperparameter tuning
    base_clf = lgb.LGBMClassifier(
        objective='binary',
        boosting_type='gbdt',
        n_estimators=1000,
        class_weight='balanced',
        n_jobs=-1,
        random_state=42,
    )

    param_dist = {
        'num_leaves': [31, 63, 127],
        'max_depth': [-1, 6, 10],
        'learning_rate': [0.01, 0.05, 0.1],
        'subsample': [0.7, 0.8, 1.0],
        'colsample_bytree': [0.7, 0.8, 1.0],
        'reg_alpha': [0.0, 0.1, 0.5],
        'reg_lambda': [0.0, 0.1, 0.5],
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    search = RandomizedSearchCV(
        estimator=base_clf,
        param_distributions=param_dist,
        n_iter=25,
        scoring='roc_auc',
        cv=cv,
        n_jobs=-1,
        verbose=1,
        random_state=42,
    )

    # Hyperparameter tuning using cross-validation
    search.fit(X_train_full, y_train_full)

    best_params = search.best_params_
    print(f"Best params: {best_params}")

    # Further split training data for early stopping
    X_train, X_valid, y_train, y_valid = train_test_split(
        X_train_full,
        y_train_full,
        test_size=0.2,
        random_state=42,
        stratify=y_train_full,
    )

    best_clf = lgb.LGBMClassifier(
        objective='binary',
        boosting_type='gbdt',
        class_weight='balanced',
        n_jobs=-1,
        random_state=42,
        n_estimators=1000,
        **best_params,
    )

    best_clf.fit(
        X_train,
        y_train,
        eval_set=[(X_valid, y_valid)],
        eval_metric='auc',
        callbacks=[
            lgb.early_stopping(50),
            lgb.log_evaluation(100),
        ],
    )

    y_pred_proba = best_clf.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)

    print(f"Accuracy: {accuracy:.3f}")
    print(f"ROC AUC: {roc_auc:.3f}")
    print(classification_report(y_test, y_pred))

    print("Feature importances:")
    feature_importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': best_clf.booster_.feature_importance(),
    }).sort_values(by='Importance', ascending=False)

    print(feature_importances.to_string())

    # Save the underlying Booster model
    model_path = "models/wl_lgbm.txt"
    best_clf.booster_.save_model(model_path)
    upload_model(model_path)

    return best_clf.booster_

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
    schedules_2025 = load_all_teams_data(2025)
    schedules_2024 = load_all_teams_data(2024)
    schedules_2023 = load_all_teams_data(2023)
    df = pd.concat([schedules_2023, schedules_2024, schedules_2025], ignore_index=True)
    #print(df.columns)
    train_lgbm_classification_model(df)
    train_run_diff_model(df)
    train_run_total_model(df)
