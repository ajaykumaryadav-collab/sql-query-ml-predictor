@echo off
echo ========================================================
echo   Starting SQL Query ML Predictor Local Stack
echo ========================================================

:: Check Docker daemon
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Docker is not running. Launching Docker Desktop...
    start "" "C:\Users\%USERNAME%\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe"
    echo Waiting for Docker engine to become ready...
    :wait_docker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if %ERRORLEVEL% NEQ 0 goto wait_docker
)

echo [*] Starting containers (PostgreSQL, FastAPI Backend, React Frontend)...
docker compose up -d

echo.
echo ========================================================
echo   Services are running locally!
echo   - Frontend UI:    http://localhost:5173
echo   - Backend API:    http://localhost:8000
echo   - API Swagger UI: http://localhost:8000/docs
echo   - PostgreSQL:     localhost:5432 (db: query_db)
echo ========================================================
echo.

:: Open default browser to Frontend
start http://localhost:5173
