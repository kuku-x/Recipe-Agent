FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ ./src/
COPY web/ ./web/
COPY pyproject.toml .
COPY .env.example .

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "recipe_agent.main"]