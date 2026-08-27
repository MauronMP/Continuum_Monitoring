FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/continuum-matplotlib \
    CONTINUUM_ROOT=/app \
    MPLBACKEND=Agg \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Resolve pinned dependencies before copying source/assets, so edits to queries
# and Python code do not download/reinstall the scientific stack every time.
COPY requirements ./requirements
RUN python -m pip install --only-binary=:all: --retries 2 --timeout 60 -r requirements/runtime.txt

COPY pyproject.toml README.md requirements-node.txt ./
COPY src ./src
COPY configs ./configs
COPY ontology ./ontology
COPY queries ./queries

RUN python -m pip install --no-deps --no-build-isolation .

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=12 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)"]

CMD ["python", "-m", "continuum_bench.node", "--host", "0.0.0.0", "--port", "8080"]
