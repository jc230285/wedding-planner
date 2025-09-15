FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
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

# Ensure the app directory is writable for database files
RUN mkdir -p /app && chmod 755 /app

# Create database directory with proper permissions
RUN mkdir -p /app/data && chmod 755 /app/data

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
echo "[APP] Directory permissions:" \n\
ls -la /app | head -5 | sed "s/^/[APP] /"\n\
echo "[APP] Environment variables:" \n\
env | grep -E "(FLASK|DOMAIN|SECRET|CLOUDFLARE|DATABASE)" | sed "s/^/[APP] /" || echo "[APP] No Flask env vars found"\n\
echo "[APP] Python version: $(python --version 2>&1)"\n\
echo "[APP] Gunicorn version: $(gunicorn --version 2>&1)"\n\
echo "[APP] Testing Python imports..."\n\
python -c "import flask; print(f\"[APP] Flask version: {flask.__version__}\")" 2>&1 | sed "s/^/[APP] /"\n\
python -c "import sqlalchemy; print(f\"[APP] SQLAlchemy version: {sqlalchemy.__version__}\")" 2>&1 | sed "s/^/[APP] /"\n\
echo "[APP] Testing Flask app import..."\n\
python -c "from app import create_app; print(\"[APP] Flask app import successful\")" 2>&1 | sed "s/^/[APP] /"\n\
echo "[APP] Testing blueprint imports..."\n\
python -c "from blueprints.public.routes import public_bp; print(\"[APP] Public blueprint import successful\")" 2>&1 | sed "s/^/[APP] /"\n\
python -c "from blueprints.admin.routes import admin_bp; print(\"[APP] Admin blueprint import successful\")" 2>&1 | sed "s/^/[APP] /"\n\
python -c "from blueprints.api.routes import api_bp; print(\"[APP] API blueprint import successful\")" 2>&1 | sed "s/^/[APP] /"\n\
echo "[APP] Health check available at: http://localhost:5070/health"\n\
echo "[APP] Debug info available at: http://localhost:5070/debug"\n\
echo "[APP] Application starting on port 5070..."\n\
echo "[APP] Container ready for traffic"\n\
echo "========================================="\n\
echo "[APP] Starting Gunicorn server..."\n\
exec gunicorn --bind 0.0.0.0:5070 --workers 4 --log-level info --access-logfile - --error-logfile - --logger-class=gunicorn.glogging.Logger app:app' > /app/start.sh && \
    chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5070/health || exit 1

# Run the application
CMD ["/app/start.sh"]
