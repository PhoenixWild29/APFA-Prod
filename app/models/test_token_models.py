"""
Test file for advanced JWT token management models
Run with: python -m pytest app/models/test_token_models.py
"""
from datetime import datetime, timezone, timedelta
from app.models.token_models import (
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenRevocationRequest,
    TokenEvent,
    WebSocketTokenMessage,
    TokenMetadata,
    TokenValidationResult,
    TokenTypeHint,
    TokenEventType,
    TokenType,
    TokenMessageType
)


def test_token_refresh_request():
    """Test creating a TokenRefreshRequest"""
    request = TokenRefreshRequest(
        refresh_token="eyJhbGciOiJIUzI1NiIs...",
        device_fingerprint="fp_abc123",
        client_metadata={"browser": "Chrome", "os": "Windows"}
    )
    
    assert request.refresh_token.startswith("eyJ")
    assert request.device_fingerprint == "fp_abc123"
    assert request.client_metadata["browser"] == "Chrome"
    print("✅ TokenRefreshRequest test passed")


def test_token_refresh_response():
    """Test creating a TokenRefreshResponse"""
    metadata = TokenMetadata(
        token_id="550e8400-e29b-41d4-a716-446655440000",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        issuer="apfa-api",
        audience=["apfa-frontend"],
        scopes=["advice:generate"]
    )
    
    response = TokenRefreshResponse(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_type="bearer",
        expires_in=1800,
        refresh_expires_in=604800,
        token_metadata=metadata
    )
    
    assert response.access_token == "new_access_token"
    assert response.token_type == "bearer"
    assert response.expires_in == 1800
    assert response.token_metadata.issuer == "apfa-api"
    print("✅ TokenRefreshResponse test passed")


def test_token_revocation_request():
    """Test creating a TokenRevocationRequest"""
    request = TokenRevocationRequest(
        token="eyJhbGci...",
        token_type_hint=TokenTypeHint.ACCESS_TOKEN,
        revoke_all_sessions=False
    )
    
    assert request.token == "eyJhbGci..."
    assert request.token_type_hint == TokenTypeHint.ACCESS_TOKEN
    assert request.revoke_all_sessions is False
    print("✅ TokenRevocationRequest test passed")


def test_token_revocation_all_sessions():
    """Test revoking all sessions"""
    request = TokenRevocationRequest(
        token="eyJhbGci...",
        token_type_hint=TokenTypeHint.REFRESH_TOKEN,
        revoke_all_sessions=True
    )
    
    assert request.revoke_all_sessions is True
    print("✅ Token revocation all sessions test passed")


def test_token_event_creation():
    """Test creating a TokenEvent"""
    event = TokenEvent(
        event_type=TokenEventType.ISSUED,
        token_id="550e8400-e29b-41d4-a716-446655440000",
        user_id="user_123",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0",
        token_type=TokenType.ACCESS,
        expiration_time=datetime.now(timezone.utc) + timedelta(hours=1),
        security_metadata={"scope": "full_access"}
    )
    
    assert event.event_type == TokenEventType.ISSUED
    assert event.token_type == TokenType.ACCESS
    assert event.timestamp.tzinfo is not None
    assert event.expiration_time.tzinfo is not None
    print("✅ TokenEvent creation test passed")


