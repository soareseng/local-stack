import os
import time
import json

import redis
import requests
from flask import jsonify, request

from common.base_service import create_service_app

app = create_service_app("auth-api")

keycloak_url = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
keycloak_realm = os.getenv("KEYCLOAK_REALM", "local-dev")
keycloak_client_id = os.getenv("KEYCLOAK_CLIENT_ID", "local-stack-client")
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
cache_ttl_seconds = int(os.getenv("TOKEN_CACHE_TTL_SECONDS", "60"))

redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


def _token_endpoint() -> str:
    return (
        f"{keycloak_url}/realms/{keycloak_realm}"
        "/protocol/openid-connect/token"
    )


def _userinfo_endpoint() -> str:
    return (
        f"{keycloak_url}/realms/{keycloak_realm}"
        "/protocol/openid-connect/userinfo"
    )


@app.route("/")
def home():
    return jsonify(service="auth-api", status="ok")


@app.route("/token", methods=["POST"])
def token():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        return jsonify(error="username_and_password_required"), 400

    form = {
        "grant_type": "password",
        "client_id": keycloak_client_id,
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(_token_endpoint(), data=form, timeout=5)
    except requests.RequestException:
        return jsonify(error="keycloak_unavailable"), 503

    if response.status_code != 200:
        return jsonify(error="token_request_failed", details=response.text), 401

    return jsonify(response.json())


@app.route("/introspect", methods=["POST"])
def introspect():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token")

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        return jsonify(error="token_required"), 400

    cache_key = f"token:{token}"
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))

    try:
        response = requests.get(
            _userinfo_endpoint(),
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
    except requests.RequestException:
        return jsonify(error="keycloak_unavailable"), 503

    if response.status_code != 200:
        return jsonify(error="invalid_token"), 401

    claims = response.json()
    claims["active"] = True
    claims["validated_at"] = int(time.time())

    redis_client.setex(cache_key, cache_ttl_seconds, json.dumps(claims))
    return jsonify(claims)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
