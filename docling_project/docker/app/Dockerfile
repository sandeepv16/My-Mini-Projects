FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create cache directory for model downloads and set permissions
RUN mkdir -p /app/.cache /usr/local/lib/python3.11/site-packages/rapidocr/models && \
    chmod -R 777 /app/.cache /usr/local/lib/python3.11/site-packages/rapidocr

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set cache directory for downloads
ENV HF_HOME=/app/.cache \
    RAPIDOCR_MODELS_DIR=/app/.cache/rapidocr

CMD ["python", "main.py"]