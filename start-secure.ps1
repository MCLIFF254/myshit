# Secure Startup Script for Windows PowerShell
# This script prepares directories and starts the Docker containers safely

Write-Host "🚀 Starting Secure YouTube Automation Pipeline..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Generating secure keys..." -ForegroundColor Yellow
    & .\setup-env.ps1
}

# Create required directories with proper permissions
Write-Host "📁 Creating data directories..." -ForegroundColor Cyan
$directories = @(
    "data/n8n",
    "data/ollama",
    "data/tts",
    "data/postgres",
    "data/redis",
    "data/filebrowser/uploads",
    "data/filebrowser/config",
    "logs"
)

foreach ($dir in $directories) {
    if (-Not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor Gray
    }
}

# Set restrictive permissions on sensitive directories
Write-Host "🔒 Setting directory permissions..." -ForegroundColor Cyan
$acl = Get-Acl "data/postgres"
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "ReadAndExecute", "Deny")
$acl.AddAccessRule($rule)
Set-Acl "data/postgres" $acl

# Pull latest images
Write-Host "📥 Pulling latest Docker images..." -ForegroundColor Cyan
docker-compose pull

# Build Python service
Write-Host "🔨 Building Python service..." -ForegroundColor Cyan
docker-compose build python

# Start all services
Write-Host "🚦 Starting services..." -ForegroundColor Cyan
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check health of services
Write-Host "🏥 Checking service health..." -ForegroundColor Cyan
$services = @("n8n", "db", "redis", "python", "grafana", "prometheus")
$allHealthy = $true

foreach ($service in $services) {
    try {
        $status = docker-compose ps --format json $service | ConvertFrom-Json
        if ($status.State -eq "running") {
            Write-Host "   ✅ $service is running" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $service status: $($status.State)" -ForegroundColor Yellow
            $allHealthy = $false
        }
    } catch {
        Write-Host "   ❌ $service check failed" -ForegroundColor Red
        $allHealthy = $false
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🎉 PIPELINE STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Access your services:" -ForegroundColor White
Write-Host "   🎬 Dashboard:      http://localhost:5001" -ForegroundColor White
Write-Host "   ⚙️  n8n Workflow:   http://localhost:5678" -ForegroundColor White
Write-Host "   📊 Grafana:        http://localhost:3000 (admin/your_grafana_password)" -ForegroundColor White
Write-Host "   📈 Prometheus:     http://localhost:9090" -ForegroundColor White
Write-Host "   📁 File Browser:   http://localhost:8080" -ForegroundColor White
Write-Host "   🤖 Ollama API:     http://localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop the pipeline:" -ForegroundColor Yellow
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "🗑️  To stop and remove all data:" -ForegroundColor Red
Write-Host "   docker-compose down -v" -ForegroundColor Gray
Write-Host ""

if (-Not $allHealthy) {
    Write-Host "⚠️  Some services may not be fully ready yet. Check logs with:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs -f" -ForegroundColor Gray
}
