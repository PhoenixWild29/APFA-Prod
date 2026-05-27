"""Billing router tests — config guards, schemas, webhook handling."""
import json

import pytest


def test_stripe_signature_error_import():
    """stripe.SignatureVerificationError must be importable (v15+ regression check)."""
    import stripe

    assert hasattr(stripe, "SignatureVerificationError")


def test_stripe_configured_guard():
    """_stripe_configured returns False when keys are empty."""
    from unittest.mock import patch

    with patch("app.api.billing.settings") as mock_settings:
        mock_settings.stripe_secret_key = ""
        mock_settings.stripe_webhook_secret = ""
        from app.api.billing import _stripe_configured

        assert not _stripe_configured()


def test_stripe_configured_true():
    """_stripe_configured returns True when both keys are set."""
    from unittest.mock import patch

    with patch("app.api.billing.settings") as mock_settings:
        mock_settings.stripe_secret_key = "sk_test_123"
        mock_settings.stripe_webhook_secret = "whsec_123"
        from app.api.billing import _stripe_configured

        assert _stripe_configured()


def test_tier_limits_values():
    """TIER_LIMITS must map free=5, pro=100, enterprise=999999."""
    from app.api.billing import TIER_LIMITS

    assert TIER_LIMITS["free"] == 5
    assert TIER_LIMITS["pro"] == 100
    assert TIER_LIMITS["enterprise"] == 999999


def test_billing_status_schema():
    """BillingStatus schema must accept all fields."""
    from app.api.billing import BillingStatus

    status = BillingStatus(
        tier="pro",
        query_count_this_period=42,
        limit=100,
        billing_period_start="2026-05-01T00:00:00Z",
        usage_percentage=42.0,
        has_subscription=True,
    )
    assert status.tier == "pro"
    assert status.has_subscription is True
    assert status.usage_percentage == 42.0


def test_billing_status_null_billing_period():
    """BillingStatus must accept null billing_period_start."""
    from app.api.billing import BillingStatus

    status = BillingStatus(
        tier="free",
        query_count_this_period=0,
        limit=5,
        billing_period_start=None,
        usage_percentage=0,
        has_subscription=False,
    )
    assert status.billing_period_start is None


def test_checkout_request_schema():
    """CheckoutRequest must accept tier string."""
    from app.api.billing import CheckoutRequest

    req = CheckoutRequest(tier="pro")
    assert req.tier == "pro"


def test_price_to_tier_mapping():
    """_get_price_to_tier must return correct mapping from config."""
    from unittest.mock import patch

    from app.api.billing import _get_price_to_tier, _price_to_tier

    # Reset global state
    import app.api.billing as billing_mod
    billing_mod._price_to_tier = {}

    with patch("app.api.billing.settings") as mock_settings:
        mock_settings.stripe_price_pro_monthly = "price_pro_123"
        mock_settings.stripe_price_enterprise_monthly = "price_ent_456"
        result = _get_price_to_tier()
        assert result["price_pro_123"] == "pro"
        assert result["price_ent_456"] == "enterprise"

    # Cleanup
    billing_mod._price_to_tier = {}


def test_price_to_tier_empty_config():
    """_get_price_to_tier must return empty dict when prices not configured."""
    from unittest.mock import patch

    import app.api.billing as billing_mod
    billing_mod._price_to_tier = {}

    with patch("app.api.billing.settings") as mock_settings:
        mock_settings.stripe_price_pro_monthly = ""
        mock_settings.stripe_price_enterprise_monthly = ""
        result = _get_price_to_tier()
        assert result == {}

    billing_mod._price_to_tier = {}


def test_billing_status_unauthenticated():
    """GET /api/billing/status without auth must return 401."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/billing/status")
    assert response.status_code == 401


def test_checkout_unauthenticated():
    """POST /api/billing/checkout without auth must return 401."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/billing/checkout",
        json={"tier": "pro"},
    )
    assert response.status_code == 401


def test_portal_unauthenticated():
    """POST /api/billing/portal without auth must return 401."""
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.post("/api/billing/portal")
    assert response.status_code == 401


def test_user_profile_includes_subscription_tier():
    """The User ORM to_dict() must include subscription_tier."""
    from app.orm_models import User

    user = User(
        id="test",
        username="test",
        email="test@test.com",
        hashed_password="hash",
        created_at="2026-01-01T00:00:00Z",
        subscription_tier="pro",
    )
    d = user.to_dict()
    assert d["subscription_tier"] == "pro"


def test_user_default_subscription_tier():
    """User ORM default subscription_tier must be 'free'."""
    from app.orm_models import User

    assert User.subscription_tier.default.arg == "free"
