"""Regression tests for CSRF middleware bypass/validation logic."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.csrf_middleware import CSRFMiddleware


@pytest.fixture
def app():
    """Minimal app exercising the CSRF middleware in isolation."""
    a = FastAPI()
    a.add_middleware(
        CSRFMiddleware,
        secret_key="test-secret-key-do-not-use-in-prod",
        cookie_secure=False,  # tests run over HTTP
    )

    @a.get("/health")
    def health():
        return {"ok": True}

    @a.post("/token")
    def login():
        return {"access_token": "fake"}

    @a.post("/api/billing/webhook")
    def webhook():
        return {"received": True}

    @a.post("/protected")
    def protected():
        return {"ok": True}

    return a


@pytest.fixture
def client(app):
    return TestClient(app)


def test_safe_method_passes_and_sets_csrf_cookie(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "csrf_token" in r.cookies


def test_exempt_login_path_passes_without_csrf(client):
    r = client.post("/token", json={})
    assert r.status_code == 200


def test_exempt_webhook_path_passes_without_csrf(client):
    r = client.post("/api/billing/webhook", json={})
    assert r.status_code == 200


def test_protected_endpoint_blocks_without_csrf(client):
    r = client.post("/protected", json={})
    assert r.status_code == 403
    assert "CSRF" in r.json()["detail"]


def test_bearer_header_bypasses_csrf_when_no_session_cookie(client):
    r = client.post(
        "/protected",
        json={},
        headers={"Authorization": "Bearer fake-jwt"},
    )
    assert r.status_code == 200


def test_api_key_header_bypasses_csrf_when_no_session_cookie(client):
    r = client.post(
        "/protected",
        json={},
        headers={"X-API-Key": "fake-key"},
    )
    assert r.status_code == 200


def test_bearer_with_session_cookie_still_requires_csrf(client):
    """Defense against Bearer-padding attack: if session cookie is present,
    CSRF must be validated even with a Bearer header."""
    r = client.post(
        "/protected",
        json={},
        headers={"Authorization": "Bearer fake-jwt"},
        cookies={"refresh_token": "fake-session"},
    )
    assert r.status_code == 403


def test_double_submit_with_matching_token_passes(client):
    # Get CSRF cookie via safe method
    r = client.get("/health")
    csrf_token = r.cookies["csrf_token"]
    r = client.post(
        "/protected",
        json={},
        cookies={"csrf_token": csrf_token, "refresh_token": "fake-session"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert r.status_code == 200


def test_double_submit_with_mismatched_token_fails(client):
    r = client.get("/health")
    csrf_token = r.cookies["csrf_token"]
    r = client.post(
        "/protected",
        json={},
        cookies={"csrf_token": csrf_token, "refresh_token": "fake-session"},
        headers={"X-CSRF-Token": "wrong-token"},
    )
    assert r.status_code == 403
