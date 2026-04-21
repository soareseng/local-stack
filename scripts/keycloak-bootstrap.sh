#!/bin/sh
set -eu

KEYCLOAK_URL="${KEYCLOAK_URL:-http://keycloak:8080}"
KEYCLOAK_ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-local-dev}"
KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-local-stack-client}"
KEYCLOAK_USER="${KEYCLOAK_USER:-alice}"
KEYCLOAK_USER_PASSWORD="${KEYCLOAK_USER_PASSWORD:-alice}"

log() {
  echo "[keycloak-bootstrap] $*"
}

request_code() {
  method="$1"
  endpoint="$2"
  shift 2
  curl -sS -o /tmp/keycloak-bootstrap-response.json -w "%{http_code}" \
    -X "$method" "$KEYCLOAK_URL$endpoint" "$@"
}

wait_for_keycloak() {
  log "Waiting for Keycloak at $KEYCLOAK_URL..."
  tries=0
  while [ "$tries" -lt 60 ]; do
    code="$(request_code GET "/")"
    if [ "$code" = "200" ] || [ "$code" = "302" ]; then
      log "Keycloak is ready."
      return 0
    fi
    tries=$((tries + 1))
    sleep 2
  done

  log "Keycloak did not respond in time."
  exit 1
}

admin_login() {
  response="$(curl -sS \
    -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" \
    -d "username=$KEYCLOAK_ADMIN_USER" \
    -d "password=$KEYCLOAK_ADMIN_PASSWORD")"

  token="$(echo "$response" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
  if [ -z "$token" ]; then
    log "Failed to obtain admin token."
    echo "$response"
    exit 1
  fi
  echo "$token"
}

ensure_realm() {
  token="$1"
  code="$(request_code GET "/admin/realms/$KEYCLOAK_REALM" -H "Authorization: Bearer $token")"

  if [ "$code" = "200" ]; then
    log "Realm '$KEYCLOAK_REALM' already exists."
    return 0
  fi

  code="$(request_code POST "/admin/realms" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{\"realm\":\"$KEYCLOAK_REALM\",\"enabled\":true}")"

  if [ "$code" = "201" ] || [ "$code" = "409" ]; then
    log "Realm '$KEYCLOAK_REALM' created (or already existed due to race condition)."
    return 0
  fi

  log "Failed to create realm '$KEYCLOAK_REALM' (HTTP $code)."
  cat /tmp/keycloak-bootstrap-response.json
  exit 1
}

ensure_public_client() {
  token="$1"

  code="$(request_code GET "/admin/realms/$KEYCLOAK_REALM/clients?clientId=$KEYCLOAK_CLIENT_ID" -H "Authorization: Bearer $token")"
  if [ "$code" = "200" ] && grep -Fq "\"clientId\":\"$KEYCLOAK_CLIENT_ID\"" /tmp/keycloak-bootstrap-response.json; then
    log "Client '$KEYCLOAK_CLIENT_ID' already exists."
    return 0
  fi

  code="$(request_code POST "/admin/realms/$KEYCLOAK_REALM/clients" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{\"clientId\":\"$KEYCLOAK_CLIENT_ID\",\"enabled\":true,\"publicClient\":true,\"directAccessGrantsEnabled\":true,\"protocol\":\"openid-connect\"}")"

  if [ "$code" = "201" ] || [ "$code" = "409" ]; then
    log "Client '$KEYCLOAK_CLIENT_ID' created (or already existed due to race condition)."
    return 0
  fi

  log "Failed to create client '$KEYCLOAK_CLIENT_ID' (HTTP $code)."
  cat /tmp/keycloak-bootstrap-response.json
  exit 1
}

ensure_user() {
  token="$1"

  code="$(request_code GET "/admin/realms/$KEYCLOAK_REALM/users?username=$KEYCLOAK_USER" -H "Authorization: Bearer $token")"
  if [ "$code" = "200" ] && grep -Fq "\"username\":\"$KEYCLOAK_USER\"" /tmp/keycloak-bootstrap-response.json; then
    log "User '$KEYCLOAK_USER' already exists."
    return 0
  fi

  code="$(request_code POST "/admin/realms/$KEYCLOAK_REALM/users" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$KEYCLOAK_USER\",\"enabled\":true,\"emailVerified\":true,\"credentials\":[{\"type\":\"password\",\"value\":\"$KEYCLOAK_USER_PASSWORD\",\"temporary\":false}]}")"

  if [ "$code" = "201" ] || [ "$code" = "409" ]; then
    log "User '$KEYCLOAK_USER' created (or already existed due to race condition)."
    return 0
  fi

  log "Failed to create user '$KEYCLOAK_USER' (HTTP $code)."
  cat /tmp/keycloak-bootstrap-response.json
  exit 1
}

wait_for_keycloak
ADMIN_TOKEN="$(admin_login)"
ensure_realm "$ADMIN_TOKEN"
ensure_public_client "$ADMIN_TOKEN"
ensure_user "$ADMIN_TOKEN"

log "Keycloak bootstrap completed successfully."
