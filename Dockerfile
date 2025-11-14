FROM python:3.11-slim

# Metadados
LABEL maintainer="CorretorIA <contato@corretordetextoonline.com.br>"
LABEL description="MarkItDown HTTP API for document conversion"

# Argumentos de build
ARG PORT=8000

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PORT=${PORT}
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema para MarkItDown
RUN apt-get update && apt-get install -y \
    # Para PDFs
    poppler-utils \
    # Para imagens (OCR)
    tesseract-ocr \
    tesseract-ocr-por \
    # Para áudio (opcional)
    ffmpeg \
    # Utilitários
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (cache de layers)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .

# Criar usuário não-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expor porta
EXPOSE ${PORT}

# Health check (testa endpoint /)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Comando de inicialização
CMD ["python", "app.py"]
