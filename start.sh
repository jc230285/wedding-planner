#!/bin/bash
set -e

echo "========================================="
echo "🚀 CONTAINER: WEDDING PLANNER APPLICATION"
echo "========================================="
echo "[APP] Starting Wedding Planner Flask Application..."
echo "[APP] Container ID: $(hostname)"
echo "[APP] Current date/time: $(date)"
echo "[APP] Working directory: $(pwd)"
echo "[APP] User: $(whoami)"
echo "[APP] Process ID: $$"
echo "[APP] Directory permissions:"
ls -la /app | head -5 | sed "s/^/[APP] /"
echo "[APP] Environment variables:"
env | grep -E "(FLASK|DOMAIN|SECRET|CLOUDFLARE|DATABASE)" | sed "s/^/[APP] /" || echo "[APP] No Flask env vars found"
echo "[APP] Python version: $(python --version 2>&1)"
echo "[APP] Gunicorn version: $(gunicorn --version 2>&1)"
echo "[APP] Testing Python imports..."

python -c "import flask; print(f\"[APP] Flask version: {flask.__version__}\")" 2>&1 | sed "s/^/[APP] /"
python -c "import sqlalchemy; print(f\"[APP] SQLAlchemy version: {sqlalchemy.__version__}\")" 2>&1 | sed "s/^/[APP] /"
echo "[APP] Testing Flask app import..."
python -c "from app import create_app; print(\"[APP] Flask app import successful\")" 2>&1 | sed "s/^/[APP] /"
echo "[APP] Testing blueprint imports..."
python -c "from blueprints.public.routes import public_bp; print(\"[APP] Public blueprint import successful\")" 2>&1 | sed "s/^/[APP] /"
python -c "from blueprints.admin.routes import admin_bp; print(\"[APP] Admin blueprint import successful\")" 2>&1 | sed "s/^/[APP] /"
python -c "from blueprints.api.routes import api_bp; print(\"[APP] API blueprint import successful\")" 2>&1 | sed "s/^/[APP] /"
echo "[APP] Health check available at: http://localhost:5070/health"
echo "[APP] Debug info available at: http://localhost:5070/debug"
echo "[APP] Application starting on port 5070..."
echo "[APP] Container ready for traffic"
echo "========================================="
echo "[APP] Starting Gunicorn server..."

# Start the application
exec gunicorn --bind 0.0.0.0:5070 --workers 4 --log-level info --access-logfile - --error-logfile - --logger-class=gunicorn.glogging.Logger app:app