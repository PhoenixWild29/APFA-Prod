import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app, settings
import os

client = TestClient(app)

# Mock API key for testing
os.environ['API_KEY'] = 'test_key'

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_generate_advice_unauthorized():
    response = client.post("/generate-advice", json={"query": "What is a good loan?"})
    assert response.status_code == 401

def test_generate_advice_invalid_input():
    response = client.post("/generate-advice", json={"query": ""}, headers={"X-API-Key": "test_key"})
    assert response.status_code == 422  # Validation error

def test_generate_advice_valid():
    response = client.post("/generate-advice", json={"query": "What is a good loan?"}, headers={"X-API-Key": "test_key"})
    assert response.status_code == 200
    assert "advice" in response.json()

def test_rate_limiting():
    # Test rate limiting by making multiple requests
    for i in range(12):  # Exceed limit
        response = client.post("/generate-advice", json={"query": "Test"}, headers={"X-API-Key": "test_key"})
    assert response.status_code == 429  # Too many requests

def test_input_validation():
    # Test regex validation
    response = client.post("/generate-advice", json={"query": "Valid query with numbers 123?"}, headers={"X-API-Key": "test_key"})
    assert response.status_code == 200

    response = client.post("/generate-advice", json={"query": "Invalid @#$%"}, headers={"X-API-Key": "test_key"})
    assert response.status_code == 422
