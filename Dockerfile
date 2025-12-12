FROM python:3.11-slim

# 1. Install uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 2. Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy dependency files
COPY pyproject.toml uv.lock* ./

# 4. Install dependencies globally in the container
# We use 'uv pip install' because it works best with the --system flag
# We use the pyproject.toml as the source
RUN uv pip install --system -r pyproject.toml

# 5. Copy the rest of the application
COPY . .

# 6. Create storage directories
RUN mkdir -p /app/data /app/models /app/embeddings_cache

EXPOSE 8000

# 7. Run standard python (no 'uv run' needed since packages are in system)
ENV PYTHONPATH=/app
CMD ["python", "app/main.py"]