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
- `keycloak-bootstrap`: creates realm/client/user in Keycloak
- `redis`: cache and simple queue
- `auth-api`: token exchange + token validation cache layer
- `user-api`, `billing-api`, `ml-api`: Flask APIs
- `prometheus`: metrics scraping
- `loki`: log storage
- `alloy`: container log collection and forwarding
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
      ALB / Nginx (80)
            |
            v
      Kong Proxy (8000)
   /     |      |        \
  v      v      v         v
Auth   User  Billing      ML
 API    API    API        API
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

- Auth API: `http://localhost:5000`
- User API: `http://localhost:5001`
- Billing API: `http://localhost:5002`
- ML API: `http://localhost:5003`

Kong-prefixed routes (through ALB/Nginx at `http://localhost`):

- Auth API via Kong: `http://localhost/api/auth`
- User API via Kong: `http://localhost/api/users`
- Billing API via Kong: `http://localhost/api/payments`
- ML API via Kong: `http://localhost/api/ml`

## Authentication Flow

1. `auth-api` exchanges username/password against Keycloak:

```bash
curl -s -X POST http://localhost:5000/token \
      -H "Content-Type: application/json" \
      -d '{"username":"alice","password":"alice"}'
```

2. Use the returned `access_token` to call protected APIs:

```bash
TOKEN="<access-token>"

curl -s http://localhost:5001/users -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:5002/payments -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:5003/predict -H "Authorization: Bearer $TOKEN"
```

3. Validation behavior:

- APIs call `auth-api /introspect`
- `auth-api` validates token with Keycloak `userinfo`
- Valid claims are cached in Redis for `TOKEN_CACHE_TTL_SECONDS` (default: `60`)

## Shared Service Structure

- Shared Python app setup and auth decorator: `services/common/base_service.py`
- Shared dependency list: `services/requirements.txt`
- Shared Dockerfile for all Python APIs: `services/Dockerfile.api`
- Shared health/readiness endpoint setup: `services/common/base_service.py`

Each API now only keeps service-specific routes in:

- `services/auth-api/app.py`
- `services/user-api/app.py`
- `services/billing-api/app.py`
- `services/ml-api/app.py`

## Tests And Coverage

The test suite uses one reusable pattern for all APIs (no duplicated test scaffolding):

- Shared test loader: `services/tests/conftest.py`
- Health contract tests for all services: `services/tests/test_health_endpoints.py`
- Protected-route contract tests for user/billing/ml: `services/tests/test_protected_endpoints.py`
- Auth-specific behavior tests: `services/tests/test_auth_api.py`

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Dependency locking is managed with `uv` using source files plus generated lock files:

- Source inputs: `services/requirements.in`, `requirements-dev.in`
- Generated, pinned + hashed outputs: `services/requirements.txt`, `requirements-dev.txt`

Regenerate both lock files:

```bash
uv pip compile services/requirements.in --generate-hashes --python-version 3.14 --output-file services/requirements.txt
uv pip compile requirements-dev.in --generate-hashes --python-version 3.14 --output-file requirements-dev.txt
```

The service runtime image is aligned to Python `3.14` in `services/Dockerfile.api`.

Run tests with coverage:

```bash
pytest
```

Coverage output:

- terminal summary with missing lines
- XML report at `coverage.xml`

Pytest configuration lives in `pytest.ini`.

## Health Checks

- Every long-running container now has a Compose `healthcheck`.
- Python APIs (`auth-api`, `user-api`, `billing-api`, `ml-api`) use shared `/health` endpoint checks.
- Bootstrap jobs (`kong-bootstrap`, `keycloak-bootstrap`) are one-shot tasks and are gated via completion/health dependencies.

## Observability

- Metrics: `/metrics` endpoint on each API
- Logs: collected by Alloy and sent to Loki
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
