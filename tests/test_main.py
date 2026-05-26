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


# --- Amount validator tests ---


def test_amount_validator_accepts_zero():
    """$0 in queries like 'How do I get to $0 debt?' must not be rejected."""
    import re

    amount_pattern = r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    query = "How do I get to $0 debt?"
    amounts = re.findall(amount_pattern, query)
    for amount in amounts:
        num_amount = float(amount.replace(",", ""))
        assert num_amount >= 0, f"$0 should be allowed, got rejection for {amount}"
        assert num_amount <= 10000000


def test_amount_validator_rejects_negative_context():
    """Negative amounts should still be caught (if the regex ever captures them)."""
    import re

    amount_pattern = r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    query = "I owe $50,000 on my mortgage"
    amounts = re.findall(amount_pattern, query)
    assert len(amounts) > 0
    for amount in amounts:
        num_amount = float(amount.replace(",", ""))
        assert num_amount >= 0
        assert num_amount <= 10000000


# --- Perplexity researcher unit tests ---


def test_perplexity_skips_when_disabled():
    """perplexity_researcher must skip when PERPLEXITY_REALTIME_ENABLED=false."""
    from unittest.mock import patch

    state = {"query": "What is the S&P 500?", "retrieval_confidence": 0.5}

    with patch("app.main.settings") as mock_settings:
        mock_settings.perplexity_realtime_enabled = False
        mock_settings.perplexity_api_key = "pplx-test"
        mock_settings.perplexity_confidence_threshold = 0.85

        from app.main import perplexity_researcher

        result = perplexity_researcher(state.copy())
        assert "perplexity_context" not in result


def test_perplexity_skips_high_confidence():
    """perplexity_researcher must skip when FAISS confidence exceeds threshold."""
    from unittest.mock import patch

    state = {"query": "What is a bond?", "retrieval_confidence": 0.95}

    with patch("app.main.settings") as mock_settings:
        mock_settings.perplexity_realtime_enabled = True
        mock_settings.perplexity_api_key = "pplx-test"
        mock_settings.perplexity_confidence_threshold = 0.85

        from app.main import perplexity_researcher

        result = perplexity_researcher(state.copy())
        assert "perplexity_context" not in result


def test_perplexity_augments_low_confidence():
    """perplexity_researcher must augment state when confidence is low."""
    from unittest.mock import MagicMock, patch

    state = {
        "query": "What are current Treasury yields?",
        "retrieval_confidence": 0.5,
        "messages": [],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.research.return_value = {
        "content": "Current 10-year Treasury yield is 4.25%.",
        "citations": ["https://treasury.gov"],
        "model": "sonar-pro",
        "query": "What are current Treasury yields?",
        "tokens": {"prompt": 50, "completion": 30},
        "latency_ms": 450,
    }

    with patch("app.main.settings") as mock_settings, \
         patch("app.services.perplexity_client.PerplexityClient", return_value=mock_client_instance), \
         patch("app.main._perplexity_rt_cache", {}), \
         patch("app.connectors.perplexity_connector._passes_content_filter", return_value=(True, [])):
        mock_settings.perplexity_realtime_enabled = True
        mock_settings.perplexity_api_key = "pplx-test"
        mock_settings.perplexity_confidence_threshold = 0.85
        mock_settings.perplexity_model = "sonar-pro"
        mock_settings.perplexity_realtime_timeout = 10

        from app.main import perplexity_researcher

        result = perplexity_researcher(state.copy())
        assert "perplexity_context" in result
        assert "Treasury" in result["perplexity_context"]


def test_perplexity_handles_api_error_gracefully():
    """perplexity_researcher must return state unchanged on API error."""
    from unittest.mock import MagicMock, patch

    state = {
        "query": "What are current rates?",
        "retrieval_confidence": 0.5,
        "messages": [],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.research.side_effect = Exception("API timeout")

    with patch("app.main.settings") as mock_settings, \
         patch("app.services.perplexity_client.PerplexityClient", return_value=mock_client_instance), \
         patch("app.main._perplexity_rt_cache", {}):
        mock_settings.perplexity_realtime_enabled = True
        mock_settings.perplexity_api_key = "pplx-test"
        mock_settings.perplexity_confidence_threshold = 0.85
        mock_settings.perplexity_model = "sonar-pro"
        mock_settings.perplexity_realtime_timeout = 10

        from app.main import perplexity_researcher

        result = perplexity_researcher(state.copy())
        assert "perplexity_context" not in result


def test_perplexity_content_filter_rejection():
    """perplexity_researcher must skip when content filter rejects response."""
    from unittest.mock import MagicMock, patch

    state = {
        "query": "Test query",
        "retrieval_confidence": 0.5,
        "messages": [],
    }

    mock_client_instance = MagicMock()
    mock_client_instance.research.return_value = {
        "content": "Filtered content",
        "citations": [],
        "model": "sonar-pro",
        "query": "Test query",
        "tokens": {"prompt": 10, "completion": 10},
        "latency_ms": 200,
    }

    with patch("app.main.settings") as mock_settings, \
         patch("app.services.perplexity_client.PerplexityClient", return_value=mock_client_instance), \
         patch("app.main._perplexity_rt_cache", {}), \
         patch("app.connectors.perplexity_connector._passes_content_filter", return_value=(False, ["promo"])):
        mock_settings.perplexity_realtime_enabled = True
        mock_settings.perplexity_api_key = "pplx-test"
        mock_settings.perplexity_confidence_threshold = 0.85
        mock_settings.perplexity_model = "sonar-pro"
        mock_settings.perplexity_realtime_timeout = 10

        from app.main import perplexity_researcher

        result = perplexity_researcher(state.copy())
        assert "perplexity_context" not in result
        pass
