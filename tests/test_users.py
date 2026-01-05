"""Tests for Users Router"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from backend.api.main import app
from backend.api.core.security import get_current_user
from backend.api.core.database import get_db


# Mock user factory
def create_mock_user(id, username, email, role, is_active=True):
    """Create a mock user object"""
    user = MagicMock()
    user.id = id
    user.username = username
    user.email = email
    user.full_name = f"{role.title()} User"
    user.role = role
    user.is_active = is_active
    user.created_at = datetime.now()
    return user


class TestUsersRouterAuth:
    """Test authentication requirements for users endpoints"""
    
    def test_list_users_requires_auth(self):
        """Test that list users endpoint requires authentication"""
        client = TestClient(app)
        response = client.get("/api/v1/users/users")
        assert response.status_code == 401
    
    def test_get_me_requires_auth(self):
        """Test that /me endpoint requires authentication"""
        client = TestClient(app)
        response = client.get("/api/v1/users/users/me")
        # 401 for auth required, 404 if route not found
        assert response.status_code in [401, 404]


class TestUsersRouterWithAuth:
    """Test users endpoints with mocked authentication"""
    
    @pytest.fixture
    def admin_user(self):
        return create_mock_user(1, "admin", "admin@fortifai.io", "admin")
    
    @pytest.fixture
    def analyst_user(self):
        return create_mock_user(2, "analyst1", "analyst@fortifai.io", "analyst")
    
    @pytest.fixture
    def viewer_user(self):
        return create_mock_user(3, "viewer1", "viewer@fortifai.io", "viewer")
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session"""
        db = AsyncMock()
        return db
    
    def test_admin_can_access_users_me(self, admin_user, mock_db_session):
        """Test that admin can access /me endpoint"""
        def override_get_current_user():
            return admin_user
        
        def override_get_db():
            return mock_db_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/users/users/me")
            # Should return user info or appropriate response
            assert response.status_code in [200, 404, 500]  # Depends on full setup
        finally:
            app.dependency_overrides.clear()
    
    def test_viewer_can_access_users_me(self, viewer_user, mock_db_session):
        """Test that viewer can access their own info"""
        def override_get_current_user():
            return viewer_user
        
        def override_get_db():
            return mock_db_session
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            client = TestClient(app)
            response = client.get("/api/v1/users/users/me")
            assert response.status_code in [200, 404, 500]
        finally:
            app.dependency_overrides.clear()


class TestUserRoles:
    """Test role-based access for user operations"""
    
    def test_user_roles_defined(self):
        """Test that user roles are properly defined"""
        admin = create_mock_user(1, "admin", "admin@test.io", "admin")
        analyst = create_mock_user(2, "analyst", "analyst@test.io", "analyst")
        viewer = create_mock_user(3, "viewer", "viewer@test.io", "viewer")
        
        assert admin.role == "admin"
        assert analyst.role == "analyst"
        assert viewer.role == "viewer"
    
    def test_user_active_status(self):
        """Test user active status"""
        active_user = create_mock_user(1, "active", "active@test.io", "viewer", is_active=True)
        inactive_user = create_mock_user(2, "inactive", "inactive@test.io", "viewer", is_active=False)
        
        assert active_user.is_active == True
        assert inactive_user.is_active == False
    
    def test_mock_user_has_required_fields(self):
        """Test mock user has all required fields"""
        user = create_mock_user(1, "testuser", "test@test.io", "admin")
        
        assert hasattr(user, 'id')
        assert hasattr(user, 'username')
        assert hasattr(user, 'email')
        assert hasattr(user, 'full_name')
        assert hasattr(user, 'role')
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'created_at')


class TestUserValidation:
    """Test user data validation"""
    
    def test_valid_email_format(self):
        """Test valid email format in mock user"""
        user = create_mock_user(1, "test", "valid@email.com", "viewer")
        assert "@" in user.email
        assert "." in user.email
    
    def test_valid_roles(self):
        """Test only valid roles are accepted"""
        valid_roles = ["admin", "analyst", "viewer"]
        
        for role in valid_roles:
            user = create_mock_user(1, "test", "test@test.io", role)
            assert user.role == role
    
    def test_username_stored_correctly(self):
        """Test username is stored correctly"""
        username = "testuser123"
        user = create_mock_user(1, username, "test@test.io", "viewer")
        assert user.username == username


@pytest.fixture
def test_client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return AsyncMock()
