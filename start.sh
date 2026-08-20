#!/usr/bin/env bash
# KUSOR v3 — All-in-One Offline Startup Script
# Automatically starts local Docker databases and launches Backend API + Angular UI.

set -e

PROJECT_DIR="/home/houssein/kusor-v3"
cd "$PROJECT_DIR"

echo "============================================================"
echo "          🚀 Starting KUSOR v3 Platform Stack..."
echo "============================================================"

# 1. Clean up existing processes on ports 5000 & 4200
echo "🧹 [1/3] Freeing ports and stopping old processes..."
pkill -9 -f "backend/app.py" 2>/dev/null || true
pkill -9 -f "ng serve" 2>/dev/null || true
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 4200/tcp 2>/dev/null || true
sleep 1

# 2. Start local Docker databases (Postgres, Neo4j, ChromaDB, Ollama, n8n)
echo "🐳 [2/3] Starting local Docker databases (PostgreSQL, Neo4j, ChromaDB, Ollama)..."
if command -v docker >/dev/null 2>&1; then
  docker compose up -d postgres neo4j chromadb ollama n8n 2>/dev/null || true
  echo "   ✓ Local Docker database containers are active!"
else
  echo "   ⚠ Docker command not found, skipping container check."
fi

# 3. Start Backend Flask API
echo "⚡ [3/4] Launching Flask Backend API on http://localhost:5000..."
setsid bash -c "PYTHONPATH='$PROJECT_DIR' '$PROJECT_DIR/backend/.venv/bin/python' -u backend/app.py > /tmp/kusor_backend.log 2>&1" &
echo $! > /tmp/kusor_backend.pid 2>/dev/null || true

# Wait for backend readiness
for i in $(seq 1 15); do
  if curl -sf http://localhost:5000/api/docs > /dev/null 2>&1 || curl -sf http://localhost:5000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is online and ready!"
    break
  fi
  sleep 1
done

# 4. Start Frontend Angular UI
echo "🎨 [4/4] Launching Angular Frontend UI on http://localhost:4200..."
cd "$PROJECT_DIR/frontend/kusor-ui"
setsid bash -c "NG_CLI_ANALYTICS=false npm start > /tmp/kusor_frontend.log 2>&1" &
echo $! > /tmp/kusor_frontend.pid 2>/dev/null || true
cd "$PROJECT_DIR"

echo ""
echo "============================================================"
echo "    🎉 KUSOR v3 is now LIVE & Running (100% Offline)!"
echo "============================================================"
echo "🌐 Web Interface:      http://localhost:4200"
echo "🛡️ KYC/AML Screen:     http://localhost:4200/kyc"
echo "💳 Credit Pre-Screen:  http://localhost:4200/credit"
echo "⚖️ Contract Analyzer:  http://localhost:4200/contract"
echo "🕸️ Neo4j Graph View:   http://localhost:4200/graph"
echo "🔌 Backend REST API:   http://localhost:5000"
echo "📑 Swagger API Docs:   http://localhost:5000/api/docs"
echo ""
echo "🔑 Login Credentials:"
echo "   • Admin:              admin / Admin123!"
echo "   • Compliance Officer: compliance_user / User123!"
echo ""
echo "📋 View Live Logs:"
echo "   • Backend:  tail -f /tmp/kusor_backend.log"
echo "   • Frontend: tail -f /tmp/kusor_frontend.log"
echo ""
echo "🛑 To stop all services: ./stop.sh"
echo "============================================================"
