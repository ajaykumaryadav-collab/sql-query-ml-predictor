from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, engine as db_engine
from ..schemas.query import (
    QueryAnalyzeRequest, 
    QueryAnalyzeResponse, 
    QueryExplainResponse, 
    QueryExecutionResponse, 
    QueryHistorySchema,
    SimulateIndexRequest,
    SimulateIndexResponse,
    RewriteQueryRequest,
    RewriteQueryResponse
)
from ..services.sql_validator import validate_sql, SQLValidationError
from ..services.explain_service import run_explain
from ..services.feature_extractor import extract_features_from_plan
from ..services.prediction_service import prediction_service
from ..services.optimizer_service import optimizer_service
from ..models.query import QueryHistory
from ..config import settings
from typing import List

router = APIRouter()

def get_perf_category(time_ms: float) -> str:
    if time_ms < settings.PERF_THRESH_LOW_MS:
        return "LOW"
    elif time_ms < settings.PERF_THRESH_MEDIUM_MS:
        return "MEDIUM"
    return "HIGH"

@router.post("/analyze", response_model=QueryAnalyzeResponse)
def analyze_query(req: QueryAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        validate_sql(req.query)
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        plan = run_explain(db, req.query, analyze=False)
        features = extract_features_from_plan(plan)
        predicted_time = prediction_service.predict(features)
        
        # Save to history
        history = QueryHistory(
            query_text=req.query,
            query_type="ANALYZE",
            postgres_estimated_cost=features.get("total_cost"),
            postgres_estimated_rows=features.get("plan_rows"),
            ml_predicted_time_ms=predicted_time,
            performance_category=get_perf_category(predicted_time)
        )
        db.add(history)
        db.commit()
        
        optimization = optimizer_service.analyze(req.query, plan, features, predicted_time)

        return QueryAnalyzeResponse(
            query=req.query,
            postgres_estimated_cost=features.get("total_cost", 0.0),
            postgres_estimated_rows=features.get("plan_rows", 0.0),
            features=features,
            predicted_execution_time_ms=predicted_time,
            performance_category=get_perf_category(predicted_time),
            optimization=optimization
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/explain", response_model=QueryExplainResponse)
def explain_query(req: QueryAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        validate_sql(req.query)
        plan = run_explain(db, req.query, analyze=False)
        features = extract_features_from_plan(plan)
        
        return QueryExplainResponse(
            raw_plan=plan,
            parsed_plan=plan,
            features=features
        )
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-execution", response_model=QueryExecutionResponse)
def execute_query(req: QueryAnalyzeRequest, db: Session = Depends(get_db)):
    try:
        validate_sql(req.query)
        plan = run_explain(db, req.query, analyze=True)
        features = extract_features_from_plan(plan)
        
        predicted_time = prediction_service.predict(features)
        
        # Actual execution stats
        actual_time = plan.get("Actual Total Time", 0.0)
        actual_rows = plan.get("Actual Rows", 0.0)
        planning_time = plan.get("Planning Time", 0.0) # wait, postgres format JSON might have this at root if we get it
        
        if actual_time > 0:
            # For microsecond queries (< 1.0 ms), normalize denominator by 1.0 ms to prevent 
            # 0.02 ms differences from artificially blowing up percentage error
            diff = abs(predicted_time - actual_time)
            effective_base = max(actual_time, 1.0)
            error_pct = round((diff / effective_base) * 100.0, 2)
        else:
            error_pct = 0.0
            
        history = QueryHistory(
            query_text=req.query,
            query_type="EXPLAIN_ANALYZE",
            postgres_estimated_cost=features.get("total_cost"),
            postgres_estimated_rows=features.get("plan_rows"),
            ml_predicted_time_ms=predicted_time,
            actual_execution_time_ms=actual_time,
            prediction_error_percent=error_pct,
            performance_category=get_perf_category(actual_time)
        )
        db.add(history)
        db.commit()
        
        optimization = optimizer_service.analyze(req.query, plan, features, actual_time)

        return QueryExecutionResponse(
            actual_execution_time_ms=actual_time,
            actual_rows=actual_rows,
            planning_time_ms=planning_time,
            plan=plan,
            ml_prediction_ms=predicted_time,
            prediction_error_percent=error_pct,
            features=features,
            postgres_estimated_cost=features.get("total_cost", 0.0),
            postgres_estimated_rows=features.get("plan_rows", 0.0),
            performance_category=get_perf_category(actual_time),
            optimization=optimization
        )
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[QueryHistorySchema])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit).all()

@router.get("/history/{id}", response_model=QueryHistorySchema)
def get_history_by_id(id: int, db: Session = Depends(get_db)):
    h = db.query(QueryHistory).filter(QueryHistory.id == id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Not found")
    return h

@router.post("/simulate-index", response_model=SimulateIndexResponse)
def simulate_index_speedup(req: SimulateIndexRequest, db: Session = Depends(get_db)):
    try:
        validate_sql(req.query)
        result = optimizer_service.simulate_index(req.query, req.index_sql, db_engine)
        return SimulateIndexResponse(**result)
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index simulation failed: {str(e)}")

@router.post("/rewrite", response_model=RewriteQueryResponse)
def rewrite_query(req: RewriteQueryRequest, db: Session = Depends(get_db)):
    try:
        validate_sql(req.query)
        result = optimizer_service.rewrite_query(req.query, db_engine)
        return RewriteQueryResponse(**result)
    except SQLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query rewrite failed: {str(e)}")
