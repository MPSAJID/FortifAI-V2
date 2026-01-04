@echo off
REM FortifAI Development Server Startup Script (Windows)

echo ==========================================
echo FortifAI Development Environment
echo ==========================================

REM Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker first.
    exit /b 1
)

REM Start infrastructure services
echo Starting database and cache services...
cd infrastructure\docker
docker-compose up -d postgres redis

REM Wait for services
echo Waiting for services to be ready...
timeout /t 10 /nobreak > nul

REM Run database migrations
echo Running database setup...
cd ..\..
python scripts\setup_database.py

echo.
echo ==========================================
echo To start services manually:
echo.
echo   API:
echo     cd backend\api
echo     uvicorn main:app --reload --port 8000
echo.
echo   ML Engine:
echo     cd backend\ml-engine
echo     python main.py
echo.
echo   Frontend:
echo     cd frontend\dashboard
echo     npm run dev
echo.
echo ==========================================
echo.
echo Services will be available at:
echo   - API:      http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Frontend: http://localhost:3000
echo ==========================================

pause
