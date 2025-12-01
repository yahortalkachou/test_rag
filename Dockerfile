FROM python:3.11-slim

WORKDIR /app

# sys dependencies 
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install uv
RUN uv pip install --system -r pyproject.toml

COPY . .

RUN mkdir -p /app/data /app/models /app/embeddings_cache

EXPOSE 8001

CMD ["uv", "run", "python", "app/main.py"]