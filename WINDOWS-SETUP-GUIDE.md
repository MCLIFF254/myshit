# 🚀 Secure YouTube Automation Pipeline - Windows Setup Guide

## Prerequisites

Before running the automation, ensure you have:

1. **Docker Desktop for Windows** installed and running
   - Download: https://www.docker.com/products/docker-desktop/
   - Enable WSL 2 backend (recommended)
   
2. **Windows PowerShell** (built-in on Windows 10/11)
   - Run as Administrator for first-time setup

3. **Git for Windows** (optional, for version control)
   - Download: https://git-scm.com/download/win

---

## 🔐 Step 1: Generate Secure Environment

Open PowerShell in the project directory and run:

```powershell
# Set execution policy if needed (run once as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Generate secure .env file with cryptographic keys
.\setup-env.ps1
```

This script will:
- ✅ Generate cryptographically secure random keys
- ✅ Create a `.env` file with all required credentials
- ✅ Use Windows native crypto APIs (no OpenSSL needed)

> ⚠️ **IMPORTANT**: After generation, open the `.env` file and change these default passwords:
> - `N8N_BASIC_AUTH_PASSWORD`
> - `FILEBROWSER_PASS`

---

## 📁 Step 2: Prepare Directories

The startup script will automatically create all required directories:

```
data/
├── n8n/          # n8n workflows and config
├── ollama/       # AI model storage
├── tts/          # Text-to-speech cache
├── postgres/     # Database files
├── redis/        # Redis persistence
└── filebrowser/  # File uploads
logs/             # Application logs
```

---

## 🚦 Step 3: Start the Pipeline

Run the secure startup script:

```powershell
.\start-secure.ps1
```

This script will:
1. ✅ Verify Docker is running
2. ✅ Generate `.env` if missing
3. ✅ Create data directories
4. ✅ Set secure permissions on database folder
5. ✅ Pull latest Docker images
6. ✅ Build Python service
7. ✅ Start all containers
8. ✅ Wait for services to initialize
9. ✅ Check health of all services

---

## 🌐 Step 4: Access Your Services

Once started, access the services in your browser:

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| 🎬 **Dashboard** | http://localhost:5001 | No auth |
| ⚙️ **n8n** | http://localhost:5678 | admin / [your password] |
| 📊 **Grafana** | http://localhost:3000 | admin / [grafana password from .env] |
| 📈 **Prometheus** | http://localhost:9090 | No auth (internal) |
| 📁 **File Browser** | http://localhost:8080 | admin / [your password] |
| 🤖 **Ollama API** | http://localhost:11434 | Internal only |

---

## 🧪 Step 5: Verify Everything Works

### Check Container Status
```powershell
docker-compose ps
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f python
```

### Test the API
Open PowerShell and run:
```powershell
curl http://localhost:5001/health
```

Expected response:
```json
{"status": "healthy", "services": {...}}
```

### Import n8n Workflow
1. Go to http://localhost:5678
2. Login with your credentials
3. Click "Workflows" → "Import from File"
4. Select `autotube-complete.json` from the project root

---

## 🛑 How to Stop

### Stop Temporarily (Preserve Data)
```powershell
docker-compose down
```
Data is preserved in the `data/` folders.

### Stop and Remove All Data (Factory Reset)
```powershell
docker-compose down -v
Remove-Item -Recurse -Force data\
Remove-Item -Recurse -Force logs\
```
⚠️ This deletes all workflows, database records, and generated videos!

---

## 🔧 Troubleshooting

### Docker Not Running
```
❌ Error: Cannot connect to the Docker daemon
```
**Solution**: Start Docker Desktop and wait for it to show "Docker Desktop is running"

### Port Already in Use
```
❌ Error: Bind for 0.0.0.0:5678 failed: port is already allocated
```
**Solution**: 
1. Find the process: `netstat -ano | findstr :5678`
2. Kill it: `taskkill /PID <PID> /F`
3. Or change the port in `docker-compose.yml`

### Permission Denied on Data Folders
```
❌ Error: mkdir data/postgres: access denied
```
**Solution**: Run PowerShell as Administrator once, or manually create folders with full permissions.

### Services Not Starting
```powershell
# Check detailed logs
docker-compose logs python
docker-compose logs db

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 Monitoring Dashboard

Access Grafana at http://localhost:3000 to view:

- 📈 API Request Rate (requests/minute)
- ⏱️ Response Time P95 latency
- 🎬 Total Videos Created
- ❌ Failed Jobs counter
- 💾 Memory Usage tracking

**Pre-configured Dashboards:**
1. AutoTube Overview
2. System Resources
3. Error Tracking

---

## 🔒 Security Features Enabled

✅ **Network Isolation**: Internal services on private network  
✅ **Encrypted Database**: PostgreSQL with strong password  
✅ **Redis Authentication**: Password-protected cache  
✅ **Rate Limiting**: 10 requests/minute per IP  
✅ **Input Validation**: Sanitized all user inputs  
✅ **Structured Logging**: JSON logs with no sensitive data  
✅ **Health Checks**: Automatic container monitoring  
✅ **No Default Passwords**: Cryptographically generated keys  

---

## 📝 Next Steps After Setup

1. **Customize Passwords**: Edit `.env` with your own secure passwords
2. **Configure n8n**: Set up YouTube API credentials in n8n
3. **Download Models**: Pull Ollama models (`ollama pull llama2`)
4. **Test Workflow**: Create a test video through the dashboard
5. **Schedule Jobs**: Set up cron triggers in n8n for automation

---

## 🆘 Need Help?

Check the logs:
```powershell
docker-compose logs -f
```

Run tests:
```powershell
pip install pytest requests
pytest tests/test_api.py -v
```

View documentation:
- API Docs: http://localhost:5001/docs
- n8n Docs: https://docs.n8n.io

---

**🎉 You're all set! Your secure YouTube automation pipeline is ready to run!**
