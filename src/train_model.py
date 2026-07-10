"""
Reproduces the winning experiment from Task 1 (Exp1: Linear Regression on
Lag_1, Lag_7, Rolling_mean_7) and persists the model + feature list so that
Task 4's prediction script can load it without re-running the whole notebook.

Run from repo root:
    python src/train_model.py
"""
import os
import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression

RAW_PATH = os.path.join("data", "raw", "aapl.csv")
MODEL_DIR = "models"
FEATURES = ["Lag_1", "Lag_7", "Rolling_mean_7"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.capitalize()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df[df["Name"] == "AAPL"].sort_values("Date").reset_index(drop=True)

    df["Lag_1"] = df["Close"].shift(1)
    df["Lag_7"] = df["Close"].shift(7)
    df["Rolling_mean_7"] = df["Close"].rolling(window=7).mean()
    return df


def main():
    df = pd.read_csv(RAW_PATH)
    df = build_features(df)
    df_model = df.dropna(subset=FEATURES + ["Close"]).reset_index(drop=True)

    X = df_model[FEATURES]
    y = df_model["Close"]

    split_idx = int(len(df_model) * 0.8)
    X_train, y_train = X.iloc[:split_idx], y.iloc[:split_idx]

    model = LinearRegression()
    model.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "aapl_close_predictor.joblib"))
    joblib.dump(FEATURES, os.path.join(MODEL_DIR, "aapl_model_features.joblib"))
    print(f"Trained on {len(X_train)} rows. Saved model + feature list to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
