"""
Aplicación FastAPI para la API REST de TICKIO

Este archivo configura la aplicación FastAPI y la integra con Django.
Se debe ejecutar por separado del servidor Django.

Uso:
    cd Tickio_project
    uvicorn api_app:app --reload --port 8001

Acceso:
    http://localhost:8001
    http://127.0.0.1:8001
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django antes de crear la app FastAPI
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tickio.settings')
sys.path.insert(0, str(BASE_DIR))
django.setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from events.api import router as eventos_router

# Crear aplicación FastAPI
app = FastAPI(
    title="TICKIO API",
    description="API REST para gestionar eventos y tickets de TICKIO",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc"
)

# Configurar CORS para permitir solicitudes desde diferentes orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(eventos_router)


@app.get("/", tags=["Root"])
async def read_root():
    """Endpoint raíz de la API"""
    return {
        "message": "Bienvenido a TICKIO API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "eventos": "/api/v1/eventos",
            "documentación": "/api/docs",
        }
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Verificar que la API está funcionando correctamente"""
    return {
        "status": "ok",
        "message": "La API está funcionando correctamente"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        reload=True
    )
