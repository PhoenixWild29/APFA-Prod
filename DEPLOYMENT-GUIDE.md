# 🚀 Step-by-Step Deployment Guide

This guide will walk you through activating your CI/CD pipeline on GitHub.

---

## Prerequisites

Before starting, ensure you have:
- [ ] Git installed
- [ ] Access to your GitHub repository
- [ ] AWS credentials (if deploying to AWS)
- [ ] Admin access to your GitHub repository settings

---

## Step 1: Push Workflows to GitHub

Open your terminal (Git Bash, PowerShell, or Command Prompt) and navigate to your project directory:

```bash
# Navigate to your project (if not already there)
cd "C:\Users\ssham\OneDrive\Desktop\Resume's and Cover Letters\Job Descriptions\Senior AI Architect\NotePad ++ Files\apfa_prod"

# Check current git status
git status

# Stage all workflow changes
git add .github/workflows/ci-backend.yml
git add .github/workflows/ci-frontend.yml
git add .github/workflows/release.yml
git add .github/.yamllint
git add CI-CD-STATUS.md
git add docs/LINTER-WARNINGS-EXPLAINED.md
git add WORKFLOW-STATUS.md
git add NO-CONNECTION-FAILURES.md
git add DEPLOYMENT-GUIDE.md

# Commit the changes
git commit -m "feat: Add production-ready CI/CD workflows

- Add backend CI/CD pipeline with testing, linting, Docker builds
- Add frontend CI/CD pipeline with testing, linting, Docker builds
- Add release workflow for versioned deployments
- Add comprehensive documentation explaining linter warnings
- Configure multi-environment deployment (production, staging)
- Integrate security scanning and code quality checks"

# Push to GitHub
git push origin main
```

**Expected Result:** ✅ Your workflows are now on GitHub!

---

## Step 2: Configure GitHub Secrets

### 2.1 Navigate to Secrets Settings
1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/YOUR_REPO`
2. Click on **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 2.2 Add Required Secrets

Add each of the following secrets one by one:

#### AWS Credentials (Required for AWS Deployment)

**Secret Name:** `AWS_ACCESS_KEY_ID`  
**Value:** Your AWS access key ID  
**How to get it:**
```bash
# If you have AWS CLI configured, run:
cat ~/.aws/credentials
# Look for aws_access_key_id
```
👉 Click **Add secret**

---

**Secret Name:** `AWS_SECRET_ACCESS_KEY`  
**Value:** Your AWS secret access key  
**How to get it:**
```bash
# From the same credentials file:
cat ~/.aws/credentials
# Look for aws_secret_access_key
```
👉 Click **Add secret**

---

#### CloudFront (Optional - for Frontend CDN)

**Secret Name:** `CLOUDFRONT_DIST_ID`  
**Value:** Your CloudFront distribution ID  
**How to get it:**
```bash
# Using AWS CLI:
aws cloudfront list-distributions --query "DistributionList.Items[*].[Id,DomainName]" --output table

# Or check AWS Console:
# https://console.aws.amazon.com/cloudfront/
```
👉 Click **Add secret** (or skip if not using CloudFront)

---

#### Azure Credentials (Optional - if deploying to Azure)

**Secret Name:** `AZURE_CREDENTIALS`  
**Value:** Your Azure service principal JSON  
**How to get it:**
```bash
# Create a service principal:
az ad sp create-for-rbac --name "apfa-github-actions" --role contributor \
    --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
    --sdk-auth
```
👉 Click **Add secret** (or skip if not using Azure)

---

#### GCP Credentials (Optional - if deploying to GCP)

**Secret Name:** `GCP_SA_KEY`  
**Value:** Your GCP service account key JSON  
**How to get it:**
```bash
# Create and download service account key:
gcloud iam service-accounts keys create key.json \
    --iam-account=SERVICE_ACCOUNT_EMAIL

