#!/bin/bash

echo "🚀 Starting VenturePulse..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env file and add your API key, then run this script again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Build and start
echo "🐳 Building Docker container..."
docker-compose build

echo ""
echo "🚀 Starting VenturePulse..."
docker-compose up -d

echo ""
echo "✅ VenturePulse is running!"
echo ""
echo "📊 Dashboard: http://localhost:8888"
echo "📁 Workspace: ./workspace"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
echo ""