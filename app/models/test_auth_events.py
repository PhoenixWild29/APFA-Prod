"""
Test file for authentication event models
Run with: python -m pytest app/models/test_auth_events.py
"""
from datetime import datetime, timezone
from app.models.auth_events import (
    AuthenticationEvent,
    WebSocketAuthMessage,
    AuthEventType,
    MessageType,
    Severity
)


def test_authentication_event_creation():
    """Test creating a valid AuthenticationEvent"""
    event = AuthenticationEvent(
        event_type=AuthEventType.LOGIN,
        user_id="user_12345",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        success=True,
        security_metadata={
            "session_id": "sess_abc123",
            "mfa_used": True
        }
    )
    
    assert event.event_type == AuthEventType.LOGIN
    assert event.user_id == "user_12345"
    assert event.success is True
    assert event.timestamp.tzinfo is not None  # Timezone-aware
    print("✅ AuthenticationEvent creation test passed")


def test_authentication_event_ipv6():
    """Test AuthenticationEvent with IPv6 address"""
    event = AuthenticationEvent(
        event_type=AuthEventType.TOKEN_REFRESH,
        user_id="user_456",
        ip_address="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        user_agent="Mozilla/5.0",
        success=True
    )
    
    assert event.ip_address == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    print("✅ IPv6 address validation test passed")


def test_authentication_event_failure():
    """Test AuthenticationEvent for failed authentication"""
    event = AuthenticationEvent(
        event_type=AuthEventType.VALIDATION_FAILURE,
        user_id="user_789",
        ip_address="203.0.113.45",
        user_agent="curl/7.68.0",
        success=False,
        error_message="Invalid JWT token signature",
        security_metadata={
            "token_expired": False,
            "signature_invalid": True
        }
    )
    
    assert event.success is False
    assert event.error_message == "Invalid JWT token signature"
    assert event.security_metadata["signature_invalid"] is True
    print("✅ Authentication failure test passed")


def test_websocket_auth_message_creation():
    """Test creating a WebSocketAuthMessage"""
    auth_event = AuthenticationEvent(
        event_type=AuthEventType.LOGIN,
        user_id="user_111",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        success=True
    )
    
    message = WebSocketAuthMessage(
        message_type=MessageType.AUTH_EVENT,
        event_data=auth_event,
        severity=Severity.INFO,
        requires_action=False
    )
    
    assert message.message_type == MessageType.AUTH_EVENT
    assert message.severity == Severity.INFO
    assert message.event_data.user_id == "user_111"
    assert message.requires_action is False
    print("✅ WebSocketAuthMessage creation test passed")


def test_security_alert_message():
    """Test creating a security alert with critical severity"""
    suspicious_event = AuthenticationEvent(
        event_type=AuthEventType.VALIDATION_FAILURE,
        user_id="attacker_user",
        ip_address="203.0.113.99",
        user_agent="python-requests/2.28.0",
        success=False,
        error_message="Multiple failed authentication attempts",
        security_metadata={
            "attempts_count": 10,
            "time_window": "5_minutes",
            "suspected_brute_force": True
        }
    )
    
    alert_message = WebSocketAuthMessage(
        message_type=MessageType.SECURITY_ALERT,
        event_data=suspicious_event,
        severity=Severity.CRITICAL,
        requires_action=True
    )
    
    assert alert_message.message_type == MessageType.SECURITY_ALERT
    assert alert_message.severity == Severity.CRITICAL
    assert alert_message.requires_action is True
    assert alert_message.event_data.security_metadata["suspected_brute_force"] is True
    print("✅ Security alert message test passed")


def test_timezone_aware_timestamp():
    """Test that timestamps are timezone-aware"""
    # Create with naive datetime (should be converted to UTC)
    naive_time = datetime(2025, 10, 11, 14, 30, 0)
    event = AuthenticationEvent(
        event_type=AuthEventType.LOGOUT,
        user_id="user_222",
        timestamp=naive_time,
        ip_address="192.168.1.50",
        user_agent="Mozilla/5.0",
        success=True
    )
    
    # Should be converted to timezone-aware
    assert event.timestamp.tzinfo is not None
    assert event.timestamp.tzinfo == timezone.utc
    print("✅ Timezone-aware timestamp test passed")


def test_json_serialization():
    """Test JSON serialization of models"""
    event = AuthenticationEvent(
        event_type=AuthEventType.LOGIN,
        user_id="user_serialize",
        ip_address="10.0.0.1",
        user_agent="TestAgent/1.0",
        success=True,
        security_metadata={"test": "data"}
    )
    
    message = WebSocketAuthMessage(
        message_type=MessageType.SESSION_UPDATE,
        event_data=event,
        severity=Severity.INFO,
        requires_action=False
    )
    
    # Test serialization
    json_str = message.model_dump_json(indent=2)
    assert "session_update" in json_str
    assert "user_serialize" in json_str
    print("✅ JSON serialization test passed")
    print("\nExample JSON output:")
    print(json_str)


if __name__ == "__main__":
    print("Running AuthenticationEvent model tests...\n")
    test_authentication_event_creation()
    test_authentication_event_ipv6()
    test_authentication_event_failure()
    test_websocket_auth_message_creation()
    test_security_alert_message()
    test_timezone_aware_timestamp()
    test_json_serialization()
    print("\n✅ All tests passed!")

