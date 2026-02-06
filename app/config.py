from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Set, List


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas do .env
    """
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "LaTeX OCR API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY: str  # ← NOVO: chave da API
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llava:7b"
    OLLAMA_FALLBACK_MODELS: str = ""  # ← NOVO: separado por vírgula
    OLLAMA_TIMEOUT: int = 120
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,webp"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10
    
    # Redis (Optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8501"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @property
    def allowed_extensions_set(self) -> Set[str]:
        """Converte string de extensões em set"""
        return {f".{ext.strip()}" for ext in self.ALLOWED_EXTENSIONS.split(",")}
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Converte string de CORS origins em lista"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def ollama_fallback_models_list(self) -> List[str]:
        """Converte string de fallback models em lista"""
        if not self.OLLAMA_FALLBACK_MODELS:
            return []
        return [model.strip() for model in self.OLLAMA_FALLBACK_MODELS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pattern: carrega settings apenas uma vez
    e cacheia para uso em toda aplicação
    """
    return Settings()
