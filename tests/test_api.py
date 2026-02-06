import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.main import app
from app.config import get_settings

client = TestClient(app)
settings = get_settings()

# API key válida para testes
TEST_API_KEY = "test-key-123"
HEADERS = {"Authorization": f"Bearer {TEST_API_KEY}"}


def create_test_image(width=200, height=100, color=(255, 255, 255)):
    """
    Cria uma imagem de teste
    """
    image = Image.new('RGB', (width, height), color)
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


class TestHealthEndpoints:
    """Testes dos endpoints de health check"""
    
    def test_root_endpoint(self):
        """Testa endpoint raiz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == settings.VERSION
    
    def test_health_check(self):
        """Testa health check"""
        response = client.get(f"{settings.API_V1_PREFIX}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "ollama_connected" in data
        assert "version" in data
    
    def test_list_models_without_auth(self):
        """Testa listagem de modelos sem autenticação"""
        response = client.get(f"{settings.API_V1_PREFIX}/models")
        assert response.status_code == 403  # Sem Bearer token
    
    def test_list_models_with_auth(self):
        """Testa listagem de modelos com autenticação"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/models",
            headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert "primary_model" in data
        assert "status" in data


class TestOCREndpoints:
    """Testes dos endpoints de OCR"""
    
    def test_ocr_without_auth(self):
        """Testa OCR sem autenticação"""
        image = create_test_image()
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex",
            files={"file": ("test.png", image, "image/png")}
        )
        assert response.status_code == 403  # Sem Bearer token
    
    def test_ocr_with_invalid_api_key(self):
        """Testa OCR com API key inválida"""
        image = create_test_image()
        invalid_headers = {"Authorization": "Bearer invalid-key"}
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex",
            headers=invalid_headers,
            files={"file": ("test.png", image, "image/png")}
        )
        assert response.status_code == 401
    
    def test_ocr_with_valid_image(self):
        """Testa OCR com imagem válida"""
        image = create_test_image()
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex",
            headers=HEADERS,
            files={"file": ("test.png", image, "image/png")}
        )
        
        # Pode falhar se Ollama não estiver rodando
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "latex" in data
            assert "processing_time_ms" in data
    
    def test_ocr_with_metadata(self):
        """Testa OCR com metadata habilitado"""
        image = create_test_image()
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex?return_metadata=true",
            headers=HEADERS,
            files={"file": ("test.png", image, "image/png")}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "metadata" in data
            if data["metadata"]:
                assert "filename" in data["metadata"]
                assert "model_used" in data["metadata"]
    
    def test_ocr_invalid_file_type(self):
        """Testa OCR com tipo de arquivo inválido"""
        # Criar arquivo texto
        file_content = b"not an image"
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex",
            headers=HEADERS,
            files={"file": ("test.txt", file_content, "text/plain")}
        )
        assert response.status_code == 400
    
    def test_ocr_too_large_file(self):
        """Testa OCR com arquivo muito grande"""
        # Criar imagem grande (> MAX_IMAGE_SIZE_MB)
        large_size = int((settings.MAX_IMAGE_SIZE_MB + 1) * 1024 * 1024)
        large_data = b"0" * large_size
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex",
            headers=HEADERS,
            files={"file": ("large.png", large_data, "image/png")}
        )
        assert response.status_code in [400, 413]


class TestBatchOCR:
    """Testes do endpoint de batch OCR"""
    
    def test_batch_ocr_without_auth(self):
        """Testa batch OCR sem autenticação"""
        image1 = create_test_image()
        image2 = create_test_image()
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex/batch",
            files=[
                ("files", ("test1.png", image1, "image/png")),
                ("files", ("test2.png", image2, "image/png"))
            ]
        )
        assert response.status_code == 403
    
    def test_batch_ocr_with_valid_images(self):
        """Testa batch OCR com imagens válidas"""
        image1 = create_test_image()
        image2 = create_test_image()
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex/batch",
            headers=HEADERS,
            files=[
                ("files", ("test1.png", image1, "image/png")),
                ("files", ("test2.png", image2, "image/png"))
            ]
        )
        
        # Pode falhar se Ollama não estiver rodando
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "results" in data
            assert "total_images" in data
            assert data["total_images"] == 2
    
    def test_batch_ocr_too_many_files(self):
        """Testa batch OCR com muitos arquivos"""
        # Criar 11 imagens (limite é 10)
        files = [
            ("files", (f"test{i}.png", create_test_image(), "image/png"))
            for i in range(11)
        ]
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/ocr/latex/batch",
            headers=HEADERS,
            files=files
        )
        assert response.status_code == 400


class TestRateLimiting:
    """Testes de rate limiting"""
    
    def test_rate_limit_exceeded(self):
        """Testa excesso de rate limit"""
        image = create_test_image()
        
        # Fazer mais requisições que o limite
        responses = []
        for _ in range(settings.RATE_LIMIT_PER_MINUTE + 5):
            response = client.post(
                f"{settings.API_V1_PREFIX}/ocr/latex",
                headers=HEADERS,
                files={"file": ("test.png", create_test_image(), "image/png")}
            )
            responses.append(response.status_code)
        
        # Pelo menos uma deve retornar 429 (Too Many Requests)
        assert 429 in responses


# Executar testes
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
