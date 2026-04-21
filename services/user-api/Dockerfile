# services/*/Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install flask
RUN pip install prometheus-flask-exporter opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-flask

COPY app.py .

CMD ["python", "app.py"]
