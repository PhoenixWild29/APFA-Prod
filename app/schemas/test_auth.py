"""
Test file for authentication schemas
Run with: python -m pytest app/schemas/test_auth.py
"""
from datetime import datetime, timezone, timedelta
from app.schemas.auth import User, Token, TokenPayload, ALLOWED_PERMISSIONS
import uuid


def test_user_creation():
    """Test creating a valid User"""
    user = User(
        username="john_doe",
        hashed_password="$2b$12$KIXwfGqW.vQNfB8p5K7TgOZhHhYXz5JX8qE4nJ0Vc7eP3aK4X5Yzi",
        disabled=False,
        full_name="John Doe",
        email="john@example.com"
    )
    
    assert user.username == "john_doe"
    assert user.disabled is False
    assert user.full_name == "John Doe"
    print("✅ User creation test passed")


def test_user_username_validation():
    """Test username format validation"""
    # Valid usernames
    valid_user = User(
        username="valid_user-123",
        hashed_password="$2b$12$test"
    )
    assert valid_user.username == "valid_user-123"
    
    # Invalid: starts with -
    try:
        User(username="-invalid", hashed_password="$2b$12$test")
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    # Invalid: ends with _
    try:
        User(username="invalid_", hashed_password="$2b$12$test")
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    print("✅ Username validation test passed")


def test_token_creation():
    """Test creating a valid Token"""
    token = Token(
        access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc",
        token_type="Bearer"
    )
    
    assert token.access_token.startswith("eyJ")
    assert token.token_type == "bearer"  # Should be lowercased
    print("✅ Token creation test passed")


def test_token_type_lowercase():
    """Test that token_type is automatically lowercased"""
    token = Token(
        access_token="test_token",
        token_type="BEARER"
    )
    
    assert token.token_type == "bearer"
    print("✅ Token type lowercase test passed")


def test_token_payload_creation():
    """Test creating a valid TokenPayload"""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    
    payload = TokenPayload(
        sub="john_doe",
        exp=future_time,
        permissions=["advice:generate", "advice:view_history"],
        session_id="sess_abc123"
    )
    
    assert payload.sub == "john_doe"
    assert payload.exp > datetime.now(timezone.utc)
    assert len(payload.permissions) == 2
    # jti should be auto-generated as UUID
    assert len(payload.jti) == 36
    print("✅ TokenPayload creation test passed")


def test_token_payload_permissions_validation():
    """Test permission validation against allowed set"""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Valid permissions
    valid_payload = TokenPayload(
        sub="user1",
        exp=future_time,
        permissions=["advice:generate", "admin:celery:view"],
        session_id="sess_123"
    )
    assert len(valid_payload.permissions) == 2
    
    # Invalid permission
    try:
        TokenPayload(
            sub="user2",
            exp=future_time,
            permissions=["invalid:permission"],
            session_id="sess_456"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "Invalid permissions" in str(e)
    
    print("✅ Permissions validation test passed")


def test_token_payload_permissions_deduplication():
    """Test that duplicate permissions are removed"""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    
    payload = TokenPayload(
        sub="user3",
        exp=future_time,
        permissions=["advice:generate", "advice:view_history", "advice:generate"],  # Duplicate
        session_id="sess_789"
    )
    
    # Should have deduplicated to 2 unique permissions
    assert len(payload.permissions) == 2
    assert "advice:generate" in payload.permissions
    assert "advice:view_history" in payload.permissions
    print("✅ Permissions deduplication test passed")


def test_token_payload_expiration_validation():
    """Test that expiration must be in the future"""
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    # Past expiration should fail
    try:
        TokenPayload(
            sub="user4",
            exp=past_time,
            session_id="sess_abc"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "future" in str(e).lower()
    
    print("✅ Expiration validation test passed")


def test_token_payload_timezone_aware():
    """Test that datetime fields are timezone-aware"""
    # Naive datetime should be converted to UTC
    naive_exp = datetime.now() + timedelta(hours=1)
    naive_iat = datetime.now()
    
    payload = TokenPayload(
        sub="user5",
        exp=naive_exp,
        iat=naive_iat,
        session_id="sess_xyz"
    )
    
    assert payload.exp.tzinfo is not None
    assert payload.iat.tzinfo is not None
    assert payload.exp.tzinfo == timezone.utc
    assert payload.iat.tzinfo == timezone.utc
    print("✅ Timezone-aware datetime test passed")


def test_token_payload_jti_validation():
    """Test JTI UUID validation"""
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Valid UUID
    valid_uuid = str(uuid.uuid4())
    payload = TokenPayload(
        sub="user6",
        exp=future_time,
        jti=valid_uuid,
        session_id="sess_123"
    )
    assert payload.jti == valid_uuid
    
    # Invalid UUID
    try:
        TokenPayload(
            sub="user7",
            exp=future_time,
            jti="not-a-valid-uuid",
            session_id="sess_456"
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "UUID" in str(e)
    
    print("✅ JTI UUID validation test passed")


def test_json_serialization():
    """Test JSON serialization of models"""
    user = User(
        username="test_user",
        hashed_password="$2b$12$test",
        disabled=False
    )
    
    token = Token(
        access_token="test_token_string",
        token_type="bearer"
    )
    
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = TokenPayload(
        sub="test_user",
        exp=future_time,
        permissions=["advice:generate"],
        session_id="sess_test"
    )
    
    # Test serialization
    user_json = user.model_dump_json()
    token_json = token.model_dump_json()
    payload_json = payload.model_dump_json()
    
    assert "test_user" in user_json
    assert "bearer" in token_json
    assert "advice:generate" in payload_json
    
    print("✅ JSON serialization test passed")


if __name__ == "__main__":
    print("Running authentication schema tests...\n")
    test_user_creation()
    test_user_username_validation()
    test_token_creation()
    test_token_type_lowercase()
    test_token_payload_creation()
    test_token_payload_permissions_validation()
    test_token_payload_permissions_deduplication()
    test_token_payload_expiration_validation()
    test_token_payload_timezone_aware()
    test_token_payload_jti_validation()
    test_json_serialization()
    print("\n✅ All tests passed!")

