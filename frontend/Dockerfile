FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero las dependencias: si solo cambia el codigo, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El codigo queda en /app/frontend para que los imports "frontend.xxx" funcionen
COPY . ./frontend

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8000"]
