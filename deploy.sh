#!/bin/bash

# ============================================================
# COSMIC Data Fusion - Quick Deployment Script
# ============================================================
# This script helps deploy the application quickly
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e  # Exit on error

ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

echo "🌌 COSMIC Data Fusion Deployment"
echo "================================="
echo "Environment: $ENVIRONMENT"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.example to .env and configure it:"
    echo "   cp .env.example .env"
    echo "   nano .env  # Edit with your values"
    exit 1
fi

# Production-specific checks
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔍 Running production checks..."
    
    # Check if required environment variables are set
    source .env
    
    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
        echo "❌ POSTGRES_PASSWORD not set properly in .env"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "generate_a_random_secret_key_here" ]; then
        echo "❌ SECRET_KEY not set properly in .env"
        echo "💡 Generate with: openssl rand -hex 32"
        exit 1
    fi
    
    COMPOSE_FILE="docker-compose.yml -f docker-compose.prod.yml"
    echo "✅ Production checks passed"
fi

# Build frontend
echo ""
echo "📦 Building frontend..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    npm run build
    cd ..
    echo "✅ Frontend built successfully"
else
    echo "⚠️  Frontend directory not found, skipping..."
fi

# Pull latest code (if in git repo)
if [ -d .git ]; then
    echo ""
    echo "📥 Pulling latest code..."
    git pull
fi

# Stop existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start containers
echo ""
echo "🚀 Starting containers..."
docker-compose -f $COMPOSE_FILE up -d --build

# Wait for database to be ready
echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo ""
echo "📊 Running database migrations..."
docker exec cosmic-data-fusion-app alembic upgrade head

# Check health
echo ""
echo "🏥 Checking application health..."
sleep 5

HEALTH_URL="http://localhost:8000/health"
if curl -f -s $HEALTH_URL > /dev/null; then
    echo "✅ Application is healthy!"
else
    echo "⚠️  Health check failed, but services might still be starting..."
fi

# Show running containers
echo ""
echo "📋 Running containers:"
docker-compose ps

# Show logs command
echo ""
echo "================================="
echo "✅ Deployment complete!"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   View app logs: docker-compose logs -f app"
echo "   Stop:          docker-compose down"
echo "   Restart:       docker-compose restart"
echo ""
echo "🌐 Endpoints:"
echo "   API:           http://localhost:8000"
echo "   API Docs:      http://localhost:8000/docs"
echo "   Health Check:  http://localhost:8000/health"
if [ -f "frontend/dist/index.html" ]; then
    echo "   Frontend:      http://localhost (via nginx)"
fi
echo ""
echo "🎉 Happy astronomical data hunting!"
