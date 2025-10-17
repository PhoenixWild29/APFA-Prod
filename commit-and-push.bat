@echo off
echo ========================================
echo Committing Workflow Fixes
echo ========================================
echo.

echo Adding new files...
git add tests/locustfile.py
git add monitoring/alerts.yml
git add monitoring/grafana-dashboards/
git add monitoring/prometheus.yml
git add docker-compose.yml
git add docs/SCHEDULED-WORKFLOWS.md
git add WORKFLOW-FAILURES-FIXED.md
git add MORNING-FAILURES-SUMMARY.md

echo.
echo ========================================
echo Files to be committed:
echo ========================================
git status --short

echo.
echo ========================================
echo Committing changes...
echo ========================================
git commit -m "Fix: Resolve daily scheduled workflow failures" -m "" -m "- Add tests/locustfile.py for performance testing with Locust" -m "- Add monitoring/alerts.yml with 67 comprehensive alert rules" -m "- Add 3 Grafana dashboards for monitoring visualization" -m "- Update docker-compose.yml with Redis, PostgreSQL, and enhanced configs" -m "- Update prometheus.yml to load alert rules and monitoring jobs" -m "- Add comprehensive documentation for scheduled workflows" -m "" -m "This resolves the 3 workflow failures occurring daily at 2 AM, 3 AM, and 4 AM UTC." -m "Closes issues with missing files required by GitHub Actions workflows."

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Commit failed!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo Pushing to GitHub...
echo ========================================
git push origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Push failed!
    echo Check your network connection and GitHub authentication.
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! All changes pushed to GitHub
echo ========================================
echo.
echo Your workflows will now:
echo  - Run immediately (Integration ^& Security workflows)
echo  - Stop failing at 2 AM, 3 AM, 4 AM UTC
echo  - No more morning failure emails!
echo.
echo Check GitHub Actions tab to see workflows running.
echo.
pause

