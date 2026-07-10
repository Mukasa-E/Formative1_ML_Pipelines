from datetime import date as date_type

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import DuplicateKeyError

from src.api.schemas import PriceCreate, PriceUpdate, PriceOut
from src.db.mongo_client import prices_collection

router = APIRouter(prefix="/mongo/prices", tags=["MongoDB - prices"])


def _to_out(doc: dict) -> PriceOut:
    return PriceOut(
        id=str(doc["_id"]),
        symbol=doc["symbol"],
        date=doc["date"],
        open=doc["open"],
        high=doc["high"],
        low=doc["low"],
        close=doc["close"],
        volume=doc["volume"],
    )


@router.post("", response_model=PriceOut, status_code=201)
def create_price(payload: PriceCreate):
    """Create a new daily price document."""
    existing = prices_collection.find_one({"symbol": payload.symbol, "date": str(payload.date)})
    if existing:
        raise HTTPException(409, f"A record for {payload.symbol} on {payload.date} already exists.")
    doc = {
        "symbol": payload.symbol,
        "date": str(payload.date),
        "open": payload.open,
        "high": payload.high,
        "low": payload.low,
        "close": payload.close,
        "volume": payload.volume,
    }
    try:
        result = prices_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, f"A record for {payload.symbol} on {payload.date} already exists.")
    doc["_id"] = result.inserted_id
    return _to_out(doc)


@router.get("/latest", response_model=PriceOut)
def get_latest_price(symbol: str = Query(..., examples=["AAPL"])):
    """Return the most recent record for a symbol."""
    doc = prices_collection.find_one({"symbol": symbol}, sort=[("date", -1)])
    if doc is None:
        raise HTTPException(404, f"No price records found for {symbol}")
    return _to_out(doc)


@router.get("/range", response_model=list[PriceOut])
def get_price_range(
    symbol: str = Query(..., examples=["AAPL"]),
    start: date_type = Query(..., description="ISO format YYYY-MM-DD", examples=["2017-01-01"]),
    end: date_type = Query(..., description="ISO format YYYY-MM-DD", examples=["2017-01-10"]),
):
    """Return records for a symbol within an inclusive date range."""
    if start > end:
        raise HTTPException(422, "`start` must not be after `end`.")
    cursor = prices_collection.find(
        {"symbol": symbol, "date": {"$gte": str(start), "$lte": str(end)}}
    ).sort("date", 1)
    return [_to_out(doc) for doc in cursor]


@router.get("/{price_id}", response_model=PriceOut)
def get_price_by_id(price_id: str):
    """Read a single document by its ObjectId."""
    try:
        oid = ObjectId(price_id)
    except InvalidId:
        raise HTTPException(422, f"'{price_id}' is not a valid document id.")
    doc = prices_collection.find_one({"_id": oid})
    if doc is None:
        raise HTTPException(404, f"No record with id {price_id}")
    return _to_out(doc)


@router.put("/{price_id}", response_model=PriceOut)
def update_price(price_id: str, payload: PriceUpdate):
    """Partially update a document's OHLCV fields."""
    try:
        oid = ObjectId(price_id)
    except InvalidId:
        raise HTTPException(422, f"'{price_id}' is not a valid document id.")
    update_fields = payload.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(422, "No fields provided to update.")
    result = prices_collection.find_one_and_update(
        {"_id": oid}, {"$set": update_fields}, return_document=True
    )
    if result is None:
        raise HTTPException(404, f"No record with id {price_id}")
    return _to_out(result)


@router.delete("/{price_id}", status_code=204)
def delete_price(price_id: str):
    """Delete a document by its ObjectId."""
    try:
        oid = ObjectId(price_id)
    except InvalidId:
        raise HTTPException(422, f"'{price_id}' is not a valid document id.")
    result = prices_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(404, f"No record with id {price_id}")
