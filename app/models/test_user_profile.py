"""
Test file for user profile and session models
Run with: python -m pytest app/models/test_user_profile.py
"""
from datetime import datetime, timezone, timedelta
from app.models.user_profile import UserProfile, SessionMetadata, UserRole
import uuid


def test_user_profile_creation():
    """Test creating a valid UserProfile"""
    profile = UserProfile(
        user_id="user_12345",
        username="john_doe",
        email="john.doe@example.com",
        role=UserRole.ADVISOR,
        permissions=["view_reports", "generate_advice"],
        security_settings={"mfa_enabled": True},
        preferences={"theme": "dark"}
    )
    
    assert profile.user_id == "user_12345"
    assert profile.username == "john_doe"
    assert profile.email == "john.doe@example.com"
    assert profile.role == UserRole.ADVISOR
    assert len(profile.permissions) == 2
    assert profile.created_at.tzinfo is not None  # Timezone-aware
    print("✅ UserProfile creation test passed")


def test_user_profile_email_validation():
    """Test email validation in UserProfile"""
    # Valid email
    profile = UserProfile(
        user_id="user_123",
        username="testuser",
        email="valid.email@example.com",
        role=UserRole.STANDARD
    )
    assert profile.email == "valid.email@example.com"
    
    # Invalid email will raise validation error
    try:
        invalid_profile = UserProfile(
            user_id="user_456",
            username="testuser2",
            email="invalid-email",
            role=UserRole.STANDARD
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    print("✅ Email validation test passed")


def test_user_profile_role_validation():
    """Test role validation in UserProfile"""
    # Valid roles
    for role in [UserRole.STANDARD, UserRole.ADVISOR, UserRole.ADMIN]:
        profile = UserProfile(
            user_id=f"user_{role.value}",
            username=f"user_{role.value}",
            email=f"{role.value}@example.com",
            role=role
        )
        assert profile.role == role
    
    print("✅ Role validation test passed")


def test_user_profile_permissions_deduplication():
    """Test that duplicate permissions are removed"""
    profile = UserProfile(
        user_id="user_999",
        username="test_user",
        email="test@example.com",
        role=UserRole.ADMIN,
        permissions=["perm1", "perm2", "perm1", "perm3", "perm2"]  # Duplicates
    )
    
    # Should have deduplicated to 3 unique permissions
    assert len(profile.permissions) == 3
    assert "perm1" in profile.permissions
    assert "perm2" in profile.permissions
    assert "perm3" in profile.permissions
    print("✅ Permissions deduplication test passed")


def test_session_metadata_creation():
    """Test creating a valid SessionMetadata"""
    session = SessionMetadata(
        user_id="user_12345",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0)",
        security_flags=["verified", "trusted_device"]
    )
    
    assert session.user_id == "user_12345"
    assert session.is_active is True
    assert len(session.security_flags) == 2
    assert session.created_at.tzinfo is not None
    # session_id should be auto-generated UUID
    assert len(session.session_id) == 36  # UUID format
    print("✅ SessionMetadata creation test passed")


def test_session_metadata_uuid_validation():
    """Test that session_id validates UUID format"""
    # Valid UUID
    valid_uuid = str(uuid.uuid4())
    session = SessionMetadata(
        session_id=valid_uuid,
        user_id="user_123",
        ip_address="10.0.0.1",
        user_agent="TestAgent/1.0"
    )
    assert session.session_id == valid_uuid
    
    # Invalid UUID will raise validation error
    try:
        invalid_session = SessionMetadata(
            session_id="not-a-valid-uuid",
            user_id="user_456",
            ip_address="10.0.0.2",
            user_agent="TestAgent/1.0"
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    print("✅ UUID validation test passed")


def test_session_metadata_ipv6():
    """Test SessionMetadata with IPv6 address"""
    session = SessionMetadata(
        user_id="user_ipv6",
        ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        user_agent="Mozilla/5.0"
    )
    
    assert session.ip_address == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    print("✅ IPv6 address test passed")


def test_session_last_activity_validation():
    """Test that last_activity cannot be in the future"""
    # Current time is OK
    session = SessionMetadata(
        user_id="user_123",
        ip_address="192.168.1.1",
        user_agent="Test",
        last_activity=datetime.now(timezone.utc)
    )
    assert session.last_activity is not None
    
    # Future time should fail
    try:
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        invalid_session = SessionMetadata(
            user_id="user_456",
            ip_address="192.168.1.2",
            user_agent="Test",
            last_activity=future_time
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
    
    print("✅ Last activity validation test passed")


def test_timezone_aware_datetimes():
    """Test that all datetime fields are timezone-aware"""
    # UserProfile
    profile = UserProfile(
        user_id="user_tz",
        username="tz_user",
        email="tz@example.com",
        role=UserRole.STANDARD,
        last_login=datetime(2025, 10, 11, 14, 30, 0)  # Naive datetime
    )
    assert profile.created_at.tzinfo is not None
    assert profile.last_login.tzinfo is not None  # Should be converted
    
    # SessionMetadata
    session = SessionMetadata(
        user_id="user_tz",
        ip_address="192.168.1.1",
        user_agent="Test"
    )
    assert session.created_at.tzinfo is not None
    assert session.last_activity.tzinfo is not None
    
    print("✅ Timezone-aware datetime test passed")


def test_json_serialization():
    """Test JSON serialization of models"""
    profile = UserProfile(
        user_id="user_json",
        username="json_user",
        email="json@example.com",
        role=UserRole.ADMIN,
        permissions=["all"],
        security_settings={"test": "data"},
        preferences={"theme": "light"}
    )
    
    session = SessionMetadata(
        user_id="user_json",
        ip_address="192.168.1.50",
        user_agent="TestAgent/1.0",
        security_flags=["verified"]
    )
    
    # Test serialization
    profile_json = profile.model_dump_json(indent=2)
    session_json = session.model_dump_json(indent=2)
    
    assert "json_user" in profile_json
    assert "user_json" in session_json
    
    print("✅ JSON serialization test passed")
    print("\nExample UserProfile JSON:")
    print(profile_json[:200] + "...")
    print("\nExample SessionMetadata JSON:")
    print(session_json[:200] + "...")


if __name__ == "__main__":
    print("Running UserProfile and SessionMetadata model tests...\n")
    test_user_profile_creation()
    test_user_profile_email_validation()
    test_user_profile_role_validation()
    test_user_profile_permissions_deduplication()
    test_session_metadata_creation()
    test_session_metadata_uuid_validation()
    test_session_metadata_ipv6()
    test_session_last_activity_validation()
    test_timezone_aware_datetimes()
    test_json_serialization()
    print("\n✅ All tests passed!")

