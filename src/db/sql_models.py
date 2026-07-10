"""
SQLAlchemy models mirroring src/db/schema_mysql.sql.

By default this connects to a local SQLite file (data/processed/stock_timeseries.db)
so the project runs anywhere without a MySQL server installed. To point it at a
real MySQL instance instead, set the DATABASE_URL environment variable, e.g.:

    export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/stock_timeseries"

The table definitions below are equivalent to schema_mysql.sql; SQLAlchemy will
create them automatically on either backend via Base.metadata.create_all().
"""
import os
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String,
    Date, Numeric, TIMESTAMP, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite:///data/processed/stock_timeseries.db"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, unique=True)
    company_name = Column(String(100), nullable=False)

    prices = relationship("DailyPrice", back_populates="company", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="company", cascade="all, delete-orphan")


class DailyPrice(Base):
    __tablename__ = "daily_prices"
    __table_args__ = (UniqueConstraint("company_id", "price_date", name="uq_company_date"),)

    price_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    price_date = Column(Date, nullable=False)
    open_price = Column(Numeric(10, 4), nullable=False)
    high_price = Column(Numeric(10, 4), nullable=False)
    low_price = Column(Numeric(10, 4), nullable=False)
    close_price = Column(Numeric(10, 4), nullable=False)
    volume = Column(BigInteger, nullable=False)

    company = relationship("Company", back_populates="prices")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    price_date = Column(Date, nullable=False)
    predicted_close = Column(Numeric(10, 4), nullable=False)
    model_name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    company = relationship("Company", back_populates="predictions")


def init_db():
    os.makedirs("data/processed", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
