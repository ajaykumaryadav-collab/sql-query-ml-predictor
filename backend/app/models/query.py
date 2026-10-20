from sqlalchemy import Column, Integer, String, Float, DateTime, Text, text
from ..database import Base

class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))
    postgres_estimated_cost = Column(Float)
    postgres_estimated_rows = Column(Float)
    ml_predicted_time_ms = Column(Float)
    actual_execution_time_ms = Column(Float)
    prediction_error_percent = Column(Float)
    performance_category = Column(String(50))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
