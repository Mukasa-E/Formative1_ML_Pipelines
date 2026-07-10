# MongoDB Collection Design

Database: `stock_timeseries`

## Collection: `prices`

One document per (symbol, date). Denormalized/flat by design — this is the
natural shape for time-series point queries (latest record, date-range scans)
and avoids the join MySQL needs between `companies` and `daily_prices`.

**Sample document:**
```json
{
  "_id": "ObjectId('...')",
  "symbol": "AAPL",
  "date": "2018-02-07",
  "open": 163.085,
  "high": 163.4,
  "low": 159.0685,
  "close": 159.54,
  "volume": 51608580
}
```

**Indexes (recommended for a real deployment):**
```js
db.prices.createIndex({ symbol: 1, date: 1 }, { unique: true })
db.prices.createIndex({ date: -1 })
```

## Collection: `predictions`

Stores model forecasts, kept separate from raw prices so predictions can be
purged/regenerated without touching source data.

**Sample document:**
```json
{
  "_id": "ObjectId('...')",
  "symbol": "AAPL",
  "date": "2018-02-08",
  "predicted_close": 158.92,
  "model_name": "linear_regression_v1",
  "created_at": "2026-07-06T18:30:00Z"
}
```

## Why this design vs. the relational schema

- MySQL splits `companies` / `daily_prices` / `predictions` to enforce
  referential integrity and avoid repeating `company_name` on every row.
- MongoDB embeds `symbol` directly into each price document. Since our
  queries are almost always "give me records for symbol X", denormalizing
  avoids a lookup/join and matches how MongoDB is typically used for
  time-series workloads (each document is self-describing).
- If the dataset grew to cover many symbols with rich company metadata
  (sector, exchange, etc.), a separate `companies` collection referenced by
  `symbol` would make more sense — not needed at this dataset's scale.
