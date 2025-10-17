@echo off
REM Simple CMD script to commit and push changes
cd /d "%~dp0"

echo.
echo ================================================
echo Git Commit and Push - Workflow Fixes
echo ================================================
echo.

echo [1/4] Adding files to git...
git add tests/locustfile.py
git add monitoring/alerts.yml
git add monitoring/grafana-dashboards/
git add monitoring/prometheus.yml
git add docker-compose.yml
git add docs/SCHEDULED-WORKFLOWS.md
git add WORKFLOW-FAILURES-FIXED.md
git add MORNING-FAILURES-SUMMARY.md
git add commit-and-push.bat
git add COMMIT-NOW.cmd

echo.
echo [2/4] Showing status...
git status --short

echo.
echo [3/4] Committing...
git commit -m "Fix: Resolve daily scheduled workflow failures" -m "- Add tests/locustfile.py for performance testing" -m "- Add monitoring/alerts.yml with alert rules" -m "- Add Grafana dashboards" -m "- Update docker-compose.yml and prometheus.yml" -m "- Add comprehensive documentation"

echo.
echo [4/4] Pushing to GitHub...
git push origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ================================================
    echo SUCCESS! Changes pushed to GitHub
    echo ================================================
    echo.
    echo Your workflows should now pass!
    echo Check: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
    echo.
) else (
    echo ================================================
    echo ERROR: Push failed
    echo ================================================
    echo.
    echo Check your internet connection and git authentication
    echo.
)

echo Press any key to close...
pause > nul

