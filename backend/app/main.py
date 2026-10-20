from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import query, dashboard, model
from .database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SQL Query ML Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(model.router, prefix="/api/model", tags=["model"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
