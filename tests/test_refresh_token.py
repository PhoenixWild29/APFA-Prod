"""Tests for refresh token rotation, family-based revocation, and grace window.

CoWork-mandated test cases:
1. Login -> refresh -> new access token, old rotated
2. Family theft: rotated token -> family revoked
3. Grace window: refresh within 10s of rotation -> successor returned

Uses an in-memory SQLite database — no PostgreSQL or Docker required.
The app's database.py (which creates a PostgreSQL engine at module level)
is NOT imported; instead we create our own Base/engine/session.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# We need to mock the database module BEFORE importing orm_models,
# because orm_models imports Base from app.database.
# Create our own Base and patch it in.
TestBase = declarative_base()

# Patch app.database before any app module imports it
import types

fake_database = types.ModuleType("app.database")
fake_database.Base = TestBase
fake_database.SessionLocal = None  # Will be set per-test
fake_database.get_db = None
sys.modules["app.database"] = fake_database

# Now we can safely set required env vars and import app modules
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_SECRET_KEY", "test")
os.environ.setdefault("API_KEY", "test")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("STRIPE_PRICE_PRO_MONTHLY", "price_test")
os.environ.setdefault("STRIPE_PRICE_ENTERPRISE_MONTHLY", "price_test")

from app.orm_models import RefreshToken, User  # noqa: E402
from app.services.refresh_token_service import (  # noqa: E402
    _hash_token,
    cleanup_expired_tokens,
    create_refresh_token,
    find_family_by_token,
    revoke_all_user_families,
    revoke_family,
    rotate_refresh_token,
)

# In-memory SQLite for fast unit tests
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables for every test."""
    TestBase.metadata.create_all(bind=engine)
    yield
    TestBase.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db):
    """Create a test user in the DB."""
    user = User(
        id="user_testuser",
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$fakehashfakehashfakehashfakehashfakehashfakehas",
        disabled=False,
        role="standard",
        type="human",
        permissions=[],
        verified=True,
        marketing_consent=False,
        subscription_tier="free",
        query_count_this_period=0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    return user


class TestCreateRefreshToken:
    def test_creates_token_and_row(self, db, test_user):
        raw_token, row = create_refresh_token(db, test_user.id)
        db.commit()

        assert raw_token is not None
        assert len(raw_token) > 30  # secrets.token_urlsafe(48) is ~64 chars
        assert row.token_hash == _hash_token(raw_token)
        assert row.user_id == test_user.id
        assert row.family_id is not None
        assert row.revoked_at is None
        assert row.replaced_by_id is None
        # SQLite may return naive datetimes — normalize for comparison
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)

    def test_new_login_creates_new_family(self, db, test_user):
        _, row1 = create_refresh_token(db, test_user.id)
        _, row2 = create_refresh_token(db, test_user.id)
        db.commit()

        assert row1.family_id != row2.family_id

    def test_same_family_when_specified(self, db, test_user):
        _, row1 = create_refresh_token(db, test_user.id, family_id="fam-1")
        _, row2 = create_refresh_token(db, test_user.id, family_id="fam-1")
        db.commit()

        assert row1.family_id == row2.family_id == "fam-1"


class TestRotateRefreshToken:
    def test_normal_rotation(self, db, test_user):
        """Login -> refresh -> new access token, old rotated."""
        raw_old, old_row = create_refresh_token(db, test_user.id)
        db.commit()

        new_raw, new_row, user_id = rotate_refresh_token(db, raw_old)
        db.commit()

        assert new_raw is not None
        assert new_row is not None
        assert user_id == test_user.id

        # Old token should be marked replaced
        db.refresh(old_row)
        assert old_row.replaced_by_id == new_row.id
        assert old_row.revoked_at is not None

        # New token should be in the same family
        assert new_row.family_id == old_row.family_id

    def test_expired_token_rejected(self, db, test_user):
        raw, row = create_refresh_token(db, test_user.id)
        row.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()

        result = rotate_refresh_token(db, raw)
        assert result == (None, None, None)

    def test_revoked_token_rejected(self, db, test_user):
        raw, row = create_refresh_token(db, test_user.id)
        row.revoked_at = datetime.now(timezone.utc)
        db.commit()

        result = rotate_refresh_token(db, raw)
        assert result == (None, None, None)

    def test_unknown_token_rejected(self, db, test_user):
        result = rotate_refresh_token(db, "nonexistent-token-value")
        assert result == (None, None, None)

    def test_theft_detection_revokes_family(self, db, test_user):
        """Family theft: rotated token reuse outside grace window -> family revoked."""
        raw_old, old_row = create_refresh_token(db, test_user.id)
        db.commit()

        # First rotation succeeds
        new_raw, new_row, _ = rotate_refresh_token(db, raw_old)
        db.commit()
        assert new_raw is not None

        # Push successor creation time outside grace window
        new_row.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        db.commit()

        # Reuse the OLD token — theft detected
        result = rotate_refresh_token(db, raw_old)
        db.commit()
        assert result == (None, None, None)

        # Entire family should be revoked
        db.refresh(new_row)
        assert new_row.revoked_at is not None

    def test_grace_window_returns_successor(self, db, test_user):
        """Grace window: refresh within 10s of rotation -> successor returned."""
        raw_old, old_row = create_refresh_token(db, test_user.id)
        db.commit()

        # First rotation
        new_raw_1, new_row_1, _ = rotate_refresh_token(db, raw_old)
        db.commit()
        assert new_raw_1 is not None

        # Immediately reuse old token (within grace window)
        grace_raw, grace_row, user_id = rotate_refresh_token(db, raw_old)
        db.commit()

        assert grace_raw is not None
        assert grace_row is not None
        assert user_id == test_user.id
        # Should be in the same family
        assert grace_row.family_id == old_row.family_id

    def test_double_rotation_chain(self, db, test_user):
        """Multiple sequential rotations work correctly."""
        raw_1, row_1 = create_refresh_token(db, test_user.id)
        db.commit()

        raw_2, row_2, _ = rotate_refresh_token(db, raw_1)
        db.commit()
        assert raw_2 is not None

        raw_3, row_3, _ = rotate_refresh_token(db, raw_2)
        db.commit()
        assert raw_3 is not None

        # All in same family
        assert row_1.family_id == row_2.family_id == row_3.family_id


