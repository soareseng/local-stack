from conftest import load_service_module

auth_app = load_service_module("auth-api")


class _MemoryRedis:
    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def setex(self, key, ttl_seconds, value):
        self._store[key] = value


class _DummyTokenResponse:
    status_code = 200

    @staticmethod
    def json():
        return {"access_token": "abc", "token_type": "Bearer"}


class _DummyUserInfoResponse:
    status_code = 200

    @staticmethod
    def json():
        return {"preferred_username": "alice", "email": "alice@example.com"}


def test_auth_health_endpoint():
    client = auth_app.app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["service"] == "auth-api"


def test_token_requires_username_password():
    client = auth_app.app.test_client()
    response = client.post("/token", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "username_and_password_required"


def test_token_success(monkeypatch):
    monkeypatch.setattr(auth_app.requests, "post", lambda *args, **kwargs: _DummyTokenResponse())

    client = auth_app.app.test_client()
    response = client.post("/token", json={"username": "alice", "password": "alice"})

    assert response.status_code == 200
    assert response.get_json()["access_token"] == "abc"


def test_introspect_requires_token():
    client = auth_app.app.test_client()
    response = client.post("/introspect", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "token_required"


def test_introspect_uses_keycloak_then_caches(monkeypatch):
    monkeypatch.setattr(auth_app, "redis_client", _MemoryRedis())
    monkeypatch.setattr(auth_app.requests, "get", lambda *args, **kwargs: _DummyUserInfoResponse())

    client = auth_app.app.test_client()

    first = client.post("/introspect", json={"token": "t1"})
    second = client.post("/introspect", json={"token": "t1"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json()["preferred_username"] == "alice"
    assert second.get_json()["preferred_username"] == "alice"
    assert first.get_json()["active"] is True
