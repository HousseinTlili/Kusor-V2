#!/usr/bin/env bash
# KUSOR — Unified Enterprise Startup Script
# Automatically starts Docker infrastructure (PostgreSQL, Neo4j, ChromaDB)
# and launches Unified Flask + Angular Single-Port Stack (Port 5000).

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "============================================================"
echo "          🚀 Démarrage de la Plateforme KUSOR..."
echo "============================================================"

# Stop any existing host processes first
echo "🛑 Arrêt des processus existants..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*backend/app.py" 2>/dev/null || true
sleep 1

# 1. Ensure Docker Services are running (Postgres, Neo4j, ChromaDB, n8n)
echo "🐳 [1/2] Démarrage de l'infrastructure Docker (PostgreSQL, Neo4j, ChromaDB, n8n)..."
if command -v docker >/dev/null 2>&1; then
  docker update --restart=no kusor_backend 2>/dev/null || true
  docker stop kusor_backend 2>/dev/null || true
  docker start kusor_postgres kusor_neo4j kusor_chroma kusor_n8n 2>/dev/null || true
  echo "   ✓ Conteneurs Docker opérationnels !"
else
  echo "   ⚠ Commande docker non trouvée, étape ignorée."
fi

# 2. Start Unified Backend + Angular SPA on port 5000
echo "⚡ [2/2] Démarrage du Serveur Unifié KUSOR sur http://localhost:5000..."
cd "$PROJECT_DIR/backend"
setsid bash -c "PYTHONPATH='$PROJECT_DIR:$PROJECT_DIR/backend' '$PROJECT_DIR/backend/.venv/bin/python' -u app.py >> /tmp/kusor_server.log 2>&1" &
disown
echo $! > /tmp/kusor_server.pid 2>/dev/null || true

# Wait for server to be ready
echo "   Vérification de la disponibilité du serveur..."
for i in $(seq 1 25); do
  if curl -sf http://localhost:5000/health > /dev/null 2>&1; then
    echo "   ✓ Le Serveur KUSOR est prêt !"
    break
  fi
  if [ "$i" -eq 25 ]; then
    echo "   ⚠ Le serveur met du temps à démarrer. Consulter : tail -f /tmp/kusor_server.log"
  fi
  sleep 1
done

echo ""
echo "============================================================"
echo "    🎉 KUSOR est en ligne sur le port unique 5000 !"
echo "============================================================"
echo "🌐 Application Web Complète : http://localhost:5000"
echo "📊 Tableau de Bord & KPIs   : http://localhost:5000/dashboard"
echo "🕸️ Graphe Interactif Neo4j : http://localhost:5000/graph"
echo "💬 Assistant Chat IA        : http://localhost:5000/chat"
echo "💳 Module Crédit (≤ 40%)    : http://localhost:5000/credit"
echo "📜 Module Contrats          : http://localhost:5000/contract"
echo "🛡️ Module AML / KYC         : http://localhost:5000/kyc"
echo "⚡ Impact Réglementaire     : http://localhost:5000/impact-viewer"
echo "⏳ Explorateur Temporel     : http://localhost:5000/temporal-explorer"
echo "🔄 Moteur Workflow n8n      : http://localhost:5678"
echo "📑 Documentation Swagger    : http://localhost:5000/api/docs"
echo "🧪 Console de Test R&D      : http://localhost:5000/test"
echo ""
echo "📋 Logs en temps réel : tail -f /tmp/kusor_server.log"
echo "🛑 Pour arrêter le serveur : ./stop.sh"
echo "============================================================"
