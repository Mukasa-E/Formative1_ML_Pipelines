"""
Loads data/raw/aapl.csv into the `prices` MongoDB collection.

Run from repo root:
    python src/db/load_mongo_data.py
"""
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.mongo_client import prices_collection

RAW_PATH = os.path.join("data", "raw", "aapl.csv")


def seed_if_empty():
    """Loads the CSV into Mongo only if the collection is currently empty.
    Safe to call from the API startup event or standalone."""
    if prices_collection.count_documents({}) > 0:
        return prices_collection.count_documents({})

    df = pd.read_csv(RAW_PATH)
    df.columns = df.columns.str.capitalize()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df[df["Name"] == "AAPL"].sort_values("Date")

    documents = [
        {
            "symbol": "AAPL",
            "date": row["Date"].strftime("%Y-%m-%d"),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        }
        for _, row in df.iterrows()
    ]
    prices_collection.insert_many(documents)
    return len(documents)


if __name__ == "__main__":
    n = seed_if_empty()
    print(f"prices collection now has {n} documents.")
