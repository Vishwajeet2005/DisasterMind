FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for ML packages and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend context
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

# Create backend directory to preserve module imports like `from backend.agent import...`
COPY . /app/backend/

EXPOSE 8000

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend

# Use Gunicorn as the process manager with a single worker to stay under Render's 512MB Free Tier limit
CMD ["gunicorn", "api.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "600"]
