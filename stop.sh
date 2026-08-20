#!/usr/bin/env bash
# KUSOR v3 — All-in-One Stop Script

echo "🛑 Stopping KUSOR v3 services..."

pkill -9 -f "backend/app.py" 2>/dev/null || true
pkill -9 -f "ng serve" 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 4200/tcp 2>/dev/null || true

rm -f /tmp/kusor_backend.pid /tmp/kusor_frontend.pid

echo "✓ Backend and Frontend stopped."
echo "💡 (Optional) To also stop Docker database containers: docker compose down"
