FROM python:3.11-slim

# Set working directory
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
EXPOSE 5000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting Wedding Planner Application..."\n\
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
