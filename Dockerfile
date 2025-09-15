FROM python:3.11-slim

# Set working direct# Health check with better logging
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f -v http://localhost:3000/health 2>&1 | head -10 || (echo "Health check failed at $(date)" && exit 1)
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 5070

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "========================================="\n\
echo "🚀 CONTAINER: WEDDING PLANNER APPLICATION"\n\
echo "========================================="\n\
echo "[APP] Starting Wedding Planner Flask Application..."\n\
echo "[APP] Container ID: $(hostname)"\n\
echo "[APP] Current date/time: $(date)"\n\
echo "[APP] Working directory: $(pwd)"\n\
echo "[APP] User: $(whoami)"\n\
echo "[APP] Process ID: $$"\n\
echo "[APP] Environment variables:" \n\
env | grep -E "(FLASK|DOMAIN|SECRET|CLOUDFLARE)" | sed "s/^/[APP] /" || echo "[APP] No Flask env vars found"\n\
echo "[APP] Python version: $(python --version 2>&1)"\n\
echo "[APP] Gunicorn version: $(gunicorn --version 2>&1)"\n\
echo "[APP] Health check available at: http://localhost:5070/health"\n\
echo "[APP] Debug info available at: http://localhost:5070/debug"\n\
echo "[APP] Application starting on port 5070..."\n\
echo "[APP] Container ready for traffic"\n\
echo "========================================="\n\
echo "[APP] Starting Gunicorn server..."\n\
exec gunicorn --bind 0.0.0.0:5070 --workers 4 --log-level info --access-logfile - --error-logfile - --logger-class=gunicorn.glogging.Logger app:app' > /app/start.sh && \
    chmod +x /app/start.sh

# Health check with better logging
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD echo "[HEALTH] Running health check at $(date)" && curl -f -v http://localhost:5070/health 2>&1 | head -10 || (echo "[HEALTH] Health check failed at $(date)" && exit 1)

# Run the application
CMD ["/app/start.sh"]
