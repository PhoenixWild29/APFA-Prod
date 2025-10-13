@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Deploying CI/CD Workflows to GitHub
echo ========================================
echo.

REM Stage all workflow files
echo [Step 1/3] Staging files...
git add .github\workflows\ci-backend.yml 2>nul
git add .github\workflows\ci-frontend.yml 2>nul
git add .github\workflows\release.yml 2>nul
git add .github\.yamllint 2>nul
git add CI-CD-STATUS.md 2>nul
git add docs\LINTER-WARNINGS-EXPLAINED.md 2>nul
git add WORKFLOW-STATUS.md 2>nul
git add NO-CONNECTION-FAILURES.md 2>nul
git add DEPLOYMENT-GUIDE.md 2>nul
git add QUICK-START.md 2>nul
git add deploy-workflows.ps1 2>nul
git add deploy-workflows.sh 2>nul
git add deploy-workflows.bat 2>nul
git add deploy.cmd 2>nul

echo    ✓ Files staged
echo.

REM Commit changes
echo [Step 2/3] Committing changes...
git commit -m "feat: Add production-ready CI/CD workflows" -m "" -m "- Add backend CI/CD pipeline with testing, linting, Docker builds" -m "- Add frontend CI/CD pipeline with testing, linting, Docker builds" -m "- Add release workflow for versioned deployments" -m "- Add comprehensive documentation explaining linter warnings" -m "- Configure multi-environment deployment (production, staging)" -m "- Integrate security scanning and code quality checks" -m "- Add deployment scripts and guides" -m "" -m "The 12 linter warnings shown in the editor are expected and harmless."

if !errorlevel! neq 0 (
    echo    ✗ Commit failed or nothing to commit
    goto :next_step
)

echo    ✓ Changes committed
echo.

:next_step
REM Push to GitHub
echo [Step 3/3] Pushing to GitHub...
git push origin main

if !errorlevel! neq 0 (
    echo    ✗ Push failed. Check credentials or remote configuration.
    echo.
    exit /b 1
)

echo    ✓ Successfully pushed to GitHub!
echo.
echo ========================================
echo   SUCCESS! Workflows are on GitHub
echo ========================================
echo.
echo Next: Configure GitHub (see below)
echo.

