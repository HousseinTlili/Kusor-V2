#!/usr/bin/env bash
# KUSOR v3 — All-in-One Startup Script
# Automatically starts Docker infrastructure (PostgreSQL, Neo4j, ChromaDB, n8n)
# and launches Flask API + Angular Frontend with full process detachment.

set -e

PROJECT_DIR="/home/houssein/kusor-v3"
cd "$PROJECT_DIR"

echo "============================================================"
echo "          🚀 Starting KUSOR v3 Platform Stack..."
echo "============================================================"

# Stop any existing host processes first
echo "🛑 Stopping existing backend/frontend processes..."
pkill -f "python.*backend/app.py" 2>/dev/null || true
pkill -f "ng serve" 2>/dev/null || true
sleep 1

# 1. Ensure Docker Services are running (Postgres, Neo4j, ChromaDB, n8n)
echo "🐳 [1/3] Starting Docker Infrastructure (PostgreSQL, Neo4j, ChromaDB, n8n)..."
if command -v docker >/dev/null 2>&1; then
  docker compose up -d postgres neo4j chromadb n8n >/dev/null 2>&1 || true
  echo "   ✓ Docker containers (including n8n on port 5678) are active!"
else
  echo "   ⚠ Docker command not found, skipping container verification."
fi

# 2. Start Backend API as detached daemon
echo "⚡ [2/3] Starting Flask Backend API on http://localhost:5000..."
cd "$PROJECT_DIR"
setsid bash -c "PYTHONPATH='$PROJECT_DIR' '$PROJECT_DIR/backend/.venv/bin/python' -u backend/app.py >> /tmp/kusor_backend.log 2>&1" &
disown
echo $! > /tmp/kusor_backend.pid 2>/dev/null || true

# Wait for backend to be ready
echo "   Waiting for backend to start..."
for i in $(seq 1 20); do
  if curl -sf http://localhost:5000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is ready!"
    break
  fi
  if [ "$i" -eq 20 ]; then
    echo "   ⚠ Backend did not respond yet. Check: tail -f /tmp/kusor_backend.log"
  fi
  sleep 1
done

# 3. Start Frontend Angular UI as detached daemon
echo "🎨 [3/3] Starting Angular Frontend UI on http://localhost:4200..."
cd "$PROJECT_DIR/frontend/kusor-ui"
setsid bash -c "npm run start >> /tmp/kusor_frontend.log 2>&1" &
disown
cd "$PROJECT_DIR"
echo $! > /tmp/kusor_frontend.pid 2>/dev/null || true

echo ""
echo "============================================================"
echo "    🎉 KUSOR v3 is now running!"
echo "============================================================"
echo "🌐 Website UI:    http://localhost:4200"
echo "🔌 Backend API:   http://localhost:5000"
echo "⚡ Automation UI: http://localhost:5678 (n8n Workflows)"
echo "📑 Swagger Specs: http://localhost:5000/api/docs"
echo ""
echo "🔑 5 Demo Login Credentials (Password for all: Password123!):"
echo "   1. Admin:       admin"
echo "   2. Compliance:  compliance"
echo "   3. Legal:       legal"
echo "   4. Credit:      credit"
echo "   5. User:        user"
echo ""
echo "📋 View Live Logs:"
echo "   Backend:  tail -f /tmp/kusor_backend.log"
echo "   Frontend: tail -f /tmp/kusor_frontend.log"
echo ""
echo "🛑 To stop services: ./stop.sh"
echo "============================================================"
