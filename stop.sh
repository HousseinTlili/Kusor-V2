#!/usr/bin/env bash
# KUSOR v3 — Stop Script

echo "🛑 Stopping KUSOR v3 processes..."

pkill -f "python.*backend/app.py" 2>/dev/null || true
pkill -f "ng serve" 2>/dev/null || true

rm -f /home/houssein/kusor-v3/.backend.pid /home/houssein/kusor-v3/.frontend.pid

echo "✓ KUSOR v3 services stopped."
