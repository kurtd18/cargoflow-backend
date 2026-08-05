FROM python:3.12-slim

WORKDIR /app

# curl solo para el healthcheck de docker-compose contra /health
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# ${PORT:-8000}: usa el puerto que la plataforma de hosting asigne (Railway,
# Render, etc. lo inyectan como variable PORT); si no existe, usa 8000
# (caso local con docker-compose).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]