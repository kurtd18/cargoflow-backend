import uuid
from pathlib import Path

from fastapi import UploadFile

BASE_UPLOAD_DIR = Path("uploads/evidencias")

TIPOS_CONTENIDO_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB


async def guardar_archivo_evidencia(archivo: UploadFile, *, operacion_id: uuid.UUID, tipo: str) -> str:
    """Guarda el archivo en disco y devuelve la ruta a guardar en Evidencia.url_archivo.

    Disco local por ahora. Si más adelante se migra a S3 (o similar), esta
    es la única función que hay que reemplazar — el router no cambia.
    """
    if archivo.content_type not in TIPOS_CONTENIDO_PERMITIDOS:
        raise ValueError(f"Tipo de archivo no permitido: {archivo.content_type}")

    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ValueError("El archivo supera el tamaño máximo permitido (10 MB)")

    extension = Path(archivo.filename or "").suffix or ".bin"
    nombre_archivo = f"{tipo}_{uuid.uuid4().hex}{extension}"

    carpeta = BASE_UPLOAD_DIR / str(operacion_id)
    carpeta.mkdir(parents=True, exist_ok=True)

    destino = carpeta / nombre_archivo
    destino.write_bytes(contenido)

    return str(destino)