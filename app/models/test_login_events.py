"""
Test file for login event models
Run with: python -m pytest app/models/test_login_events.py
"""
from datetime import datetime
from app.models.login_events import LoginEvent, WebSocketLoginMessage, LoginEventType, MessageType


def test_login_event_creation():
    """Test creating a valid LoginEvent"""
    event = LoginEvent(
        event_type=LoginEventType.LOGIN_SUCCESS,
        username="testuser",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        success=True,
        security_score=0.15,
        user_id="user_12345",
        device_fingerprint="fp_abc123",
        geographic_location={
            "country": "US",
            "city": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    )
    
    assert event.event_type == LoginEventType.LOGIN_SUCCESS
    assert event.username == "testuser"
    assert event.success is True
    assert 0.0 <= event.security_score <= 1.0
    print("✅ LoginEvent creation test passed")


def test_login_event_validation():
    """Test LoginEvent validation"""
    # Valid security score
    event = LoginEvent(
        event_type=LoginEventType.LOGIN_FAILURE,
        username="baduser",
        ip_address="203.0.113.45",
        user_agent="curl/7.68.0",
        success=False,
        failure_reason="Invalid password",
        security_score=0.85
    )
    
    assert event.failure_reason == "Invalid password"
    print("✅ LoginEvent validation test passed")


def test_websocket_message_creation():
    """Test creating a WebSocketLoginMessage"""
    login_event = LoginEvent(
        event_type=LoginEventType.LOGIN_SUCCESS,
        username="admin",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        success=True,
        security_score=0.1
    )
    
    message = WebSocketLoginMessage(
        message_type=MessageType.LOGIN_EVENT,
        event_data=login_event,
        risk_assessment={
            "threat_level": "low",
            "reasons": [],
            "recommended_action": "none"
        },
        requires_admin_attention=False
    )
    
    assert message.message_type == MessageType.LOGIN_EVENT
    assert message.event_data.username == "admin"
    assert message.requires_admin_attention is False
    print("✅ WebSocketLoginMessage creation test passed")


def test_security_alert_message():
    """Test creating a security alert message"""
    suspicious_event = LoginEvent(
        event_type=LoginEventType.LOGIN_FAILURE,
        username="admin",
        ip_address="203.0.113.99",
        user_agent="curl/7.68.0",
        success=False,
        failure_reason="Invalid password (5th attempt)",
        security_score=0.95
    )
    
    alert_message = WebSocketLoginMessage(
        message_type=MessageType.SECURITY_ALERT,
        event_data=suspicious_event,
        risk_assessment={
            "threat_level": "critical",
            "reasons": ["repeated_failures", "suspicious_ip", "unusual_user_agent"],
            "recommended_action": "block_ip"
        },
        requires_admin_attention=True
    )
    
    assert alert_message.message_type == MessageType.SECURITY_ALERT
    assert alert_message.requires_admin_attention is True
    assert alert_message.risk_assessment["threat_level"] == "critical"
    print("✅ Security alert message test passed")


def test_json_serialization():
    """Test JSON serialization of models"""
    event = LoginEvent(
        event_type=LoginEventType.LOGIN_SUCCESS,
        username="testuser",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        success=True,
        security_score=0.2
    )
    
    message = WebSocketLoginMessage(
        message_type=MessageType.LOGIN_EVENT,
        event_data=event,
        risk_assessment={"threat_level": "low"},
        requires_admin_attention=False
    )
    
    # Test serialization
    json_str = message.model_dump_json(indent=2)
    assert "login_event" in json_str
    assert "testuser" in json_str
    print("✅ JSON serialization test passed")
    print("\nExample JSON output:")
    print(json_str)


if __name__ == "__main__":
    print("Running LoginEvent model tests...\n")
    test_login_event_creation()
    test_login_event_validation()
    test_websocket_message_creation()
    test_security_alert_message()
    test_json_serialization()
    print("\n✅ All tests passed!")

