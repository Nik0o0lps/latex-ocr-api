from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import time

from app.models.schemas import (
    OCRResponse, OCRBatchResponse, HealthResponse, ErrorResponse
)
from app.models.ollama_client import OllamaOCR
from app.utils.image_processing import (
    validate_and_process_image, 
    validate_batch_images,
    get_image_info
)
from app.utils.latex_validator import post_process_latex
from app.core.security import verify_api_key
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Instância global do cliente Ollama (singleton)
ollama_client = OllamaOCR(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    fallback_models=settings.ollama_fallback_models_list,
    timeout=settings.OLLAMA_TIMEOUT
)

# Variável para tracking de uptime
_start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    
    Verifica se API e Ollama estão funcionando
    """
    try:
        ollama_connected = ollama_client.check_connection()
        
        return HealthResponse(
            status="healthy" if ollama_connected else "degraded",
            ollama_connected=ollama_connected,
            ollama_model=settings.OLLAMA_MODEL,
            version=settings.VERSION,
            uptime_seconds=time.time() - _start_time
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            ollama_connected=False,
            ollama_model=settings.OLLAMA_MODEL,
            version=settings.VERSION,
            uptime_seconds=time.time() - _start_time
        )


@router.get("/models", tags=["Health"])
async def list_models(user: dict = Depends(verify_api_key)):
    """
    Lista modelos disponíveis e seu status
    
    Requer autenticação
    """
    try:
        models_status = ollama_client.check_all_models()
        return JSONResponse(content=models_status)
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr/latex", response_model=OCRResponse, tags=["OCR"])
async def ocr_latex(
    file: UploadFile = File(..., description="Image file containing mathematical equation"),
    return_metadata: bool = Query(False, description="Include processing metadata"),
    validate_latex: bool = Query(True, description="Validate and clean LaTeX output"),
    use_fallback: bool = Query(True, description="Use fallback models if primary fails"),
    user: dict = Depends(verify_api_key)
):
    """
    Extract LaTeX code from image
    
    **Parameters:**
    - **file**: Image file (jpg, jpeg, png, webp)
    - **return_metadata**: Include processing metadata in response
    - **validate_latex**: Validate and clean LaTeX syntax
    - **use_fallback**: Try fallback models if primary model fails
    
    **Returns:**
    - LaTeX code extracted from the image
    - Processing time
    - Optional metadata
    """
    try:
        # Validar e processar imagem
        image, image_bytes = await validate_and_process_image(
            file, 
            settings.MAX_IMAGE_SIZE_MB,
            settings.allowed_extensions_set
        )
        
        # Extrair LaTeX usando Ollama
        latex_raw, processing_time, model_used = ollama_client.predict(
            image, 
            image_bytes,
            use_fallback=use_fallback
        )
        
        # Processar e validar LaTeX
        if validate_latex:
            latex_processed = post_process_latex(latex_raw)
            latex_code = latex_processed['cleaned']
            latex_rendered = latex_processed['rendered']
            validation_errors = latex_processed['validation_errors']
        else:
            latex_code = latex_raw
            latex_rendered = latex_raw
            validation_errors = []
        
        # Construir metadata se solicitado
        metadata = None
        if return_metadata:
            image_info = get_image_info(image)
            metadata = {
                "filename": file.filename,
                "user": user.get("name"),
                "user_tier": user.get("tier"),
                "model_used": model_used,
                "image_info": image_info,
                "validation_errors": validation_errors
            }
        
        logger.info(
            f"OCR successful - User: {user.get('name')}, "
            f"Model: {model_used}, Time: {processing_time:.2f}ms"
        )
        
        return OCRResponse(
            success=True,
            latex=latex_code,
            latex_rendered=latex_rendered,
            processing_time_ms=processing_time,
            metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"OCR processing failed: {str(e)}"
        )


@router.post("/ocr/latex/batch", response_model=OCRBatchResponse, tags=["OCR"])
async def ocr_latex_batch(
    files: List[UploadFile] = File(..., description="List of image files"),
    return_metadata: bool = Query(False, description="Include processing metadata"),
    validate_latex: bool = Query(True, description="Validate and clean LaTeX output"),
    use_fallback: bool = Query(True, description="Use fallback models if primary fails"),
    user: dict = Depends(verify_api_key)
):
    """
    Batch process multiple images
    
    **Parameters:**
    - **files**: List of image files (max 10)
    - **return_metadata**: Include processing metadata
    - **validate_latex**: Validate and clean LaTeX syntax
    - **use_fallback**: Try fallback models if primary model fails
    
    **Returns:**
    - List of OCR results for each image
    - Summary statistics
    """
    # Validar batch
    validated_images = await validate_batch_images(
        files,
        settings.MAX_IMAGE_SIZE_MB,
        settings.allowed_extensions_set,
        max_batch_size=10
    )
    
    results = []
    successful = 0
    total_time = 0
    
    for image, image_bytes, filename in validated_images:
        try:
            # Processar cada imagem
            latex_raw, processing_time, model_used = ollama_client.predict(
                image,
                image_bytes,
                use_fallback=use_fallback
            )
            
            # Validar LaTeX
            if validate_latex:
                latex_processed = post_process_latex(latex_raw)
                latex_code = latex_processed['cleaned']
                latex_rendered = latex_processed['rendered']
            else:
                latex_code = latex_raw
                latex_rendered = latex_raw
            
            # Metadata
            metadata = None
            if return_metadata:
                metadata = {
                    "filename": filename,
                    "model_used": model_used
                }
            
            results.append(OCRResponse(
                success=True,
                latex=latex_code,
                latex_rendered=latex_rendered,
                processing_time_ms=processing_time,
                metadata=metadata
            ))
            
            successful += 1
            total_time += processing_time
            
        except Exception as e:
            logger.error(f"Batch item failed ({filename}): {str(e)}")
            
            # Adicionar resultado de erro
            results.append(OCRResponse(
                success=False,
                latex="",
                metadata={"filename": filename, "error": str(e)}
            ))
    
    logger.info(
        f"Batch OCR completed - User: {user.get('name')}, "
        f"Total: {len(files)}, Success: {successful}, Failed: {len(files) - successful}"
    )
    
    return OCRBatchResponse(
        success=True,
        results=results,
        total_images=len(files),
        successful=successful,
        failed=len(files) - successful,
        total_processing_time_ms=total_time
    )


@router.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/health"
    }
