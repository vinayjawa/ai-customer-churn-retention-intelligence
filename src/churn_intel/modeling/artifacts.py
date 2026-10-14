"""Load persisted model artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from churn_intel.config import PROJECT_ROOT

MODELS_DIR = PROJECT_ROOT / "artifacts" / "models"
DEFAULT_PIPELINE_PATH = MODELS_DIR / "baseline_churn_pipeline.joblib"
DEFAULT_METADATA_PATH = MODELS_DIR / "baseline_model_metadata.json"
MODEL_VERSION = "baseline_logistic_v1"
MODEL_NAME = "logistic_regression_balanced"


def load_pipeline(path: Path | None = None) -> Pipeline:
    target = path or DEFAULT_PIPELINE_PATH
    if not target.is_file():
        raise FileNotFoundError(f"Model pipeline not found: {target}")
    pipeline = joblib.load(target)
    if not isinstance(pipeline, Pipeline):
        raise TypeError("Expected sklearn Pipeline artifact.")
    return pipeline


def load_metadata(path: Path | None = None) -> dict:
    target = path or DEFAULT_METADATA_PATH
    if not target.is_file():
        raise FileNotFoundError(f"Model metadata not found: {target}")
    return json.loads(target.read_text(encoding="utf-8"))
