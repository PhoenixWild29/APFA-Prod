# CI/CD Pipeline Documentation
## APFA - Continuous Integration & Deployment

**Version:** 1.0  
**Last Updated:** October 12, 2025  
**Status:** ✅ Active

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [GitHub Actions Workflows](#github-actions-workflows)
4. [Deployment Strategies](#deployment-strategies)
5. [Environment Configuration](#environment-configuration)
6. [Security & Secrets](#security--secrets)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Troubleshooting](#troubleshooting)

---

## 📊 OVERVIEW

The APFA CI/CD pipeline provides automated testing, building, and deployment across multiple environments and cloud providers.

### **Key Features:**
- ✅ Automated testing (unit, integration, E2E)
- ✅ Code quality checks (linting, formatting, type checking)
- ✅ Security scanning (dependencies, secrets, containers)
- ✅ Docker image building & registry management
- ✅ Multi-cloud deployment (AWS, Azure, GCP)
- ✅ Environment-based workflows (dev, staging, production)
- ✅ Automated rollback on failure
- ✅ Performance & smoke testing

---

## 🏗️ PIPELINE ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────┐
│  Code Push / PR                                               │
└────────────────┬─────────────────────────────────────────────┘
                 │
    ┌────────────▼─────────────┐
    │  Trigger CI Workflows    │
    └────────────┬─────────────┘
                 │
    ┌────────────▼──────────────────────────────────────┐
    │                                                    │
┌───▼────┐  ┌────▼─────┐  ┌────▼────┐  ┌────▼─────┐
│Testing │  │  Linting │  │Security │  │  Build   │
│  Unit  │  │  Format  │  │  Scan   │  │  Docker  │
│  E2E   │  │TypeCheck │  │  OWASP  │  │  Images  │
└───┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘
    │            │              │            │
    └────────────┴──────────────┴────────────┘
                 │
    ┌────────────▼─────────────┐
    │  All Checks Pass?        │
    └────────────┬─────────────┘
                 │ YES
    ┌────────────▼─────────────────────────────────┐
    │  Deploy (based on branch)                    │
    │  - main → Production                         │
    │  - staging → Staging                         │
    │  - develop → Development                     │
    └────────────┬─────────────────────────────────┘
                 │
    ┌────────────▼─────────────┐
    │  Post-Deployment Tests   │
    │  - Smoke tests           │
    │  - Health checks         │
    │  - Metrics validation    │
    └──────────────────────────┘
```

---

## 🔄 GITHUB ACTIONS WORKFLOWS

### **1. Backend CI/CD** (`ci-backend.yml`)

**Triggers:**
- Push to main, develop, staging
- Pull requests to main, develop
- Changes to backend files

**Jobs:**
1. **Test** - Run pytest with coverage
2. **Lint** - Black, Flake8, MyPy, Bandit
3. **Build** - Build & push Docker image
4. **Deploy** - Environment-based deployment

**Duration:** ~8-12 minutes

### **2. Frontend CI/CD** (`ci-frontend.yml`)

**Triggers:**
- Push to main, develop, staging
- Pull requests to main, develop
- Changes to frontend files

**Jobs:**
1. **Test** - Jest, accessibility tests
2. **Lint** - ESLint, Prettier
3. **Build** - Vite production build
4. **Docker Build** - Container image
5. **Deploy** - CDN/static hosting

**Duration:** ~6-10 minutes

### **3. Integration Tests** (`ci-integration.yml`)

**Triggers:**
- Push to main, develop
- Pull requests to main
- Daily schedule (2 AM UTC)

**Jobs:**
1. **E2E Tests** - Full stack integration
2. **Performance Tests** - Load testing with Locust
3. **API Tests** - Endpoint validation

**Duration:** ~15-20 minutes

### **4. Security Scanning** (`security-scan.yml`)

**Triggers:**
- Push to main, develop
- Pull requests
- Daily schedule (3 AM UTC)

**Jobs:**
1. **Dependency Scan** - Safety, npm audit
2. **Code Security** - CodeQL analysis
3. **Secret Scan** - TruffleHog
4. **Container Scan** - Trivy
5. **OWASP Check** - Dependency vulnerabilities

**Duration:** ~10-15 minutes

### **5. Docker Compose** (`ci-docker-compose.yml`)

**Triggers:**
- Changes to docker-compose.yml
- Changes to Dockerfile or monitoring configs

**Jobs:**
1. **Validation** - Config syntax
2. **Integration Test** - Full stack startup
3. **Monitoring Validation** - Prometheus/Grafana

**Duration:** ~5-8 minutes

### **6. Monitoring** (`ci-monitoring.yml`)

**Triggers:**
- Changes to monitoring configs
- Daily schedule

**Jobs:**
1. **Validate Prometheus** - Config validation
2. **Validate Grafana** - Dashboard JSON
3. **Test Metrics** - Endpoint validation

**Duration:** ~3-5 minutes

### **7. Release** (`release.yml`)

**Triggers:**
- Tag push (v*.*.*)

**Jobs:**
1. **Create Release** - GitHub release with changelog
2. **Build Release Images** - Versioned Docker images
3. **Deploy Release** - Production deployment
4. **Validation** - Post-deployment tests

**Duration:** ~20-30 minutes

### **8. Multi-Cloud Deploy** (`cd-multi-cloud.yml`)

**Triggers:**
- Manual workflow dispatch

**Jobs:**
1. **Deploy AWS** - ECS Fargate via CDK
2. **Deploy Azure** - AKS via Terraform
3. **Deploy GCP** - GKE via Helm
4. **Post-Deployment** - Validation tests

**Duration:** ~15-25 minutes per cloud

---

## 🚀 DEPLOYMENT STRATEGIES

### **Branch-Based Deployment**

| Branch | Environment | Auto-Deploy | Approval Required |
|--------|-------------|-------------|-------------------|
| `main` | Production | ✅ | ✅ (GitHub Environment) |
| `staging` | Staging | ✅ | ❌ |
| `develop` | Development | ✅ | ❌ |
| `feature/*` | Preview (optional) | ❌ | ❌ |

### **Deployment Flow**

```
Feature Branch → develop → staging → main → production
     (PR)          (Auto)    (Auto)   (Auto+Approval)
```

### **Rollback Strategy**

1. **Automatic Rollback:**
   - Failed health checks
   - Failed smoke tests
   - Error rate spike

2. **Manual Rollback:**
   ```bash
   # Revert to previous version
   git revert HEAD
   git push origin main
   
   # Or deploy specific version
   git checkout v1.2.3
   git push origin main --force  # With approval
   ```

---

## ⚙️ ENVIRONMENT CONFIGURATION

### **GitHub Environments**

**Production:**
- **Protection Rules:** Require approval from maintainers
- **Secrets:** AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- **Variables:** ENVIRONMENT=production, DOMAIN=apfa.yourdomain.com

**Staging:**
- **Protection Rules:** None
- **Secrets:** AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- **Variables:** ENVIRONMENT=staging, DOMAIN=staging.apfa.yourdomain.com

**Development:**
- **Protection Rules:** None
- **Secrets:** AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- **Variables:** ENVIRONMENT=development

### **Required Secrets**

**AWS Deployment:**
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_ACCOUNT_ID
AWS_REGION
```

**Azure Deployment:**
```
AZURE_CREDENTIALS
AZURE_SUBSCRIPTION_ID
AZURE_RESOURCE_GROUP
```

**GCP Deployment:**
```
GCP_SA_KEY
GCP_PROJECT_ID
GCP_REGION
```

**Container Registry:**
```
GITHUB_TOKEN (automatically provided)
```

**Notifications:**
```
SLACK_WEBHOOK_URL (optional)
TEAMS_WEBHOOK_URL (optional)
```

---

## 🔒 SECURITY & SECRETS

### **Secret Management**

1. **GitHub Secrets:**
   - Navigate to Settings → Secrets and variables → Actions
   - Add repository secrets for each environment
   - Use environment-specific secrets for isolation

2. **Secret Rotation:**
   - Rotate secrets quarterly
   - Update in GitHub and deployment targets
   - Document rotation in CHANGELOG

### **Security Scanning**

**Automated Scans:**
- ✅ Dependency vulnerabilities (Safety, npm audit)
- ✅ Code security (CodeQL, Bandit)
- ✅ Container vulnerabilities (Trivy)
- ✅ Secret exposure (TruffleHog)
- ✅ OWASP dependencies

**Scan Results:**
- View in GitHub Security tab
- SARIF files uploaded automatically
- Alerts for critical issues

---

## 📊 MONITORING & ALERTS

### **Pipeline Monitoring**

**GitHub Actions:**
- View workflow runs in Actions tab
- Status badges in README
- Email notifications for failures

**Metrics Tracked:**
- Build duration
- Test pass rate
- Deployment success rate
- Code coverage trends

### **Deployment Alerts**

**Success Notifications:**
- Deployment complete
- All tests passed
- Services healthy

**Failure Alerts:**
- Test failures
- Build failures
- Deployment failures
- Security vulnerabilities

**Integration Options:**
- Slack webhooks
- Microsoft Teams
- Email notifications
- PagerDuty (for production)

---

## 🛠️ TROUBLESHOOTING

### **Common Issues**

**1. Tests Failing:**
```bash
# Run locally first
pytest tests/ -v
npm test

# Check for environment differences
```

**2. Build Failures:**
```bash
# Check Docker build locally
docker build -t apfa-backend:test .
docker run -p 8000:8000 apfa-backend:test
```

**3. Deployment Failures:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Validate CDK stack
cd infra && cdk synth
```

**4. Security Scan Failures:**
```bash
# Check dependencies locally
safety check
npm audit

# Fix vulnerabilities
pip install --upgrade <package>
npm audit fix
```

### **Debug Workflows**

**Enable Debug Logging:**
1. Go to Settings → Secrets
2. Add secret: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run workflow

**View Logs:**
- GitHub Actions tab → Select workflow run
- Download logs for offline analysis
- Check job annotations for specific failures

---

## 📚 ADDITIONAL RESOURCES

### **Related Documentation**
- [Deployment Runbooks](./deployment-runbooks.md)
- [Architecture Documentation](./architecture.md)
- [Security Best Practices](./security-best-practices.md)
- [Testing Guide](../tests/README.md)

### **External Resources**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Terraform Documentation](https://www.terraform.io/docs)

---

## ✅ CI/CD CHECKLIST

### **Setup Checklist**
- [x] GitHub Actions workflows created
- [x] Environment configurations set
- [x] Secrets configured
- [x] Branch protection rules enabled
- [x] Status checks required
- [x] Auto-merge configured (optional)
- [x] Notification webhooks set up

### **Per-Deployment Checklist**
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Secrets rotated (if needed)
- [ ] Monitoring confirmed
- [ ] Rollback plan ready
- [ ] Stakeholders notified

---

**CI/CD Pipeline Status:** ✅ **ACTIVE & OPERATIONAL**

**Last Updated:** October 12, 2025  
**Maintained By:** DevOps Team

