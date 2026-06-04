#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-status}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

HOST="127.0.0.1"
API_PORT="8000"
FRONTEND_PORT="4321"
SEESEA_BASE_URL="${SEESEA_BASE_URL:-http://127.0.0.1:18080}"

RUN_DIR="/tmp/moyu-local"
API_LOG="$RUN_DIR/api.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"

API_PID_FILE="$RUN_DIR/api.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

UVICORN_BIN="$BACKEND_DIR/.venv/bin/uvicorn"
ASTRO_BIN="$FRONTEND_DIR/node_modules/.bin/astro"

mkdir -p "$RUN_DIR"

log() {
  printf '%s\n' "$*"
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    log "Missing required file: $path"
    exit 1
  fi
}

is_listening() {
  local port="$1"
  lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

wait_http_ready() {
  local name="$1"
  local url="$2"
  local timeout="${3:-45}"
  local elapsed=0

  while (( elapsed < timeout )); do
    if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
      log "$name ready: $url"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  log "$name not ready after ${timeout}s: $url"
  return 1
}

stop_port_process() {
  local port="$1"
  local pids

  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  log "Stopping listeners on port $port: $pids"
  kill $pids || true
  sleep 1

  if is_listening "$port"; then
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN || true)"
    if [[ -n "$pids" ]]; then
      log "Force stopping listeners on port $port: $pids"
      kill -9 $pids || true
    fi
  fi
}

start_api() {
  if is_listening "$API_PORT"; then
    log "API already running on $HOST:$API_PORT"
    return 0
  fi

  log "Starting API on $HOST:$API_PORT"
  (
    cd "$BACKEND_DIR"
    nohup env NO_PROXY='*' no_proxy='*' HTTP_PROXY='' HTTPS_PROXY='' ALL_PROXY='' \
      SEESEA_BASE_URL="$SEESEA_BASE_URL" PYTHONPATH=. \
      "$UVICORN_BIN" app.main:app --host "$HOST" --port "$API_PORT" \
      >"$API_LOG" 2>&1 &
    local pid=$!
    disown "$pid" 2>/dev/null || true
    echo "$pid" >"$API_PID_FILE"
  )
}

start_frontend() {
  if is_listening "$FRONTEND_PORT"; then
    log "Frontend already running on $HOST:$FRONTEND_PORT"
    return 0
  fi

  log "Starting frontend on $HOST:$FRONTEND_PORT"
  (
    cd "$FRONTEND_DIR"
    nohup env NO_PROXY='*' no_proxy='*' HTTP_PROXY='' HTTPS_PROXY='' ALL_PROXY='' \
      PUBLIC_API_BASE="http://$HOST:$API_PORT/api" \
      "$ASTRO_BIN" dev --host "$HOST" --port "$FRONTEND_PORT" \
      >"$FRONTEND_LOG" 2>&1 &
    local pid=$!
    disown "$pid" 2>/dev/null || true
    echo "$pid" >"$FRONTEND_PID_FILE"
  )
}

show_status() {
  if curl -fsS --max-time 5 "$SEESEA_BASE_URL/api/health" >/dev/null 2>&1; then
    log "SeeSea external health: ok ($SEESEA_BASE_URL)"
  else
    log "SeeSea external health: fail ($SEESEA_BASE_URL)"
  fi

  if is_listening "$API_PORT"; then
    log "API: listening on $HOST:$API_PORT"
  else
    log "API: stopped"
  fi

  if is_listening "$FRONTEND_PORT"; then
    log "Frontend: listening on $HOST:$FRONTEND_PORT"
  else
    log "Frontend: stopped"
  fi

  if curl -fsS --max-time 5 "http://$HOST:$API_PORT/healthz" >/dev/null 2>&1; then
    log "API health: ok"
  else
    log "API health: fail"
  fi

  if curl -fsS --max-time 5 "http://$HOST:$FRONTEND_PORT/" >/dev/null 2>&1; then
    log "Frontend health: ok"
  else
    log "Frontend health: fail"
  fi

  log "Logs: $RUN_DIR"
}

start_all() {
  require_file "$UVICORN_BIN"
  require_file "$ASTRO_BIN"

  wait_http_ready "SeeSea external service" "$SEESEA_BASE_URL/api/health" 10 || true

  start_api
  wait_http_ready "API" "http://$HOST:$API_PORT/healthz" 60

  start_frontend
  wait_http_ready "Frontend" "http://$HOST:$FRONTEND_PORT/" 90

  show_status
}

stop_all() {
  stop_port_process "$FRONTEND_PORT"
  stop_port_process "$API_PORT"

  rm -f "$API_PID_FILE" "$FRONTEND_PID_FILE"
  log "Local API/frontend services stopped"
}

case "$ACTION" in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  restart)
    stop_all
    start_all
    ;;
  status)
    show_status
    ;;
  *)
    log "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
