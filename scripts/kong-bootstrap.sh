#!/bin/sh
set -eu

KONG_ADMIN_URL="${KONG_ADMIN_URL:-http://kong:8001}"

log() {
  echo "[kong-bootstrap] $*"
}

request_code() {
  method="$1"
  endpoint="$2"
  shift 2
  curl -sS -o /tmp/kong-bootstrap-response.json -w "%{http_code}" \
    -X "$method" "$KONG_ADMIN_URL$endpoint" "$@"
}

wait_for_kong() {
  log "Waiting for Kong Admin API at $KONG_ADMIN_URL..."
  tries=0
  while [ "$tries" -lt 60 ]; do
    code="$(request_code GET "/services")"
    if [ "$code" = "200" ]; then
      log "Kong Admin API is ready."
      return 0
    fi

    tries=$((tries + 1))
    sleep 2
  done

  log "Kong Admin API did not respond in time."
  exit 1
}

ensure_service() {
  name="$1"
  url="$2"

  code="$(request_code GET "/services/$name")"

  if [ "$code" = "200" ]; then
    log "Service '$name' already exists."
    return 0
  fi

  if [ "$code" != "404" ]; then
    log "Error checking service '$name' (HTTP $code)."
    cat /tmp/kong-bootstrap-response.json
    exit 1
  fi

  code="$(request_code POST "/services" --data "name=$name" --data "url=$url")"
  if [ "$code" = "201" ] || [ "$code" = "409" ]; then
    log "Service '$name' created (or already existed due to race condition)."
    return 0
  fi

  log "Failed to create service '$name' (HTTP $code)."
  cat /tmp/kong-bootstrap-response.json
  exit 1
}

ensure_route() {
  service_name="$1"
  route_name="$2"
  route_path="$3"

  code="$(request_code GET "/routes/$route_name")"
  if [ "$code" = "200" ]; then
    log "Route '$route_name' already exists."
    return 0
  fi

  if [ "$code" != "404" ]; then
    log "Error checking route '$route_name' (HTTP $code)."
    cat /tmp/kong-bootstrap-response.json
    exit 1
  fi

  code="$(request_code GET "/services/$service_name/routes")"
  if [ "$code" != "200" ]; then
    log "Error listing routes for service '$service_name' (HTTP $code)."
    cat /tmp/kong-bootstrap-response.json
    exit 1
  fi

  if grep -Fq "\"$route_path\"" /tmp/kong-bootstrap-response.json; then
    log "A route with path '$route_path' already exists on service '$service_name'."
    return 0
  fi

  code="$(request_code POST "/services/$service_name/routes" --data "name=$route_name" --data "paths[]=$route_path")"
  if [ "$code" = "201" ] || [ "$code" = "409" ]; then
    log "Route '$route_name' created (or already existed due to race condition)."
    return 0
  fi

  log "Failed to create route '$route_name' (HTTP $code)."
  cat /tmp/kong-bootstrap-response.json
  exit 1
}

wait_for_kong

ensure_service "user-api" "http://user-api:5000"
ensure_route "user-api" "user-api-route" "/api/users"

ensure_service "billing-api" "http://billing-api:5000"
ensure_route "billing-api" "billing-api-route" "/api/payments"

ensure_service "ml-api" "http://ml-api:5000"
ensure_route "ml-api" "ml-api-route" "/api/ml"

ensure_service "auth-api" "http://auth-api:5000"
ensure_route "auth-api" "auth-api-route" "/api/auth"

log "Route bootstrap completed successfully."
