#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  . "${ROOT_DIR}/.env"
  set +a
fi

action="${1:-up}"

case "$action" in
  up)
    docker-compose up --build -d
    ;;
  down)
    docker-compose down
    ;;
  index)
    docker-compose run --rm web python -c "from app.rag import RAGEngine; RAGEngine().build_index()"
    ;;
  smoke)
    curl -fsS http://localhost:8080/health || true
    ;;
  *)
    echo "用法: $0 [up|down|index|smoke]"
    exit 2
    ;;
esac
