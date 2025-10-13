#!/usr/bin/env pwsh
# Direct PowerShell script - run with: pwsh .git-push-helper.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Adding files to git..."
& git add .github/workflows/ci-backend.yml
& git add .github/workflows/ci-frontend.yml  
& git add .github/workflows/release.yml
& git add .github/.yamllint
& git add CI-CD-STATUS.md
& git add docs/LINTER-WARNINGS-EXPLAINED.md
& git add WORKFLOW-STATUS.md
& git add NO-CONNECTION-FAILURES.md
& git add DEPLOYMENT-GUIDE.md
& git add QUICK-START.md
& git add deploy-workflows.ps1
& git add deploy-workflows.sh
& git add deploy-workflows.bat
& git add deploy.cmd
& git add .git-push-helper.ps1

Write-Host "Committing..."
& git commit -m "feat: Add production-ready CI/CD workflows" -m "- Backend/Frontend CI/CD pipelines" -m "- Release workflows" -m "- Complete documentation"

Write-Host "Pushing to GitHub..."
& git push origin main

Write-Host "Done!" -ForegroundColor Green


