import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, root_mean_squared_error, r2_score

def train_lgbm_regression_model(year: int, df: pd.DataFrame) -> lgb.Booster:
    df = pd.read_csv(f"data/processed/mlb_teams_schedules_{year}_processed.csv")
    
    features = [
        'Home_Away', 'Rank', 'cLI', 'Streak',
        'RunDiff_MA3', 'RunDiff_MA5', 'RunDiff_MA10',
        'Opp_Rank', 'Opp_cLI', 'Opp_Streak',
        'Opp_RunDiff_MA3', 'Opp_RunDiff_MA5', 'Opp_RunDiff_MA10'
    ]
    target = 'Run_Diff'
    
    df = df.dropna(subset=features + [target])
    X = df[features]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'verbose': -1
    }
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, valid_data],
    )
    
    y_pred = model.predict(X_test)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    #print(y_test[:10], y_pred[:10])
    print(f"RMSE: {rmse:.3f}")
    print(f"R^2: {r2:.3f}")
    
    print("Feature importances:")
    feature_importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importance()
    }).sort_values(by='Importance', ascending=False)
    print(feature_importances)
    
    return model
    
def train_lgbm_classification_model(year: int, df: pd.DataFrame) -> lgb.Booster:
    df = pd.read_csv(f"data/processed/mlb_teams_schedules_{year}_processed.csv")
    
    features = [
        'Home_Away', 'Rank', 'cLI', 'Streak',
        'RunDiff_MA3', 'RunDiff_MA5', 'RunDiff_MA10',
        'Opp_Rank', 'Opp_cLI', 'Opp_Streak',
        'Opp_RunDiff_MA3', 'Opp_RunDiff_MA5', 'Opp_RunDiff_MA10'
    ]
    target = 'W/L' # 1 = win, 0 = loss
    
    df = df.dropna(subset=features + [target])
    X = df[features]
    y = df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    train_data = lgb.Dataset(X_train, label=y_train)
    valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
    
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type': 'gbdt',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'verbose': -1
    }
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=500,
        valid_sets=[train_data, valid_data],
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
    
    return model