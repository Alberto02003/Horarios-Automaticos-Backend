# -- Stage 1: builder
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# -- Stage 2: runtime
FROM python:3.12-slim AS runtime
RUN useradd -m -u 1001 appuser
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
RUN chmod +x entrypoint.sh && mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
CMD ["./entrypoint.sh"]
