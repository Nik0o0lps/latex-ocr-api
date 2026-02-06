from PIL import Image
from io import BytesIO
from fastapi import UploadFile, HTTPException
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


async def validate_and_process_image(
    file: UploadFile,
    max_size_mb: int = 10,
    allowed_extensions: set = {".jpg", ".jpeg", ".png", ".webp"}
) -> Tuple[Image.Image, bytes]:
    """
    Valida e processa imagem do upload
    
    Args:
        file: Arquivo enviado via FastAPI
        max_size_mb: Tamanho máximo em MB
        allowed_extensions: Extensões permitidas
    
    Returns:
        Tuple[Image.Image, bytes]: (PIL Image, bytes da imagem)
    
    Raises:
        HTTPException: Se validação falhar
    """
    # Validar nome do arquivo
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )
    
    # Validar extensão
    file_ext = "." + file.filename.split(".")[-1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file_ext}'. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Ler conteúdo
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Error reading uploaded file"
        )
    
    # Validar tamanho
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.2f}MB). Maximum size: {max_size_mb}MB"
        )
    
    # Validar se é imagem válida
    try:
        image = Image.open(BytesIO(contents))
        
        # Verificar se imagem está corrompida
        image.verify()
        
        # Reabrir (verify() fecha a imagem)
        image = Image.open(BytesIO(contents))
        
        # Converter para RGB se necessário
        if image.mode not in ("RGB", "L"):
            logger.info(f"Converting image from {image.mode} to RGB")
            image = image.convert("RGB")
        
        logger.info(
            f"Image validated successfully: {file.filename}, "
            f"size: {size_mb:.2f}MB, dimensions: {image.size}, mode: {image.mode}"
        )
        
        return image, contents
        
    except Exception as e:
        logger.error(f"Invalid image file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or corrupted image file: {str(e)}"
        )


def validate_image_dimensions(
    image: Image.Image,
    min_width: int = 50,
    min_height: int = 50,
    max_width: int = 4096,
    max_height: int = 4096
) -> Tuple[bool, str]:
    """
    Valida dimensões da imagem
    
    Args:
        image: PIL Image
        min_width: Largura mínima em pixels
        min_height: Altura mínima em pixels
        max_width: Largura máxima em pixels
        max_height: Altura máxima em pixels
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    width, height = image.size
    
    if width < min_width or height < min_height:
        return False, f"Image too small ({width}x{height}). Minimum: {min_width}x{min_height}"
    
    if width > max_width or height > max_height:
        return False, f"Image too large ({width}x{height}). Maximum: {max_width}x{max_height}"
    
    return True, ""


def resize_image_if_needed(
    image: Image.Image,
    max_dimension: int = 2048
) -> Image.Image:
    """
    Redimensiona imagem se for muito grande (mantém aspect ratio)
    
    Args:
        image: PIL Image
        max_dimension: Dimensão máxima (largura ou altura)
    
    Returns:
        Image.Image: Imagem redimensionada (ou original se não precisar)
    """
    width, height = image.size
    
    if width <= max_dimension and height <= max_dimension:
        return image
    
    # Calcular novo tamanho mantendo aspect ratio
    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    
    logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
    
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized


def get_image_info(image: Image.Image) -> dict:
    """
    Extrai informações da imagem
    
    Args:
        image: PIL Image
    
    Returns:
        dict: Informações da imagem
    """
    width, height = image.size
    
    info = {
        "width": width,
        "height": height,
        "mode": image.mode,
        "format": image.format,
        "megapixels": round((width * height) / 1_000_000, 2)
    }
    
    return info


async def validate_batch_images(
    files: list[UploadFile],
    max_size_mb: int = 10,
    allowed_extensions: set = {".jpg", ".jpeg", ".png", ".webp"},
    max_batch_size: int = 10
) -> list[Tuple[Image.Image, bytes, str]]:
    """
    Valida múltiplas imagens em batch
    
    Args:
        files: Lista de arquivos
        max_size_mb: Tamanho máximo por imagem
        allowed_extensions: Extensões permitidas
        max_batch_size: Máximo de imagens no batch
    
    Returns:
        list[Tuple[Image.Image, bytes, str]]: Lista de (imagem, bytes, filename)
    
    Raises:
        HTTPException: Se validação falhar
    """
    if len(files) > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum batch size: {max_batch_size}"
        )
    
    if len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="No files provided"
        )
    
    results = []
    
    for idx, file in enumerate(files):
        try:
            image, image_bytes = await validate_and_process_image(
                file,
                max_size_mb,
                allowed_extensions
            )
            results.append((image, image_bytes, file.filename))
            
        except HTTPException as e:
            # Re-raise com informação do índice
            raise HTTPException(
                status_code=e.status_code,
                detail=f"File {idx + 1} ({file.filename}): {e.detail}"
            )
    
    logger.info(f"Batch validation successful: {len(results)} images")
    
    return results
