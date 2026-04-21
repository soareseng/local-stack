# local-stack

A local stack with APIs, gateway, and observability for development.

## Stack Overview

- `alb` (Nginx): HTTP entrypoint on port `80`
- `kong`: API Gateway (proxy `8000`, admin `8001`)
- `kong-db` (Postgres): Kong database
- `kong-migrations`: Kong database migrations
- `kong-bootstrap`: idempotent Kong service and route bootstrap
- `keycloak`: authentication and authorization
- `keycloak-db` (Postgres): Keycloak database
- `redis`: cache and simple queue
- `user-api`, `billing-api`, `ml-api`: Flask APIs
- `prometheus`: metrics scraping
- `loki`: log storage
- `promtail`: container log collection
- `jaeger`: distributed tracing
- `grafana`: metrics, logs, and traces visualization
- `cadvisor`: container metrics

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2 (`docker compose`)

## How To Run

1. Start the full stack:

```bash
docker compose up -d --build
```

2. Check status:

```bash
docker compose ps
```

3. View logs for a service:

```bash
docker compose logs -f user-api
```

## Request Flow
```plaintext
         Client
            |
            v
        ALB/Nginx (80)
            |
            v
    Kong Proxy (8000)
  |         |         |
  v         v         v
User API  Billing API  ML API
```

## Access URLs

- ALB/Nginx: `http://localhost`
- Kong Proxy: `http://localhost:8000`
- Kong Admin API: `http://localhost:8001`
- Keycloak: `http://localhost:8080`
- Grafana: `http://localhost:3000` (`admin` / `admin`)
- Prometheus: `http://localhost:9090`
- Jaeger: `http://localhost:16686`
- Loki API: `http://localhost:3100`
- cAdvisor: `http://localhost:8088`

## API Endpoints

- User API: `http://localhost:5001`
- Billing API: `http://localhost:5002`
- ML API: `http://localhost:5003`

## Observability

- Metrics: `/metrics` endpoint on each API
- Logs: collected by Promtail and sent to Loki
- Traces: sent by APIs to Jaeger via OTLP
- Grafana: Prometheus, Loki, and Jaeger datasources are pre-provisioned

## Stop And Remove

```bash
docker compose down
```

To remove volumes as well:

```bash
docker compose down -v
```

## TODO

- [ ] Add health checks for all services
- [ ] Review and finalize Redis + Keycloak configuration for production-like local setup
