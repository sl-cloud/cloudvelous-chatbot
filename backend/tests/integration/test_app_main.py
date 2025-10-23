"""Smoke tests for root FastAPI endpoints."""

from __future__ import annotations


def test_root_endpoint_returns_metadata(api_client) -> None:
    response = api_client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Cloudvelous Chat Assistant API"
    assert payload["status"].startswith("Phase")


def test_health_endpoint_reports_healthy(api_client) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"

