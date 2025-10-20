@echo off
echo 🚀 Starting VenturePulse...
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  No .env file found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo 📝 Please edit .env file and add your API key, then run this script again.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Build and start
echo 🐳 Building Docker container...
docker-compose build

echo.
echo 🚀 Starting VenturePulse...
docker-compose up -d

echo.
echo ✅ VenturePulse is running!
echo.
echo 📊 Dashboard: http://localhost:8888
echo 📁 Workspace: .\workspace
echo.
echo To stop: docker-compose down
echo To view logs: docker-compose logs -f
echo.
pause