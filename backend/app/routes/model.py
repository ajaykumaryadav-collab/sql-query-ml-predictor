import os
import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.query import QueryHistory
from ..services.explain_service import run_explain
from ..services.feature_extractor import extract_features_from_plan
from ..services.prediction_service import prediction_service
from ..ml.train import train_models_from_csv, DEFAULT_DATASET_PATH, TARGET_COLUMN
import pandas as pd

logger = logging.getLogger(__name__)
router = APIRouter()

METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "trained_models", "metrics.json")

@router.get("/metrics")
def get_model_metrics():
    """Returns training metrics, leaderboard, and feature list for champion models."""
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"message": "Metrics not found"}

@router.post("/retrain-from-history")
def retrain_from_history(db: Session = Depends(get_db)):
    """
    Self-Tuning Continuous Learning Pipeline.
    Extracts live execution records from query_history, generates deep features,
    incorporates them into the training dataset, and retrains the champion models.
    """
    history_records = db.query(QueryHistory).filter(
        QueryHistory.actual_execution_time_ms != None
    ).order_by(QueryHistory.id.desc()).limit(200).all()

    if not history_records or len(history_records) < 3:
        raise HTTPException(
            status_code=400,
            detail="Need at least 3 executed queries in history to trigger self-tuning retraining. Run queries using 'EXPLAIN ANALYZE' first."
        )

    incorporated = 0
    new_rows = []

    for item in history_records:
        try:
            plan = run_explain(db, item.query_text, analyze=False)
            if not plan:
                continue
            features = extract_features_from_plan(plan)
            features[TARGET_COLUMN] = float(item.actual_execution_time_ms)
            new_rows.append(features)
            incorporated += 1
        except Exception:
            continue

    if not new_rows:
        raise HTTPException(status_code=500, detail="Could not extract plan features from query history.")

    df_new = pd.DataFrame(new_rows)
    csv_path = Path(DEFAULT_DATASET_PATH)

    # Append to dataset matching existing CSV schema
    if csv_path.exists():
        expected_cols = pd.read_csv(csv_path, nrows=0).columns.tolist()
        for col in expected_cols:
            if col not in df_new.columns:
                df_new[col] = 0.0
        df_new = df_new[expected_cols]
        df_new.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        df_new.to_csv(csv_path, mode="w", header=True, index=False)

    # Retrain champion model in log space
    train_models_from_csv(csv_path)

    # Reload prediction service
    prediction_service.model = None
    prediction_service.load_model()

    # Read updated metrics
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        updated_metrics = json.load(f)

    return {
        "status": "success",
        "message": f"Successfully incorporated {incorporated} live queries into model training.",
        "samples_incorporated": incorporated,
        "champion_model": updated_metrics.get("best_model"),
        "total_dataset_samples": updated_metrics.get("total_dataset_samples")
    }
