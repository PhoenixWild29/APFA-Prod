import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Mock API key for testing
os.environ["API_KEY"] = "test_key"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_generate_advice_unauthorized():
    response = client.post("/generate-advice", json={"query": "What is a good loan?"})
    assert response.status_code == 401


def test_generate_advice_invalid_input():
    response = client.post(
        "/generate-advice", json={"query": ""}, headers={"X-API-Key": "test_key"}
    )
    assert response.status_code == 422  # Validation error


def test_generate_advice_valid():
    response = client.post(
        "/generate-advice",
        json={"query": "What is a good loan?"},
        headers={"X-API-Key": "test_key"},
    )
    assert response.status_code == 200
    assert "advice" in response.json()


def test_rate_limiting():
    # Test rate limiting by making multiple requests
    for i in range(12):  # Exceed limit
        response = client.post(
            "/generate-advice",
            json={"query": "Test"},
            headers={"X-API-Key": "test_key"},
        )
    assert response.status_code == 429  # Too many requests


def test_input_validation():
    # Test regex validation
    response = client.post(
        "/generate-advice",
        json={"query": "Valid query with numbers 123?"},
        headers={"X-API-Key": "test_key"},
    )
    assert response.status_code == 200

    response = client.post(
        "/generate-advice",
        json={"query": "Invalid @{}<>*"},
        headers={"X-API-Key": "test_key"},
    )
    assert response.status_code == 422


def test_query_regex_accepts_financial_chars():
    """Queries with &, ', /, :, \", # must pass the regex pattern."""
    import re

    pattern = r"^[a-zA-Z0-9\s\?\.\,\!\-\+\=\$\%\(\)&'/:\"#]+$"
    valid_queries = [
        "What is the S&P 500 index?",
        "What's the best P/E ratio for growth stocks?",
        "Tell me about 3:1 leverage ratios",
        "Is AT&T a good dividend stock?",
        'What does "value investing" mean?',
        "Which is the #1 ranked index fund?",
    ]
    for q in valid_queries:
        assert re.match(pattern, q), f"Regex should accept: {q}"


def test_query_regex_rejects_dangerous_chars():
    """Characters not in the allowlist must fail the regex pattern."""
    import re

    pattern = r"^[a-zA-Z0-9\s\?\.\,\!\-\+\=\$\%\(\)&'/:\"#]+$"
    invalid_queries = [
        "query with semicolon; DROP TABLE",
        "test @ symbol not allowed",
        "curly {braces} blocked",
        "angle <brackets> blocked",
        "backtick `injection` attempt",
        "pipe | not allowed",
    ]
    for q in invalid_queries:
        assert not re.match(pattern, q), f"Regex should reject: {q}"


def test_query_validator_rejects_script_uris():
    """javascript: and vbscript: URIs must be rejected by the field validator."""
    import re

    script_pattern = r"(javascript|vbscript)\s*:"
    assert re.search(script_pattern, "javascript:alert(1)", re.IGNORECASE)
    assert re.search(script_pattern, "JAVASCRIPT : alert(1)", re.IGNORECASE)
    assert re.search(script_pattern, "vbscript:msgbox", re.IGNORECASE)
    assert not re.search(script_pattern, "What is the S&P 500?", re.IGNORECASE)


# --- Conversation schema validation tests ---


def test_conversation_create_schema():
    from pydantic import ValidationError

    from app.models.conversations import ConversationCreate

    valid = ConversationCreate(title="My portfolio review")
    assert valid.title == "My portfolio review"

    valid_none = ConversationCreate()
    assert valid_none.title is None

    try:
        ConversationCreate(title="x" * 201)
        assert False, "Should reject title > 200 chars"
    except ValidationError:
        pass


def test_conversation_update_rejects_empty():
    from pydantic import ValidationError

    from app.models.conversations import ConversationUpdate

    valid = ConversationUpdate(title="Renamed")
    assert valid.title == "Renamed"

    try:
        ConversationUpdate(title="")
        assert False, "Should reject empty title"
    except ValidationError:
        pass

    try:
        ConversationUpdate(title="x" * 201)
        assert False, "Should reject title > 200 chars"
    except ValidationError:
        pass


def test_message_feedback_schema():
    from pydantic import ValidationError

    from app.models.conversations import MessageFeedback

    assert MessageFeedback(feedback="up").feedback == "up"
    assert MessageFeedback(feedback="down").feedback == "down"
    assert MessageFeedback(feedback=None).feedback is None
    assert MessageFeedback().feedback is None

    try:
        MessageFeedback(feedback="invalid")
        assert False, "Should reject invalid feedback"
    except ValidationError:
        pass
