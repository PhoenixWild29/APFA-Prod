#!/bin/bash
# Build Docker image
docker build -t silk-river-agent ../app
# Push to ECR (assume AWS CLI configured)
REPO_URI=$(aws ecr describe-repositories --repository-names silk-river --query 'repositories[0].repositoryUri' --output text)
docker tag silk-river-agent:latest $REPO_URI:latest
docker push $REPO_URI:latest
# Deploy CDK stack
cdk deploy SilkRiverStack --require-approval never
# Optional: Test endpoint
# curl -X POST "http://your-alb-dns/generate-advice" -H "Content-Type: application/json" -d '{"query": "Simulate loan for high-risk applicant"}'
