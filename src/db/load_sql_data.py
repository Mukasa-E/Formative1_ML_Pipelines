"""
Loads data/raw/aapl.csv into the SQL database (companies + daily_prices).

Run from repo root:
    python src/db/load_sql_data.py
"""
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.sql_models import init_db, SessionLocal, Company, DailyPrice

RAW_PATH = os.path.join("data", "raw", "aapl.csv")


def load():
    init_db()
    db = SessionLocal()
    try:
        df = pd.read_csv(RAW_PATH)
        df.columns = df.columns.str.capitalize()
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df[df["Name"] == "AAPL"].sort_values("Date")

        company = db.query(Company).filter_by(symbol="AAPL").first()
        if company is None:
            company = Company(symbol="AAPL", company_name="Apple Inc.")
            db.add(company)
            db.commit()
            db.refresh(company)

        existing_dates = {
            d for (d,) in db.query(DailyPrice.price_date).filter_by(company_id=company.company_id)
        }

        inserted = 0
        for _, row in df.iterrows():
            row_date = row["Date"].date()
            if row_date in existing_dates:
                continue
            db.add(DailyPrice(
                company_id=company.company_id,
                price_date=row_date,
                open_price=float(row["Open"]),
                high_price=float(row["High"]),
                low_price=float(row["Low"]),
                close_price=float(row["Close"]),
                volume=int(row["Volume"]),
            ))
            inserted += 1

        db.commit()
        print(f"Loaded {inserted} new daily_prices rows for AAPL "
              f"(company_id={company.company_id}).")
    finally:
        db.close()


if __name__ == "__main__":
    load()
