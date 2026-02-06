# 🦙 LaTeX OCR API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Professional REST API for extracting LaTeX code from images of mathematical equations using **Llama Vision** (via Ollama).

## ✨ Features

- 🔍 **OCR for Mathematical Equations** - Extract LaTeX from images
- 🔄 **Automatic Fallback** - Multiple model support with automatic failover
- ✅ **LaTeX Validation** - Automatic cleaning and validation
- 📦 **Batch Processing** - Process multiple images at once (up to 10)
- 🔐 **API Key Authentication** - Secure access control
- 🚦 **Rate Limiting** - Configurable request limits
- 📊 **Metadata & Metrics** - Processing time and model tracking
- 🐳 **Docker Ready** - Full containerization with Ollama included
- ☁️ **Azure Ready** - Prepared for cloud deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- Llama Vision model pulled: \`ollama pull llava:7b\`

### Installation

1. **Clone the repository**
\`\`\`bash
git clone <your-repo-url>
cd latex-ocr-api
\`\`\`

2. **Create virtual environment**
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
\`\`\`

3. **Install dependencies**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

4. **Setup environment variables**
\`\`\`bash
cp .env.example .env
nano .env  # Edit and set your SECRET_KEY
\`\`\`

5. **Start Ollama**
\`\`\`bash
ollama serve
\`\`\`

6. **Run the API**
\`\`\`bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

7. **Access documentation**
\`\`\`
http://localhost:8000/docs
\`\`\`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

\`\`\`bash
# Copy environment file
cp .env.example .env

# Edit .env and set SECRET_KEY
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
\`\`\`

### Using Docker directly

\`\`\`bash
# Build image
docker build -t latex-ocr-api:latest .

# Run container
docker run -d \\
  --name latex-ocr-api \\
  -p 8000:8000 \\
  -e SECRET_KEY=your-secret-key \\
  -e OLLAMA_MODEL=llava:7b \\
  -v ollama-data:/root/.ollama \\
  latex-ocr-api:latest
\`\`\`

## 📖 API Documentation

### Authentication

All endpoints (except \`/health\`) require authentication via Bearer token:

\`\`\`bash
Authorization: Bearer your-api-key-here
\`\`\`

**Default test API keys:**
- \`test-key-123\` - Free tier (10 req/min)
- \`dev-key-456\` - Premium tier (100 req/min)

### Endpoints

#### Health Check
\`\`\`http
GET /api/v1/health
\`\`\`

**Response:**
\`\`\`json
{
  "status": "healthy",
  "ollama_connected": true,
  "ollama_model": "llava:7b",
  "version": "1.0.0",
  "uptime_seconds": 3600.5
}
\`\`\`

#### Single Image OCR
\`\`\`http
POST /api/v1/ocr/latex
Content-Type: multipart/form-data
Authorization: Bearer your-api-key

file: <image-file>
return_metadata: true
validate_latex: true
use_fallback: true
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "latex": "\\\\frac{a}{b} = c",
  "latex_rendered": "\\\\frac{a}{b} = c",
  "processing_time_ms": 450.5,
  "metadata": {
    "filename": "equation.png",
    "model_used": "llava:7b",
    "image_info": {
      "width": 800,
      "height": 600,
      "megapixels": 0.48
    }
  },
  "timestamp": "2026-02-06T13:25:00Z"
}
\`\`\`

#### Batch OCR
\`\`\`http
POST /api/v1/ocr/latex/batch
Content-Type: multipart/form-data
Authorization: Bearer your-api-key

files: <image-file-1>
files: <image-file-2>
...
\`\`\`

**Response:**
\`\`\`json
{
  "success": true,
  "results": [
    {
      "success": true,
      "latex": "x^2 + y^2 = z^2",
      "processing_time_ms": 430.2
    },
    {
      "success": true,
      "latex": "\\\\int_0^\\\\infty e^{-x} dx",
      "processing_time_ms": 520.8
    }
  ],
  "total_images": 2,
  "successful": 2,
  "failed": 0,
  "total_processing_time_ms": 951.0
}
\`\`\`

#### List Available Models
\`\`\`http
GET /api/v1/models
Authorization: Bearer your-api-key
\`\`\`

**Response:**
\`\`\`json
{
  "primary_model": "llava:7b",
  "fallback_models": ["llava:13b", "bakllava"],
  "available_models": ["llava:7b", "llava:13b"],
  "status": {
    "llava:7b": true,
    "llava:13b": true,
    "bakllava": false
  }
}
\`\`\`

## 🔧 Configuration

Edit \`.env\` file to configure:

\`\`\`env
# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=LaTeX OCR API
VERSION=1.0.0
DEBUG=False

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llava:7b
OLLAMA_FALLBACK_MODELS=llava:13b,bakllava
OLLAMA_TIMEOUT=120

# Image Processing
MAX_IMAGE_SIZE_MB=10
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# Logging
LOG_LEVEL=INFO
\`\`\`

## 🧪 Testing

\`\`\`bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py::TestHealthEndpoints::test_health_check -v
\`\`\`

## 📊 Usage Examples

### Python
\`\`\`python
import requests

url = "http://localhost:8000/api/v1/ocr/latex"
headers = {"Authorization": "Bearer test-key-123"}
files = {"file": open("equation.png", "rb")}
params = {"return_metadata": True}

response = requests.post(url, headers=headers, files=files, params=params)
data = response.json()

print(f"LaTeX: {data['latex']}")
print(f"Time: {data['processing_time_ms']}ms")
\`\`\`

### cURL
\`\`\`bash
curl -X POST "http://localhost:8000/api/v1/ocr/latex" \\
  -H "Authorization: Bearer test-key-123" \\
  -F "file=@equation.png" \\
  -F "return_metadata=true"
\`\`\`

### JavaScript
\`\`\`javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/ocr/latex', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer test-key-123'
  },
  body: formData
});

const data = await response.json();
console.log('LaTeX:', data.latex);
\`\`\`

## 🏗️ Architecture

\`\`\`
latex-ocr-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── security.py         # Authentication & security
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic models
│   │   └── ollama_client.py    # Ollama client with fallback
│   └── utils/
│       ├── __init__.py
│       ├── image_processing.py # Image validation
│       └── latex_validator.py  # LaTeX cleaning & validation
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
└── README.md
\`\`\`

## 🔒 Security Considerations

- **Never commit \`.env\`** - Contains secrets
- **Change SECRET_KEY** in production - Use strong random key
- **Use HTTPS** in production - Never HTTP for sensitive data
- **Implement proper API key management** - Use database instead of hardcoded keys
- **Enable CORS restrictions** - Only allow trusted origins
- **Monitor rate limits** - Prevent abuse
- **Keep dependencies updated** - Regular security patches

## 🚀 Performance Tips

1. **Use Redis for caching** - Cache repeated OCR results
2. **Enable GPU** - Much faster inference (requires GPU-enabled Ollama)
3. **Adjust model size** - Balance speed vs accuracy
4. **Configure resource limits** - Set appropriate CPU/memory limits
5. **Use fallback models wisely** - Balance reliability vs latency

## 🐛 Troubleshooting

### Ollama connection failed
\`\`\`bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
\`\`\`

### Model not found
\`\`\`bash
# Pull the model
ollama pull llava:7b

# List available models
ollama list
\`\`\`

### Docker build fails
\`\`\`bash
# Clear cache and rebuild
docker-compose build --no-cache

# Check logs
docker-compose logs
\`\`\`

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 🙏 Acknowledgments

- [Llama Vision](https://ai.meta.com/llama/) by Meta
- [Ollama](https://ollama.com/) for easy model deployment
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing framework
- [AI Engineering Hub](https://github.com/patchy631/ai-engineering-hub) for the project inspiration

---

Made with ❤️ using Llama Vision and FastAPI
EOF