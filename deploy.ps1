# ============================================================
# COSMIC Data Fusion - Quick Deployment Script (PowerShell)
# ============================================================
# This script helps deploy the application quickly on Windows
# Usage: .\deploy.ps1 [environment]
# Example: .\deploy.ps1 production

param(
    [string]$Environment = "development"
)

$ErrorActionPreference = "Stop"

Write-Host "🌌 COSMIC Data Fusion Deployment" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "📝 Please copy .env.example to .env and configure it:" -ForegroundColor Yellow
    Write-Host "   Copy-Item .env.example .env"
    Write-Host "   notepad .env  # Edit with your values"
    exit 1
}

$ComposeFiles = "docker-compose.yml"

# Production-specific checks
if ($Environment -eq "production") {
    Write-Host "🔍 Running production checks..." -ForegroundColor Yellow
    
    # Load .env file
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value)
        }
    }
    
    $postgresPassword = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")
    $secretKey = [Environment]::GetEnvironmentVariable("SECRET_KEY")
    
    if ([string]::IsNullOrEmpty($postgresPassword) -or $postgresPassword -eq "your_secure_password_here") {
        Write-Host "❌ POSTGRES_PASSWORD not set properly in .env" -ForegroundColor Red
        exit 1
    }
    
    if ([string]::IsNullOrEmpty($secretKey) -or $secretKey -eq "generate_a_random_secret_key_here") {
        Write-Host "❌ SECRET_KEY not set properly in .env" -ForegroundColor Red
        Write-Host "💡 Generate with PowerShell:" -ForegroundColor Yellow
        Write-Host '   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | % {[char]$_})'
        exit 1
    }
    
    $ComposeFiles = "docker-compose.yml -f docker-compose.prod.yml"
    Write-Host "✅ Production checks passed" -ForegroundColor Green
}

# Build frontend
Write-Host ""
Write-Host "📦 Building frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Push-Location frontend
    npm install
    npm run build
    Pop-Location
    Write-Host "✅ Frontend built successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend directory not found, skipping..." -ForegroundColor Yellow
}

# Pull latest code (if in git repo)
if (Test-Path .git) {
    Write-Host ""
    Write-Host "📥 Pulling latest code..." -ForegroundColor Yellow
    git pull
}

# Stop existing containers
Write-Host ""
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Build and start containers
Write-Host ""
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
Invoke-Expression "docker-compose $ComposeFiles up -d --build"

# Wait for database to be ready
Write-Host ""
Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run database migrations
Write-Host ""
Write-Host "📊 Running database migrations..." -ForegroundColor Yellow
docker exec cosmic-data-fusion-app alembic upgrade head

# Check health
Write-Host ""
Write-Host "🏥 Checking application health..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$HealthUrl = "http://localhost:8000/health"
try {
    $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Application is healthy!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Health check failed, but services might still be starting..." -ForegroundColor Yellow
}

# Show running containers
Write-Host ""
Write-Host "📋 Running containers:" -ForegroundColor Yellow
docker-compose ps

# Show useful commands
Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Useful commands:" -ForegroundColor Yellow
Write-Host "   View logs:     docker-compose logs -f"
Write-Host "   View app logs: docker-compose logs -f app"
Write-Host "   Stop:          docker-compose down"
Write-Host "   Restart:       docker-compose restart"
Write-Host ""
Write-Host "🌐 Endpoints:" -ForegroundColor Yellow
Write-Host "   API:           http://localhost:8000"
Write-Host "   API Docs:      http://localhost:8000/docs"
Write-Host "   Health Check:  http://localhost:8000/health"
if (Test-Path "frontend/dist/index.html") {
    Write-Host "   Frontend:      http://localhost (via nginx)"
}
Write-Host ""
Write-Host "🎉 Happy astronomical data hunting!" -ForegroundColor Cyan
