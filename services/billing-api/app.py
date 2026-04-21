import os

from flask import Flask, jsonify
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

service_name = os.getenv("OTEL_SERVICE_NAME", "billing-api")
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318")

resource = Resource.create({"service.name": service_name})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

FlaskInstrumentor().instrument_app(app)
PrometheusMetrics(app)

@app.route("/")
def home():
    return jsonify(service="billing-api")

@app.route("/payments")
def payments():
    return jsonify(payments=[100,200])

app.run(host="0.0.0.0", port=5000)