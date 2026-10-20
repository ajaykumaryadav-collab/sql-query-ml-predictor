import os
import json
import logging
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..database import get_db
from ..models.query import QueryHistory
from ..services.explain_service import run_explain
from ..services.feature_extractor import extract_features_from_plan
from ..services.prediction_service import prediction_service
from ..ml.train import train_models_from_csv, DEFAULT_DATASET_PATH, TARGET_COLUMN, FEATURE_COLUMNS

logger = logging.getLogger(__name__)
router = APIRouter()

METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "trained_models", "metrics.json")

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_queries = db.query(QueryHistory).count()
    
    avg_pred = db.query(func.avg(QueryHistory.ml_predicted_time_ms)).scalar() or 0.0
    avg_actual = db.query(func.avg(QueryHistory.actual_execution_time_ms)).filter(QueryHistory.actual_execution_time_ms != None).scalar() or 0.0
    avg_error = db.query(func.avg(QueryHistory.prediction_error_percent)).filter(QueryHistory.prediction_error_percent != None).scalar() or 0.0
    
    high_cost_queries = db.query(QueryHistory).filter(QueryHistory.performance_category == 'HIGH').count()
    
    return {
        "queries_analyzed": total_queries,
        "average_predicted_time_ms": round(avg_pred, 2),
        "average_actual_time_ms": round(avg_actual, 2),
        "average_prediction_error_percent": round(avg_error, 2),
        "high_cost_queries": high_cost_queries
    }

@router.get("/analytics")
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Rich system analytics for Dashboard 2.0.
    Provides latency distribution, accuracy trend lines, slowest queries, and risk breakdowns.
    """
    total_queries = db.query(QueryHistory).count()
    executed_queries = db.query(QueryHistory).filter(QueryHistory.actual_execution_time_ms != None).count()
    
    avg_pred = db.query(func.avg(QueryHistory.ml_predicted_time_ms)).scalar() or 0.0
    avg_actual = db.query(func.avg(QueryHistory.actual_execution_time_ms)).filter(QueryHistory.actual_execution_time_ms != None).scalar() or 0.0
    avg_error = db.query(func.avg(QueryHistory.prediction_error_percent)).filter(QueryHistory.prediction_error_percent != None).scalar() or 0.0

    low_risk = db.query(QueryHistory).filter(QueryHistory.performance_category == 'LOW').count()
    med_risk = db.query(QueryHistory).filter(QueryHistory.performance_category == 'MEDIUM').count()
    high_risk = db.query(QueryHistory).filter(QueryHistory.performance_category == 'HIGH').count()

    # Latency Distribution Bucketing
    b_under_1 = db.query(QueryHistory).filter(QueryHistory.actual_execution_time_ms != None, QueryHistory.actual_execution_time_ms < 1.0).count()
    b_1_10 = db.query(QueryHistory).filter(QueryHistory.actual_execution_time_ms != None, QueryHistory.actual_execution_time_ms >= 1.0, QueryHistory.actual_execution_time_ms < 10.0).count()
    b_10_50 = db.query(QueryHistory).filter(QueryHistory.actual_execution_time_ms != None, QueryHistory.actual_execution_time_ms >= 10.0, QueryHistory.actual_execution_time_ms < 50.0).count()
    b_50_200 = db.query(QueryHistory).filter(QueryHistory.actual_execution_time_ms != None, QueryHistory.actual_execution_time_ms >= 50.0, QueryHistory.actual_execution_time_ms < 200.0).count()
    b_over_200 = db.query(QueryHistory).filter(QueryHistory.actual_execution_time_ms != None, QueryHistory.actual_execution_time_ms >= 200.0).count()

    latency_distribution = [
        {"range": "< 1 ms", "count": b_under_1, "description": "Instant / Index Lookups", "color": "#10b981"},
        {"range": "1–10 ms", "count": b_1_10, "description": "Fast Indexed Scans", "color": "#3b82f6"},
        {"range": "10–50 ms", "count": b_10_50, "description": "Moderate Hash Joins", "color": "#6366f1"},
        {"range": "50–200 ms", "count": b_50_200, "description": "Heavy Aggregations", "color": "#f59e0b"},
        {"range": "> 200 ms", "count": b_over_200, "description": "Unbounded Table Scans", "color": "#ef4444"}
    ]

    # Recent Accuracy Trends (last 20 executed queries, ordered ascending for time series)
    recent_records = db.query(QueryHistory).filter(
        QueryHistory.actual_execution_time_ms != None,
        QueryHistory.ml_predicted_time_ms != None
    ).order_by(QueryHistory.id.desc()).limit(20).all()

    recent_records.reverse()
    accuracy_trends = []
    for r in recent_records:
        accuracy_trends.append({
            "id": r.id,
            "query_preview": (r.query_text[:28] + "...") if len(r.query_text) > 28 else r.query_text,
            "actual_ms": round(float(r.actual_execution_time_ms), 2),
            "predicted_ms": round(float(r.ml_predicted_time_ms), 2),
            "error_pct": round(float(r.prediction_error_percent or 0.0), 1),
            "created_at": r.created_at.strftime("%H:%M:%S") if r.created_at else ""
        })

    # Slowest Queries Leaderboard (Top 5)
    slowest_records = db.query(QueryHistory).filter(
        QueryHistory.actual_execution_time_ms != None
    ).order_by(QueryHistory.actual_execution_time_ms.desc()).limit(5).all()

    slowest_queries = []
    for idx, r in enumerate(slowest_records):
        slowest_queries.append({
            "rank": idx + 1,
            "id": r.id,
            "query_text": r.query_text,
            "actual_time_ms": round(float(r.actual_execution_time_ms), 2),
            "predicted_time_ms": round(float(r.ml_predicted_time_ms or 0.0), 2),
            "error_pct": round(float(r.prediction_error_percent or 0.0), 1),
            "performance_category": r.performance_category or "MEDIUM",
            "created_at": r.created_at.strftime("%b %d, %H:%M") if r.created_at else ""
        })

    category_breakdown = [
        {"name": "Low Latency (< 50ms)", "count": low_risk, "color": "#10b981"},
        {"name": "Medium Latency (50–500ms)", "count": med_risk, "color": "#f59e0b"},
        {"name": "High Latency (> 500ms)", "count": high_risk, "color": "#ef4444"}
    ]

    return {
        "summary": {
            "total_queries": total_queries,
            "executed_queries": executed_queries,
            "average_predicted_time_ms": round(avg_pred, 2),
            "average_actual_time_ms": round(avg_actual, 2),
            "average_prediction_error_percent": round(avg_error, 2),
            "high_cost_queries": high_risk
        },
        "latency_distribution": latency_distribution,
        "accuracy_trends": accuracy_trends,
        "slowest_queries": slowest_queries,
        "category_breakdown": category_breakdown
    }

@router.get("/metrics")
def get_model_metrics():
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

    # Append to dataset
    if csv_path.exists():
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
