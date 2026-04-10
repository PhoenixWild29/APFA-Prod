"""SQLAlchemy ORM models for APFA.

These are the database-backed models. Pydantic models in app/models/ remain as
request/response schemas — they are not replaced by these.

APFA-013 scope: only the User model. Other in-memory stores (audit_trail_db,
request_status_db, reindex_operations, embeddings_cache) stay in-memory and
will be migrated in future sprints.
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    JSON,
    String,
)

from app.database import Base


class User(Base):
    """User account — replaces the fake_users_db dict in main.py.

    Field mapping from the old dict schema:
        user_id                 -> id (primary key)
        username                -> username (indexed, unique)
        email                   -> email (indexed, unique)
        hashed_password         -> hashed_password
        disabled                -> disabled
        role                    -> role (default "standard" to match registration code)
        permissions             -> permissions (JSON array, was a Python list)
        verified                -> verified
        verification_token      -> verification_token
        token_expiration        -> token_expiration (DateTime, was ISO string)
        verified_at             -> verified_at (DateTime, was ISO string)
        created_at              -> created_at (DateTime)
        first_name              -> first_name (from registration form)
        last_name               -> last_name (from registration form)
        marketing_consent       -> marketing_consent (from registration form)
        subscription_tier       -> subscription_tier (default "free")
        stripe_customer_id      -> stripe_customer_id (indexed for webhook reverse-lookup)
        stripe_subscription_id  -> stripe_subscription_id
        query_count_this_period -> query_count_this_period
        billing_period_start    -> billing_period_start (DateTime)
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)
    role = Column(String, default="standard", nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True)
    token_expiration = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    subscription_tier = Column(String, default="free", nullable=False)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True)
    query_count_this_period = Column(Integer, default=0, nullable=False)
    billing_period_start = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_users_stripe_customer", "stripe_customer_id"),
    )

    def to_dict(self) -> dict:
        """Convert ORM row to the legacy dict shape expected by existing code paths.

        The rest of main.py was written assuming fake_users_db returned dicts.
        This method lets us drop-in replace dict access without rewriting every
        consumer. Keeps the refactor scope tight (APFA-013 success criterion #5).
        """
        return {
            "user_id": self.id,
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "disabled": self.disabled,
            "role": self.role,
            "permissions": self.permissions or [],
            "verified": self.verified,
            "verification_token": self.verification_token,
            "token_expiration": (
                self.token_expiration.isoformat() if self.token_expiration else None
            ),
            "verified_at": (
                self.verified_at.isoformat() if self.verified_at else None
            ),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "first_name": self.first_name,
            "last_name": self.last_name,
            "marketing_consent": self.marketing_consent,
            "subscription_tier": self.subscription_tier,
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "query_count_this_period": self.query_count_this_period,
            "billing_period_start": (
                self.billing_period_start.isoformat()
                if self.billing_period_start
                else None
            ),
        }
