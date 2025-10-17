# Scheduled GitHub Actions Workflows

## Overview

This project has **three scheduled workflows** that run automatically every morning to ensure code quality, security, and system health. These workflows run on cron schedules in addition to being triggered by code pushes and pull requests.

---

## 📅 Scheduled Workflows

### 1. Integration & E2E Tests (`ci-integration.yml`)

**Schedule:** Daily at **2:00 AM UTC** (10:00 PM EST / 7:00 PM PST)

**Purpose:** Runs comprehensive integration tests, performance tests, and security scans.

**What it does:**
- ✅ Starts Redis and PostgreSQL test databases
- ✅ Runs end-to-end integration tests
- ✅ Tests API endpoints (health, metrics)
- ✅ Runs performance/load tests with Locust (100 users, 60 seconds)
- ✅ Scans for security vulnerabilities with Trivy
- ✅ Runs OWASP Dependency Check

**Expected Duration:** 10-15 minutes

**Files Required:**
- `tests/test_comprehensive.py` ✅
- `tests/test_phase_validation.py` ✅
- `tests/locustfile.py` ✅ (newly created)
- `docker-compose.yml` ✅

**Common Failure Points:**
- Docker Compose services not starting properly
- Locust performance tests timing out
- Database connection issues

---

### 2. Security Scanning (`security-scan.yml`)

**Schedule:** Daily at **3:00 AM UTC** (11:00 PM EST / 8:00 PM PST)

**Purpose:** Comprehensive security scanning of code, dependencies, and containers.

**What it does:**
- 🔒 Scans Python dependencies for vulnerabilities (Safety)
- 🔒 Scans npm dependencies for vulnerabilities (npm audit)
- 🔒 Runs CodeQL security analysis (Python & JavaScript)
- 🔒 Scans for exposed secrets (TruffleHog)
- 🔒 Scans Docker images for vulnerabilities (Trivy)
- 🔒 Runs OWASP Dependency Check

**Expected Duration:** 15-20 minutes

**Common Failure Points:**
- New vulnerabilities discovered in dependencies
- False positives in secret scanning
- Docker build failures

**Note:** Most security scan steps have `continue-on-error: true` to prevent minor issues from blocking the workflow.

---

### 3. Monitoring & Observability (`ci-monitoring.yml`)

**Schedule:** Daily at **4:00 AM UTC** (12:00 AM EST / 9:00 PM PST)

**Purpose:** Validates monitoring infrastructure and configuration.

**What it does:**
- 📊 Validates Prometheus configuration
- 📊 Validates Prometheus alert rules
- 📊 Validates Grafana dashboard JSON files
- 📊 Tests metrics endpoints
- 📊 Verifies monitoring system health

**Expected Duration:** 5-10 minutes

**Files Required:**
- `monitoring/prometheus.yml` ✅
- `monitoring/alerts.yml` ✅ (newly created)
- `monitoring/grafana-dashboards/*.json` ✅ (newly created)
- `docker-compose.yml` ✅

**Common Failure Points:**
- Invalid Prometheus configuration syntax
- Invalid alert rule expressions
- Malformed Grafana dashboard JSON
- Metrics endpoints not responding

---

## 🔧 What We Fixed

### Missing Files Created:

1. **`tests/locustfile.py`** - Performance testing configuration
   - Simulates various user loads (10-100+ concurrent users)
   - Tests health, metrics, and API endpoints
   - Includes multiple test scenarios (QuickLoadTest, StressTest, SpikeTest)

2. **`monitoring/alerts.yml`** - Prometheus alert rules
   - Application health alerts (down, high error rate, slow response)
   - Resource utilization alerts (CPU, memory)
   - Redis alerts (down, high memory, connection limits)
   - Database alerts (connection pool, slow queries)
   - Security alerts (failed logins, unauthorized access)
   - Celery/background job alerts
   - Document processing alerts
   - FAISS index alerts
   - Disk space and storage alerts

3. **`monitoring/grafana-dashboards/`** - Grafana dashboard configurations
   - `apfa-overview.json` - Application overview dashboard
   - `apfa-performance.json` - Performance metrics dashboard
   - `apfa-security.json` - Security monitoring dashboard

### Docker Compose Updates:

- ✅ Added Redis service (required by integration tests)
- ✅ Added PostgreSQL service (required by integration tests)
- ✅ Updated Prometheus to load alert rules
- ✅ Updated Grafana to load dashboard configurations
- ✅ Added health checks for all services
- ✅ Added data persistence volumes

---

## 🚀 How to Test Locally

### Test the Integration Workflow:

```bash
# Start services
docker-compose up -d

# Wait for services to be healthy
sleep 30

# Run integration tests
pytest tests/test_comprehensive.py -v
pytest tests/test_phase_validation.py -v

# Run performance tests
pip install locust
locust -f tests/locustfile.py --headless -u 100 -r 10 -t 60s --host http://localhost:8000

# Check API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Test the Monitoring Workflow:

```bash
# Validate Prometheus config
docker run --rm -v $(pwd)/monitoring:/config prom/prometheus:latest promtool check config /config/prometheus.yml

# Validate alert rules
docker run --rm -v $(pwd)/monitoring:/config prom/prometheus:latest promtool check rules /config/alerts.yml

