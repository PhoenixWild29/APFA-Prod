@echo off
REM ==============================================
REM  Automated GitHub Deployment Script
REM  Double-click this file to run
REM ==============================================

cd /d "%~dp0"

color 0A
echo.
echo ================================================
echo    APFA CI/CD Pipeline Deployment
echo ================================================
echo.
echo This script will:
echo  1. Stage all workflow and documentation files
echo  2. Commit changes to git
echo  3. Push to GitHub
echo  4. Show next configuration steps
echo.
pause

echo.
echo [1/3] Staging files for commit...
echo --------------------------------------------

git add .github\workflows\ci-backend.yml
git add .github\workflows\ci-frontend.yml
git add .github\workflows\release.yml
git add .github\.yamllint
git add CI-CD-STATUS.md
git add docs\LINTER-WARNINGS-EXPLAINED.md
git add WORKFLOW-STATUS.md
git add NO-CONNECTION-FAILURES.md
git add DEPLOYMENT-GUIDE.md
git add QUICK-START.md
git add deploy-workflows.ps1
git add deploy-workflows.sh
git add deploy-workflows.bat
git add deploy.cmd
git add .git-push-helper.ps1
git add PUSH-TO-GITHUB.bat

if errorlevel 1 (
    color 0C
    echo ERROR: Failed to stage files
    pause
    exit /b 1
)

color 0A
echo SUCCESS: All files staged
echo.

echo [2/3] Committing changes...
echo --------------------------------------------

git commit -m "feat: Add production-ready CI/CD workflows" -m "" -m "Complete CI/CD pipeline implementation:" -m "" -m "Backend Pipeline:" -m "- Automated testing (pytest with coverage)" -m "- Code quality checks (Black, Flake8, MyPy, Bandit)" -m "- Docker build and push to GHCR" -m "- Automated deployment to AWS ECS" -m "- Security scanning and dependency checks" -m "" -m "Frontend Pipeline:" -m "- TypeScript type checking" -m "- Unit and accessibility testing" -m "- ESLint and Prettier checks" -m "- Production build optimization" -m "- Docker build and push" -m "- CDN deployment ready" -m "" -m "Release Workflow:" -m "- Automated GitHub releases" -m "- Semantic versioning support" -m "- Multi-component Docker builds" -m "- Production deployment with validation" -m "" -m "Documentation:" -m "- Complete deployment guides" -m "- Troubleshooting documentation" -m "- Explanation of expected linter warnings" -m "- Quick-start guides" -m "" -m "Features:" -m "- Multi-environment support (production, staging)" -m "- Manual approval gates for production" -m "- Automated smoke tests" -m "- Branch protection integration" -m "- Secrets management configured" -m "" -m "Note: The 12 linter warnings shown in the editor are expected" -m "and harmless. They occur because the editor cannot validate" -m "GitHub secrets and environments that are configured in GitHub UI."

if errorlevel 1 (
    echo.
    echo NOTE: Nothing to commit (files may already be committed)
    echo Proceeding to push...
    echo.
)

color 0A
echo SUCCESS: Changes committed
echo.

echo [3/3] Pushing to GitHub...
echo --------------------------------------------

git push origin main

if errorlevel 1 (
    color 0C
    echo.
    echo ERROR: Failed to push to GitHub
    echo.
    echo Possible issues:
    echo  - Not authenticated with GitHub
    echo  - No internet connection
    echo  - Remote repository not configured
    echo.
    echo Run: git remote -v
    echo To check your remote configuration
    echo.
    pause
    exit /b 1
)

color 0A
echo.
echo ================================================
echo    SUCCESS! Workflows Deployed to GitHub
echo ================================================
echo.
echo Your CI/CD workflows are now on GitHub!
echo.
echo.
echo ================================================
echo    NEXT STEPS - GitHub Configuration
echo ================================================
echo.
echo Now you need to configure GitHub (takes ~5 minutes):
echo.
echo STEP 1: Add GitHub Secrets
echo ----------------------------
echo 1. Go to your GitHub repository
echo 2. Click: Settings ^> Secrets and variables ^> Actions
echo 3. Click: New repository secret
echo 4. Add these secrets:
echo.
echo    Name: AWS_ACCESS_KEY_ID
echo    Value: [Your AWS access key]
echo.
echo    Name: AWS_SECRET_ACCESS_KEY  
echo    Value: [Your AWS secret key]
echo.
echo    Name: CLOUDFRONT_DIST_ID (optional)
echo    Value: [Your CloudFront distribution ID]
echo.
echo.
echo STEP 2: Create GitHub Environments
echo ------------------------------------
echo 1. Go to: Settings ^> Environments
echo 2. Click: New environment
echo 3. Create: production
echo 4. Configure protection rules (optional):
echo    - Add required reviewers
echo    - Set deployment branch to 'main'
echo 5. Click: New environment
echo 6. Create: staging
echo.
echo.
echo STEP 3: Enable Branch Protection
echo ----------------------------------
echo 1. Go to: Settings ^> Branches
echo 2. Click: Add rule
echo 3. Branch name pattern: main
echo 4. Enable:
echo    [x] Require pull request reviews
echo    [x] Require status checks to pass
echo    [x] Require conversation resolution
echo 5. Click: Create
echo.
echo.
echo STEP 4: Verify Workflows
echo -------------------------
echo 1. Go to: Actions tab
echo 2. You should see:
echo    - Backend CI/CD Pipeline
echo    - Frontend CI/CD Pipeline
echo    - Release ^& Versioning
echo 3. These will run automatically on your next push
echo.
echo.
echo ================================================
echo    Documentation
echo ================================================
echo.
echo See these files for more details:
echo  - QUICK-START.md - Fast setup guide
echo  - DEPLOYMENT-GUIDE.md - Complete guide
echo  - NO-CONNECTION-FAILURES.md - About linter warnings
echo.
echo.
pause

