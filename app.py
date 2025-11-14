#!/usr/bin/env python3
"""
MarkItDown HTTP API - VERSÃO CORRIGIDA
Usa a biblioteca Python diretamente (não CLI)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import tempfile
import time
import re
from typing import Optional
from markitdown import MarkItDown
import uvicorn

# Configuração
API_TOKEN = os.getenv("API_TOKEN", "change-me-in-production")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 52428800))  # 50MB default
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Inicializar FastAPI
app = FastAPI(
    title="MarkItDown API",
    description="HTTP API for document to Markdown conversion",
    version="1.0.1"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# MarkItDown instance (criado uma vez, reutilizado)
md_converter = MarkItDown()

# Models
class ConversionResponse(BaseModel):
    success: bool
    markdown: Optional[str] = None
    plain_text: Optional[str] = None
    metadata: dict
    processing_time_ms: int
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int


# Globals
start_time = time.time()


# Middleware de autenticação
def verify_token(authorization: str = Header(None)):
    """Verifica token de autenticação"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.replace("Bearer ", "")

    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid API token")

    return token


# Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "version": "1.0.1",
        "uptime_seconds": int(time.time() - start_time)
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.1",
        "uptime_seconds": int(time.time() - start_time)
    }


@app.post("/convert", response_model=ConversionResponse)
async def convert_document(
    file: UploadFile = File(...),
    keep_data_uris: bool = False,
    authorization: str = Header(None, alias="Authorization")
):
    """
    Converte documento para Markdown

    Args:
        file: Arquivo para conversão (PDF, DOCX, XLSX, etc.)
        keep_data_uris: Manter data URIs para imagens (default: False)
        authorization: Bearer token para autenticação

    Returns:
        JSON com markdown, texto plano e metadados
    """
    start = time.time()
    temp_path = None

    try:
        # Autenticação
        verify_token(authorization)

        # Validar tamanho
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Salvar em arquivo temporário
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            temp_path = tmp.name

        print(f"[INFO] Converting file: {file.filename} ({file_size} bytes) at {temp_path}")

        # Converter usando biblioteca Python (NÃO CLI)
        result = md_converter.convert(temp_path)

        if not result or not result.text_content:
            raise HTTPException(
                status_code=500,
                detail="Conversion failed: empty result"
            )

        # Processar resultado
        markdown = result.text_content

        # Plain text (remove markdown syntax)
        plain_text = markdown_to_plain_text(markdown)

        # Metadados
        metadata = {
            "file_name": file.filename,
            "file_size_bytes": file_size,
            "file_type": file.content_type,
            "characters": len(markdown),
            "words": len(markdown.split()),
            "estimated_pages": estimate_pages(plain_text),
            "detected_format": detect_format(markdown)
        }

        processing_time = int((time.time() - start) * 1000)

        print(f"[SUCCESS] Converted in {processing_time}ms")

        return {
            "success": True,
            "markdown": markdown,
            "plain_text": plain_text,
            "metadata": metadata,
            "processing_time_ms": processing_time
        }

    except HTTPException:
        raise

    except Exception as e:
        processing_time = int((time.time() - start) * 1000)

        print(f"[ERROR] Conversion failed: {str(e)}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "markdown": None,
                "plain_text": None,
                "metadata": {},
                "processing_time_ms": processing_time,
                "error": str(e)
            }
        )

    finally:
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                print(f"[WARN] Failed to delete temp file: {e}")


# Utility functions
def markdown_to_plain_text(markdown: str) -> str:
    """Remove markdown syntax"""
    text = markdown

    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic
    text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)

    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def estimate_pages(text: str) -> int:
    """Estimate number of pages (2000 chars per page)"""
    CHARS_PER_PAGE = 2000
    return max(1, len(text) // CHARS_PER_PAGE)


def detect_format(markdown: str) -> str:
    """Detect original format from markdown patterns"""
    if '|' in markdown and markdown.count('|') > 10:
        return "spreadsheet"
    elif '---' in markdown:
        return "presentation"
    elif '[' in markdown and '](' in markdown:
        return "html"
    else:
        return "document"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"[STARTUP] Starting MarkItDown API on port {port}")
    print(f"[STARTUP] Max file size: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB")
    print(f"[STARTUP] CORS origins: {ALLOWED_ORIGINS}")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
