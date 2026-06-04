#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT_DIR"

PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup EXIT INT TERM

python -m components.perception_demo.mock_server &
PIDS+=("$!")

python -m components.path_planner_demo.mock_server &
PIDS+=("$!")

python -m components.json_demo.mock_server &
PIDS+=("$!")

echo "Started mock servers: perception_demo=5001 path_planner_demo=5002 json_demo=5003"
wait
