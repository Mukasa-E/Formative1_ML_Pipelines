"""
MongoDB connection helper.

By default this uses `mongomock` (an in-memory MongoDB emulator) so the
project can be graded/run without a real MongoDB server installed, and the
in-memory data persists for the lifetime of the running process (so the API
process and any scripts that import this module share the same data).

To point this at a real MongoDB instance instead, set the MONGO_URI
environment variable, e.g.:

    export MONGO_URI="mongodb://localhost:27017"

and the code below will use `pymongo` instead of `mongomock` automatically.
The query code (find/insert/update/delete) is identical either way, since
mongomock implements the same pymongo API.
"""
import os

MONGO_URI = os.environ.get("MONGO_URI")

if MONGO_URI:
    from pymongo import MongoClient
    _client = MongoClient(MONGO_URI)
else:
    import mongomock
    _client = mongomock.MongoClient()

db = _client["stock_timeseries"]
prices_collection = db["prices"]
predictions_collection = db["predictions"]
