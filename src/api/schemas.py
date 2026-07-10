from datetime import date as date_type
from pydantic import BaseModel, Field


class PriceCreate(BaseModel):
    symbol: str = Field(..., examples=["AAPL"])
    date: date_type = Field(..., examples=["2018-02-08"])
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceUpdate(BaseModel):
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None


class PriceOut(BaseModel):
    id: str
    symbol: str
    date: date_type
    open: float
    high: float
    low: float
    close: float
    volume: int
