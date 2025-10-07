#!/bin/bash

# APFA Deployment Script

set -e

echo "🚀 Starting APFA deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure your variables."
    exit 1
fi

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check health
echo "🔍 Checking application health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ APFA is healthy and running!"
    echo "🌐 Application: http://localhost:8000"
    echo "📊 Prometheus: http://localhost:9090"
    echo "📈 Grafana: http://localhost:3000"
else
    echo "❌ APFA health check failed. Check logs with: docker-compose logs apfa"
    exit 1
fi

echo "🎉 Deployment completed successfully!"