"""
Integration tests for Phase 3 endpoints.

These tests verify that the admin training interface API endpoints
work correctly with authentication and database operations.
"""

import pytest
from datetime import timedelta

from app.main import app
from app.middleware.auth import create_access_token
from app.config import settings
from app.models import get_db, TrainingSession
from tests.conftest import StubDBSession


@pytest.fixture
def admin_token():
    """Create a valid admin JWT token."""
    data = {"sub": "admin", "role": "admin"}
    return create_access_token(data, expires_delta=timedelta(hours=1))


@pytest.fixture
def admin_api_key():
    """Get the admin API key."""
    return settings.ADMIN_API_KEY


class TestAuthentication:
    """Test authentication requirements."""

    def test_protected_endpoint_without_auth(self, api_client):
        """Test that protected endpoints require authentication."""
        # Try to access admin stats without authentication
        response = api_client.get("/api/admin/stats")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, api_client):
        """Test that invalid tokens are rejected."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = api_client.get("/api/admin/stats", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self, api_client, admin_token):
        """Test that valid JWT tokens are accepted."""
        db = StubDBSession()

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = api_client.get("/api/admin/stats", headers=headers)
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_protected_endpoint_with_api_key(self, api_client, admin_api_key):
        """Test that valid API keys are accepted."""
        db = StubDBSession()

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"X-API-Key": admin_api_key}
            response = api_client.get("/api/admin/stats", headers=headers)
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestEmbeddingInspector:
    """Test embedding inspector endpoint."""

    def test_inspector_requires_auth(self, api_client):
        """Test that inspector requires authentication."""
        response = api_client.get("/api/embedding-inspector/1")
        assert response.status_code == 401

    def test_inspector_with_invalid_session(self, api_client, admin_token):
        """Test inspector with non-existent session."""
        db = StubDBSession()

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = api_client.get("/api/embedding-inspector/999999", headers=headers)
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestAdminEndpoints:
    """Test admin management endpoints."""

    def test_sessions_list_requires_auth(self, api_client):
        """Test that session listing requires authentication."""
        response = api_client.post("/api/admin/sessions", json={
            "page": 1,
            "page_size": 20
        })
        assert response.status_code == 401

    def test_sessions_list_with_auth(self, api_client, admin_token):
        """Test session listing with valid authentication."""
        db = StubDBSession()

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = api_client.post("/api/admin/sessions", json={
                "page": 1,
                "page_size": 20,
                "sort_by": "created_at",
                "sort_order": "desc"
            }, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "sessions" in data
            assert "total_count" in data
            assert "page" in data
            assert "page_size" in data
            assert "total_pages" in data
        finally:
            app.dependency_overrides.clear()

    def test_stats_endpoint_with_auth(self, api_client, admin_token):
        """Test stats endpoint with authentication."""
        db = StubDBSession()

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = api_client.get("/api/admin/stats", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "accuracy_stats" in data
            assert "provider_stats" in data
            assert "top_performing_chunks" in data
            assert "underperforming_chunks" in data
        finally:
            app.dependency_overrides.clear()


class TestWorkflowSearch:
    """Test workflow search endpoints."""

    def test_workflow_search_requires_auth(self, api_client):
        """Test that workflow search requires authentication."""
        response = api_client.post("/api/workflows/search", json={
            "query_text": "test query",
            "top_k": 5
        })
        assert response.status_code == 401

    def test_workflow_search_with_auth(self, api_client, admin_token, monkeypatch):
        """Test workflow search with valid authentication."""
        db = StubDBSession()

        # Stub the embedder
        class StubEmbedder:
            def embed_text(self, text):
                return [0.1] * 8

        monkeypatch.setattr("app.routers.workflows.get_embedder", lambda: StubEmbedder())

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = api_client.post("/api/workflows/search", json={
                "query_text": "How do I configure Docker?",
                "successful_only": False,
                "min_similarity": 0.7,
                "top_k": 5
            }, headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "total_found" in data
            assert "query_text" in data
        finally:
            app.dependency_overrides.clear()

    def test_workflow_search_requires_query(self, api_client, admin_token):
        """Test that workflow search requires a query."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.post("/api/workflows/search", json={
            "top_k": 5
            # Missing query_text or query_embedding
        }, headers=headers)

        assert response.status_code == 400


class TestTrainingEndpoint:
    """Test enhanced training endpoint."""

    def test_training_requires_auth(self, api_client):
        """Test that training endpoint now requires authentication."""
        response = api_client.post("/api/train", json={
            "session_id": 1,
            "is_correct": True,
            "feedback_type": "correct"
        })
        assert response.status_code == 401

    def test_training_with_auth_invalid_session(self, api_client, admin_token):
        """Test training with non-existent session."""
        db = StubDBSession()

        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = api_client.post("/api/train", json={
                "session_id": 999999,
                "is_correct": True,
                "feedback_type": "correct"
            }, headers=headers)

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test that health endpoints remain public."""

    def test_root_endpoint_public(self, api_client):
        """Test that root endpoint doesn't require auth."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "0.3.0"

    def test_health_endpoint_public(self, api_client):
        """Test that health endpoint doesn't require auth."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.3.0"
