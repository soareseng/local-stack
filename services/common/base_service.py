import os
from functools import wraps

import requests
from flask import Flask, jsonify, request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_flask_exporter import PrometheusMetrics


def create_service_app(service_name: str) -> Flask:
    app = Flask(__name__)
    _setup_observability(app, service_name)
    _register_health_routes(app, service_name)
    return app


def _register_health_routes(app: Flask, service_name: str) -> None:
    @app.route("/health")
    @app.route("/ready")
    def health():
        return jsonify(service=service_name, status="ok")


def _setup_observability(app: Flask, service_name: str) -> None:
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FlaskInstrumentor().instrument_app(app)
    PrometheusMetrics(app)


def require_auth(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(error="missing_bearer_token"), 401

        token = auth_header.split(" ", 1)[1].strip()
        auth_api_url = os.getenv("AUTH_API_URL", "http://auth-api:5000")

        try:
            response = requests.post(
                f"{auth_api_url}/introspect",
                json={"token": token},
                timeout=3,
            )
        except requests.RequestException:
            return jsonify(error="auth_service_unavailable"), 503

        if response.status_code != 200:
            return jsonify(error="invalid_token"), 401

        request.token_claims = response.json()
        return view_func(*args, **kwargs)

    return wrapped
