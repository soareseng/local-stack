from flask import jsonify, request

from common.base_service import create_service_app, require_auth

app = create_service_app("ml-api")

@app.route("/")
def home():
    return jsonify(service="ml-api")

@app.route("/predict")
@require_auth
def predict():
    principal = request.token_claims.get("preferred_username", "unknown")
    return jsonify(prediction="cat", requested_by=principal)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
