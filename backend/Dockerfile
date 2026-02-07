FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY services/ services/
COPY utils/ utils/
COPY models/ models/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Download spaCy German model
RUN python -m spacy download de_core_news_lg || python -m spacy download de_core_news_sm || true

# Create data directories
RUN mkdir -p /app/data/vectorstore /app/data/documents /app/data/audit

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
