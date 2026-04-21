from flask import jsonify, request

from common.base_service import create_service_app, require_auth

app = create_service_app("user-api")

@app.route("/")
def home():
    return jsonify(service="user-api", status="ok")

@app.route("/users")
@require_auth
def users():
    principal = request.token_claims.get("preferred_username", "unknown")
    return jsonify(users=["alice", "bob"], requested_by=principal)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
