"""
Shared pytest fixtures/setup.

app.py currently reads MONGO_DB_USERNAME/MONGO_DB_PASSWORD and constructs a
MongoClient at module import time. pymongo connects lazily, so constructing
a MongoClient with dummy credentials does not require a live database or
real credentials — but the env vars must at least be *present*, or app.py
raises RuntimeError before we can import _label_from_prediction from it.

Longer-term improvement: move the Mongo client construction and model
loading into a FastAPI startup event / dependency instead of module-level
code, so the app module can be imported for testing without any
side effects at all. Left as-is for now to keep this session's diff
focused, but worth doing before this app.py grows further.
"""

import os

os.environ.setdefault("MONGO_DB_USERNAME", "test_user")
os.environ.setdefault("MONGO_DB_PASSWORD", "test_password")