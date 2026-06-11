FROM python:3.12-slim

WORKDIR /app

# Install system dependencies required for some ML packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend context
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create backend directory to preserve module imports like `from backend.agent import...`
COPY . /app/backend/

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
