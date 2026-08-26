FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/continuum-matplotlib \
    CONTINUUM_ROOT=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
COPY ontology ./ontology
COPY queries ./queries

RUN python -m pip install --no-cache-dir .

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=12 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"]

CMD ["python", "-m", "continuum_bench.node", "--host", "0.0.0.0", "--port", "8080"]