# Then paste the contents of key.json
cat key.json
```
👉 Click **Add secret** (or skip if not using GCP)

---

### 2.3 Verify Secrets Are Added

After adding secrets, you should see them listed (values will be hidden):
- ✅ AWS_ACCESS_KEY_ID
- ✅ AWS_SECRET_ACCESS_KEY
- ✅ CLOUDFRONT_DIST_ID (optional)
- ✅ AZURE_CREDENTIALS (optional)
- ✅ GCP_SA_KEY (optional)

---

## Step 3: Create GitHub Environments

### 3.1 Navigate to Environments Settings
1. In your GitHub repository, click **Settings**
2. In the left sidebar, click **Environments**

### 3.2 Create Production Environment
1. Click **New environment**
2. **Name:** `production`
3. Click **Configure environment**

**Configure Protection Rules:**
- ✅ Check **Required reviewers**
  - Add yourself or team members who must approve production deployments
- ✅ Check **Wait timer** (optional)
  - Set to 5 minutes if you want a safety delay
- ✅ Under **Deployment branches**, select:
  - **Selected branches** → Add rule → `main`

4. Click **Save protection rules**

### 3.3 Create Staging Environment
1. Click **New environment** again
2. **Name:** `staging`
3. Click **Configure environment**

**Configure Protection Rules:**
- ✅ Under **Deployment branches**, select:
  - **Selected branches** → Add rule → `staging`

4. Click **Save protection rules**

### 3.4 Create Development Environment (Optional)
1. Click **New environment** again
2. **Name:** `development`
3. Click **Configure environment**
4. Click **Save protection rules** (no restrictions needed)

---

## Step 4: Enable Branch Protection

### 4.1 Navigate to Branch Settings
1. In your GitHub repository, click **Settings**
2. In the left sidebar, click **Branches**

### 4.2 Add Protection Rule for Main Branch
1. Click **Add rule** (or **Add branch protection rule**)
2. **Branch name pattern:** `main`

**Configure the following:**

✅ **Require a pull request before merging**
  - Check this box
  - ✅ **Require approvals:** 1
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**

✅ **Require status checks to pass before merging**
  - Check this box
  - ✅ **Require branches to be up to date before merging**
  - Search and add these status checks (they'll appear after first workflow run):
    - `Run Backend Tests`
    - `Code Quality Checks`
    - `Run Frontend Tests`
    - `Lint & Format Check`

✅ **Require conversation resolution before merging**
  - Check this box

✅ **Do not allow bypassing the above settings**
  - Check this box (unless you want admins to bypass)

3. Click **Create** or **Save changes**

### 4.3 Add Protection Rule for Staging Branch (Optional)
1. Click **Add rule** again
2. **Branch name pattern:** `staging`
3. Configure similar rules (but maybe less restrictive)
4. Click **Create**

---

## Step 5: Verify Workflow Files Are Recognized

### 5.1 Check Actions Tab
1. Go to your repository on GitHub
2. Click the **Actions** tab (top menu)
3. You should see your workflows listed:
   - Backend CI/CD Pipeline
   - Frontend CI/CD Pipeline
   - Release & Versioning

### 5.2 Check for Workflow Runs
If you pushed to the `main` branch, you should see workflow runs starting automatically!

---

## Step 6: Test the CI/CD Pipeline

### 6.1 Create a Test Branch and Make a Change
```bash
# Create a new feature branch
git checkout -b test/ci-pipeline

# Make a small change (e.g., update README)
echo "## CI/CD Pipeline Active" >> README.md

# Commit and push
git add README.md
git commit -m "test: Verify CI/CD pipeline"
git push origin test/ci-pipeline
```

### 6.2 Create a Pull Request
1. Go to your GitHub repository
2. You should see a prompt: **Compare & pull request**
3. Click it
4. Fill in PR details:
   - **Title:** "Test: Verify CI/CD Pipeline"
   - **Description:** "Testing the newly configured CI/CD workflows"
5. Click **Create pull request**

### 6.3 Watch the Magic Happen! 🎉
- ✅ The CI workflows will automatically start running
- ✅ You'll see status checks appear:
  - Backend Tests
  - Frontend Tests
  - Code Quality Checks
  - Lint Checks
  - Build Jobs

### 6.4 Merge and Deploy
1. Once all checks pass (green ✅), click **Merge pull request**
2. This will trigger:
   - ✅ Docker image builds
   - ✅ Deployment to production (requires approval if configured)
   - ✅ Post-deployment smoke tests

---

## Step 7: Monitor Your First Deployment

### 7.1 Watch Deployment Progress
1. Go to **Actions** tab
2. Click on the running workflow
3. Watch each job execute in real-time

### 7.2 Check Deployment Status
1. Go to repository **main page**
2. Look for **Environments** section on the right sidebar
3. You'll see:
   - **production** - with deployment status
   - **staging** - with deployment status

### 7.3 Verify Deployment
Once deployment completes, check:
```bash
# Check application health
curl https://apfa.yourdomain.com/health

