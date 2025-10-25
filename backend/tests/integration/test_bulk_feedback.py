"""
Integration tests for bulk feedback partial failures.

These tests verify that the bulk feedback endpoint handles partial
failures gracefully and returns appropriate results for each item.
"""

import pytest
from datetime import datetime, timezone
from datetime import timedelta

from app.main import app
from app.middleware.auth import create_access_token
from app.config import settings
from app.models import get_db, TrainingSession, EmbeddingLink, KnowledgeChunk
from tests.conftest import StubDBSession, StubQuery


@pytest.fixture
def admin_token():
    """Create a valid admin JWT token."""
    data = {"sub": "admin", "role": "admin"}
    return create_access_token(data, expires_delta=timedelta(hours=1))


class TestBulkFeedbackPartialFailures:
    """Test bulk feedback with partial failures."""

    def test_bulk_feedback_with_some_invalid_sessions(self, api_client, admin_token):
        """Test bulk feedback where some sessions don't exist."""
        db = StubDBSession()
        
        # Add valid session
        session1 = TrainingSession(
            id=1,
            query="test query 1",
            response="test response 1",
            llm_provider="openai",
            llm_model="gpt-4",
            has_feedback=0,
            is_correct=None,
            created_at=datetime.now(timezone.utc)
        )
        
        # StubQuery doesn't filter, so we need a custom query handler
        # that returns different results based on queries
        query_count = [0]  # Use list to allow mutation in nested function
        
        def custom_query(model):
            query_count[0] += 1
            # First query (session_id=1) should return session1
            if query_count[0] == 1:
                return StubQuery([session1])
            # Subsequent queries (session_id=999, 998) should return empty
            else:
                return StubQuery([])
        
        # Override the query method
        db.query = custom_query
        
        # Also need to handle EmbeddingLink queries (return empty for all)
        original_query = db.query
        def smart_query(model):
            if model == EmbeddingLink:
                return StubQuery([])
            return original_query(model)
        db.query = smart_query
        
        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Submit feedback for 3 sessions: 1 valid, 2 invalid
            request_data = {
                "feedback_items": [
                    {
                        "session_id": 1,
                        "feedback_type": "positive",
                        "is_correct": True,
                        "chunk_feedback": []
                    },
                    {
                        "session_id": 999,  # Invalid session
                        "feedback_type": "positive",
                        "is_correct": True,
                        "chunk_feedback": []
                    },
                    {
                        "session_id": 998,  # Invalid session
                        "feedback_type": "negative",
                        "is_correct": False,
                        "chunk_feedback": []
                    }
                ]
            }
            
            response = api_client.post(
                "/api/admin/bulk-feedback",
                json=request_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Check results
            assert data["total_processed"] == 3
            assert data["successful"] == 1
            assert data["failed"] == 2
            
            # Check individual results
            results = data["results"]
            assert len(results) == 3
            
            # First should succeed
            assert results[0]["session_id"] == 1
            assert results[0]["success"] is True
            
            # Second and third should fail
            assert results[1]["session_id"] == 999
            assert results[1]["success"] is False
            assert "not found" in results[1]["error"].lower()
            
            assert results[2]["session_id"] == 998
            assert results[2]["success"] is False
            assert "not found" in results[2]["error"].lower()
            
        finally:
            app.dependency_overrides.clear()

    def test_bulk_feedback_exceeds_max_size(self, api_client, admin_token):
        """Test bulk feedback with too many items."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create request with more items than MAX_BULK_FEEDBACK_SIZE
        max_size = settings.MAX_BULK_FEEDBACK_SIZE
        feedback_items = [
            {
                "session_id": i,
                "feedback_type": "positive",
                "is_correct": True,
                "chunk_feedback": []
            }
            for i in range(max_size + 1)
        ]
        
        request_data = {"feedback_items": feedback_items}
        
        response = api_client.post(
            "/api/admin/bulk-feedback",
            json=request_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"].lower()

    def test_bulk_feedback_with_chunk_feedback_errors(self, api_client, admin_token):
        """Test bulk feedback with invalid chunk feedback."""
        db = StubDBSession()
        
        # Add valid session
        session1 = TrainingSession(
            id=1,
            query="test query",
            response="test response",
            llm_provider="openai",
            llm_model="gpt-4",
            has_feedback=0,
            is_correct=None,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add_query_result(TrainingSession, [session1])
        # No embedding links, so chunk feedback will fail
        db.add_query_result(EmbeddingLink, [])
        
        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            request_data = {
                "feedback_items": [
                    {
                        "session_id": 1,
                        "feedback_type": "positive",
                        "is_correct": True,
                        "chunk_feedback": [
                            {
                                "chunk_id": 999,  # Non-existent chunk
                                "was_useful": True
                            }
                        ]
                    }
                ]
            }
            
            response = api_client.post(
                "/api/admin/bulk-feedback",
                json=request_data,
                headers=headers
            )
            
            # Should still succeed but with warnings about chunks
            assert response.status_code == 200
            data = response.json()
            assert data["total_processed"] == 1
            
        finally:
            app.dependency_overrides.clear()

    def test_bulk_feedback_empty_list(self, api_client, admin_token):
        """Test bulk feedback with empty list."""
        db = StubDBSession()
        
        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            request_data = {"feedback_items": []}
            
            response = api_client.post(
                "/api/admin/bulk-feedback",
                json=request_data,
                headers=headers
            )
            
            # Empty list should succeed with 0 items processed
            assert response.status_code == 200
            data = response.json()
            assert data["total_processed"] == 0
            assert data["successful"] == 0
            assert data["failed"] == 0
            
        finally:
            app.dependency_overrides.clear()

    def test_bulk_feedback_all_failures(self, api_client, admin_token):
        """Test bulk feedback where all items fail."""
        db = StubDBSession()
        
        # No sessions in DB
        db.add_query_result(TrainingSession, [])
        
        def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            request_data = {
                "feedback_items": [
                    {
                        "session_id": 1,
                        "feedback_type": "positive",
                        "is_correct": True,
                        "chunk_feedback": []
                    },
                    {
                        "session_id": 2,
                        "feedback_type": "negative",
                        "is_correct": False,
                        "chunk_feedback": []
                    }
                ]
            }
            
            response = api_client.post(
                "/api/admin/bulk-feedback",
                json=request_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_processed"] == 2
            assert data["successful"] == 0
            assert data["failed"] == 2
            
            # All results should have errors
            for result in data["results"]:
                assert result["success"] is False
                assert "error" in result
                
        finally:
            app.dependency_overrides.clear()

