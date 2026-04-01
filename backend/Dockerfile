# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim AS runner
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=deps /usr/local/bin/alembic /usr/local/bin/alembic
COPY . .
RUN adduser --system --uid 1001 appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
