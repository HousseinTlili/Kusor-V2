#!/bin/bash

# ==============================================================================
# KUSOR — Command Reference & Run Script
# ==============================================================================
# This script lists and executes all necessary operations for the Kusor project.
# You can run individual parts by passing the corresponding argument, e.g.:
#   ./commands.sh start-db
#   ./commands.sh backend
#   ./commands.sh frontend
#   ./commands.sh test
# ==============================================================================

PROJECT_ROOT="/home/houssein/kusor"

show_help() {
    echo "Kusor Helper Script"
    echo "Usage: ./commands.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  all          - Start databases, backend API, and frontend dev server"
    echo "  start-db     - Start the database containers (PostgreSQL, Neo4j, ChromaDB)"
    echo "  stop-db      - Stop the database containers"
    echo "  backend      - Start the Flask REST API server (port 5000)"
    echo "  frontend     - Start the Angular UI dev server (port 4200)"
    echo "  test         - Run all backend unit tests"
    echo "  db-migrate   - Apply PostgreSQL database migrations"
    echo "  db-init-neo4j- Initialize Neo4j constraints & indexes"
    echo "  ingest-bulk  - Download and ingest all older BCT circulars (initial run)"
    echo "  status       - Check Docker container and port status"
}

start_db() {
    echo "--> Starting databases (PostgreSQL, Neo4j, ChromaDB) in Docker..."
    cd "$PROJECT_ROOT/docker" || exit
    docker compose up -d
    echo "--> Databases started successfully."
}

stop_db() {
    echo "--> Stopping databases in Docker..."
    cd "$PROJECT_ROOT/docker" || exit
    docker compose down
    echo "--> Databases stopped."
}

run_backend() {
    echo "--> Starting backend Flask REST API (http://localhost:5000)..."
    cd "$PROJECT_ROOT/backend" || exit
    if [ ! -d ".venv" ]; then
        echo "Error: Virtual environment (.venv) not found in backend/."
        exit 1
    fi
    source .venv/bin/activate
    flask run --port 5000
}

run_frontend() {
    echo "--> Starting frontend Angular UI (http://localhost:4200)..."
    cd "$PROJECT_ROOT/frontend/kusor-ui" || exit
    npm run start
}

run_tests() {
    echo "--> Running backend unit tests with pytest..."
    cd "$PROJECT_ROOT/backend" || exit
    source .venv/bin/activate
    python -m pytest -v --tb=short
}

db_migrate() {
    echo "--> Running Alembic database migrations (Flask DB upgrade)..."
    cd "$PROJECT_ROOT/backend" || exit
    source .venv/bin/activate
    flask db upgrade -d ../migrations
}

db_init_neo4j() {
    echo "--> Initializing Neo4j graph schemas & indexes..."
    cd "$PROJECT_ROOT/backend" || exit
    source .venv/bin/activate
    python scripts/init_neo4j.py
}

ingest_bulk() {
    echo "--> Ingesting older BCT circulars (this may take a few minutes)..."
    cd "$PROJECT_ROOT/backend" || exit
    source .venv/bin/activate
    python scripts/initial_bulk_scrape.py
}

check_status() {
    echo "=== Docker Containers ==="
    docker ps
    echo ""
    echo "=== Ports in Use ==="
    echo "PostgreSQL (5432):"
    ss -lntp 2>/dev/null | grep :5432
    echo "Neo4j (7474/7687):"
    ss -lntp 2>/dev/null | grep -E ":7474|:7687"
    echo "ChromaDB (8001):"
    ss -lntp 2>/dev/null | grep :8001
    echo "Flask API (5000):"
    ss -lntp 2>/dev/null | grep :5000
    echo "Angular UI (4200):"
    ss -lntp 2>/dev/null | grep :4200
}

wait_for_port() {
    local port=$1
    local name=$2
    echo "Waiting for $name on port $port..."
    while ! (echo > /dev/tcp/127.0.0.1/$port) >/dev/null 2>&1; do
        sleep 1
    done
    echo "--> $name is ready!"
}

case "$1" in
    start-db)
        start_db
        ;;
    stop-db)
        stop_db
        ;;
    backend)
        run_backend
        ;;
    frontend)
        run_frontend
        ;;
    test)
        run_tests
        ;;
    db-migrate)
        db_migrate
        ;;
    db-init-neo4j)
        db_init_neo4j
        ;;
    ingest-bulk)
        ingest_bulk
        ;;
    status)
        check_status
        ;;
    all)
        start_db
        wait_for_port 5432 "PostgreSQL"
        wait_for_port 7687 "Neo4j"
        wait_for_port 8001 "ChromaDB"
        
        # Spawn backend in background
        echo "Launching backend in the background..."
        nohup "$PROJECT_ROOT/commands.sh" backend > "$PROJECT_ROOT/backend.log" 2>&1 & disown
        
        # Spawn frontend in background
        echo "Launching frontend in the background..."
        nohup "$PROJECT_ROOT/commands.sh" frontend > "$PROJECT_ROOT/frontend.log" 2>&1 & disown
        
        echo "--> All services are starting up! Check status with: ./commands.sh status"
        ;;
    *)
        show_help
        ;;
esac
