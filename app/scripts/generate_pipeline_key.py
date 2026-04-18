"""Generate a pipeline API key for machine-to-machine auth.

Creates the pipeline@apfa.internal service account (if it doesn't exist)
and inserts a new api_keys row with a bcrypt-hashed key.

The raw key is printed ONCE to stdout. It is NEVER stored in the database —
only the bcrypt hash is persisted.

Usage:
    # From within the Docker container or with DATABASE_URL set:
    python -m app.scripts.generate_pipeline_key --name "perplexity-computer"

    # With custom expiry (days):
    python -m app.scripts.generate_pipeline_key --name "dev-testing" --expires-days 90

Environment:
    DATABASE_URL — PostgreSQL connection string (defaults to docker-compose value)
"""

import argparse
import logging
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

PIPELINE_KEY_PREFIX = "apfa_pipe_"
SERVICE_ACCOUNT_USERNAME = "pipeline"
SERVICE_ACCOUNT_EMAIL = "pipeline@apfa.internal"


def generate_key() -> str:
    """Generate an apfa_pipe_<48-char-urlsafe> token."""
    return f"{PIPELINE_KEY_PREFIX}{secrets.token_urlsafe(48)}"


def hash_key(raw_key: str, rounds: int = 12) -> str:
    """Bcrypt-hash a raw API key."""
    return bcrypt.hashpw(
        raw_key.encode("utf-8"),
        bcrypt.gensalt(rounds=rounds),
    ).decode("utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a pipeline API key for APFA"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Human-readable name for this key (e.g. 'perplexity-computer')",
    )
    parser.add_argument(
        "--expires-days",
        type=int,
        default=None,
        help="Key expiry in days (default: no expiry)",
    )
    parser.add_argument(
        "--bcrypt-rounds",
        type=int,
        default=12,
        help="Bcrypt cost factor (default: 12)",
    )
    args = parser.parse_args()

    # Import after arg parsing to fail fast on bad args
    from app.database import SessionLocal
    from app.orm_models import ApiKey, User

    db = SessionLocal()

    try:
        # Ensure the pipeline service account exists
        service_user = (
            db.query(User)
            .filter(User.username == SERVICE_ACCOUNT_USERNAME)
            .first()
        )

        if service_user is None:
            now = datetime.now(timezone.utc)
            service_user = User(
                id=str(uuid.uuid4()),
                username=SERVICE_ACCOUNT_USERNAME,
                email=SERVICE_ACCOUNT_EMAIL,
                # Service accounts don't use password auth — set an unusable hash
                hashed_password="!service-account-no-password-login",
                disabled=False,
                role="pipeline",
                type="service",
                permissions=[],
                verified=True,
                created_at=now,
            )
            db.add(service_user)
            db.commit()
            logger.info(f"Created service account: {SERVICE_ACCOUNT_USERNAME}")
        else:
            logger.info(f"Service account exists: {SERVICE_ACCOUNT_USERNAME}")

        # Generate the key
        raw_key = generate_key()
        key_hash = hash_key(raw_key, args.bcrypt_rounds)

        expires_at = None
        if args.expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=args.expires_days)

        api_key = ApiKey(
            user_id=service_user.id,
            key_hash=key_hash,
            name=args.name,
            expires_at=expires_at,
        )
        db.add(api_key)
        db.commit()

        # Print the raw key — this is the ONLY time it's visible
        print()
        print("=" * 70)
        print("  PIPELINE API KEY GENERATED")
        print("=" * 70)
        print()
        print(f"  Key ID:     {api_key.id}")
        print(f"  Name:       {args.name}")
        print(f"  User:       {SERVICE_ACCOUNT_USERNAME} (id: {service_user.id})")
        print(f"  Expires:    {expires_at.isoformat() if expires_at else 'never'}")
        print()
        print(f"  Raw key (SAVE THIS — shown only once):")
        print()
        print(f"    {raw_key}")
        print()
        print("  Usage:")
        print(f'    curl -H "Authorization: Bearer {raw_key}" \\')
        print(f"         https://apfa.secureai.dev/admin/connectors/faiss/rebuild")
        print()
        print("  To revoke:")
        print(f"    UPDATE api_keys SET revoked_at = NOW() WHERE id = {api_key.id};")
        print()
        print("=" * 70)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate key: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
