# AutoTube - Secure YouTube Automation Pipeline

A complete, secure YouTube Shorts automation system with AI-powered content generation, video creation, and a modern web dashboard.

## 🔐 Security Improvements

This version includes critical security enhancements:

- **Strong Authentication**: All services require secure credentials (no defaults)
- **Encrypted Storage**: n8n encryption key required for credential storage
- **Database Security**: PostgreSQL with strong password authentication
- **API Protection**: Rate limiting, input validation, path traversal prevention
- **File Browser Security**: Restricted directory access, mandatory authentication
- **No Debug Info**: Production-mode error handling without information disclosure

## 📋 Prerequisites

- Docker & Docker Compose installed
- At least 8GB RAM available
- 20GB free disk space
- Python 3.11+ (for local testing)

## 🚀 Quick Start

### Step 1: Clone and Setup

```bash
cd /workspace
```

### Step 2: Generate Secure Credentials

Generate the required secure keys:

```bash
# Generate encryption key for n8n
openssl rand -hex 32

# Generate app secret key
openssl rand -hex 32

# Generate Redis password
openssl rand -hex 16
```

### Step 3: Create .env File

Copy the example and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your secure values:

```bash
# n8n Authentication
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=your_email@example.com
N8N_BASIC_AUTH_PASSWORD=YourStrongPassword123!

# Encryption Key (from openssl rand -hex 32)
N8N_ENCRYPTION_KEY=your_32_char_random_key_here

# PostgreSQL Database
POSTGRES_USER=n8n
POSTGRES_PASSWORD=YourSecureDBPassword456!
POSTGRES_DB=n8n

# File Browser
FILEBROWSER_USERNAME=admin
FILEBROWSER_PASSWORD=YourFileBrowserPassword789!

# Redis
REDIS_PASSWORD=YourRedisPassword!

# API Keys (get from respective providers)
GROQ_API_KEY=your_groq_api_key
HUGGINGFACE_TOKEN=your_huggingface_token

# Application
APP_SECRET_KEY=your_app_secret_key_from_openssl
FLASK_ENV=production
DEBUG_MODE=false
```

### Step 4: Start the Pipeline

Run the secure startup script:

```bash
./start-secure.sh
```

Or manually:

```bash
# Create directories
mkdir -p data/n8n data/ollama data/tts data/postgres data/redis data/filebrowser
mkdir -p videos scripts templates assets

# Pull images
docker-compose pull

# Build Python container
docker-compose build python

# Start all services
docker-compose up -d
```

## 📍 Access Points

Once running, access the services:

| Service | URL | Purpose |
|---------|-----|---------|
| **n8n Workflow Editor** | http://localhost:5678 | Visual automation builder |
| **Python Video API** | http://localhost:5001 | Video generation endpoint |
| **File Browser** | http://localhost:8080 | Manage videos & files |
| **Ollama AI** | http://localhost:11434 | Local AI models |
| **TTS Server** | http://localhost:5500 | Text-to-speech |
| **Web Dashboard** | Open `templates/dashboard.html` | Interactive UI |

## 🎬 Creating Your First Video

### Option 1: Using the Web Dashboard

1. Open `templates/dashboard.html` in your browser
2. Fill in the video details (topic, hook, content, CTA, title)
3. Click "Generate Video"
4. Wait for processing to complete
5. Download your video from the Recent Videos list

### Option 2: Using n8n Workflow

1. Open http://localhost:5678 and log in
2. Import the workflow from `autotube-complete.json`
3. Configure API credentials (Groq, etc.)
4. Trigger the workflow manually or on schedule
5. Videos will be saved to the `/videos` directory

### Option 3: Direct API Call

```bash
curl -X POST http://localhost:5001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "hook": "Did you know this amazing fact?",
    "content": "Point 1\nPoint 2\nPoint 3",
    "cta": "Follow for more!",
    "title": "Amazing Facts",
    "useAiImages": true
  }'
```

## 🛑 Stopping the Pipeline

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

## 📁 Directory Structure

```
/workspace/
├── docker-compose.yml      # Service configuration
├── Dockerfile.python       # Python API container
├── .env                    # Your secure credentials (DO NOT COMMIT)
├── .env.example            # Template for .env
├── start-secure.sh         # Secure startup script
├── video_api.py            # Secured Flask API
├── create_video.py         # Video generation logic
├── ai_generator.py         # AI image generation
├── autotube-complete.json  # n8n workflow template
├── templates/
│   └── dashboard.html      # Interactive web UI
├── videos/                 # Generated videos
├── scripts/                # Custom scripts
├── assets/                 # Media assets
└── data/                   # Persistent data
    ├── n8n/                # n8n database
    ├── ollama/             # AI models
    ├── postgres/           # PostgreSQL data
    └── redis/              # Redis cache
```

## 🔒 Security Best Practices

1. **Never commit `.env`** - It contains sensitive credentials
2. **Use strong passwords** - Minimum 16 characters, mix of types
3. **Rotate keys regularly** - Especially API keys and encryption keys
4. **Keep Docker updated** - Security patches are important
5. **Monitor logs** - Check for suspicious activity
6. **Restrict network access** - Use firewall rules if exposing publicly
7. **Backup regularly** - Export n8n workflows and backup data

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart python
```

### API not responding
```bash
# Check Python container
docker-compose logs python

# Test health endpoint
curl http://localhost:5001/health
```

### Permission errors
```bash
# Fix directory permissions
sudo chown -R $USER:$USER data/ videos/ scripts/
```

### Out of memory
```bash
# Limit container resources in docker-compose.yml
# See ollama service for example resource limits
```

## 📊 Features

- ✅ **AI-Powered Script Generation** - Using Groq/Llama models
- ✅ **AI Image Generation** - Pollinations.ai or HuggingFace Z-Image
- ✅ **Professional Video Creation** - MoviePy with transitions
- ✅ **Text-to-Speech** - OpenTTS integration
- ✅ **Interactive Dashboard** - Modern web UI
- ✅ **Rate Limiting** - API protection against abuse
- ✅ **Input Validation** - Prevents injection attacks
- ✅ **Path Security** - No directory traversal
- ✅ **Error Handling** - No information leakage
- ✅ **Persistent Storage** - PostgreSQL + Redis
- ✅ **File Management** - Secure file browser

## 🆘 Support

For issues:
1. Check the logs: `docker-compose logs`
2. Review `.env` configuration
3. Ensure ports 5678, 5001, 8080, 11434, 5500 are available
4. Verify Docker is running: `docker ps`

## 📝 License

MIT License - See LICENSE file for details

---

**Built with security first** 🔐
