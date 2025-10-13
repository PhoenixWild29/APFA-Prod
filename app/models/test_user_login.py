"""
Test file for user login models
Run with: python -m pytest app/models/test_user_login.py
"""
from datetime import datetime, timezone
from app.models.user_login import UserLoginRequest, LoginResponse
from app.models.user_profile import UserProfile, SessionMetadata, UserRole


def test_user_login_request_basic():
    """Test creating a basic UserLoginRequest"""
    request = UserLoginRequest(
        username="john_doe",
        password="SecurePass123!"
    )
    
    assert request.username == "john_doe"
    assert request.password == "SecurePass123!"
    assert request.remember_me is False  # Default
    assert request.mfa_token is None
    print("✅ Basic login request test passed")


def test_user_login_request_with_mfa():
    """Test UserLoginRequest with MFA token"""
    request = UserLoginRequest(
        username="admin_user",
        password="AdminPass456!",
        remember_me=True,
        mfa_token="123456",
        device_fingerprint="fp_device123"
    )
    
    assert request.mfa_token == "123456"
    assert request.device_fingerprint == "fp_device123"
    assert request.remember_me is True
    print("✅ Login request with MFA test passed")


def test_user_login_request_with_metadata():
    """Test UserLoginRequest with client metadata"""
    request = UserLoginRequest(
        username="test_user",
        password="TestPass789!",
        client_metadata={
            "browser": "Chrome",
            "browser_version": "118.0",
            "os": "Windows",
            "device_type": "desktop"
        }
    )
    
    assert request.client_metadata["browser"] == "Chrome"
    assert request.client_metadata["os"] == "Windows"
    print("✅ Login request with metadata test passed")


def test_login_response_creation():
    """Test creating a LoginResponse"""
    # Create user profile
    user_profile = UserProfile(
        user_id="user_12345",
        username="john_doe",
        email="john@example.com",
        role=UserRole.ADVISOR,
        permissions=["advice:generate", "advice:view_history"]
    )
    
    # Create session metadata
    session_metadata = SessionMetadata(
        user_id="user_12345",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0"
    )
    
    # Create login response
    response = LoginResponse(
        access_token="eyJhbGciOiJIUzI1NiIs...",
        refresh_token="eyJhbGciOiJIUzI1NiIs...",
        token_type="bearer",
        expires_in=1800,
        user_profile=user_profile,
        session_metadata=session_metadata,
        requires_mfa=False,
        mfa_methods=[]
    )
    
    assert response.access_token.startswith("eyJ")
    assert response.token_type == "bearer"
    assert response.expires_in == 1800
    assert response.user_profile.username == "john_doe"
    assert response.session_metadata.user_id == "user_12345"
    assert response.requires_mfa is False
    print("✅ Login response creation test passed")


def test_login_response_with_mfa():
    """Test LoginResponse requiring MFA"""
    user_profile = UserProfile(
        user_id="user_999",
        username="mfa_user",
        email="mfa@example.com",
        role=UserRole.ADMIN,
        security_settings={"mfa_enabled": True}
    )
    
    session_metadata = SessionMetadata(
        user_id="user_999",
        ip_address="10.0.0.1",
        user_agent="Test"
    )
    
    response = LoginResponse(
        access_token="temporary_token",
        refresh_token="",
        expires_in=300,  # 5 minutes for MFA completion
        user_profile=user_profile,
        session_metadata=session_metadata,
        requires_mfa=True,
        mfa_methods=["totp", "sms"]
    )
    
    assert response.requires_mfa is True
    assert len(response.mfa_methods) == 2
    assert "totp" in response.mfa_methods
    print("✅ Login response with MFA test passed")


def test_username_validation():
    """Test username length validation"""
    # Too short
    try:
        UserLoginRequest(username="ab", password="Pass123!")
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    # Too long
    try:
        UserLoginRequest(
            username="a" * 51,  # 51 characters
            password="Pass123!"
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    # Valid
    request = UserLoginRequest(username="valid_user", password="Pass123!")
    assert request.username == "valid_user"
    
    print("✅ Username validation test passed")


def test_mfa_token_validation():
    """Test MFA token length validation"""
    # Too short
    try:
        UserLoginRequest(
            username="user",
            password="Pass123!",
            mfa_token="123"  # Only 3 digits
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    # Too long
    try:
        UserLoginRequest(
            username="user",
            password="Pass123!",
            mfa_token="12345678901"  # 11 digits
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    # Valid
    request = UserLoginRequest(
        username="user",
        password="Pass123!",
        mfa_token="123456"
    )
    assert request.mfa_token == "123456"
    
    print("✅ MFA token validation test passed")


def test_json_serialization():
    """Test JSON serialization of models"""
    request = UserLoginRequest(
        username="json_user",
        password="JsonPass123!",
        remember_me=True
    )
    
    user_profile = UserProfile(
        user_id="user_json",
        username="json_user",
        email="json@test.com",
        role=UserRole.STANDARD
    )
    
    session_metadata = SessionMetadata(
        user_id="user_json",
        ip_address="192.168.1.1",
        user_agent="Test"
    )
    
    response = LoginResponse(
        access_token="test_token",
        refresh_token="test_refresh",
        expires_in=1800,
        user_profile=user_profile,
        session_metadata=session_metadata
    )
    
    request_json = request.model_dump_json()
    response_json = response.model_dump_json()
    
    assert "json_user" in request_json
    assert "test_token" in response_json
    
    print("✅ JSON serialization test passed")


if __name__ == "__main__":
    print("Running user login model tests...\n")
    test_user_login_request_basic()
    test_user_login_request_with_mfa()
    test_user_login_request_with_metadata()
    test_login_response_creation()
    test_login_response_with_mfa()
    test_username_validation()
    test_mfa_token_validation()
    test_json_serialization()
    print("\n✅ All tests passed!")

