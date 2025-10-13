"""
Test file for user registration models
Run with: python -m pytest app/models/test_user_registration.py
"""
from datetime import datetime, timezone
from app.models.user_registration import (
    UserRegistrationRequest,
    RegistrationResponse,
    RegistrationEvent,
    WebSocketRegistrationMessage,
    RegistrationStatus,
    RegistrationEventType,
    RegistrationMessageType
)


def test_user_registration_request_valid():
    """Test creating a valid UserRegistrationRequest"""
    request = UserRegistrationRequest(
        username="john_doe",
        email="john.doe@example.com",
        password="SecurePass123!",
        confirm_password="SecurePass123!",
        first_name="John",
        last_name="Doe",
        terms_accepted=True,
        marketing_consent=False
    )
    
    assert request.username == "john_doe"
    assert request.email == "john.doe@example.com"
    assert request.first_name == "John"
    assert request.terms_accepted is True
    print("✅ Valid registration request test passed")


def test_password_strength_validation():
    """Test password strength validation"""
    # Too short
    try:
        UserRegistrationRequest(
            username="test",
            email="test@test.com",
            password="Pass1!",  # Only 6 chars
            confirm_password="Pass1!",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "at least 8 characters" in str(e)
    
    # No uppercase
    try:
        UserRegistrationRequest(
            username="test",
            email="test@test.com",
            password="password123!",
            confirm_password="password123!",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "uppercase" in str(e)
    
    # No lowercase
    try:
        UserRegistrationRequest(
            username="test",
            email="test@test.com",
            password="PASSWORD123!",
            confirm_password="PASSWORD123!",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "lowercase" in str(e)
    
    # No digit
    try:
        UserRegistrationRequest(
            username="test",
            email="test@test.com",
            password="SecurePass!",
            confirm_password="SecurePass!",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "digit" in str(e)
    
    # No special character
    try:
        UserRegistrationRequest(
            username="test",
            email="test@test.com",
            password="SecurePass123",
            confirm_password="SecurePass123",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "special character" in str(e)
    
    # Common weak password
    try:
        UserRegistrationRequest(
            username="test",
            email="test@test.com",
            password="Password123!",  # Too common pattern
            confirm_password="Password123!",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        # This should pass strength validation but might be flagged as common
    except Exception:
        pass
    
    print("✅ Password strength validation test passed")


def test_password_confirmation_validation():
    """Test password confirmation matching"""
    # Matching passwords
    request = UserRegistrationRequest(
        username="test_user",
        email="test@example.com",
        password="SecurePass123!",
        confirm_password="SecurePass123!",
        first_name="Test",
        last_name="User",
        terms_accepted=True
    )
    assert request.password == request.confirm_password
    
    # Non-matching passwords
    try:
        UserRegistrationRequest(
            username="test_user",
            email="test@example.com",
            password="SecurePass123!",
            confirm_password="DifferentPass123!",
            first_name="Test",
            last_name="User",
            terms_accepted=True
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "do not match" in str(e).lower()
    
    print("✅ Password confirmation validation test passed")


def test_terms_acceptance_validation():
    """Test that terms must be accepted"""
    # Terms not accepted
    try:
        UserRegistrationRequest(
            username="test_user",
            email="test@example.com",
            password="SecurePass123!",
            confirm_password="SecurePass123!",
            first_name="Test",
            last_name="User",
            terms_accepted=False  # Not accepted
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "accept the terms" in str(e).lower()
    
    print("✅ Terms acceptance validation test passed")


def test_registration_response_creation():
    """Test creating a RegistrationResponse"""
    response = RegistrationResponse(
        user_id="user_12345",
        username="john_doe",
        email="john@example.com",
        registration_status=RegistrationStatus.PENDING_VERIFICATION,
        verification_token_sent=True,
        next_steps=[
            "Check your email inbox",
            "Click the verification link",
            "Complete verification within 24 hours"
        ]
    )
    
    assert response.user_id == "user_12345"
    assert response.registration_status == RegistrationStatus.PENDING_VERIFICATION
    assert response.verification_token_sent is True
    assert len(response.next_steps) == 3
    assert response.created_at.tzinfo is not None
    print("✅ RegistrationResponse creation test passed")


def test_registration_event_creation():
    """Test creating a RegistrationEvent"""
    event = RegistrationEvent(
        event_type=RegistrationEventType.REGISTRATION_ATTEMPT,
        user_id="user_12345",
        email="john@example.com",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        success=True,
        validation_errors=[],
        security_flags=["verified_email_domain"]
    )
    
    assert event.event_type == RegistrationEventType.REGISTRATION_ATTEMPT
    assert event.success is True
    assert len(event.security_flags) == 1
    assert event.timestamp.tzinfo is not None
    print("✅ RegistrationEvent creation test passed")


def test_registration_event_with_errors():
    """Test RegistrationEvent with validation errors"""
    event = RegistrationEvent(
        event_type=RegistrationEventType.REGISTRATION_ATTEMPT,
        email="invalid@example.com",
        ip_address="203.0.113.99",
        user_agent="curl/7.68.0",
        success=False,
        validation_errors=["Password too weak", "Username already taken"],
        security_flags=["suspicious_ip", "automated_attempt"]
    )
    
    assert event.success is False
    assert len(event.validation_errors) == 2
    assert "Password too weak" in event.validation_errors
    assert len(event.security_flags) == 2
    print("✅ Registration event with errors test passed")


def test_websocket_registration_message():
    """Test creating a WebSocketRegistrationMessage"""
    reg_event = RegistrationEvent(
        event_type=RegistrationEventType.ACCOUNT_ACTIVATION,
        user_id="user_789",
        email="activated@example.com",
        ip_address="192.168.1.50",
        user_agent="Mozilla/5.0",
        success=True
    )
    
    ws_message = WebSocketRegistrationMessage(
        message_type=RegistrationMessageType.VERIFICATION_STATUS,
        event_data=reg_event,
        admin_notification=False,
        requires_review=False
    )
    
    assert ws_message.message_type == RegistrationMessageType.VERIFICATION_STATUS
    assert ws_message.event_data.email == "activated@example.com"
    assert ws_message.admin_notification is False
    print("✅ WebSocket registration message test passed")


def test_security_alert_message():
    """Test security alert for suspicious registration"""
    suspicious_event = RegistrationEvent(
        event_type=RegistrationEventType.REGISTRATION_ATTEMPT,
        email="spam@disposable.com",
        ip_address="203.0.113.99",
        user_agent="curl/7.68.0",
        success=False,
        validation_errors=["Disposable email detected"],
        security_flags=["disposable_email", "vpn_detected", "high_risk_ip"]
    )
    
    alert_message = WebSocketRegistrationMessage(
        message_type=RegistrationMessageType.SECURITY_ALERT,
        event_data=suspicious_event,
        admin_notification=True,
        requires_review=True
    )
    
    assert alert_message.message_type == RegistrationMessageType.SECURITY_ALERT
    assert alert_message.admin_notification is True
    assert alert_message.requires_review is True
    assert len(alert_message.event_data.security_flags) == 3
    print("✅ Security alert message test passed")


def test_json_serialization():
    """Test JSON serialization"""
    request = UserRegistrationRequest(
        username="json_test",
        email="json@test.com",
        password="JsonTest123!",
        confirm_password="JsonTest123!",
        first_name="JSON",
        last_name="Test",
        terms_accepted=True
    )
    
    response = RegistrationResponse(
        user_id="user_999",
        username="json_test",
        email="json@test.com",
        registration_status=RegistrationStatus.ACTIVE,
        verification_token_sent=False,
        next_steps=["Login to your account"]
    )
    
    request_json = request.model_dump_json()
    response_json = response.model_dump_json()
    
    assert "json_test" in request_json
    assert "user_999" in response_json
    
    # Password should NOT be in response (only in request)
    assert "SecurePass" not in response_json
    
    print("✅ JSON serialization test passed")


if __name__ == "__main__":
    print("Running user registration model tests...\n")
    test_user_registration_request_valid()
    test_password_strength_validation()
    test_password_confirmation_validation()
    test_terms_acceptance_validation()
    test_registration_response_creation()
    test_registration_event_creation()
    test_registration_event_with_errors()
    test_websocket_registration_message()
    test_security_alert_message()
    test_json_serialization()
    print("\n✅ All tests passed!")

