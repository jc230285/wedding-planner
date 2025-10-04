# Deployment Guide

## Overview
This guide covers deploying the wedding planner application using Docker containers with Cloudflare tunnel for external access.

## Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **Git** for version control
- **Text Editor** (VS Code recommended)

### Required Accounts
- **GitHub** account for source code
- **Supabase** account for PostgreSQL database
- **Cloudflare** account for tunnel service

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/jc230285/wedding-planner.git
cd wedding-planner
```

### 2. Environment Variables
Create `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database

# Cloudflare Tunnel (for external access)
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token_here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
```

#### Getting Database URL
1. Sign up for Supabase at https://supabase.com
2. Create a new project
3. Go to Settings > Database
4. Copy the connection string
5. Format: `postgresql://postgres:[password]@[host]:5432/postgres`

#### Getting Cloudflare Tunnel Token
1. Sign up for Cloudflare at https://cloudflare.com
2. Go to Zero Trust dashboard
3. Navigate to Access > Tunnels
4. Create a new tunnel
5. Copy the tunnel token

### 3. Database Setup
Run the database setup scripts:

```bash
# Create tables
python scripts/create_supabase_table.py

# Import initial data (if available)
python scripts/import_supabase.py
```

## Docker Deployment

### 1. Build and Run
```bash
# Build and start all services
docker-compose up --build

# Run in detached mode (background)
docker-compose up --build -d
```

### 2. Verify Deployment
Check that both containers are running:
```bash
docker-compose ps
```

Expected output:
```
NAME                           COMMAND                  SERVICE             STATUS
wedding-planner-web-1          "gunicorn --bind 0.0…"   web                 running
wedding-planner-tunnel-1       "cloudflared tunnel …"   tunnel              running
```

### 3. Access Application
- **Local Access**: http://localhost:5000
- **External Access**: https://your-domain.com (via Cloudflare tunnel)

## Container Configuration

### Web Container (Flask App)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Tunnel Container (Cloudflare)
```yaml
tunnel:
  image: cloudflare/cloudflared:latest
  command: tunnel --no-autoupdate run
  environment:
    - CLOUDFLARE_TUNNEL_TOKEN=${CLOUDFLARE_TUNNEL_TOKEN}
  depends_on:
    - web
```

## Production Deployment

### 1. Server Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ recommended
- **Storage**: 20GB+ available space
- **OS**: Linux (Ubuntu 20.04+ or similar)

### 2. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Deploy Application
```bash
# Clone repository
git clone https://github.com/jc230285/wedding-planner.git
cd wedding-planner

# Create environment file
cp .env.example .env
# Edit .env with production values

# Deploy
docker-compose up --build -d

# Check logs
docker-compose logs -f
```

### 4. SSL/TLS Configuration
Cloudflare tunnel automatically provides SSL/TLS encryption for external access.

For direct access, consider using:
- **Let's Encrypt** with Certbot
- **Reverse proxy** (Nginx/Apache) with SSL

## Monitoring & Maintenance

### 1. Container Health Checks
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs web
docker-compose logs tunnel

# Monitor resource usage
docker stats
```

### 2. Application Logs
```bash
# Real-time logs
docker-compose logs -f web

# Search logs
docker-compose logs web | grep "ERROR"

# Export logs
docker-compose logs --no-color web > app.log
```

### 3. Database Maintenance
```bash
# Connect to database (if needed)
docker-compose exec web python
>>> from utils.db import get_db_connection
>>> conn = get_db_connection()
# Run maintenance queries
```

### 4. Backup Strategy
```bash
# Database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Application backup
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz .
```

## Updates & Maintenance

### 1. Application Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up --build -d

# Clean up old images
docker image prune -f
```

### 2. Database Migrations
```bash
# Run migration scripts
python scripts/add_column.py

# Verify schema
python scripts/check_schema.py
```

### 3. Security Updates
```bash
# Update base images
docker-compose pull

# Rebuild with latest base images
docker-compose up --build -d

# Update system packages
sudo apt update && sudo apt upgrade -y
```

## Troubleshooting

### 1. Common Issues

#### Container Won't Start
```bash
# Check logs for errors
docker-compose logs web

# Common fixes:
# - Verify environment variables
# - Check port conflicts
# - Ensure database connectivity
```

#### Database Connection Issues
```bash
# Test database connection
python -c "
from utils.db import get_db_connection
try:
    conn = get_db_connection()
    print('Database connection successful')
except Exception as e:
    print(f'Database error: {e}')
"
```

#### Cloudflare Tunnel Issues
```bash
# Check tunnel logs
docker-compose logs tunnel

# Verify tunnel token
echo $CLOUDFLARE_TUNNEL_TOKEN

# Test tunnel connectivity
curl -I https://your-domain.com
```

### 2. Performance Issues

#### High CPU Usage
```bash
# Monitor resource usage
docker stats

# Check for infinite loops in logs
docker-compose logs web | grep -i error

# Restart if needed
docker-compose restart web
```

#### Memory Issues
```bash
# Check memory usage
free -h
docker stats

# Increase container limits if needed
# (edit docker-compose.yml)
```

### 3. Debug Mode
For debugging, temporarily enable debug mode:

```yaml
# docker-compose.yml
environment:
  - FLASK_DEBUG=True
  - FLASK_ENV=development
```

## Scaling Considerations

### 1. Horizontal Scaling
```yaml
# docker-compose.yml
services:
  web:
    scale: 3  # Run multiple instances
```

### 2. Load Balancer
Consider adding Nginx for load balancing:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

### 3. Database Scaling
For high traffic:
- Consider read replicas
- Implement connection pooling
- Optimize queries and indexes

## Security Hardening

### 1. Container Security
```bash
# Run containers as non-root user
# Limit container resources
# Use minimal base images
# Regular security updates
```

### 2. Network Security
```bash
# Restrict container network access
# Use internal networks for inter-container communication
# Implement proper firewall rules
```

### 3. Data Protection
```bash
# Encrypt data at rest
# Use secure connection strings
# Regular security audits
# Backup encryption
```

## Automation

### 1. CI/CD Pipeline
Consider setting up GitHub Actions:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          # SSH and deploy commands
```

### 2. Automated Backups
```bash
# Cron job for regular backups
0 2 * * * /path/to/backup_script.sh
```

### 3. Health Monitoring
```bash
# Health check script
#!/bin/bash
curl -f http://localhost:5000/health || docker-compose restart web
```

## Support & Maintenance

### 1. Log Rotation
```bash
# Configure Docker log rotation
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 2. Monitoring Setup
- Use Docker monitoring tools
- Set up alerting for failures
- Monitor database performance
- Track application metrics

### 3. Documentation Updates
- Keep deployment docs current
- Document any custom configurations
- Maintain runbook for common issues
- Regular security review