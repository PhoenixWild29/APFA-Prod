# User Authentication & Authorization - Blueprint Template

**Section:** 12.0 User Authentication & Authorization  
**References:** APFA security-best-practices.md, api-spec.yaml

---

## 12.1 Overview

Authentication and authorization evolve from basic JWT tokens (Phase 1) to enterprise-grade 
security with RBAC, SSO, and zero-trust architecture (Phase 3-5).

---

## 12.2 Phase 1: Current State (Basic JWT)

### Architecture

```python
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# JWT configuration
JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

# User storage (IN-MEMORY MOCK)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "disabled": False,
    }
}
```

**Reference:** `app/main.py` lines 300-358

**Limitations:**
- ❌ In-memory storage (data loss on restart)
- ❌ No role-based access control
- ❌ All authenticated users have same permissions
- ❌ No audit trail
- ❌ No session management
- ❌ No password policies (complexity, expiration)

---

## 12.3 Phase 2: Production Security ← **DOCUMENTED & READY**

### 12.3.1 Role-Based Access Control (RBAC)

**Status:** ✅ **Complete implementation provided**

**Reference:** [docs/security-best-practices.md](../security-best-practices.md)

**Roles & Permissions:**

```python
class Role(str, Enum):
    USER = "user"                           # Generate advice
    FINANCIAL_ADVISOR = "financial_advisor" # + View metrics
    ADMIN = "admin"                         # + Manage tasks/indexes
    SUPER_ADMIN = "super_admin"             # All permissions

class Permission(str, Enum):
    # User permissions
    GENERATE_ADVICE = "advice:generate"
    VIEW_ADVICE_HISTORY = "advice:view_history"
    
    # Admin permissions
    VIEW_CELERY_TASKS = "admin:celery:view"
    MANAGE_CELERY_TASKS = "admin:celery:manage"
    VIEW_METRICS = "admin:metrics:view"
    MANAGE_INDEX = "admin:index:manage"
    MANAGE_USERS = "admin:users:manage"
    VIEW_AUDIT_LOGS = "admin:audit:view"

ROLE_PERMISSIONS = {
    Role.USER: {Permission.GENERATE_ADVICE, Permission.VIEW_ADVICE_HISTORY},
    Role.FINANCIAL_ADVISOR: {Permission.GENERATE_ADVICE, Permission.VIEW_ADVICE_HISTORY, Permission.VIEW_METRICS},
    Role.ADMIN: {Permission.GENERATE_ADVICE, Permission.VIEW_CELERY_TASKS, Permission.MANAGE_CELERY_TASKS, Permission.MANAGE_INDEX},
    Role.SUPER_ADMIN: set(Permission),
}

def check_permission(required: Permission):
    async def checker(user: dict = Depends(get_current_user)):
        role = Role(user.get("role", "user"))
        if required not in ROLE_PERMISSIONS[role]:
            raise HTTPException(403, "Permission denied")
        return user
    return checker

# Protect admin endpoint
@app.post("/api/admin/celery/jobs/embed-all")
async def trigger_job(user: dict = Depends(check_permission(Permission.MANAGE_CELERY_TASKS))):
    task = embed_all_documents.apply_async()
    return {"job_id": str(task.id)}
```

---

### 12.3.2 PostgreSQL User Storage

**Migration from in-memory:**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    disabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

**SQLAlchemy Models:**

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", index=True)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="sessions")
```

---

### 12.3.3 Audit Logging

**Reference:** [docs/security-best-practices.md](../security-best-practices.md) section "Audit Logging"

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    status = Column(String(20))  # success, failure
    metadata = Column(JSON)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="audit_logs")

# Log all admin actions
await audit_logger.log(
    action='trigger_embedding_job',
    user_id=current_user['id'],
    resource_type='celery_job',
    resource_id=str(task.id),
    status='submitted',
    ip_address=request.client.host
)
```

**Compliance:** SOC 2, GDPR audit requirements

---