# Validate Grafana dashboards
for dashboard in monitoring/grafana-dashboards/*.json; do
  echo "Validating $dashboard"
  jq empty "$dashboard" && echo "✅ Valid" || echo "❌ Invalid"
done
```

### Test Security Scanning:

```bash
# Scan Python dependencies
pip install safety
safety check

# Scan npm dependencies
npm audit

# Build and scan Docker image
docker build -t apfa-backend:test .
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasecurity/trivy:latest image apfa-backend:test
```

---

## 📊 Monitoring Workflow Results

### Where to Find Results:

1. **GitHub Actions Tab**
   - Go to your repository
   - Click "Actions" tab
   - Look for workflow runs with the clock icon (scheduled runs)

2. **Workflow Status Badges** (optional)
   Add to your README.md:
   ```markdown
   ![Integration Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Integration%20&%20E2E%20Tests/badge.svg)
   ![Security Scan](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Security%20Scanning/badge.svg)
   ![Monitoring](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Monitoring%20&%20Observability/badge.svg)
   ```

3. **Email Notifications**
   - GitHub sends email notifications for failed workflows
   - Configure in: Settings → Notifications → Actions

---

## 🔔 Handling Workflow Failures

### If Integration Tests Fail:

1. **Check the logs:**
   - Go to Actions → Failed workflow run
   - Click on the failed job
   - Review detailed logs

2. **Common fixes:**
   - Update test data or expectations
   - Fix broken API endpoints
   - Update database schemas
   - Adjust performance test thresholds

### If Security Scans Fail:

1. **Review vulnerabilities:**
   - Check which dependencies are vulnerable
   - Review CodeQL security alerts

2. **Common fixes:**
   - Update vulnerable dependencies: `pip install --upgrade <package>`
   - Update npm packages: `npm audit fix`
   - Add security exceptions for false positives
   - Rotate exposed secrets immediately

### If Monitoring Tests Fail:

1. **Check configuration:**
   - Validate YAML syntax
   - Check for typos in metric names
   - Verify alert rule expressions

2. **Common fixes:**
   - Fix Prometheus config syntax
   - Update metric names in alerts
   - Fix malformed JSON in dashboards

---

## ⚙️ Customizing Schedules

To change when workflows run, edit the `cron` expression in each workflow file:

```yaml
schedule:
  - cron: '0 2 * * *'  # Format: minute hour day month day-of-week
```

**Cron Examples:**
- `'0 2 * * *'` - Every day at 2:00 AM UTC
- `'0 */6 * * *'` - Every 6 hours
- `'0 2 * * 1'` - Every Monday at 2:00 AM
- `'0 2 * * 1-5'` - Weekdays only at 2:00 AM

**Recommendation:** Stagger workflows to avoid resource contention (currently 2 AM, 3 AM, 4 AM).

---

## 🛑 Disabling Scheduled Workflows

If you want to temporarily disable scheduled runs (but keep manual/PR triggers):

### Option 1: Comment out the schedule (Recommended)
```yaml
# Temporarily disabled - uncomment to re-enable
# schedule:
#   - cron: '0 2 * * *'
```

### Option 2: Disable the entire workflow
- Go to: Actions → Select workflow → Click "..." → Disable workflow

### Option 3: Remove the schedule section
Delete the entire `schedule:` section from the workflow file.

---

## 📈 Best Practices

### 1. Monitor Workflow Execution Time
- Keep workflows under 30 minutes
- Use parallelization where possible
- Cache dependencies (pip, npm)

### 2. Set Up Notifications
- Enable email notifications for failures
- Consider Slack integration for critical workflows
- Set up PagerDuty for production alerts

### 3. Review Results Regularly
- Check for new security vulnerabilities weekly
- Review performance trends monthly
- Update dependencies quarterly

### 4. Keep Tests Current
- Update test data as application evolves
- Adjust performance baselines based on real metrics
- Add new tests for new features

### 5. Documentation
- Document why tests fail and how to fix them
- Keep runbooks up to date
- Share knowledge with team members

---

## 🎯 Success Criteria

Your scheduled workflows are working correctly when:

- ✅ All three workflows complete successfully each morning
- ✅ No email notifications about failures
- ✅ All tests pass consistently
- ✅ Security scans show no new critical vulnerabilities
- ✅ Monitoring configurations are valid
- ✅ Workflow execution time is stable
- ✅ No manual intervention required

---

## 📞 Troubleshooting

### Workflows Not Running?

1. **Check if workflows are enabled:**
   - Actions → Select workflow → Ensure it's not disabled

2. **Check repository activity:**
   - Scheduled workflows only run in active repositories
   - Make at least one commit per 60 days to keep them active

3. **Check GitHub status:**
   - Visit https://www.githubstatus.com
   - Actions may be delayed during incidents

### Tests Consistently Failing?

1. **Review what changed:**
   - Check recent commits
   - Review dependency updates
   - Check for infrastructure changes

2. **Run tests locally:**
   - Use the test commands above
   - Debug with verbose output
   - Check Docker logs

3. **Update test expectations:**
   - If application behavior changed intentionally
   - Update test assertions accordingly

---

## 📚 Related Documentation

- [CI/CD Pipeline Documentation](../docs/CI-CD-PIPELINE.md)
- [Deployment Guide](../DEPLOYMENT-GUIDE.md)
- [Security Best Practices](../docs/security-best-practices.md)
- [Monitoring & Observability](../docs/observability.md)

---

## ✅ Summary

With all files created and configurations updated, your scheduled workflows should now:

1. ✅ Run successfully every morning
2. ✅ Provide comprehensive test coverage
3. ✅ Identify security vulnerabilities early
4. ✅ Validate monitoring infrastructure
5. ✅ Give you confidence in your application's health

**Next Steps:**
1. Commit and push these changes to GitHub
2. Monitor the first few scheduled runs
3. Adjust thresholds and expectations as needed
4. Set up notifications for your team

---

**Last Updated:** October 2024  
**Maintained By:** DevOps Team  
**Questions?** Check GitHub Issues or contact the team

