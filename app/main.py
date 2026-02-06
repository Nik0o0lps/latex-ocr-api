from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import logging
import time

from app.config import get_settings
from app.api import routes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('latex-ocr-api.log')
    ]
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Configurar log level do .env
logging.getLogger().setLevel(settings.LOG_LEVEL)

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    **LaTeX OCR API** powered by Llama Vision (Ollama)
    
    Extract LaTeX code from images of mathematical equations.
    
    ## Features
    - 🔍 OCR for mathematical equations
    - 🔄 Automatic fallback to alternative models
    - ✅ LaTeX validation and cleaning
    - 📦 Batch processing support
    - 🔐 API key authentication
    - 📊 Metadata and processing metrics
    
    ## Authentication
    Include your API key in the Authorization header:
    ```
    Authorization: Bearer your-api-key-here
    ```
    
    ## Rate Limiting
    Default: {settings.RATE_LIMIT_PER_MINUTE} requests per minute per IP
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Adicionar rate limiter ao app state
app.state.limiter = limiter

# Middleware: Rate Limiting
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware: Request timing e logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware para medir tempo de resposta e logging
    """
    start_time = time.time()
    
    # Log da requisição
    logger.info(f"Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Calcular tempo de processamento
        process_time = (time.time() - start_time) * 1000  # ms
        response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
        
        # Log da resposta
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Time: {process_time:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)}")
        raise


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handler para 404 Not Found"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "error_code": "NOT_FOUND",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handler para 500 Internal Server Error"""
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Executa ao iniciar a aplicação
    """
    logger.info("="*50)
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"Ollama Model: {settings.OLLAMA_MODEL}")
    logger.info(f"Fallback Models: {settings.ollama_fallback_models_list}")
    logger.info(f"Rate Limit: {settings.RATE_LIMIT_PER_MINUTE}/min")
    logger.info("="*50)
    
    # Verificar conexão com Ollama
    from app.models.ollama_client import OllamaOCR
    ollama_client = OllamaOCR(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        fallback_models=settings.ollama_fallback_models_list
    )
    
    if ollama_client.check_connection():
        logger.info(" Ollama connection successful")
        
        # Verificar modelos disponíveis
        models_status = ollama_client.check_all_models()
        logger.info(f"Available models: {models_status['available_models']}")
        
        for model, available in models_status['status'].items():
            status_icon = "✅" if available else "❌"
            logger.info(f"{status_icon} Model '{model}': {'Available' if available else 'Not found'}")
    else:
        logger.warning("⚠️  Ollama connection failed - API will have limited functionality")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Executa ao desligar a aplicação
    """
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


# Incluir rotas
app.include_router(
    routes.router,
    prefix=settings.API_V1_PREFIX,
    tags=["API v1"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "status": "online",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "health": f"{settings.API_V1_PREFIX}/health",
            "ocr": f"{settings.API_V1_PREFIX}/ocr/latex",
            "batch": f"{settings.API_V1_PREFIX}/ocr/latex/batch"
        }
    }


# Desenvolvimento: ponto de entrada
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
