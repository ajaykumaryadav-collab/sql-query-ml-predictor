from pydantic import BaseModel
from typing import Optional, Any, Dict, List

class QueryAnalyzeRequest(BaseModel):
    query: str

class QueryAnalyzeResponse(BaseModel):
    query: str
    postgres_estimated_cost: float
    postgres_estimated_rows: float
    features: Dict[str, float]
    predicted_execution_time_ms: float
    performance_category: str
    optimization: Optional[Dict[str, Any]] = None

class QueryExplainResponse(BaseModel):
    raw_plan: Any
    parsed_plan: Any
    features: Dict[str, float]

class QueryExecutionResponse(BaseModel):
    actual_execution_time_ms: float
    actual_rows: float
    planning_time_ms: float
    plan: Any
    ml_prediction_ms: float
    prediction_error_percent: float
    features: Dict[str, float]
    postgres_estimated_cost: float
    postgres_estimated_rows: float
    performance_category: str
    optimization: Optional[Dict[str, Any]] = None

class QueryHistorySchema(BaseModel):
    id: int
    query_text: str
    query_type: Optional[str]
    postgres_estimated_cost: Optional[float]
    postgres_estimated_rows: Optional[float]
    ml_predicted_time_ms: Optional[float]
    actual_execution_time_ms: Optional[float]
    prediction_error_percent: Optional[float]
    performance_category: Optional[str]
    created_at: Any

    class Config:
        from_attributes = True

class SimulateIndexRequest(BaseModel):
    query: str
    index_sql: str

class SimulateIndexResponse(BaseModel):
    index_sql: str
    before_time_ms: float
    after_time_ms: float
    before_cost: float
    after_cost: float
    before_rows: float
    after_rows: float
    speedup_ratio: str
    time_saved_ms: float
    percentage_drop: float
    before_node_type: str
    after_node_type: str
    before_plan: Any
    after_plan: Any
    status: str

class RewriteQueryRequest(BaseModel):
    query: str

class RewriteImprovement(BaseModel):
    rule: str
    impact: str
    description: str

class RewriteQueryResponse(BaseModel):
    original_query: str
    optimized_query: str
    improvements: List[RewriteImprovement]
    has_changes: bool
    original_cost: Optional[float] = None
    optimized_cost: Optional[float] = None
    estimated_speedup: Optional[str] = None
