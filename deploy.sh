#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-theme-heat}"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ".env created from .env.example"
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
else
  echo "Skipping git pull: current directory is not inside a git work tree."
fi

docker compose down
docker compose build
docker compose up -d
docker compose ps

HEALTH_URL="${HEALTH_URL:-http://localhost/health}"
curl --fail --show-error --silent "$HEALTH_URL" >/dev/null
echo "Health check passed: $HEALTH_URL"

echo "Frontend: http://localhost"
echo "Backend health: $HEALTH_URL"
