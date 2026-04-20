"""Refresh token service — rotation, family-based revocation, grace window.

Design: Plan agent. Approved by CoWork with additions:
- Grace window (10s default) for multi-tab race safety
- Token families track lineage from a single login session
- Reuse of a rotated-out token outside the grace window revokes the
  entire family (theft detection)
- Opaque tokens (secrets.token_urlsafe), stored as SHA-256 hashes
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.orm_models import RefreshToken

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (SQLite returns naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _hash_token(raw_token: str) -> str:
    """SHA-256 hash of the raw opaque token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_token(
    db: Session, user_id: str, family_id: Optional[str] = None
) -> tuple[str, RefreshToken]:
    """Issue a new opaque refresh token and persist its hash.

    Args:
        db: Database session.
        user_id: Owner's user ID.
        family_id: Token family UUID. None = new login (creates new family).

    Returns:
        (raw_token, db_row) — raw_token is returned ONCE to the client.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)

    if family_id is None:
        family_id = str(uuid.uuid4())

    row = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        family_id=family_id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(row)
    db.flush()  # Assign row.id before returning
    return raw_token, row


def rotate_refresh_token(
    db: Session, raw_token: str
) -> tuple[Optional[str], Optional[RefreshToken], Optional[str]]:
    """Validate and rotate a refresh token.

    Returns:
        (new_raw_token, new_row, user_id) on success.
        (None, None, None) on failure (expired, revoked, theft detected).

    Side effects:
        - Marks old token as replaced.
        - On reuse outside grace window: revokes entire family.
    """
    token_hash = _hash_token(raw_token)
    now = _utcnow()

    old_row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if old_row is None:
        logger.warning("Refresh token not found (hash mismatch)")
        return None, None, None

    # Expired?
    if _ensure_aware(old_row.expires_at) < now:
        logger.info(f"Refresh token expired for user_id={old_row.user_id}")
        return None, None, None

    # Absolute session max — revoke if family is older than limit (CoWork #5)
    family_origin = (
        db.query(RefreshToken.created_at)
        .filter(RefreshToken.family_id == old_row.family_id)
        .order_by(RefreshToken.id)
        .first()
    )
    if family_origin:
        family_age = (now - _ensure_aware(family_origin[0])).total_seconds()
        max_seconds = settings.absolute_session_max_days * 86400
        if family_age > max_seconds:
            logger.info(
                f"Absolute session max exceeded for family={old_row.family_id} "
                f"age={family_age/86400:.1f}d"
            )
            _revoke_family(db, old_row.family_id, now)
            return None, None, None

    # Already rotated (replaced_by_id is set)?
    # Check this BEFORE revoked_at because normal rotation sets both fields.
    if old_row.replaced_by_id is not None:
        # Grace window: if the replacement was created within the grace
        # window, return the successor token instead of revoking.
        grace_seconds = settings.refresh_token_grace_window_seconds
        successor = (
            db.query(RefreshToken)
            .filter(RefreshToken.id == old_row.replaced_by_id)
            .first()
        )
        if successor and (now - _ensure_aware(successor.created_at)).total_seconds() <= grace_seconds:
            # Within grace window — return the existing successor.
            # Re-issue the raw token for the successor so the client gets
            # a usable value. But we can't — we only store hashes.
            # Instead, create a NEW successor in the same family and
            # mark the old successor as replaced.
            logger.info(
                f"Grace window hit for family={old_row.family_id}, "
                f"issuing new successor"
            )
            new_raw, new_row = create_refresh_token(
                db, old_row.user_id, old_row.family_id
            )
            successor.replaced_by_id = new_row.id
            successor.revoked_at = now
            return new_raw, new_row, old_row.user_id

        # Outside grace window — theft detected
        logger.warning(
            f"Token reuse outside grace window! "
            f"Revoking family={old_row.family_id} user_id={old_row.user_id}"
        )
        _revoke_family(db, old_row.family_id, now)
        return None, None, None

    # Explicitly revoked (no replacement — admin/logout action)?
    if old_row.revoked_at is not None:
        logger.warning(
            f"Revoked refresh token presented for family={old_row.family_id}"
        )
        _revoke_family(db, old_row.family_id, now)
        return None, None, None

    # Normal rotation: mark old as replaced, issue new
    new_raw, new_row = create_refresh_token(
        db, old_row.user_id, old_row.family_id
    )
    old_row.replaced_by_id = new_row.id
    old_row.revoked_at = now

    return new_raw, new_row, old_row.user_id


def revoke_family(db: Session, family_id: str) -> int:
    """Revoke all tokens in a family (logout). Returns count revoked."""
    now = datetime.now(timezone.utc)
    return _revoke_family(db, family_id, now)


def revoke_all_user_families(db: Session, user_id: str) -> int:
    """Revoke ALL refresh tokens for a user (password change, logout-all).
    Returns count revoked."""
    now = datetime.now(timezone.utc)
    count = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .update({"revoked_at": now})
    )
    logger.info(f"Revoked all families for user_id={user_id}, count={count}")
    return count


def find_family_by_token(db: Session, raw_token: str) -> Optional[str]:
    """Look up the family_id for a raw token. Returns None if not found."""
    token_hash = _hash_token(raw_token)
    row = (
        db.query(RefreshToken.family_id)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    return row[0] if row else None


def cleanup_expired_tokens(db: Session) -> int:
    """Delete expired and rotated-out refresh tokens (CoWork #8).

    Removes tokens that are either:
    - Expired (expires_at < now)
    - Revoked more than 24h ago (keep recent revocations for audit)

    Returns count of deleted rows.
    """
    now = _utcnow()
    cutoff = now - timedelta(hours=24)

    count = (
        db.query(RefreshToken)
        .filter(
            (RefreshToken.expires_at < now)
            | (
                RefreshToken.revoked_at.isnot(None)
                & (RefreshToken.revoked_at < cutoff)
            )
        )
        .delete(synchronize_session="fetch")
    )
    logger.info(f"Cleaned up {count} expired/revoked refresh tokens")
    return count


def _revoke_family(db: Session, family_id: str, now: datetime) -> int:
    """Internal: revoke all non-revoked tokens in a family."""
    count = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.family_id == family_id,
            RefreshToken.revoked_at.is_(None),
        )
        .update({"revoked_at": now})
    )
    logger.warning(f"Revoked family={family_id}, count={count}")
    return count
