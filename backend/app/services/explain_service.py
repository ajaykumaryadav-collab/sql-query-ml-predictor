from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging

logger = logging.getLogger(__name__)

def run_explain(db: Session, query: str, analyze: bool = False):
    """
    Executes EXPLAIN on the given query.
    If analyze is True, executes EXPLAIN ANALYZE BUFFERS.
    Returns the parsed JSON plan.
    """
    try:
        # Wrap the query in EXPLAIN
        if analyze:
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        else:
            explain_query = f"EXPLAIN (FORMAT JSON) {query}"
        
        result = db.execute(text(explain_query))
        plan_json = result.scalar()
        
        # Postgres returns a list containing one dictionary representing the plan
        if isinstance(plan_json, str):
            plan_data = json.loads(plan_json)
        else:
            plan_data = plan_json
            
        if plan_data and len(plan_data) > 0:
            return plan_data[0].get("Plan", {})
        return {}
        
    except Exception as e:
        logger.error(f"Error executing EXPLAIN: {str(e)}")
        raise e
