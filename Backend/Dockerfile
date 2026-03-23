# ─── Build / dependency install ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --pre -r requirements.txt

# ─── Runtime image ───────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Azure Web Apps health probe port
EXPOSE 8000

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Default to 1 worker — agent initialisation runs as a background task and
# multiple workers would race to create/update the same Foundry agents.
# Scale via the UVICORN_WORKERS App Service app-setting when needed.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1}"]
