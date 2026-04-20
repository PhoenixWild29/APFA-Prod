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
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
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
    # "human" for regular users, "service" for pipeline service accounts
    type = Column(String(20), default="human", nullable=False)
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
            "type": self.type,
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


class MarketData(Base):
    """Structured market data from Finnhub/Mboum connectors.

    NOT embedded into FAISS — served via agent tools (get_quote, etc.).
    Upserted by (ticker, data_type) to keep latest values.
    """

    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    data_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50), default="")
    change_pct = Column(Float, nullable=True)
    timestamp = Column(String(50), nullable=False)
    source = Column(String(50), default="finnhub")
    metadata_json = Column(Text, default="{}")

    __table_args__ = (
        UniqueConstraint("ticker", "data_type", name="uq_market_data_ticker_type"),
        Index("idx_market_data_ticker", "ticker"),
        Index("idx_market_data_type", "data_type"),
    )


class ApiKey(Base):
    """Machine-to-machine API keys for pipeline authentication.

    Token format: apfa_pipe_<secrets.token_urlsafe(48)>
    Only the bcrypt hash is stored — the raw key is shown once at creation.

    Key rotation: insert new row with same user_id, cutover client,
    set revoked_at on old row. No redeploy needed.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(128), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class PipelineAuditLog(Base):
    """Write-once audit trail for all pipeline operations.

    GLBA Safeguards Rule: retain >= 7 years for financial products.
    Never update rows — append only.
    """

    __tablename__ = "pipeline_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    source_connector = Column(String(50), nullable=False)
    source_url = Column(Text, server_default="")
    content_hash = Column(String(64), server_default="")
    action = Column(String(20), nullable=False)  # create | update | delete
    parent_document_id = Column(String(200), server_default="")
    chunk_count = Column(Integer, server_default="0")
    request_ip = Column(String(45), server_default="")
    user_agent = Column(String(500), server_default="")
    status = Column(String(20), nullable=False)  # success | rejected | partial
    error_code = Column(String(50), server_default="")


class RefreshToken(Base):
    """Opaque refresh tokens with rotation and family-based revocation.

    Each login creates a new token family. Each refresh rotates the token
    (old is marked replaced, new is issued). If a rotated-out token is
    presented outside the grace window, the entire family is revoked
    (theft detection).

    Only SHA-256 hashes are stored — the raw token is returned once to
    the client in an httpOnly cookie.
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    family_id = Column(String(36), nullable=False, index=True)  # UUID per login
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    replaced_by_id = Column(Integer, ForeignKey("refresh_tokens.id"), nullable=True)

    __table_args__ = (
        Index("idx_refresh_tokens_family", "family_id"),
        Index("idx_refresh_tokens_user", "user_id"),
    )
