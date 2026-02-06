#!/bin/bash
set -e

echo "=========================================="
echo "Starting LaTeX OCR API"
echo "=========================================="

# Verificar se Ollama está instalado
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found"
    exit 1
fi

echo "✅ Ollama found"

# Iniciar Ollama em background
echo "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Aguardar Ollama ficar pronto
echo "Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Ollama failed to start"
        exit 1
    fi
    sleep 1
done

# Verificar se modelo está disponível
MODEL_NAME=${OLLAMA_MODEL:-llava:7b}
echo "Checking if model '$MODEL_NAME' is available..."

if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "⚠️  Model '$MODEL_NAME' not found, pulling..."
    ollama pull "$MODEL_NAME"
    echo "✅ Model '$MODEL_NAME' downloaded"
else
    echo "✅ Model '$MODEL_NAME' already available"
fi

# Baixar modelos fallback (se definidos)
if [ ! -z "$OLLAMA_FALLBACK_MODELS" ]; then
    IFS=',' read -ra FALLBACK_ARRAY <<< "$OLLAMA_FALLBACK_MODELS"
    for fallback_model in "${FALLBACK_ARRAY[@]}"; do
        fallback_model=$(echo "$fallback_model" | xargs)  # trim
        if [ ! -z "$fallback_model" ]; then
            echo "Checking fallback model '$fallback_model'..."
            if ! ollama list | grep -q "$fallback_model"; then
                echo "⚠️  Fallback model '$fallback_model' not found, pulling..."
                ollama pull "$fallback_model"
                echo "✅ Fallback model '$fallback_model' downloaded"
            else
                echo "✅ Fallback model '$fallback_model' already available"
            fi
        fi
    done
fi

echo "=========================================="
echo "Starting FastAPI application..."
echo "=========================================="

# Executar comando passado (FastAPI)
exec "$@"
