#!/usr/bin/env bash
# KUSOR — Stop Script

echo "🛑 Arrêt des services KUSOR..."

pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*backend/app.py" 2>/dev/null || true

rm -f /tmp/kusor_server.pid /tmp/kusor_backend.pid /tmp/kusor_frontend.pid 2>/dev/null || true

echo "✓ Tous les services KUSOR ont été arrêtés."
