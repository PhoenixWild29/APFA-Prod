# Compliance & Data Governance - Blueprint Template

**Section:** 19.0 Compliance & Data Governance  
**References:** APFA security-best-practices.md, architecture-roadmap.md

---

## 19.1 Overview

Governance evolves from basic security (Phase 1) to comprehensive compliance (Phase 2) 
to automated data governance (Phase 3-5).

---

## 19.2 Phase 1: Basic Security

- HTTPS/TLS encryption
- Password hashing (bcrypt)
- No PII protection
- No audit trail
- No compliance framework

---

## 19.3 Phase 2: Production Compliance ← **DOCUMENTED**

### 19.3.1 OWASP Top 10 Mitigation

**Reference:** [docs/security-best-practices.md](../security-best-practices.md)

| Risk | Mitigation | Implementation |
|------|-----------|----------------|
| **A01: Broken Access Control** | RBAC | `check_permission()` decorator |
| **A02: Cryptographic Failures** | TLS 1.3, AES-256 | Enforced in config |
| **A03: Injection** | Input validation | Pydantic validators with SQL/XSS prevention |
| **A04: Insecure Design** | Threat modeling | ADRs, security reviews |
| **A05: Security Misconfiguration** | Security headers | HSTS, CSP, X-Frame-Options |
| **A06: Vulnerable Components** | Dependency scanning | Dependabot, Snyk, Safety |
| **A07: Authentication Failures** | Strong passwords, MFA-ready | bcrypt cost=12 |
| **A08: Software Integrity** | Code signing | Docker image signatures |
| **A09: Logging Failures** | Audit logs | Comprehensive audit trail |
| **A10: SSRF** | URL validation | Input sanitization |

**Status:** ✅ All mitigations implemented

---

### 19.3.2 Audit Logging

```python
class AuditLogger:
    async def log(self, action, user_id, resource_type, resource_id, status, metadata, ip):
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': status,
            'metadata': metadata,
            'ip_address': ip,
        }
        
        # Persist (immutable)
        await db.audit_logs.insert_one(audit_entry)
        await s3.put_object(Bucket='audit-logs', Body=json.dumps(audit_entry))

# Log all admin actions
await audit_logger.log(
    action='trigger_embedding_job',
    user_id=current_user['id'],
    resource_type='celery_job',
    resource_id=str(task.id),
    status='submitted',
    metadata={'task_name': 'embed_all_documents'},
    ip_address=request.client.host
)
```

**Retention:** 90 days (compliance requirement)  
**Storage:** PostgreSQL + S3 (immutable)

---

### 19.3.3 PII Protection

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

def detect_pii(text):
    return analyzer.analyze(
        text=text,
        entities=['SSN', 'CREDIT_CARD', 'PHONE_NUMBER', 'EMAIL'],
        language='en'
    )

def anonymize_for_logging(text):
    results = detect_pii(text)
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized.text

# Safe logging
logger.info(f"Processing query: {anonymize_for_logging(user_query)}")
```

**Compliance:** GDPR, CCPA, PCI-DSS

---

## 19.4 Phase 3: Enterprise Governance

### Data Classification

```python
class DataClassifier:
    def classify(self, text):
        pii = detect_pii(text)
        
        if any(r.entity_type in ['SSN', 'CREDIT_CARD'] for r in pii):
            return 'RESTRICTED'  # Highest security
        elif any(r.entity_type in ['EMAIL', 'PHONE_NUMBER'] for r in pii):
            return 'SENSITIVE'
        elif 'confidential' in text.lower():
            return 'INTERNAL'
        else:
            return 'PUBLIC'

# Tag all data
classification = classifier.classify(document_text)
db.documents.update({'classification': classification})
```

### Data Retention Policies

```python
# GDPR: Right to deletion
@app.delete("/users/{user_id}/data")
async def delete_user_data(user_id: str, admin: User = Depends(get_admin)):
    # Delete user data
    await db.users.delete(user_id)
    await db.queries.delete_many({'user_id': user_id})
    await db.embeddings.delete_many({'user_id': user_id})
    
    # Audit log (keep for compliance)
    await audit_logger.log('user_data_deleted', admin.id, 'user', user_id, 'success')
```

---

## 19.5 Phase 4-5: Advanced Governance

### Automated Compliance Reporting

```python
class ComplianceReporter:
    def generate_soc2_report(self):
        return {
            'access_controls': self.audit_access_controls(),
            'encryption': self.verify_encryption(),
            'logging': self.verify_audit_logs(),
            'monitoring': self.verify_security_monitoring(),
            'backup': self.verify_backup_procedures(),
        }
    
    def generate_gdpr_report(self):
        return {
            'data_inventory': self.catalog_pii(),
            'consent_tracking': self.verify_consent(),
            'deletion_requests': self.track_deletions(),
            'breach_notifications': self.track_breaches(),
        }
```

### Data Lineage Tracking

```python
# Track data flow
lineage = {
    'source': 'customer_crm',
    'transformations': [
        {'step': 'extract', 'timestamp': '2025-10-01T00:00:00Z'},
        {'step': 'embed', 'timestamp': '2025-10-01T01:00:00Z'},
        {'step': 'index', 'timestamp': '2025-10-01T01:05:00Z'},
    ],
    'consumers': ['apfa_api', 'analytics_dashboard'],
}
```

---

## 19.6 Summary

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Standards** | None | OWASP Top 10 | + SOC 2 | + GDPR, SOX, HIPAA |
| **Audit** | Basic logs | Full audit trail | Immutable logs | Real-time compliance |
| **PII** | No protection | Detection + masking | Classification | Field-level encryption |
| **Governance** | None | Manual | Automated | AI-powered |

**Reference:** [docs/security-best-practices.md](../security-best-practices.md) complete guide

