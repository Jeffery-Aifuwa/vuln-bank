FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1

# Install PostgreSQL client cleanly without cache artifacts
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root system group and user with fixed UID/GID
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR /app

# Leverage Docker layer caching for Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-create writable upload directory with dedicated ownership
RUN mkdir -p /app/static/uploads /app/templates && \
    chown -R appuser:appgroup /app/static/uploads && \
    chmod 750 /app/static/uploads

# Copy application source code
COPY . .

# Ensure start script is executable and uploads directory remains writable by appuser
RUN chmod +x /app/start.sh && \
    chown -R appuser:appgroup /app/static/uploads

EXPOSE 5000

# Enforce least-privilege non-root execution
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=5).getcode() == 200 else sys.exit(1)"

CMD ["./start.sh"]