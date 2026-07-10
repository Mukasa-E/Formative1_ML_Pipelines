"""
Seeds (if needed) and runs the 3+ required MongoDB queries, printing results.
Run from repo root:

    python src/db/mongo_queries_demo.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.mongo_client import prices_collection
from src.db.load_mongo_data import seed_if_empty


def main():
    seed_if_empty()

    print("=" * 60)
    print("Query 1: Latest record for AAPL")
    print("=" * 60)
    latest = list(
        prices_collection.find({"symbol": "AAPL"}).sort("date", -1).limit(1)
    )[0]
    print({k: v for k, v in latest.items() if k != "_id"})

    print("\n" + "=" * 60)
    print("Query 2: Records in a date range (2017-01-01 to 2017-01-10)")
    print("=" * 60)
    cursor = prices_collection.find(
        {"symbol": "AAPL", "date": {"$gte": "2017-01-01", "$lte": "2017-01-10"}}
    ).sort("date", 1)
    for doc in cursor:
        print({k: v for k, v in doc.items() if k != "_id"})

    print("\n" + "=" * 60)
    print("Query 3: Average close price and total volume per year (aggregation)")
    print("=" * 60)
    pipeline = [
        {"$match": {"symbol": "AAPL"}},
        {"$group": {
            "_id": {"$substr": ["$date", 0, 4]},
            "avg_close": {"$avg": "$close"},
            "total_volume": {"$sum": "$volume"},
        }},
        {"$sort": {"_id": 1}},
    ]
    for row in prices_collection.aggregate(pipeline):
        print(f"{row['_id']} | avg_close={row['avg_close']:.2f} | total_volume={row['total_volume']}")

    print("\n" + "=" * 60)
    print("Query 4: Highest single-day trading volume on record")
    print("=" * 60)
    top_volume = list(
        prices_collection.find({"symbol": "AAPL"}).sort("volume", -1).limit(1)
    )[0]
    print({k: v for k, v in top_volume.items() if k != "_id"})


if __name__ == "__main__":
    main()
