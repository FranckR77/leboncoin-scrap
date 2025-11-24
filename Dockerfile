# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Avoid Python buffering logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps if scraper needs them (lxml, etc.)
RUN apt-get update && apt-get install -y \
  build-essential \
  libxml2-dev \
  libxslt-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Launch with Uvicorn
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