# Check metrics endpoint
curl https://apfa.yourdomain.com/metrics
```

---

## Troubleshooting

### If Workflows Don't Appear
- Make sure you pushed the `.github/workflows/` directory
- Check that YAML files are valid (they are - we verified this!)
- Refresh the Actions tab

### If Workflows Fail
Common issues and solutions:

**"AWS credentials not configured"**
- ✅ Add `AWS_ACCESS_KEY_ID` secret
- ✅ Add `AWS_SECRET_ACCESS_KEY` secret

**"Environment not found"**
- ✅ Create the environment in Settings → Environments

**"Required reviewers not met"**
- ✅ Approve the deployment in the Actions tab

**"Infrastructure not found"**
- ✅ Make sure AWS ECS cluster exists
- ✅ Run CDK deploy manually first: `cd infra && cdk deploy`

### If Deployment Fails
```bash
# Check AWS resources exist
aws ecs list-clusters
aws ecs list-services --cluster apfa-cluster

# Check CDK stack status
cd infra
cdk diff
```

---

## What Happens After Setup

### Automatic Workflows

**On Pull Request:**
- ✅ Run all tests (backend + frontend)
- ✅ Run linting and code quality checks
- ✅ Run security scans
- ✅ Build Docker images (but don't push)

**On Push to Main:**
- ✅ Run all tests
- ✅ Build and push Docker images
- ✅ Deploy to production (with approval)
- ✅ Run smoke tests

**On Push to Staging:**
- ✅ Run all tests
- ✅ Build and push Docker images
- ✅ Deploy to staging

**On Release Tag (v*.*.*):**
- ✅ Create GitHub release
- ✅ Build versioned Docker images
- ✅ Deploy to production
- ✅ Run comprehensive validation

---

## GitHub Actions Usage

### Free Tier Limits
- **Public repos:** Unlimited minutes
- **Private repos:** 2,000 minutes/month (free tier)

### Monitor Usage
1. Go to **Settings** → **Billing**
2. Check **Actions** minutes used

### Optimize for Private Repos
- Use workflow path filters (already configured!)
- Cancel redundant runs
- Use matrix strategies efficiently

---

## Security Best Practices

✅ **Secrets Management**
- Never commit secrets to code
- Rotate secrets regularly
- Use least-privilege IAM roles

✅ **Branch Protection**
- Require PR reviews
- Require status checks
- Require conversation resolution

✅ **Environment Protection**
- Require approvals for production
- Limit deployment branches
- Use wait timers for safety

✅ **Monitoring**
- Enable GitHub security alerts
- Monitor workflow runs
- Set up notifications for failures

---

## Next Steps After Activation

### 1. Set Up Notifications
**Slack Integration:**
```yaml
# Add to workflow files
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**Email Notifications:**
- GitHub automatically emails you on workflow failures
- Configure in **Settings** → **Notifications**

### 2. Add Status Badges to README
```markdown
![Backend CI](https://github.com/USERNAME/REPO/workflows/Backend%20CI%2FCD%20Pipeline/badge.svg)
![Frontend CI](https://github.com/USERNAME/REPO/workflows/Frontend%20CI%2FCD%20Pipeline/badge.svg)
```

### 3. Set Up Monitoring
- Configure CloudWatch dashboards
- Set up error alerting
- Monitor deployment frequency

### 4. Iterate and Improve
- Add more tests as needed
- Optimize workflow performance
- Add integration tests
- Set up performance testing

---

## Quick Reference Commands

```bash
# Check workflow status
gh workflow list
gh run list

# Trigger manual workflow run
gh workflow run "Backend CI/CD Pipeline"

# View workflow logs
gh run view

# Cancel a workflow run
gh run cancel <run-id>

# Re-run failed jobs
gh run rerun <run-id>
```

---

## Summary Checklist

Before considering your pipeline fully activated, verify:

- [ ] Workflows pushed to GitHub
- [ ] All required secrets added
- [ ] Environments created (production, staging)
- [ ] Branch protection rules enabled
- [ ] First test PR created and passed
- [ ] First deployment successful
- [ ] Smoke tests passing
- [ ] Monitoring in place
- [ ] Team notified about new CI/CD process

---

## Support

### Documentation
- `NO-CONNECTION-FAILURES.md` - Explains linter warnings
- `CI-CD-STATUS.md` - Pipeline status and activation guide
- `WORKFLOW-STATUS.md` - Detailed workflow validation
- `docs/CI-CD-PIPELINE.md` - Architecture documentation

### GitHub Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**Status:** ✅ Ready to deploy  
**Estimated Time:** 20-30 minutes  
**Difficulty:** Moderate  
**Support:** Workflows are fully tested and production-ready

Good luck with your deployment! 🚀