### 12.3.4 Session Management

```python
from redis import Redis

session_store = Redis(host='localhost', port=6379, db=1)

async def create_session(user_id: int, token: str, request: Request):
    """Create session with metadata."""
    session_id = str(uuid.uuid4())
    
    session_data = {
        'user_id': user_id,
        'token_hash': hashlib.sha256(token.encode()).hexdigest(),
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent'),
        'created_at': datetime.utcnow().isoformat(),
    }
    
    # Store in Redis (30-min TTL)
    session_store.setex(
        f"session:{session_id}",
        1800,  # 30 minutes
        json.dumps(session_data)
    )
    
    # Store in PostgreSQL (permanent record)
    db_session = Session(
        id=session_id,
        user_id=user_id,
        token_hash=session_data['token_hash'],
        ip_address=session_data['ip_address'],
        user_agent=session_data['user_agent'],
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    db.add(db_session)
    await db.commit()
    
    return session_id

async def revoke_session(session_id: str):
    """Revoke session immediately."""
    session_store.delete(f"session:{session_id}")
    await db.execute(
        update(Session).where(Session.id == session_id).values(revoked=True)
    )
```

---

## 12.4 Phase 3: Enterprise Authentication

### 12.4.1 SSO/SAML Integration

```python
from onelogin.saml2.auth import OneLogin_Saml2_Auth

@app.get("/auth/saml/login")
async def saml_login(request: Request):
    saml_auth = OneLogin_Saml2_Auth(request, saml_settings)
    return RedirectResponse(saml_auth.login())

@app.post("/auth/saml/acs")
async def saml_callback(request: Request):
    saml_auth = OneLogin_Saml2_Auth(request, saml_settings)
    saml_auth.process_response()
    
    if saml_auth.is_authenticated():
        user_data = saml_auth.get_attributes()
        # Create/update user, create session
        return create_jwt_from_saml(user_data)
```

### 12.4.2 Multi-Factor Authentication (MFA)

```python
import pyotp

# Generate MFA secret
secret = pyotp.random_base32()
totp = pyotp.TOTP(secret)

# Verify MFA code
@app.post("/auth/mfa/verify")
async def verify_mfa(code: str, user: User):
    totp = pyotp.TOTP(user.mfa_secret)
    if totp.verify(code, valid_window=1):
        return create_access_token({"sub": user.username})
    raise HTTPException(401, "Invalid MFA code")
```

---

## 12.5 Phase 4-5: Zero-Trust Architecture

### Continuous Authentication

```python
# Risk-based authentication
class RiskAssessor:
    def calculate_risk(self, user, request):
        risk_score = 0
        
        # New IP address
        if request.client.host not in user.known_ips:
            risk_score += 30
        
        # New device
        if request.headers.get('user-agent') not in user.known_devices:
            risk_score += 20
        
        # Unusual time
        if is_unusual_time(user, datetime.utcnow()):
            risk_score += 15
        
        # High-value action
        if request.url.path.startswith('/admin/'):
            risk_score += 35
        
        return risk_score  # 0-100
    
    def require_additional_auth(self, risk_score):
        if risk_score > 50:
            return "mfa"  # Require MFA
        elif risk_score > 30:
            return "email_verification"
        return None  # Allow
```

---

## 12.6 Summary: Authentication Evolution

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Storage** | In-memory | PostgreSQL | PostgreSQL + Redis | Multi-region DB |
| **Access Control** | None | RBAC (4 roles) | RBAC + ABAC | Zero-trust |
| **Authentication** | JWT | JWT + Session | JWT + SSO/SAML | + MFA + Risk-based |
| **Audit** | Logs only | Full audit trail | Immutable logs | Real-time alerting |
| **Password Policy** | None | Complexity rules | + Expiration | + Biometrics |
| **Compliance** | None | OWASP Top 10 | + SOC 2 | + GDPR, SOX |

**Reference:** [docs/security-best-practices.md](../security-best-practices.md)

