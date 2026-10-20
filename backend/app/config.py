from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/query_db"
    
    # Performance classification thresholds in ms
    PERF_THRESH_LOW_MS: int = 100
    PERF_THRESH_MEDIUM_MS: int = 500

    class Config:
        env_file = ".env"

settings = Settings()
