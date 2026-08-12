#!/bin/bash

# ===================================
# AutoTube - Secure Startup Script
# ===================================
# This script sets up and runs the secure YouTube automation pipeline

set -e

echo "🚀 AutoTube - Secure YouTube Automation Pipeline"
echo "================================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "📝 Please create a .env file with your secure credentials:"
    echo ""
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your secure passwords and API keys"
    echo ""
    echo "Required settings in .env:"
    echo "  - N8N_BASIC_AUTH_USER (your email)"
    echo "  - N8N_BASIC_AUTH_PASSWORD (strong password)"
    echo "  - N8N_ENCRYPTION_KEY (generate with: openssl rand -hex 32)"
    echo "  - DB_PASSWORD (strong database password)"
    echo "  - REDIS_PASSWORD (Redis authentication)"
    echo "  - FILEBROWSER_USER (file browser username)"
    echo "  - FILEBROWSER_PASSWORD (file browser password)"
    echo "  - GRAFANA_USER (monitoring username)"
    echo "  - GRAFANA_PASSWORD (monitoring password)"
    echo "  - APP_SECRET_KEY (generate with: openssl rand -hex 32)"
    echo ""
    exit 1
fi

# Check for placeholder values in .env
echo "🔒 Checking security configuration..."
if grep -q "YOUR_" .env || grep -q "your_" .env || grep -q "change-me" .env; then
    echo "⚠️  WARNING: Placeholder values detected in .env file!"
    echo ""
    echo "Please replace all placeholder values in .env before running:"
    echo "  - YOUR_STRONG_PASSWORD_HERE"
    echo "  - YOUR_32_CHAR_RANDOM_KEY_HERE"
    echo "  - YOUR_SECURE_DB_PASSWORD_HERE"
    echo "  - YOUR_SECURE_FILEBROWSER_PASSWORD"
    echo "  - YOUR_APP_SECRET_KEY_GENERATED_WITH_OPENSSL_RAND_HEX_32"
    echo ""
    read -p "Do you want to continue anyway? (not recommended) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/n8n data/ollama data/tts data/postgres data/redis data/filebrowser
mkdir -p data/videos data/prometheus data/grafana data/loki logs
mkdir -p videos scripts templates assets

# Set secure permissions on .env file
chmod 600 .env

# Pull latest images
echo "🐳 Pulling latest Docker images..."
docker-compose pull

# Build Python API container
echo "🔨 Building Python API container..."
docker-compose build python

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

echo ""
echo "✅ AutoTube is now running!"
echo ""
echo "📍 Access Points:"
echo "   • n8n Workflow Editor:   http://localhost:5678"
echo "   • Python Video API:      http://localhost:5001"
echo "   • Interactive Dashboard: http://localhost:5001/"
echo "   • File Browser:          http://localhost:8080"
echo "   • Grafana Monitoring:    http://localhost:3000"
echo "   • Prometheus Metrics:    http://localhost:9090"
echo "   • Ollama AI:             http://localhost:11434"
echo ""
echo "📊 Features Enabled:"
echo "   ✓ Network isolation (internal/private networks)"
echo "   ✓ Redis-backed rate limiting"
echo "   ✓ Prometheus metrics collection"
echo "   ✓ Grafana dashboards"
echo "   ✓ Centralized logging with Loki"
echo "   ✓ Structured application logging"
echo "   ✓ Health checks on all services"
echo ""
echo "🔐 Security Reminders:"
echo "   • Change default passwords in .env"
echo "   • Never commit .env to version control"
echo "   • Use strong, unique passwords"
echo "   • Keep your API keys secret"
echo ""
echo "📚 Next Steps:"
echo "   1. Open http://localhost:5678 and log in with your credentials"
echo "   2. Import the workflow from autotube-complete.json"
echo "   3. Configure your API credentials in n8n"
echo "   4. Open http://localhost:3000 for monitoring dashboards"
echo "   5. Run tests: pytest tests/ -v"
echo ""
echo "🛑 To stop: docker-compose down"
echo ""