class TestRevokeFamily:
    def test_revoke_family(self, db, test_user):
        _, row1 = create_refresh_token(db, test_user.id, family_id="fam-x")
        _, row2 = create_refresh_token(db, test_user.id, family_id="fam-x")
        _, row3 = create_refresh_token(db, test_user.id, family_id="fam-y")
        db.commit()

        count = revoke_family(db, "fam-x")
        db.commit()

        assert count == 2
        db.refresh(row1)
        db.refresh(row2)
        db.refresh(row3)
        assert row1.revoked_at is not None
        assert row2.revoked_at is not None
        assert row3.revoked_at is None  # Different family

    def test_revoke_all_user_families(self, db, test_user):
        _, row1 = create_refresh_token(db, test_user.id, family_id="fam-a")
        _, row2 = create_refresh_token(db, test_user.id, family_id="fam-b")
        db.commit()

        count = revoke_all_user_families(db, test_user.id)
        db.commit()

        assert count == 2
        db.refresh(row1)
        db.refresh(row2)
        assert row1.revoked_at is not None
        assert row2.revoked_at is not None


class TestFindFamily:
    def test_find_family(self, db, test_user):
        raw, row = create_refresh_token(db, test_user.id, family_id="fam-find")
        db.commit()

        assert find_family_by_token(db, raw) == "fam-find"

    def test_not_found(self, db):
        assert find_family_by_token(db, "bogus") is None


class TestAbsoluteSessionMax:
    def test_session_within_max_is_allowed(self, db, test_user):
        """Session younger than absolute max should rotate normally."""
        raw, row = create_refresh_token(db, test_user.id)
        db.commit()

        new_raw, new_row, uid = rotate_refresh_token(db, raw)
        db.commit()
        assert new_raw is not None
        assert uid == test_user.id

    def test_session_exceeding_max_is_revoked(self, db, test_user):
        """Session older than absolute max should be rejected."""
        raw, row = create_refresh_token(db, test_user.id)
        # Backdate the family origin to exceed 90 days
        row.created_at = datetime.now(timezone.utc) - timedelta(days=91)
        db.commit()

        result = rotate_refresh_token(db, raw)
        db.commit()
        assert result == (None, None, None)

        # Token should be revoked
        db.refresh(row)
        assert row.revoked_at is not None


class TestCleanupExpiredTokens:
    def test_deletes_expired_tokens(self, db, test_user):
        """Expired tokens should be cleaned up."""
        _, row_expired = create_refresh_token(db, test_user.id)
        row_expired.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        _, row_valid = create_refresh_token(db, test_user.id)
        db.commit()
        expired_id = row_expired.id
        valid_id = row_valid.id

        count = cleanup_expired_tokens(db)
        db.commit()

        assert count >= 1
        assert db.query(RefreshToken).filter(RefreshToken.id == valid_id).first() is not None
        assert db.query(RefreshToken).filter(RefreshToken.id == expired_id).first() is None

    def test_deletes_old_revoked_tokens(self, db, test_user):
        """Revoked tokens older than 24h should be cleaned up."""
        _, row_old_revoked = create_refresh_token(db, test_user.id)
        row_old_revoked.revoked_at = datetime.now(timezone.utc) - timedelta(hours=25)
        _, row_recent_revoked = create_refresh_token(db, test_user.id)
        row_recent_revoked.revoked_at = datetime.now(timezone.utc) - timedelta(hours=1)
        db.commit()
        old_id = row_old_revoked.id
        recent_id = row_recent_revoked.id

        count = cleanup_expired_tokens(db)
        db.commit()

        assert db.query(RefreshToken).filter(RefreshToken.id == old_id).first() is None
        assert db.query(RefreshToken).filter(RefreshToken.id == recent_id).first() is not None

    def test_keeps_active_tokens(self, db, test_user):
        """Active (non-expired, non-revoked) tokens should not be cleaned up."""
        _, row = create_refresh_token(db, test_user.id)
        db.commit()

        count = cleanup_expired_tokens(db)
        db.commit()

        assert count == 0
        assert db.query(RefreshToken).filter(RefreshToken.id == row.id).first() is not None
