"""
Task 3: CRUD + time-series API for both the SQL and MongoDB backends.

Run from repo root:
    uvicorn src.api.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive Swagger UI.
"""
from fastapi import FastAPI

from src.api.sql_routes import router as sql_router
from src.api.mongo_routes import router as mongo_router
from src.db.sql_models import init_db
from src.db.load_sql_data import load as load_sql_data
from src.db.load_mongo_data import seed_if_empty as seed_mongo_data

app = FastAPI(
    title="AAPL Time-Series API",
    description="CRUD + latest/date-range endpoints backed by both a SQL "
                 "(MySQL-compatible) database and MongoDB.",
    version="1.0.0",
)


@app.on_event("startup")
def startup_seed():
    """Ensures both databases have data on first run, so the API works
    out of the box without a manual seeding step."""
    init_db()
    load_sql_data()
    seed_mongo_data()


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "docs": "/docs"}


app.include_router(sql_router)
app.include_router(mongo_router)
