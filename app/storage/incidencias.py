import uuid
from pathlib import Path

from fastapi import UploadFile

BASE_UPLOAD_DIR = Path("uploads/incidencias")

TIPOS_CONTENIDO_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB


async def guardar_foto_incidencia(archivo: UploadFile, *, operacion_id: uuid.UUID) -> str:
    """Guarda la foto de una incidencia en disco y devuelve la ruta a
    guardar en Incidencia.foto_url. Mismo patrón que app/storage/evidencias.py.
    """
    if archivo.content_type not in TIPOS_CONTENIDO_PERMITIDOS:
        raise ValueError(f"Tipo de archivo no permitido: {archivo.content_type}")

    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido (10 MB)")

    extension = Path(archivo.filename or "").suffix or ".bin"
    nombre_archivo = f"incidencia_{uuid.uuid4().hex}{extension}"

    carpeta = BASE_UPLOAD_DIR / str(operacion_id)
    carpeta.mkdir(parents=True, exist_ok=True)

    destino = carpeta / nombre_archivo
    destino.write_bytes(contenido)

    return str(destino)