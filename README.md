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
- Llama Vision model pulled: `ollama pull llava:7b`

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Nik0o0lps/latex-ocr-api
cd latex-ocr-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
nano .env  # Edit and set your API_KEY
```

5. **Start Ollama**
```bash
ollama serve
```

6. **Run the API**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access documentation**
```
http://localhost:8000/docs
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Edit .env and set API_KEY
nano .env

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📖 API Documentation

### Authentication

All endpoints require authentication via API key in header:

```bash
X-API-Key: your-api-key-here
```

### Endpoints

#### Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "ollama_model": "llava:7b",
  "version": "1.0.0"
}
```

#### Single Image OCR
```http
POST /api/v1/ocr
Content-Type: multipart/form-data
X-API-Key: your-api-key

file: <image-file>
```

**Response:**
```json
{
  "success": true,
  "latex": "\frac{a}{b} = c",
  "latex_rendered": "\frac{a}{b} = c",
  "processing_time_ms": 450.5,
  "timestamp": "2026-02-06T13:25:00Z"
}
```

## 🔧 Configuration

Edit `.env` file to configure:

```env
# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=LaTeX OCR API
VERSION=1.0.0
DEBUG=False

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
API_KEY=your-secret-api-key-here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llava:7b
OLLAMA_FALLBACK_MODELS=
OLLAMA_TIMEOUT=300

# Image Processing
MAX_IMAGE_SIZE_MB=10
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# Logging
LOG_LEVEL=INFO
```

## 📊 Usage Examples

### Python
```python
import requests

url = "http://localhost:8000/api/v1/ocr"
headers = {"X-API-Key": "your-api-key-here"}
files = {"file": open("equation.png", "rb")}

response = requests.post(url, headers=headers, files=files)
data = response.json()

print(f"LaTeX: {data['latex']}")
print(f"Time: {data['processing_time_ms']}ms")
```

### cURL
```bash
curl -X POST "http://localhost:8000/api/v1/ocr" \
  -H "X-API-Key: your-api-key-here" \
  -F "file=@equation.png"
```

### JavaScript
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/v1/ocr', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key-here'
  },
  body: formData
});

const data = await response.json();
console.log('LaTeX:', data.latex);
```

## 🏗️ Architecture

```
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
│   │   └── ollama_client.py    # Ollama client
│   └── utils/
│       ├── __init__.py
│       └── latex_validator.py  # LaTeX validation
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔒 Security Considerations

- **Never commit `.env`** - Contains secrets
- **Change API_KEY** in production - Use strong random key
- **Use HTTPS** in production - Never HTTP for sensitive data
- **Enable CORS restrictions** - Only allow trusted origins
- **Monitor rate limits** - Prevent abuse

## 🐛 Troubleshooting

### Ollama connection failed
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Model not found
```bash
# Pull the model
ollama pull llava:7b

# List available models
ollama list
```

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

---

Made with ❤️ using Llama Vision and FastAPI
