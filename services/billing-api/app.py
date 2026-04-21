from flask import jsonify, request

from common.base_service import create_service_app, require_auth

app = create_service_app("billing-api")

@app.route("/")
def home():
    return jsonify(service="billing-api")

@app.route("/payments")
@require_auth
def payments():
    principal = request.token_claims.get("preferred_username", "unknown")
    return jsonify(payments=[100, 200], requested_by=principal)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
