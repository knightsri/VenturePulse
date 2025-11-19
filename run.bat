@echo off
echo 🎯 Starting VenturePulse GUI...
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Copying from .env.example...
    copy .env.example .env
    echo 📝 Please edit .env and add your OPENROUTER_API_KEY
    echo.
    echo You can get an API key from https://openrouter.ai/keys
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    echo.
    echo Install Docker Desktop from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Build and start containers
echo 🔨 Building containers...
docker-compose build

echo.
echo 🚀 Starting services...
docker-compose up -d

echo.
echo ✅ VenturePulse is running!
echo.
echo 📱 Frontend: http://localhost:3000
echo 🔌 API:      http://localhost:4000
echo 📊 Redis:    localhost:6379
echo.
echo To view logs:  docker-compose logs -f
echo To stop:       docker-compose down
echo.
