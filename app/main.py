from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, evidencias, incidencias, operaciones
from app.core.config import settings

app = FastAPI(
    title="CargoFlow API",
    description="Backend de CargoFlow — plataforma de gestión de operaciones logísticas.",
    version="0.1.0",
    docs_url="/docs" if settings.expose_docs else None,
    redoc_url="/redoc" if settings.expose_docs else None,
    openapi_url="/openapi.json" if settings.expose_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(operaciones.router)
app.include_router(evidencias.router)
app.include_router(incidencias.router)


@app.get("/health")
def health():
    return {"status": "ok"}