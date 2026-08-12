# Secure Key Generator for Windows PowerShell
# Run this script to automatically create your .env file with secure keys

Write-Host "Generating secure cryptographic keys..." -ForegroundColor Cyan

# Function to generate secure random string
function Get-SecureKey {
    param (
        [int]$Length = 32
    )
    $bytes = New-Object byte[] ($Length)
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($bytes)
    return [System.Convert]::ToBase64String($bytes).Replace('+', '-').Replace('/', '_').Substring(0, $Length)
}

# Generate Keys
$N8N_KEY = Get-SecureKey -Length 64
$APP_KEY = Get-SecureKey -Length 64
$REDIS_PASS = Get-SecureKey -Length 32
$DB_PASS = Get-SecureKey -Length 32
$GRAFANA_PASS = Get-SecureKey -Length 32

# Define Content
$content = @"
# ==========================================
# SECURE ENVIRONMENT CONFIGURATION
# Generated automatically on $(Get-Date -Format "yyyy-MM-dd")
# ==========================================

# n8n Configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=ChangeMeInEnvFile!
N8N_ENCRYPTION_KEY=$N8N_KEY
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
WEBHOOK_URL=http://localhost:5678/

# Application Security
APP_SECRET_KEY=$APP_KEY
APP_DEBUG=false
LOG_LEVEL=INFO

# Database Configuration (PostgreSQL)
POSTGRES_DB=autotube_db
POSTGRES_USER=autotube_user
POSTGRES_PASSWORD=$DB_PASS
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://autotube_user:$DB_PASS@db:5432/autotube_db

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASS
REDIS_URL=redis://:$REDIS_PASS@redis:6379/0

# Ollama Configuration
OLLAMA_HOST=0.0.0.0
OLLAMA_PORT=11434

# Grafana Configuration
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_PASS
GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource

# File Browser
FILEBROWSER_USER=admin
FILEBROWSER_PASS=ChangeMeInEnvFile!

# Timezone
TIMEZONE=Europe/London

# Docker Networks
INTERNAL_NETWORK=internal-net
PUBLIC_NETWORK=public-net
"@

# Write to file
Set-Content -Path ".env" -Value $content

Write-Host "✅ Successfully created .env file with secure keys!" -ForegroundColor Green
Write-Host "⚠️  IMPORTANT: Please open the .env file and change the default passwords:" -ForegroundColor Yellow
Write-Host "   - N8N_BASIC_AUTH_PASSWORD"
Write-Host "   - FILEBROWSER_PASS"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Edit .env to set your custom passwords"
Write-Host "2. Run: .\start-secure.ps1"
