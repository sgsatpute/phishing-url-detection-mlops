import os
import sys
from pathlib import Path
from typing import Annotated
from urllib.parse import quote_plus, urlparse

import certifi
import pandas as pd
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from starlette.responses import RedirectResponse
from starlette.templating import _TemplateResponse
from uvicorn import run as app_run

from network_security.constant.training_pipeline import (
    DATA_INGESTION_COLLECTION_NAME,
    DATA_INGESTION_DATABASE_NAME,
)
from network_security.exception.exception import NetworkSecurityException
from network_security.logging.logger import logging
from network_security.pipeline.training_pipeline import TrainingPipeline
from network_security.utils.main_utils.utils import load_object
from network_security.utils.ml_utils.feature_extraction import FEATURE_COLUMNS, extract_features
from network_security.utils.ml_utils.model.estimator import NetworkModel

ca = certifi.where()


load_dotenv()
_raw_username = os.getenv("MONGO_DB_USERNAME")
_raw_password = os.getenv("MONGO_DB_PASSWORD")
if not _raw_username or not _raw_password:
    # Without this check, quote_plus(None) raises a bare
    # "TypeError: quote_from_bytes() expected bytes" at import time — before
    # FastAPI even starts — which gives no hint that the real problem is a
    # missing .env file / unset MONGO_DB_USERNAME or MONGO_DB_PASSWORD.
    raise RuntimeError(
        "MONGO_DB_USERNAME and MONGO_DB_PASSWORD must be set (e.g. in a .env "
        "file) before starting the app.",
    )
username = quote_plus(_raw_username)
password = quote_plus(_raw_password)

# /train runs the full pipeline (ingestion, validation, transformation,
# GridSearchCV across 5 models) and was previously unauthenticated — any
# unauthenticated GET request could trigger it, making it a trivial
# resource-exhaustion vector against a publicly deployed instance. Require
# a shared secret via the X-Train-Api-Key header. If TRAIN_API_KEY isn't
# set, /train is disabled entirely rather than silently left open.
TRAIN_API_KEY = os.getenv("TRAIN_API_KEY")


def _verify_train_api_key(x_train_api_key: str | None = Header(default=None)) -> None:
    if not TRAIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="TRAIN_API_KEY is not configured on the server; /train is disabled.",
        )
    if not x_train_api_key or x_train_api_key != TRAIN_API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid X-Train-Api-Key header.")

mongo_db_url: str = f"mongodb+srv://{username}:{password}@cluster0.lbvk3s8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(mongo_db_url, server_api=ServerApi("1"), tlsCAFile=ca)


database = client[DATA_INGESTION_DATABASE_NAME]
collection = database[DATA_INGESTION_COLLECTION_NAME]

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory="./templates")


def _silence_estimator_verbosity(estimator) -> None:
    """Recursively turn off `verbose` on an estimator (and each step, if it's
    a Pipeline), so predict() calls don't spam stdout with sklearn/joblib
    Parallel progress logs like:
        [Parallel(n_jobs=1)]: Done 32 out of 32 | elapsed: 0.0s finished
    """
    if hasattr(estimator, "verbose"):
        try:
            estimator.verbose = 0
        except Exception:
            pass
    # Pipeline objects expose .steps as a list of (name, transformer/estimator)
    if hasattr(estimator, "steps"):
        for _, step in estimator.steps:
            _silence_estimator_verbosity(step)
    # Some meta-estimators (e.g. GridSearchCV-wrapped, VotingClassifier) expose
    # .estimator or .estimators_
    if hasattr(estimator, "estimator"):
        _silence_estimator_verbosity(estimator.estimator)
    if hasattr(estimator, "estimators_"):
        for sub in estimator.estimators_:
            _silence_estimator_verbosity(sub)


def _looks_like_valid_url(url: str) -> bool:
    """Reject obvious non-URLs (empty strings, page fragments/anchors like
    '#batch-upload', localhost, missing scheme/host) before running the full
    feature-extraction pipeline on them. Prevents nonsense input like
    'http://localhost:8080/#batch-upload' from silently getting a confident
    'Legitimate'/'Phishing' verdict instead of a clear error.
    """
    if not url or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc:
        return False
    hostname = (parsed.hostname or "").lower()
    if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return False  # a phishing checker has no business "checking" itself
    return True


# Load the model + preprocessor once at startup and cache them in memory,
# instead of re-reading both pickle files from disk on every /predict call.
# /train refreshes these in-memory objects after a successful retrain.
try:
    _preprocessor = load_object("final_model/preprocessor.pkl")
    _model = load_object("final_model/model.pkl")
    _silence_estimator_verbosity(_preprocessor)
    _silence_estimator_verbosity(_model)
    network_model: NetworkModel | None = NetworkModel(preprocessor=_preprocessor, model=_model)
except Exception as e:
    # Don't crash app startup if no model has been trained yet — /predict
    # will simply return a clear error until /train has run at least once.
    logging.warning(f"Could not load model/preprocessor at startup ({e}). Run /train first.")
    network_model = None


