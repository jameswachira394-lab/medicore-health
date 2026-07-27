import httpx
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert "auth" in r.json()["routes"]


def test_unknown_prefix_returns_404():
    r = client.get("/unknown-service/whatever")
    assert r.status_code == 404


@patch("app.routers.proxy.httpx.AsyncClient")
def test_proxies_to_auth_service(mock_client_cls):
    mock_response = httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", "http://x"))
    mock_instance = AsyncMock()
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_client_cls.return_value.__aenter__.return_value = mock_instance

    r = client.get("/auth/me", headers={"Authorization": "Bearer faketoken"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    called_url = mock_instance.request.call_args.args[1]
    assert called_url == "http://auth-service:8000/auth/me"
