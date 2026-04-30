FROM python:3.12-slim

# Instala curl e utilitários de rede
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
RUN pip install --no-cache-dir \
    requests \
    python-dotenv \
    rich

WORKDIR /app

# Scripts serão montados via bind mount (não copiados)
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
