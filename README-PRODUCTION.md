# 🚀 AutoTube - Production-Ready YouTube Automation Pipeline

A secure, observable, and scalable YouTube Shorts automation system with complete monitoring, testing, and CI/CD capabilities.

## 🔐 Security Features

- **Network Isolation**: Services separated into internal and public networks
- **Authentication**: All services require strong credentials (no defaults)
- **Rate Limiting**: Redis-backed rate limiting to prevent abuse
- **Input Validation**: Comprehensive sanitization and validation on all endpoints
- **Secrets Management**: Environment variables with placeholder validation
- **Encrypted Storage**: PostgreSQL with encryption for sensitive data

## 📊 Observability Stack

- **Prometheus**: Metrics collection from all services
- **Grafana**: Real-time dashboards for monitoring
- **Loki**: Centralized log aggregation
- **Structured Logging**: JSON-formatted logs with request tracing
- **Health Checks**: Automated health monitoring for all containers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Public Network                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   n8n    │  │ Python   │  │ Grafana  │  │ File     │    │
│  │  :5678   │  │   API    │  │  :3000   │  │ Browser  │    │
│  │          │  │  :5001   │  │          │  │  :8080   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼───────────┘
        │             │             │             │
┌───────┼─────────────┼─────────────┼─────────────┼───────────┐
│       │    Internal Network (Isolated)          │           │
│  ┌────▼─────┐  ┌────▼─────┐  ┌────▼─────┐  ┌───▼───────┐   │
│  │PostgreSQL│  │  Redis   │  │  Ollama  │  │Prometheus │   │
│  │  :5432   │  │  :6379   │  │ :11434   │  │  :9090    │   │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Loki Logging                       │   │
│  │                   :3100                              │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Git (for version control)
- At least 8GB RAM recommended

### Step 1: Clone and Setup

```bash
cd /workspace
cp .env.example .env
```

### Step 2: Generate Secure Credentials

```bash
# Generate encryption keys
openssl rand -hex 32  # For N8N_ENCRYPTION_KEY
openssl rand -hex 32  # For APP_SECRET_KEY
openssl rand -hex 16  # For REDIS_PASSWORD
openssl rand -hex 16  # For DB_PASSWORD
openssl rand -hex 16  # For GRAFANA_PASSWORD
```

### Step 3: Configure .env File

Edit `.env` with your generated credentials:

```env
N8N_BASIC_AUTH_USER=your@email.com
N8N_BASIC_AUTH_PASSWORD=YourStrongPassword123!
N8N_ENCRYPTION_KEY=<32-char-key-from-openssl>

DB_USER=n8n
DB_PASSWORD=<16-char-password>
DB_NAME=n8n

REDIS_PASSWORD=<16-char-password>

FILEBROWSER_USER=admin
FILEBROWSER_PASSWORD=YourFileBrowserPass!

GRAFANA_USER=admin
GRAFANA_PASSWORD=<16-char-password>

APP_SECRET_KEY=<32-char-key-from-openssl>
TIMEZONE=UTC
```

### Step 4: Start the Pipeline

```bash
chmod +x start-secure.sh
./start-secure.sh
```

## 📍 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| n8n Workflow Editor | http://localhost:5678 | Your N8N_BASIC_AUTH_* |
| Video API | http://localhost:5001 | N/A |
| Interactive Dashboard | http://localhost:5001/ | N/A |
| File Browser | http://localhost:8080 | FILEBROWSER_* |
| Grafana Monitoring | http://localhost:3000 | GRAFANA_* |
| Prometheus Metrics | http://localhost:9090 | N/A |
| Ollama AI | http://localhost:11434 | N/A |

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov requests

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=video_api --cov-report=html
```

## 📊 Monitoring Dashboards

### Grafana Dashboards

Access Grafana at http://localhost:3000 to view:

1. **API Request Rate** - Real-time request throughput
2. **Response Time** - P95 latency tracking
3. **Video Creation Stats** - Success/failure rates
4. **Resource Usage** - Memory and CPU consumption
5. **Error Rates** - Application error tracking

### Prometheus Metrics

Key metrics available at http://localhost:5001/metrics:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `videos_created_total` - Successful video creations
- `video_creation_errors_total` - Failed video creations

## 🔧 Configuration

### Dynamic Configuration Endpoints

The API supports runtime configuration changes:

```bash
# Get current configuration
curl http://localhost:5001/api/config

# Update voice model
curl -X POST http://localhost:5001/api/config/voice \
  -H "Content-Type: application/json" \
  -d '{"model": "en_US-lessac-medium"}'

# Update video style
curl -X POST http://localhost:5001/api/config/style \
  -H "Content-Type: application/json" \
  -d '{"style": "modern", "duration": 60}'
```

### Resource Management

Redis-based job queuing serializes video rendering:

```python
# Jobs are automatically queued in Redis
# Only one video renders at a time to prevent CPU overload
# Queue status available at /api/queue/status
```

## 🛠️ Troubleshooting

### Check Service Health

```bash
docker-compose ps
docker-compose logs python
docker-compose logs grafana
```

### View Logs

```bash
# Application logs
tail -f logs/app.log

# Grafana logs
docker-compose logs grafana

# Loki query (in Grafana Explore tab)
{container="autotube-api"} |= "ERROR"
```

### Restart Services

```bash
# Restart specific service
docker-compose restart python

# Restart all
docker-compose restart

# Full rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔄 CI/CD Pipeline

GitHub Actions workflow included:

1. **Test Stage**: Runs pytest on every push/PR
2. **Build Stage**: Builds Docker images
3. **Security Scan**: Scans for vulnerabilities
4. **Deploy Stage**: Deploys to production (main branch only)

Enable in your repository settings under Actions.

## 📁 Project Structure

```
/workspace
├── docker-compose.yml      # Service orchestration
├── Dockerfile.python       # Python API container
├── video_api.py           # Flask API with metrics
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── start-secure.sh       # Startup script
├── templates/
│   └── dashboard.html    # Interactive UI
├── monitoring/
│   ├── prometheus.yml    # Metrics config
│   ├── loki-config.yaml  # Logging config
│   └── grafana/
│       ├── datasources/  # Data source configs
│       └── dashboards/   # Dashboard JSON files
├── tests/
│   └── test_api.py       # Pytest test suite
├── .github/
│   └── workflows/
│       └── ci-cd.yml     # CI/CD pipeline
└── data/                 # Persistent volumes
    ├── postgres/
    ├── redis/
    ├── n8n/
    ├── videos/
    ├── prometheus/
    ├── grafana/
    └── loki/
```

## 🔒 Security Best Practices

1. **Never commit .env** - Added to .gitignore
2. **Rotate credentials regularly** - Especially API keys
3. **Update images monthly** - `docker-compose pull`
4. **Monitor logs daily** - Check Grafana dashboards
5. **Backup data weekly** - Copy data/ directory
6. **Use HTTPS in production** - Add reverse proxy (nginx/traefik)

## 🎯 Next Steps

1. **Import n8n Workflow**: Open n8n and import `autotube-complete.json`
2. **Configure API Keys**: Add Groq, HuggingFace tokens in n8n credentials
3. **Pull AI Models**: `docker exec autotube-ollama ollama pull llama2`
4. **Create First Video**: Use the dashboard at http://localhost:5001/
5. **Set Up Alerts**: Configure Grafana alerts for errors/latency

## 📞 Support

For issues or questions:
- Check logs: `docker-compose logs <service>`
- Review metrics: http://localhost:3000
- Test API: `curl http://localhost:5001/health`

---

**Built with security, observability, and scalability in mind.** 🚀
