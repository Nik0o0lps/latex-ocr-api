from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security_scheme = HTTPBearer()


# Simples API Key storage (em produção, usar banco de dados)
API_KEYS_DB: Dict[str, dict] = {
    "test-key-123": {
        "name": "Test User",
        "tier": "free",
        "rate_limit": 10,
        "active": True
    },
    "dev-key-456": {
        "name": "Developer",
        "tier": "premium",
        "rate_limit": 100,
        "active": True
    },
    # Adicione mais keys aqui ou carregue de banco de dados
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se senha corresponde ao hash
    
    Args:
        plain_password: Senha em texto
        hashed_password: Senha hasheada
    
    Returns:
        bool: True se senha correta
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash da senha
    
    Args:
        password: Senha em texto
    
    Returns:
        str: Hash bcrypt da senha
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria JWT access token
    
    Args:
        data: Dados para incluir no token
        expires_delta: Tempo de expiração
    
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida JWT token
    
    Args:
        token: JWT token
    
    Returns:
        Optional[dict]: Payload do token ou None se inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> dict:
    """
    Valida API key do header Authorization: Bearer <key>
    
    Args:
        credentials: Credenciais do header
    
    Returns:
        dict: Dados do usuário associado à API key
    
    Raises:
        HTTPException: Se API key inválida
    """
    api_key = credentials.credentials
    
    # Verificar se key existe
    if api_key not in API_KEYS_DB:
        logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar se key está ativa
    user_data = API_KEYS_DB[api_key]
    if not user_data.get("active", False):
        logger.warning(f"Inactive API key attempted: {user_data.get('name')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"API key validated for user: {user_data.get('name')}")
    
    return {
        "api_key": api_key,
        **user_data
    }


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> dict:
    """
    Valida JWT token do header Authorization: Bearer <token>
    
    Args:
        credentials: Credenciais do header
    
    Returns:
        dict: Payload do token
    
    Raises:
        HTTPException: Se token inválido
    """
    token = credentials.credentials
    
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar expiração
    exp = payload.get("exp")
    if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme)
) -> dict:
    """
    Obtém usuário atual (tenta API key primeiro, depois JWT)
    
    Args:
        credentials: Credenciais do header
    
    Returns:
        dict: Dados do usuário
    
    Raises:
        HTTPException: Se autenticação falhar
    """
    # Tentar como API key primeiro
    try:
        return await verify_api_key(credentials)
    except HTTPException:
        pass
    
    # Tentar como JWT token
    try:
        return await verify_jwt_token(credentials)
    except HTTPException:
        pass
    
    # Se nenhum funcionou
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def check_rate_limit(user_data: dict) -> bool:
    """
    Verifica rate limit do usuário (placeholder)
    
    Em produção, implementar com Redis
    
    Args:
        user_data: Dados do usuário
    
    Returns:
        bool: True se dentro do limite
    """
    # TODO: Implementar com Redis
    # Por enquanto, sempre permite
    return True


async def require_premium_tier(
    user: dict = Depends(verify_api_key)
) -> dict:
    """
    Dependency que requer tier premium
    
    Args:
        user: Dados do usuário
    
    Returns:
        dict: Dados do usuário
    
    Raises:
        HTTPException: Se não for premium
    """
    if user.get("tier") != "premium":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires premium tier"
        )
    
    return user
