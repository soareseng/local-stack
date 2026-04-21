import pytest

from conftest import load_service_module


@pytest.mark.parametrize("service_name", ["auth-api", "user-api", "billing-api", "ml-api"])
def test_health_endpoint(service_name):
    module = load_service_module(service_name)
    client = module.app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["service"] == service_name
    assert response.get_json()["status"] == "ok"
