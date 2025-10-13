# Security Best Practices & Implementation Guide

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** Security & Compliance Team  
**Status:** Production Security Specification

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [API Security](#api-security)
4. [WebSocket Security](#websocket-security)
5. [Secrets Management](#secrets-management)
6. [Network Security](#network-security)
7. [Data Protection](#data-protection)
8. [Threat Detection & Response](#threat-detection--response)
9. [Audit Logging](#audit-logging)
10. [Compliance](#compliance)

---

## Security Overview

### Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (Perimeter)                         │
│  ├─ WAF (Web Application Firewall)                             │
│  ├─ DDoS protection                                            │
│  ├─ TLS 1.3 encryption                                         │
│  └─ Network segmentation (VPC/VNet)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  Layer 2: Application Security (API Gateway)                   │
│  ├─ Rate limiting (10 req/min)                                 │
│  ├─ Input validation (Pydantic)                                │
│  ├─ Content sanitization (HTML, SQL injection)                 │
│  └─ CORS policy (whitelist origins)                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  Layer 3: Authentication & Authorization                       │
│  ├─ JWT tokens (HS256 signed)                                  │
│  ├─ Password hashing (bcrypt, cost=12)                         │
│  ├─ Role-based access control (RBAC)                           │
│  └─ Session management (Redis)                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  Layer 4: Data Protection                                      │
│  ├─ Encryption at rest (AES-256)                               │
│  ├─ Encryption in transit (TLS 1.3)                            │
│  ├─ PII masking in logs                                        │
│  └─ Secure deletion (crypto-shredding)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  Layer 5: Monitoring & Detection                               │
│  ├─ Anomaly detection (ML-based)                               │
│  ├─ Audit logging (immutable)                                  │
│  ├─ Security metrics (Prometheus)                              │
│  └─ Incident response (automated + manual)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization

### JWT Token Security

**Current Implementation (Enhanced):**

```python
# backend/app/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional

# Security configuration
JWT_SECRET = settings.jwt_secret  # From environment/secrets manager
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing (bcrypt with cost factor 12)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor (higher = more secure, slower)
)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """Create JWT access token with enhanced security."""
    to_encode = data.copy()
    
    # Expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "nbf": datetime.utcnow(),  # Not before
        "iss": "apfa-api",         # Issuer
        "aud": "apfa-client",      # Audience
    })
    
    # Additional claims (roles, permissions)
    if additional_claims:
        to_encode.update(additional_claims)
    
    # Sign token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token with comprehensive validation."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="apfa-client",
            issuer="apfa-api",
        )
        
        # Check token is not expired
        if payload.get("exp") < datetime.utcnow().timestamp():
            raise JWTError("Token expired")
        
        # Check token is not used before valid time
        if payload.get("nbf") > datetime.utcnow().timestamp():
            raise JWTError("Token not yet valid")
        
        return payload
    
    except JWTError as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Role-Based Access Control (RBAC)

**Implementation:**

```python
# backend/app/rbac.py
from enum import Enum
from typing import List, Set
from fastapi import Depends, HTTPException

class Role(str, Enum):
    USER = "user"
    FINANCIAL_ADVISOR = "financial_advisor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class Permission(str, Enum):
    # Advice permissions
    GENERATE_ADVICE = "advice:generate"
    VIEW_ADVICE_HISTORY = "advice:view_history"
    
    # Admin permissions
    VIEW_CELERY_TASKS = "admin:celery:view"
    MANAGE_CELERY_TASKS = "admin:celery:manage"
    VIEW_METRICS = "admin:metrics:view"
    MANAGE_INDEX = "admin:index:manage"
    
    # Super admin permissions
    MANAGE_USERS = "admin:users:manage"
    VIEW_AUDIT_LOGS = "admin:audit:view"

# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.USER: {
        Permission.GENERATE_ADVICE,
        Permission.VIEW_ADVICE_HISTORY,
    },
    Role.FINANCIAL_ADVISOR: {
        Permission.GENERATE_ADVICE,
        Permission.VIEW_ADVICE_HISTORY,
        Permission.VIEW_METRICS,
    },
    Role.ADMIN: {
        Permission.GENERATE_ADVICE,
        Permission.VIEW_ADVICE_HISTORY,
        Permission.VIEW_CELERY_TASKS,
        Permission.MANAGE_CELERY_TASKS,
        Permission.VIEW_METRICS,
        Permission.MANAGE_INDEX,
    },
    Role.SUPER_ADMIN: set(Permission),  # All permissions
}

def get_user_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())

def check_permission(required_permission: Permission):
    """Dependency to check if user has required permission."""
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        user_role = Role(current_user.get("role", "user"))
        user_permissions = get_user_permissions(user_role)
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {required_permission}"
            )
        
        return current_user
    
    return permission_checker

# Usage in endpoints
@app.post("/api/admin/celery/jobs/embed-all")
async def trigger_embedding_job(
    current_user: dict = Depends(check_permission(Permission.MANAGE_CELERY_TASKS))
):
    """Only users with MANAGE_CELERY_TASKS permission can trigger jobs."""
    task = embed_all_documents.apply_async()
    return {"job_id": str(task.id)}
```

---

## API Security

### Input Validation & Sanitization

**Enhanced Validation:**

```python
# backend/app/validators.py
from pydantic import BaseModel, Field, field_validator
import re
import html
from typing import Optional

class LoanQuerySecure(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Financial query (5-500 characters)"
    )
    user_context: Optional[dict] = Field(
        None,
        description="Additional user context (optional)"
    )
    
    @field_validator('query')
    @classmethod
    def validate_query_security(cls, v: str) -> str:
        """Comprehensive security validation."""
        
        # 1. SQL Injection prevention
        sql_patterns = [
            r"(\bOR\b.*\b=\b)",
            r"(\bUNION\b.*\bSELECT\b)",
            r"(;.*DROP\b)",
            r"(;.*DELETE\b)",
            r"(;.*UPDATE\b)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potential SQL injection detected")
        
        # 2. XSS prevention (HTML sanitization)
        if re.search(r'<[^>]+>', v):
            # Strip HTML tags
            v = html.escape(v)
        
        # 3. Command injection prevention
        command_chars = [';', '|', '&', '$', '`', '(', ')', '{', '}']
        if any(char in v for char in command_chars):
            raise ValueError("Invalid characters detected")
        
        # 4. Path traversal prevention
        if '../' in v or '..\\' in v:
            raise ValueError("Path traversal attempt detected")
        
        # 5. Profanity check (existing)
        from profanity_check import predict_prob
        if predict_prob([v])[0] > 0.8:
            raise ValueError("Inappropriate content detected")
        
        # 6. Financial relevance check (existing)
        financial_keywords = ['loan', 'credit', 'mortgage', 'finance', 'interest', 'payment', 'debt', 'borrow']
        if not any(keyword in v.lower() for keyword in financial_keywords):
            raise ValueError("Query must be finance-related")
        
        # 7. Length and repetition checks (existing)
        words = v.lower().split()
        if len(words) > len(set(words)) * 2:
            raise ValueError("Excessive repetition detected")
        
        return v
    
    @field_validator('user_context')
    @classmethod
    def validate_user_context(cls, v: Optional[dict]) -> Optional[dict]:
        """Validate user context doesn't contain sensitive data."""
        if v:
            # Prevent injection of sensitive keys
            forbidden_keys = ['password', 'token', 'secret', 'key', 'credential']
            for key in v.keys():
                if any(forbidden in key.lower() for forbidden in forbidden_keys):
                    raise ValueError(f"Forbidden key in context: {key}")
            
            # Limit context size
            import json
            if len(json.dumps(v)) > 1000:
                raise ValueError("User context too large (max 1KB)")
        
        return v
```

---

## WebSocket Security

### Authentication & Authorization

```python
# backend/app/websocket_security.py
from jose import jwt
from datetime import datetime

@sio.event
async def connect(sid, environ, auth):
    """Enhanced WebSocket authentication with role checking."""
    try:
        # 1. Verify JWT token
        token = auth.get('token')
        if not token:
            logger.warning(f"[WS Auth] No token provided (sid={sid}, ip={get_client_ip(environ)})")
            return False
        
        # 2. Decode and validate token
        try:
            payload = verify_token(token)
        except Exception as e:
            logger.warning(f"[WS Auth] Invalid token (sid={sid}, error={e})")
            return False
        
        user_id = payload.get('sub')
        user_role = payload.get('role', 'user')
        
        # 3. Check admin role for admin endpoints
        if environ.get('PATH_INFO', '').startswith('/ws/admin/'):
            if user_role not in ['admin', 'super_admin']:
                logger.warning(f"[WS Auth] Non-admin access attempt (sid={sid}, user={user_id}, role={user_role})")
                return False
        
        # 4. Rate limiting (max 3 connections per user)
        existing_connections = await get_user_connection_count(user_id)
        if existing_connections >= 3:
            logger.warning(f"[WS Auth] Too many connections (sid={sid}, user={user_id}, count={existing_connections})")
            return False
        
        # 5. Store session with security metadata
        await sio.save_session(sid, {
            'user_id': user_id,
            'role': user_role,
            'ip': get_client_ip(environ),
            'connected_at': datetime.utcnow().isoformat(),
            'user_agent': environ.get('HTTP_USER_AGENT'),
        })
        
        # 6. Subscribe to user-specific room only
        sio.enter_room(sid, f"user:{user_id}")
        
        # 7. Audit log
        await audit_log(
            action="websocket_connect",
            user_id=user_id,
            metadata={'sid': sid, 'endpoint': environ.get('PATH_INFO')}
        )
        
        logger.info(f"[WS Auth] Connection authorized (sid={sid}, user={user_id}, role={user_role})")
        return True
    
    except Exception as e:
        logger.error(f"[WS Auth] Connection error: {e}")
        return False

@sio.event
async def disconnect(sid):
    """Enhanced disconnect with audit logging."""
    session = await sio.get_session(sid)
    user_id = session.get('user_id')
    
    # Audit log
    await audit_log(
        action="websocket_disconnect",
        user_id=user_id,
        metadata={'sid': sid, 'duration': calculate_duration(session)}
    )
    
    logger.info(f"[WS Auth] Disconnected (sid={sid}, user={user_id})")

def get_client_ip(environ) -> str:
    """Get real client IP (handle proxies)."""
    # Check X-Forwarded-For header (proxy/load balancer)
    forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    # Check X-Real-IP header
    real_ip = environ.get('HTTP_X_REAL_IP')
    if real_ip:
        return real_ip
    
    # Fall back to REMOTE_ADDR
    return environ.get('REMOTE_ADDR', 'unknown')
```

---

## Secrets Management

### AWS Secrets Manager Integration

```python
# backend/app/secrets.py
import boto3
import json
from functools import lru_cache
from typing import Any

class SecretsManager:
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    @lru_cache(maxsize=100)
    def get_secret(self, secret_name: str) -> dict:
        """Get secret with caching."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response['SecretString']
            return json.loads(secret_string)
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {e}")
            raise
    
    def rotate_secret(self, secret_name: str, new_value: str):
        """Rotate secret with zero-downtime."""
        # 1. Create new version
        self.client.put_secret_value(
            SecretId=secret_name,
            SecretString=new_value,
        )
        
        # 2. Clear cache
        self.get_secret.cache_clear()
        
        # 3. Trigger app reload (graceful)
        # Applications will fetch new secret on next request

# Singleton instance
secrets_manager = SecretsManager()

# Usage
JWT_SECRET = secrets_manager.get_secret("apfa/prod/jwt-secret")["value"]
API_KEY = secrets_manager.get_secret("apfa/prod/api-key")["value"]
```

### Environment Variable Security

```bash
# .env.example (NEVER commit actual values)
# Use this as template, copy to .env and fill in real values

# Authentication
JWT_SECRET=CHANGE_ME_TO_RANDOM_STRING_32_CHARS
API_KEY=CHANGE_ME_TO_RANDOM_STRING_64_CHARS

# Database
DATABASE_URL=postgresql://user:CHANGE_PASSWORD@localhost:5432/apfa

# External Services
MINIO_ACCESS_KEY=CHANGE_ME
MINIO_SECRET_KEY=CHANGE_ME
AWS_ACCESS_KEY_ID=CHANGE_ME
AWS_SECRET_ACCESS_KEY=CHANGE_ME

# Generate strong secrets with:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Threat Detection & Response

### Anomaly Detection

```python
# backend/app/security/anomaly_detection.py
from collections import defaultdict
import time
from prometheus_client import Counter

# Metrics
SUSPICIOUS_ACTIVITY = Counter(
    'apfa_suspicious_activity_total',
    'Suspicious activity detected',
    ['type', 'severity']
)

class AnomalyDetector:
    def __init__(self):
        self.user_activity = defaultdict(list)  # {user_id: [timestamps]}
        self.failed_logins = defaultdict(list)  # {ip: [timestamps]}
    
    async def detect_anomalies(self, user_id: str, action: str, metadata: dict):
        """Detect suspicious patterns."""
        now = time.time()
        
        # 1. Rapid-fire requests (potential DDoS)
        self.user_activity[user_id].append(now)
        recent_requests = [t for t in self.user_activity[user_id] if now - t < 60]
        
        if len(recent_requests) > 100:  # >100 requests in 1 minute
            SUSPICIOUS_ACTIVITY.labels(type='rapid_fire', severity='high').inc()
            await self.trigger_alert(
                severity='high',
                title='Rapid-fire requests detected',
                details=f'User {user_id}: {len(recent_requests)} requests in 1 minute'
            )
            return True
        
        # 2. Unusual access patterns (e.g., admin access from new IP)
        if action == 'admin_access':
            user_ips = await get_user_historical_ips(user_id)
            current_ip = metadata.get('ip')
            
            if current_ip not in user_ips:
                SUSPICIOUS_ACTIVITY.labels(type='new_ip_admin', severity='medium').inc()
                await self.trigger_alert(
                    severity='medium',
                    title='Admin access from new IP',
                    details=f'User {user_id} from {current_ip}'
                )
        
        # 3. Failed login attempts (brute force)
        if action == 'failed_login':
            ip = metadata.get('ip')
            self.failed_logins[ip].append(now)
            recent_failures = [t for t in self.failed_logins[ip] if now - t < 300]
            
            if len(recent_failures) > 5:  # >5 failures in 5 minutes
                SUSPICIOUS_ACTIVITY.labels(type='brute_force', severity='critical').inc()
                await self.block_ip(ip, duration=3600)  # Block for 1 hour
                await self.trigger_alert(
                    severity='critical',
                    title='Brute force attack detected',
                    details=f'IP {ip}: {len(recent_failures)} failed logins'
                )
        
        return False
    
    async def trigger_alert(self, severity: str, title: str, details: str):
        """Send security alert to monitoring system."""
        # Send to Slack, PagerDuty, email, etc.
        logger.warning(f"[Security Alert] {severity}: {title} - {details}")

detector = AnomalyDetector()
```

---

## Audit Logging

### Comprehensive Audit Trail

```python
# backend/app/audit.py
from datetime import datetime
import json
from typing import Optional

class AuditLogger:
    def __init__(self, storage_backend='database'):  # or 's3', 'cloudwatch'
        self.storage = storage_backend
    
    async def log(
        self,
        action: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        status: str = 'success',
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ):
        """
        Log auditable action.
        
        Examples:
        - User authentication
        - Admin operations (trigger job, revoke task)
        - Data access (view sensitive info)
        - Configuration changes
        """
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': status,
            'metadata': metadata or {},
            'ip_address': ip_address,
            'session_id': get_session_id(),
        }
        
        # Log to structured logging
        logger.info(
            f"[Audit] {action}",
            extra={'audit': audit_entry}
        )
        
        # Persist to database/S3/CloudWatch
        await self.persist(audit_entry)
        
        # Update Prometheus metric
        AUDIT_EVENTS.labels(
            action=action,
            resource_type=resource_type,
            status=status
        ).inc()
    
    async def persist(self, audit_entry: dict):
        """Persist audit log (immutable)."""
        if self.storage == 'database':
            await db.audit_logs.insert_one(audit_entry)
        elif self.storage == 's3':
            await s3.put_object(
                Bucket='apfa-audit-logs',
                Key=f"{audit_entry['timestamp']}/{audit_entry['action']}.json",
                Body=json.dumps(audit_entry)
            )
        elif self.storage == 'cloudwatch':
            cloudwatch.put_log_events(
                logGroupName='/apfa/audit',
                logStreamName=audit_entry['user_id'],
                logEvents=[{
                    'timestamp': int(datetime.utcnow().timestamp() * 1000),
                    'message': json.dumps(audit_entry)
                }]
            )

audit_logger = AuditLogger()

# Usage in endpoints
@app.post("/api/admin/celery/jobs/embed-all")
async def trigger_embedding_job(
    current_user: dict = Depends(get_current_admin),
    request: Request
):
    # Trigger job
    task = embed_all_documents.apply_async()
    
    # Audit log
    await audit_logger.log(
        action='trigger_embedding_job',
        user_id=current_user['username'],
        resource_type='celery_job',
        resource_id=str(task.id),
        status='submitted',
        metadata={'task_name': 'embed_all_documents'},
        ip_address=request.client.host
    )
    
    return {"job_id": str(task.id)}
```

---

## Data Protection

### PII Masking in Logs

```python
# backend/app/security/pii_masking.py
import re
from typing import Any

class PIIMasker:
    """Mask personally identifiable information in logs."""
    
    # PII patterns
    PATTERNS = {
        'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX'),
        'credit_card': (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'XXXX-XXXX-XXXX-XXXX'),
        'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'XXX@XXX.XXX'),
        'phone': (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'XXX-XXX-XXXX'),
    }
    
    @classmethod
    def mask(cls, text: str) -> str:
        """Mask all PII in text."""
        masked = text
        
        for pii_type, (pattern, replacement) in cls.PATTERNS.items():
            masked = re.sub(pattern, replacement, masked)
        
        return masked
    
    @classmethod
    def mask_dict(cls, data: dict) -> dict:
        """Recursively mask PII in dictionary."""
        masked = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                masked[key] = cls.mask(value)
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [cls.mask(v) if isinstance(v, str) else v for v in value]
            else:
                masked[key] = value
        
        return masked

# Usage in logging
logger.info(f"Processing query: {PIIMasker.mask(user_query)}")
```

---

## Compliance & Standards

### OWASP Top 10 Mitigation

| OWASP Risk | Mitigation | Implementation |
|------------|-----------|----------------|
| **A01: Broken Access Control** | RBAC, permission checks | check_permission() decorator |
| **A02: Cryptographic Failures** | TLS 1.3, AES-256, bcrypt | Enforced in config |
| **A03: Injection** | Input validation, parameterized queries | Pydantic validators |
| **A04: Insecure Design** | Threat modeling, security reviews | ADRs, architecture docs |
| **A05: Security Misconfiguration** | Security headers, defaults | FastAPI middleware |
| **A06: Vulnerable Components** | Dependency scanning, updates | Dependabot, snyk |
| **A07: Identity Failures** | MFA-ready, strong passwords | bcrypt cost=12 |
| **A08: Software Integrity** | Code signing, SRI | Docker image signatures |
| **A09: Logging Failures** | Comprehensive audit logs | audit_logger |
| **A10: SSRF** | URL validation, network policies | Input validation |

### SOC 2 Compliance Readiness

**Controls Implemented:**

✅ **CC6.1 - Logical Access Controls:**
- JWT authentication
- RBAC with granular permissions
- Session management

✅ **CC6.6 - Audit Logging:**
- Comprehensive audit trail
- Immutable logs (S3 with versioning)
- Retention policy (90 days)

✅ **CC6.7 - Restricted Access:**
- VPC isolation (private subnets)
- Security groups (least privilege)
- Bastion host for SSH access

✅ **CC7.2 - Threat Detection:**
- Anomaly detection (ML-based)
- Automated alerts (PagerDuty)
- Incident response runbooks

---

## Security Checklist

### Pre-Production Security Review

- [ ] All secrets in environment variables or secrets manager (no hardcoded)
- [ ] JWT secret is strong (>32 characters, random)
- [ ] bcrypt cost factor ≥12
- [ ] TLS 1.3 enforced (no TLS 1.0/1.1)
- [ ] CORS whitelist configured (no allow_origins=["*"])
- [ ] Rate limiting enabled (10 req/min)
- [ ] Input validation on all endpoints (Pydantic)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (HTML escaping)
- [ ] CSRF protection (SameSite cookies)
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] Dependency scanning (Snyk, Dependabot)
- [ ] Container scanning (Trivy, Grype)
- [ ] Audit logging enabled
- [ ] PII masking in logs
- [ ] Encryption at rest (S3, RDS)
- [ ] Encryption in transit (TLS)
- [ ] Network segmentation (VPC)
- [ ] Least privilege IAM roles
- [ ] MFA for admin access

---

**Document Status:** Production Security Specification  
**Compliance:** OWASP Top 10, SOC 2 ready  
**Next Steps:** Security audit, penetration testing

