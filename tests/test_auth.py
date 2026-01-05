"""
FortifAI Authentication Tests
"""
import pytest
import importlib

auth_service = importlib.import_module('backend.auth-service.main')
AuthService = auth_service.AuthService

class TestAuthService:
    """Tests for AuthService"""
    
    def setup_method(self):
        self.auth = AuthService()
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = self.auth.get_password_hash(password)
        
        assert hashed != password
        assert self.auth.verify_password(password, hashed)
        assert not self.auth.verify_password("wrong_password", hashed)
    
    def test_create_access_token(self):
        """Test access token creation"""
        token = self.auth.create_access_token({"sub": "testuser", "role": "viewer"})
        
        assert token is not None
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = self.auth.create_refresh_token({"sub": "testuser", "role": "viewer"})
        
        assert token is not None
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Test decoding valid token"""
        token = self.auth.create_access_token({"sub": "testuser", "role": "admin"})
        decoded = self.auth.decode_token(token)
        
        assert decoded is not None
        assert decoded.username == "testuser"
        assert decoded.role == "admin"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        decoded = self.auth.decode_token("invalid_token_here")
        
        assert decoded is None
