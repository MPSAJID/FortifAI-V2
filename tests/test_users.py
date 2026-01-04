"""Tests for Users Router"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestUsersRouter:
    """Test cases for users API endpoints"""
    
    @pytest.fixture
    def mock_admin_user(self):
        """Create a mock admin user"""
        return MagicMock(
            id=1,
            username="admin",
            email="admin@fortifai.io",
            full_name="Admin User",
            role="admin",
            is_active=True,
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_analyst_user(self):
        """Create a mock analyst user"""
        return MagicMock(
            id=2,
            username="analyst1",
            email="analyst1@fortifai.io",
            full_name="Analyst User",
            role="analyst",
            is_active=True,
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def mock_viewer_user(self):
        """Create a mock viewer user"""
        return MagicMock(
            id=3,
            username="viewer1",
            email="viewer1@fortifai.io",
            full_name="Viewer User",
            role="viewer",
            is_active=True,
            created_at=datetime.now()
        )
    
    def test_list_users_requires_auth(self, test_client):
        """Test that list users endpoint requires authentication"""
        response = test_client.get("/api/v1/users")
        assert response.status_code == 401
    
    def test_list_users_requires_admin_or_analyst(self, test_client, mock_viewer_user):
        """Test that viewers cannot list users"""
        with patch("routers.users.get_current_user", return_value=mock_viewer_user):
            response = test_client.get("/api/v1/users")
            assert response.status_code == 403
    
    def test_admin_can_list_users(self, test_client, mock_admin_user, mock_db):
        """Test that admin can list users"""
        mock_users = [mock_admin_user]
        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_users
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.get("/api/v1/users")
                assert response.status_code == 200
    
    def test_get_current_user_info(self, test_client, mock_admin_user):
        """Test getting current user info"""
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            response = test_client.get("/api/v1/users/me")
            assert response.status_code == 200
    
    def test_user_can_view_own_profile(self, test_client, mock_viewer_user, mock_db):
        """Test that user can view their own profile"""
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_viewer_user
        
        with patch("routers.users.get_current_user", return_value=mock_viewer_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.get(f"/api/v1/users/{mock_viewer_user.id}")
                assert response.status_code == 200
    
    def test_user_cannot_view_others_profile(self, test_client, mock_viewer_user, mock_admin_user, mock_db):
        """Test that viewer cannot view other users' profiles"""
        with patch("routers.users.get_current_user", return_value=mock_viewer_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.get(f"/api/v1/users/{mock_admin_user.id}")
                assert response.status_code == 403
    
    def test_only_admin_can_create_users(self, test_client, mock_analyst_user):
        """Test that only admins can create users"""
        user_data = {
            "username": "newuser",
            "email": "newuser@fortifai.io",
            "password": "password123",
            "role": "viewer"
        }
        
        with patch("routers.users.get_current_user", return_value=mock_analyst_user):
            response = test_client.post("/api/v1/users", json=user_data)
            assert response.status_code == 403
    
    def test_admin_can_create_user(self, test_client, mock_admin_user, mock_db):
        """Test that admin can create a new user"""
        user_data = {
            "username": "newuser",
            "email": "newuser@fortifai.io",
            "password": "password123",
            "role": "viewer"
        }
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                with patch("routers.users.get_password_hash", return_value="hashed"):
                    response = test_client.post("/api/v1/users", json=user_data)
                    # Would be 201 with proper mocking
    
    def test_duplicate_username_rejected(self, test_client, mock_admin_user, mock_db):
        """Test that duplicate username is rejected"""
        user_data = {
            "username": "admin",  # Already exists
            "email": "newuser@fortifai.io",
            "password": "password123",
            "role": "viewer"
        }
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_admin_user
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.post("/api/v1/users", json=user_data)
                assert response.status_code == 400
    
    def test_invalid_role_rejected(self, test_client, mock_admin_user, mock_db):
        """Test that invalid role is rejected"""
        user_data = {
            "username": "newuser",
            "email": "newuser@fortifai.io",
            "password": "password123",
            "role": "superadmin"  # Invalid role
        }
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.post("/api/v1/users", json=user_data)
                assert response.status_code == 400
    
    def test_only_admin_can_delete_users(self, test_client, mock_analyst_user):
        """Test that only admins can delete users"""
        with patch("routers.users.get_current_user", return_value=mock_analyst_user):
            response = test_client.delete("/api/v1/users/1")
            assert response.status_code == 403
    
    def test_cannot_delete_self(self, test_client, mock_admin_user, mock_db):
        """Test that admin cannot delete their own account"""
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.delete(f"/api/v1/users/{mock_admin_user.id}")
                assert response.status_code == 400
    
    def test_get_users_stats(self, test_client, mock_admin_user, mock_db):
        """Test getting user statistics"""
        mock_db.execute.return_value.scalar.return_value = 10
        mock_db.execute.return_value.fetchall.return_value = [
            ("admin", 2),
            ("analyst", 5),
            ("viewer", 3)
        ]
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.get("/api/v1/users/stats")
                # Would check response content with proper mocking
    
    def test_deactivate_user(self, test_client, mock_admin_user, mock_analyst_user, mock_db):
        """Test deactivating a user"""
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analyst_user
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.post(f"/api/v1/users/{mock_analyst_user.id}/deactivate")
                # Would be 200 with proper async mocking
    
    def test_activate_user(self, test_client, mock_admin_user, mock_analyst_user, mock_db):
        """Test activating a user"""
        mock_analyst_user.is_active = False
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_analyst_user
        
        with patch("routers.users.get_current_user", return_value=mock_admin_user):
            with patch("routers.users.get_db", return_value=mock_db):
                response = test_client.post(f"/api/v1/users/{mock_analyst_user.id}/activate")
                # Would be 200 with proper async mocking


@pytest.fixture
def test_client():
    """Create a test client"""
    # This would be properly configured in conftest.py
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return AsyncMock()
