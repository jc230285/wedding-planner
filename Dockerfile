FROM node:18-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

FROM alpine:3.18
WORKDIR /app

# Install runtime deps
RUN apk add --no-cache nodejs npm python3 py3-pip supervisor curl bash

# Copy frontend
COPY --from=frontend-build /frontend/.next /app/frontend/.next
COPY --from=frontend-build /frontend/public /app/frontend/public
COPY --from=frontend-build /frontend/node_modules /app/frontend/node_modules
COPY --from=frontend-build /frontend/package.json /app/frontend/package.json

# Copy backend
COPY --from=backend /backend /app/backend

# Install cloudflared
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

# Supervisor config
COPY supervisord.conf /etc/supervisord.conf

EXPOSE 5070 5071
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
