# frontend/Dockerfile
# Multi-stage container build for KUSOR v3 Angular 17 UI

# ── Stage 1: Build Angular SPA ───────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install build dependencies
COPY kusor-ui/package*.json ./
RUN npm install --legacy-peer-deps

# Copy Angular source code and build production bundle
COPY kusor-ui/ ./
RUN npm run build

# ── Stage 2: Serve via Nginx Alpine ──────────────────
FROM nginx:alpine

# Remove default nginx html
RUN rm -rf /usr/share/nginx/html/*

# Copy built Angular distribution assets
COPY --from=builder /app/dist/kusor-ui/browser /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
