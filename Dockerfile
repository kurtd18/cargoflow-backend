FROM python:3.12-slim

WORKDIR /app

# curl solo para el healthcheck de docker-compose contra /health
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Corre las migraciones automáticamente al arrancar el contenedor,
# antes de levantar el servidor -- así nunca queda una versión de la API
# corriendo contra un esquema desactualizado.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]