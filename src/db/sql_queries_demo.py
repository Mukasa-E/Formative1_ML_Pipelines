"""
Runs the 3+ required SQL queries against the relational database and prints
their results. Run from repo root after src/db/load_sql_data.py:

    python src/db/sql_queries_demo.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import func
from src.db.sql_models import SessionLocal, Company, DailyPrice


def main():
    db = SessionLocal()
    company = db.query(Company).filter_by(symbol="AAPL").first()

    print("=" * 60)
    print("Query 1: Latest record for AAPL")
    print("=" * 60)
    latest = (
        db.query(DailyPrice)
        .filter_by(company_id=company.company_id)
        .order_by(DailyPrice.price_date.desc())
        .first()
    )
    print(f"{latest.price_date} | close={latest.close_price} | volume={latest.volume}")

    print("\n" + "=" * 60)
    print("Query 2: Records in a date range (2017-01-01 to 2017-01-10)")
    print("=" * 60)
    rows = (
        db.query(DailyPrice)
        .filter(
            DailyPrice.company_id == company.company_id,
            DailyPrice.price_date >= "2017-01-01",
            DailyPrice.price_date <= "2017-01-10",
        )
        .order_by(DailyPrice.price_date)
        .all()
    )
    for r in rows:
        print(f"{r.price_date} | open={r.open_price} close={r.close_price}")

    print("\n" + "=" * 60)
    print("Query 3: Average close price and total volume per year")
    print("=" * 60)
    yearly = (
        db.query(
            func.strftime("%Y", DailyPrice.price_date).label("year"),
            func.avg(DailyPrice.close_price).label("avg_close"),
            func.sum(DailyPrice.volume).label("total_volume"),
        )
        .filter(DailyPrice.company_id == company.company_id)
        .group_by("year")
        .order_by("year")
        .all()
    )
    for year, avg_close, total_volume in yearly:
        print(f"{year} | avg_close={float(avg_close):.2f} | total_volume={total_volume}")

    print("\n" + "=" * 60)
    print("Query 4: Highest single-day trading volume on record")
    print("=" * 60)
    top_volume = (
        db.query(DailyPrice)
        .filter_by(company_id=company.company_id)
        .order_by(DailyPrice.volume.desc())
        .first()
    )
    print(f"{top_volume.price_date} | volume={top_volume.volume} | close={top_volume.close_price}")

    db.close()


if __name__ == "__main__":
    main()
