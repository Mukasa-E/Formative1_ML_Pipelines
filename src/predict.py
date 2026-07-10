"""
Task 4: Consolidated prediction script.

Steps (as required by the assignment):
  1. Fetch a time-series record (a recent window) from the running API.
  2. Preprocess it the same way as Task 1 (Lag_1, Lag_7, Rolling_mean_7).
  3. Load the trained model from Task 1 (models/aapl_close_predictor.joblib).
  4. Make a prediction for the next trading day's close price.

Requires the API to be running first:
    uvicorn src.api.main:app --reload

Then run this script from repo root:
    python src/predict.py --symbol AAPL --source sql
    python src/predict.py --symbol AAPL --source mongo
"""
import argparse
import os
import sys
from datetime import datetime, timedelta

import joblib
import pandas as pd
import requests

MODEL_PATH = os.path.join("models", "aapl_close_predictor.joblib")
FEATURES_PATH = os.path.join("models", "aapl_model_features.joblib")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


def fetch_recent_window(symbol: str, source: str, lookback_days: int = 40) -> pd.DataFrame:
    """Fetches the last `lookback_days` calendar days of records from the API
    (we need >= 7 trading days of history to build Lag_7 / Rolling_mean_7)."""
    latest_resp = requests.get(f"{API_BASE_URL}/{source}/prices/latest", params={"symbol": symbol})
    latest_resp.raise_for_status()
    latest_date = datetime.strptime(latest_resp.json()["date"], "%Y-%m-%d")

    start_date = (latest_date - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = latest_date.strftime("%Y-%m-%d")

    range_resp = requests.get(
        f"{API_BASE_URL}/{source}/prices/range",
        params={"symbol": symbol, "start": start_date, "end": end_date},
    )
    range_resp.raise_for_status()
    records = range_resp.json()
    if not records:
        raise RuntimeError(f"No records returned from {source} API for {symbol}.")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Mirrors the Task 1 preprocessing pipeline (Lag_1, Lag_7, Rolling_mean_7)."""
    df = df.copy()
    df["Lag_1"] = df["close"].shift(1)
    df["Lag_7"] = df["close"].shift(7)
    df["Rolling_mean_7"] = df["close"].rolling(window=7).mean()
    return df


def main():
    parser = argparse.ArgumentParser(description="Predict next-day AAPL close price.")
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--source", choices=["sql", "mongo"], default="sql",
                         help="Which backend to fetch the record(s) from.")
    args = parser.parse_args()

    print(f"1. Fetching recent {args.symbol} records from the {args.source.upper()} API...")
    df = fetch_recent_window(args.symbol, args.source)
    print(f"   Retrieved {len(df)} records, latest date = {df['date'].iloc[-1].date()}")

    print("2. Building features (Lag_1, Lag_7, Rolling_mean_7)...")
    df_features = build_features(df)
    last_row = df_features.iloc[[-1]]
    if last_row[["Lag_1", "Lag_7", "Rolling_mean_7"]].isnull().any(axis=None):
        print("   ERROR: not enough history in the fetched window to build all features.")
        sys.exit(1)

    print("3. Loading trained model from Task 1...")
    if not (os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH)):
        print(f"   ERROR: model not found at {MODEL_PATH}. Run `python src/train_model.py` first.")
        sys.exit(1)
    model = joblib.load(MODEL_PATH)
    features = joblib.load(FEATURES_PATH)

    print("4. Making prediction...")
    X = last_row[features]
    prediction = model.predict(X)[0]

    latest_close = last_row["close"].values[0]
    latest_date = last_row["date"].values[0]
    print("\n" + "=" * 50)
    print(f"Last known close ({pd.Timestamp(latest_date).date()}): ${latest_close:.2f}")
    print(f"Predicted next-day close for {args.symbol}: ${prediction:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
