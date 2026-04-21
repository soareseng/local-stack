import pytest

import common.base_service as base_service
from conftest import load_service_module


class _DummyResponse:
    status_code = 200

    @staticmethod
    def json():
        return {"preferred_username": "alice", "active": True}


@pytest.mark.parametrize(
    "service_name,route",
    [
        ("user-api", "/users"),
        ("billing-api", "/payments"),
        ("ml-api", "/predict"),
    ],
)
def test_protected_route_requires_token(service_name, route):
    module = load_service_module(service_name)
    client = module.app.test_client()

    response = client.get(route)

    assert response.status_code == 401
    assert response.get_json()["error"] == "missing_bearer_token"


@pytest.mark.parametrize(
    "service_name,route",
    [
        ("user-api", "/users"),
        ("billing-api", "/payments"),
        ("ml-api", "/predict"),
    ],
)
def test_protected_route_accepts_valid_token(monkeypatch, service_name, route):
    monkeypatch.setattr(base_service.requests, "post", lambda *args, **kwargs: _DummyResponse())

    module = load_service_module(service_name)
    client = module.app.test_client()

    response = client.get(route, headers={"Authorization": "Bearer valid-token"})

    assert response.status_code == 200
    assert response.get_json()["requested_by"] == "alice"
