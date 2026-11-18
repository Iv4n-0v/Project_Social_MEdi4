FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# /data guarda la llave privada JWT (se monta como volumen para que no cambie al reiniciar)
RUN useradd --create-home appuser && mkdir /data && chown -R appuser /app /data
USER appuser

EXPOSE 8005
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
