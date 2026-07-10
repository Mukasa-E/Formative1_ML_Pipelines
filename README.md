# Formative 1 — Time-Series ML Pipeline (AAPL Stock Prices)

A full pipeline covering time-series EDA and modeling, relational + non-relational
database design, a CRUD/time-series API, and an end-to-end prediction script.

**Dataset:** AAPL daily OHLCV prices, 2013-02-08 to 2018-02-07 (subset of the
Kaggle "S&P 500 stock data" dataset by camnugent). **Target:** next-day Close price.

## Project structure

```
├── notebooks/
│   └── Task1_Preprocessing_and_EDA.ipynb   # Task 1: EDA, feature engineering, model experiments
├── data/
│   └── raw/aapl.csv                        # Cleaned AAPL slice used across all tasks
├── docs/
│   ├── erd.png                             # Entity-relationship diagram (Task 2)
│   └── mongo_design.md                     # MongoDB collection design + sample docs (Task 2)
├── models/
│   ├── aapl_close_predictor.joblib         # Trained model (Task 1 winner, reused in Task 4)
│   └── aapl_model_features.joblib          # Feature list the model expects
├── src/
│   ├── train_model.py                      # Reproduces Task 1's best model, saves artifact
│   ├── db/
│   │   ├── schema_mysql.sql                # MySQL DDL (3 tables, FKs) — Task 2
│   │   ├── sql_models.py                   # SQLAlchemy models mirroring schema_mysql.sql
│   │   ├── load_sql_data.py                # Seeds SQL DB from data/raw/aapl.csv
│   │   ├── sql_queries_demo.py             # Runs 4 required SQL queries, prints results
│   │   ├── mongo_client.py                 # Mongo connection (mongomock by default)
│   │   ├── load_mongo_data.py              # Seeds `prices` collection from the CSV
│   │   └── mongo_queries_demo.py           # Runs 4 required Mongo queries, prints results
│   ├── api/
│   │   ├── main.py                         # FastAPI app (Task 3), auto-seeds both DBs on startup
│   │   ├── schemas.py                      # Pydantic request/response models
│   │   ├── sql_routes.py                   # Full CRUD + /latest + /range for the SQL backend
│   │   └── mongo_routes.py                 # Full CRUD + /latest + /range for the Mongo backend
│   └── predict.py                          # Task 4: fetch → preprocess → load model → predict
├── CONTRIBUTIONS.md                        # Per-member commit/role log (fill in before submitting)
└── requirements.txt
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```

## Task 1 — Preprocessing & EDA

Open `notebooks/Task1_Preprocessing_and_EDA.ipynb`. Covers time range/frequency,
missing values, 5 analytical questions (including lag features and moving
averages), and a 4-experiment model comparison (Linear Regression beats a
tuned Random Forest on this chronologically-split test set — see the
notebook's interpretation for why).

To regenerate the model artifact used by Task 4 without re-running the whole
notebook:

```bash
python src/train_model.py
```

## Task 2 — Databases

**Relational (MySQL):** `companies` → `daily_prices` → `predictions`
(see `docs/erd.png` and `src/db/schema_mysql.sql`). By default the project
runs against a local SQLite file so it works without a MySQL server; point it
at real MySQL with:
```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/stock_timeseries"
```

**MongoDB:** see `docs/mongo_design.md` for the collection design and sample
documents. By default this uses `mongomock` (in-memory, no server needed);
point it at a real Mongo instance with:
```bash
export MONGO_URI="mongodb://localhost:27017"
```

Seed and query both databases directly (outside the API):
```bash
python src/db/load_sql_data.py
python src/db/sql_queries_demo.py

python src/db/mongo_queries_demo.py   # seeds automatically if empty
```

## Task 3 — CRUD + Time-Series API

```bash
uvicorn src.api.main:app --reload
```
Both databases are auto-seeded on startup. Open **http://127.0.0.1:8000/docs**
for interactive Swagger UI, or use curl:

```bash
# Latest record
curl "http://127.0.0.1:8000/sql/prices/latest?symbol=AAPL"
curl "http://127.0.0.1:8000/mongo/prices/latest?symbol=AAPL"

# Date range (ISO format required: YYYY-MM-DD)
curl "http://127.0.0.1:8000/sql/prices/range?symbol=AAPL&start=2017-01-01&end=2017-01-10"

# Create
curl -X POST "http://127.0.0.1:8000/sql/prices" -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","date":"2018-02-08","open":163.0,"high":164.0,"low":159.0,"close":160.0,"volume":50000000}'

# Update
curl -X PUT "http://127.0.0.1:8000/sql/prices/1260" -H "Content-Type: application/json" -d '{"close":161.5}'

# Delete
curl -X DELETE "http://127.0.0.1:8000/sql/prices/1260"
```
Every endpoint above exists identically under both `/sql/prices` and `/mongo/prices`.

## Task 4 — Prediction Script

With the API running (`uvicorn src.api.main:app`), in a separate terminal:
```bash
python src/predict.py --symbol AAPL --source sql
python src/predict.py --symbol AAPL --source mongo
```
This fetches a recent window of records from the live API, rebuilds the
Lag_1 / Lag_7 / Rolling_mean_7 features exactly as in Task 1, loads
`models/aapl_close_predictor.joblib`, and prints a next-day close prediction.
