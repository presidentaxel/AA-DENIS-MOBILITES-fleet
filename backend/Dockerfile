FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Copier les scripts pour les tests
COPY scripts ./scripts
# Copier Alembic pour les migrations
COPY alembic.ini .
COPY alembic ./alembic

ENV PYTHONUNBUFFERED=1

# Exposer le port 8080 pour correspondre au port par défaut utilisé par Digital Ocean/Kubernetes pour les health checks
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

