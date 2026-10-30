FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/src CONTINUUM_ROOT=/app
ENV CONTINUUM_OWL_JAVA_HEAP=512m MAVEN_OPTS="-Dmaven.repo.local=/app/.runtime/maven"
WORKDIR /app
COPY requirements-node.txt ./
RUN pip install --no-cache-dir -r requirements-node.txt
ARG INSTALL_DL=false
# Cache pinned runtime dependencies independently of application source changes.
COPY tools/owl/pom.xml ./tools/owl/pom.xml
RUN if [ "$INSTALL_DL" = "true" ]; then \
      apt-get update && apt-get install -y --no-install-recommends default-jdk-headless maven konclude && \
      mkdir -p /app/.runtime && \
      for backend in hermit openllet jfact; do \
        mvn -f /app/tools/owl/pom.xml -P"$backend" dependency:build-classpath \
          -Dmdep.outputFile=/app/.runtime/owl-validation-"$backend".classpath || exit 1; \
      done && \
      cp /app/.runtime/owl-validation-openllet.classpath /app/.runtime/owl-validation.classpath && \
      rm -rf /var/lib/apt/lists/*; fi
COPY src ./src
COPY configs ./configs
COPY ontology ./ontology
COPY queries ./queries
COPY tools ./tools
RUN if [ "$INSTALL_DL" = "true" ]; then \
      python tools/install_owl_reasoners.py --verify-only --java-heap 512m; fi
RUN useradd --uid 10001 --create-home worker && chown -R worker:worker /app
USER worker
ENTRYPOINT ["python", "-m", "continuum_bench.node"]