def _label_from_prediction(prediction: float) -> str:
    """Map the model's raw class output to a display label.

    IMPORTANT: the trained model's classes are 0.0 (phishing) and 1.0
    (legitimate) — confirmed against data_transformation.py, which replaces
    the raw dataset's Result values of -1 (phishing) with 0 before training.
    A previous version of this check compared against -1 directly, which
    could never match and silently reported "Legitimate" on every single
    prediction. Extracted into its own function (rather than left inline in
    the route) specifically so it can be unit tested in isolation — see
    tests/test_label_mapping.py.
    """
    return "Legitimate" if prediction == 1 else "Phishing"


@app.get("/")
async def index(request: Request) -> _TemplateResponse:
    return templates.TemplateResponse(request, "index.html", {})
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/predict-url")
async def predict_url_route(request: Request, url: Annotated[str, Form()]) -> _TemplateResponse:
    try:
        if network_model is None:
            return templates.TemplateResponse(
                request,
                "index.html",
                {"error": "No trained model available yet. Call /train first."},
            )

        if not _looks_like_valid_url(url):
            return templates.TemplateResponse(
                request,
                "index.html",
                {
                    "error": "That doesn't look like a valid http(s) URL. Please check and try again.",
                    "checked_url": url,
                },
            )

        features_df = extract_features(url)
        prediction = network_model.predict(features_df)[0]
        result = _label_from_prediction(prediction)

        # Confidence score, if the underlying estimator supports predict_proba.
        # Not all models do (e.g. plain SVC without probability=True), so this
        # degrades gracefully to no confidence shown rather than erroring.
        confidence = None
        try:
            if hasattr(network_model, "predict_proba"):
                proba = network_model.predict_proba(features_df)[0]
                confidence = round(float(max(proba)) * 100, 1)
        except Exception as proba_err:
            logging.warning(f"predict_proba unavailable for {url}: {proba_err}")

        return templates.TemplateResponse(
            request,
            "index.html",
            {"result": result, "checked_url": url, "confidence": confidence},
        )
    except Exception as e:
        logging.warning(f"predict-url failed for {url}: {e}")
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "error": "Couldn't analyze that URL. Make sure it's reachable and try again.",
                "checked_url": url,
            },
        )


@app.get("/docs-redirect")
async def docs_redirect() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health() -> dict:
    mongo_ok = True
    mongo_error = None
    try:
        client.admin.command("ping")
    except Exception as e:
        mongo_ok = False
        mongo_error = str(e)

    return {
        "status": "ok" if (network_model is not None and mongo_ok) else "degraded",
        "model_loaded": network_model is not None,
        "mongo_connected": mongo_ok,
        **({"mongo_error": mongo_error} if mongo_error else {}),
    }


@app.get("/train", dependencies=[Depends(_verify_train_api_key)])
async def train_route() -> Response:
    global network_model
    try:
        train_pipeline = TrainingPipeline()
        train_pipeline.run_pipeline()
        # Refresh the in-memory model so /predict immediately uses the
        # newly trained artifact without needing an app restart.
        preprocessor = load_object("final_model/preprocessor.pkl")
        model = load_object("final_model/model.pkl")
        _silence_estimator_verbosity(preprocessor)
        _silence_estimator_verbosity(model)
        network_model = NetworkModel(preprocessor=preprocessor, model=model)
        return Response("Training is successful")
    except Exception as e:
        raise NetworkSecurityException(e, sys)


@app.post("/predict")
async def predict_route(request: Request, file: Annotated[UploadFile, File()] = ...) -> _TemplateResponse:
    try:
        if network_model is None:
            return templates.TemplateResponse(
                request,
                "index.html",
                {"error": "No trained model available yet. Call /train first."},
            )

        df = pd.read_csv(file.file)

        # Validate columns up front instead of letting a mismatched CSV
        # (e.g. the wrong file entirely) blow up deep inside sklearn with a
        # raw stack trace shown to the user. Consistent with the upfront
        # validation already done on /predict-url.
        missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
        if missing_cols:
            preview = ", ".join(missing_cols[:5])
            more = f" (+{len(missing_cols) - 5} more)" if len(missing_cols) > 5 else ""
            return templates.TemplateResponse(
                request,
                "index.html",
                {
                    "error": (
                        "That CSV doesn't have the expected feature columns "
                        f"— missing: {preview}{more}. Make sure you're uploading "
                        "a file with the phishing-detection feature columns, "
                        "not an unrelated dataset."
                    ),
                },
            )

        y_pred = network_model.predict(df[FEATURE_COLUMNS])
        df["predicted_column"] = y_pred

        Path("prediction_output").mkdir(exist_ok=True)
        df.to_csv("prediction_output/output.csv")
        table_html = df.to_html(classes="table table-striped")
        return templates.TemplateResponse(
            request, "table.html", {"table": table_html},
        )

    except Exception as e:
        logging.warning(f"predict (CSV) failed: {e}")
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": "Couldn't process that CSV. Please check the file and try again."},
        )


if __name__ == "__main__":
    app_run(app, host="0.0.0.0", port=8080)