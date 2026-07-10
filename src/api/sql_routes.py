from datetime import date as date_type

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.exc import IntegrityError

from src.api.schemas import PriceCreate, PriceUpdate, PriceOut
from src.db.sql_models import SessionLocal, Company, DailyPrice

router = APIRouter(prefix="/sql/prices", tags=["SQL - prices"])


def _get_or_create_company(db, symbol: str) -> Company:
    company = db.query(Company).filter_by(symbol=symbol).first()
    if company is None:
        company = Company(symbol=symbol, company_name=symbol)
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


def _to_out(row: DailyPrice, symbol: str) -> PriceOut:
    return PriceOut(
        id=str(row.price_id),
        symbol=symbol,
        date=row.price_date,
        open=float(row.open_price),
        high=float(row.high_price),
        low=float(row.low_price),
        close=float(row.close_price),
        volume=row.volume,
    )


@router.post("", response_model=PriceOut, status_code=201)
def create_price(payload: PriceCreate):
    """Create a new daily price record."""
    db = SessionLocal()
    try:
        company = _get_or_create_company(db, payload.symbol)
        row = DailyPrice(
            company_id=company.company_id,
            price_date=payload.date,
            open_price=payload.open,
            high_price=payload.high,
            low_price=payload.low,
            close_price=payload.close,
            volume=payload.volume,
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, f"A record for {payload.symbol} on {payload.date} already exists.")
        db.refresh(row)
        return _to_out(row, payload.symbol)
    finally:
        db.close()


@router.get("/latest", response_model=PriceOut)
def get_latest_price(symbol: str = Query(..., examples=["AAPL"])):
    """Return the most recent record for a symbol."""
    db = SessionLocal()
    try:
        company = db.query(Company).filter_by(symbol=symbol).first()
        if company is None:
            raise HTTPException(404, f"Unknown symbol: {symbol}")
        row = (
            db.query(DailyPrice)
            .filter_by(company_id=company.company_id)
            .order_by(DailyPrice.price_date.desc())
            .first()
        )
        if row is None:
            raise HTTPException(404, f"No price records found for {symbol}")
        return _to_out(row, symbol)
    finally:
        db.close()


@router.get("/range", response_model=list[PriceOut])
def get_price_range(
    symbol: str = Query(..., examples=["AAPL"]),
    start: date_type = Query(..., description="ISO format YYYY-MM-DD", examples=["2017-01-01"]),
    end: date_type = Query(..., description="ISO format YYYY-MM-DD", examples=["2017-01-10"]),
):
    """Return records for a symbol within an inclusive date range."""
    db = SessionLocal()
    try:
        if start > end:
            raise HTTPException(422, "`start` must not be after `end`.")
        company = db.query(Company).filter_by(symbol=symbol).first()
        if company is None:
            raise HTTPException(404, f"Unknown symbol: {symbol}")
        rows = (
            db.query(DailyPrice)
            .filter(
                DailyPrice.company_id == company.company_id,
                DailyPrice.price_date >= start,
                DailyPrice.price_date <= end,
            )
            .order_by(DailyPrice.price_date)
            .all()
        )
        return [_to_out(r, symbol) for r in rows]
    finally:
        db.close()


@router.get("/{price_id}", response_model=PriceOut)
def get_price_by_id(price_id: int):
    """Read a single record by its primary key."""
    db = SessionLocal()
    try:
        row = db.query(DailyPrice).filter_by(price_id=price_id).first()
        if row is None:
            raise HTTPException(404, f"No record with id {price_id}")
        symbol = row.company.symbol
        return _to_out(row, symbol)
    finally:
        db.close()


@router.put("/{price_id}", response_model=PriceOut)
def update_price(price_id: int, payload: PriceUpdate):
    """Partially update a record's OHLCV fields."""
    db = SessionLocal()
    try:
        row = db.query(DailyPrice).filter_by(price_id=price_id).first()
        if row is None:
            raise HTTPException(404, f"No record with id {price_id}")
        data = payload.model_dump(exclude_unset=True)
        if "open" in data:
            row.open_price = data["open"]
        if "high" in data:
            row.high_price = data["high"]
        if "low" in data:
            row.low_price = data["low"]
        if "close" in data:
            row.close_price = data["close"]
        if "volume" in data:
            row.volume = data["volume"]
        db.commit()
        db.refresh(row)
        return _to_out(row, row.company.symbol)
    finally:
        db.close()


@router.delete("/{price_id}", status_code=204)
def delete_price(price_id: int):
    """Delete a record by its primary key."""
    db = SessionLocal()
    try:
        row = db.query(DailyPrice).filter_by(price_id=price_id).first()
        if row is None:
            raise HTTPException(404, f"No record with id {price_id}")
        db.delete(row)
        db.commit()
    finally:
        db.close()
