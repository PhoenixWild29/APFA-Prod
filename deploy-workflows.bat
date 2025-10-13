@echo off
echo =================================
echo   Deploying CI/CD Workflows
echo =================================
echo.

echo Staging workflow files...
git add .github/workflows/ci-backend.yml
git add .github/workflows/ci-frontend.yml
git add .github/workflows/release.yml
git add .github/.yamllint
git add CI-CD-STATUS.md
git add docs/LINTER-WARNINGS-EXPLAINED.md
git add WORKFLOW-STATUS.md
git add NO-CONNECTION-FAILURES.md
git add DEPLOYMENT-GUIDE.md
git add QUICK-START.md
git add deploy-workflows.ps1
git add deploy-workflows.sh
git add deploy-workflows.bat

echo Files staged successfully!
echo.

echo Committing changes...
git commit -m "feat: Add production-ready CI/CD workflows" -m "- Add backend CI/CD pipeline with testing, linting, Docker builds" -m "- Add frontend CI/CD pipeline with testing, linting, Docker builds" -m "- Add release workflow for versioned deployments" -m "- Add comprehensive documentation explaining linter warnings" -m "- Configure multi-environment deployment (production, staging)" -m "- Integrate security scanning and code quality checks"

if %errorlevel% neq 0 (
    echo Commit failed!
    pause
    exit /b 1
)

echo Changes committed successfully!
echo.

echo Pushing to GitHub...
git push origin main

if %errorlevel% neq 0 (
    echo Push failed! Check your credentials.
    pause
    exit /b 1
)

echo.
echo =================================
echo   SUCCESS!
echo =================================
echo.
echo Your workflows are now on GitHub!
echo.
echo Next steps:
echo 1. Configure GitHub Secrets
echo 2. Create GitHub Environments
echo 3. Enable Branch Protection
echo.
echo See DEPLOYMENT-GUIDE.md for details
echo.
pause