def test_token_event_types():
    """Test all token event types"""
    event_types = [
        TokenEventType.ISSUED,
        TokenEventType.REFRESHED,
        TokenEventType.REVOKED,
        TokenEventType.EXPIRED,
        TokenEventType.VALIDATION_FAILED
    ]
    
    for event_type in event_types:
        event = TokenEvent(
            event_type=event_type,
            token_id="test_id",
            user_id="user_123",
            ip_address="192.168.1.1",
            user_agent="Test",
            token_type=TokenType.ACCESS,
            expiration_time=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert event.event_type == event_type
    
    print("✅ Token event types test passed")


def test_websocket_token_message():
    """Test creating a WebSocketTokenMessage"""
    token_event = TokenEvent(
        event_type=TokenEventType.REFRESHED,
        token_id="550e8400-e29b-41d4-a716-446655440000",
        user_id="user_456",
        ip_address="10.0.0.1",
        user_agent="Mozilla/5.0",
        token_type=TokenType.ACCESS,
        expiration_time=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    message = WebSocketTokenMessage(
        message_type=TokenMessageType.TOKEN_EVENT,
        event_data=token_event,
        security_assessment={"threat_level": "low"},
        requires_action=False
    )
    
    assert message.message_type == TokenMessageType.TOKEN_EVENT
    assert message.event_data.user_id == "user_456"
    assert message.requires_action is False
    print("✅ WebSocketTokenMessage test passed")


def test_security_violation_message():
    """Test security violation message"""
    violation_event = TokenEvent(
        event_type=TokenEventType.VALIDATION_FAILED,
        token_id="invalid_token",
        user_id="attacker",
        ip_address="203.0.113.99",
        user_agent="curl/7.68.0",
        token_type=TokenType.ACCESS,
        expiration_time=datetime.now(timezone.utc),
        security_metadata={"reason": "invalid_signature"}
    )
    
    message = WebSocketTokenMessage(
        message_type=TokenMessageType.SECURITY_VIOLATION,
        event_data=violation_event,
        security_assessment={
            "threat_level": "critical",
            "risk_factors": ["invalid_signature", "suspicious_ip"],
            "recommended_action": "block_ip"
        },
        requires_action=True
    )
    
    assert message.message_type == TokenMessageType.SECURITY_VIOLATION
    assert message.requires_action is True
    assert message.security_assessment["threat_level"] == "critical"
    print("✅ Security violation message test passed")


def test_token_metadata():
    """Test creating TokenMetadata"""
    now = datetime.now(timezone.utc)
    
    metadata = TokenMetadata(
        token_id="550e8400-e29b-41d4-a716-446655440000",
        issued_at=now,
        expires_at=now + timedelta(hours=1),
        issuer="apfa-api",
        audience=["apfa-frontend", "apfa-mobile"],
        scopes=["advice:generate", "advice:view_history"],
        device_fingerprint="fp_device123",
        ip_address="192.168.1.100",
        security_level="standard"
    )
    
    assert metadata.issuer == "apfa-api"
    assert len(metadata.audience) == 2
    assert len(metadata.scopes) == 2
    assert metadata.security_level == "standard"
    print("✅ TokenMetadata test passed")


def test_token_metadata_expiration_validation():
    """Test that expiration must be after issuance"""
    now = datetime.now(timezone.utc)
    
    # Valid: expires after issued
    metadata = TokenMetadata(
        token_id="test_id",
        issued_at=now,
        expires_at=now + timedelta(hours=1),
        issuer="test",
        audience=["test"],
        scopes=["test"]
    )
    assert metadata.expires_at > metadata.issued_at
    
    # Invalid: expires before issued
    try:
        TokenMetadata(
            token_id="test_id",
            issued_at=now,
            expires_at=now - timedelta(hours=1),  # In the past
            issuer="test",
            audience=["test"],
            scopes=["test"]
        )
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "after issuance" in str(e)
    
    print("✅ Token expiration validation test passed")


def test_token_validation_result_valid():
    """Test TokenValidationResult for valid token"""
    result = TokenValidationResult(
        is_valid=True,
        token_id="550e8400-e29b-41d4-a716-446655440000",
        user_id="user_123",
        expiration_time=datetime.now(timezone.utc) + timedelta(hours=1),
        validation_errors=[],
        security_warnings=["Token expires in 5 minutes"],
        remaining_ttl_seconds=300
    )
    
    assert result.is_valid is True
    assert result.user_id == "user_123"
    assert result.remaining_ttl_seconds == 300
    assert len(result.validation_errors) == 0
    assert len(result.security_warnings) == 1
    print("✅ Valid token validation result test passed")


def test_token_validation_result_invalid():
    """Test TokenValidationResult for invalid token"""
    result = TokenValidationResult(
        is_valid=False,
        token_id="invalid_token",
        validation_errors=["Token expired", "Invalid signature"],
        security_warnings=[]
    )
    
    assert result.is_valid is False
    assert len(result.validation_errors) == 2
    assert "Token expired" in result.validation_errors
    assert result.user_id is None
    assert result.remaining_ttl_seconds is None
    print("✅ Invalid token validation result test passed")


def test_json_serialization():
    """Test JSON serialization of all models"""
    # TokenRefreshRequest
    refresh_req = TokenRefreshRequest(refresh_token="test_token")
    assert "test_token" in refresh_req.model_dump_json()
    
    # TokenValidationResult
    validation = TokenValidationResult(
        is_valid=True,
        token_id="test_id",
        user_id="user_123"
    )
    validation_json = validation.model_dump_json()
    assert "user_123" in validation_json
    
    print("✅ JSON serialization test passed")


if __name__ == "__main__":
    print("Running advanced JWT token management model tests...\n")
    test_token_refresh_request()
    test_token_refresh_response()
    test_token_revocation_request()
    test_token_revocation_all_sessions()
    test_token_event_creation()
    test_token_event_types()
    test_websocket_token_message()
    test_security_violation_message()
    test_token_metadata()
    test_token_metadata_expiration_validation()
    test_token_validation_result_valid()
    test_token_validation_result_invalid()
    test_json_serialization()
    print("\n✅ All tests passed!")

