"""Test configuration and utilities."""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient

from app.main import create_app
from app.config import settings


@pytest.fixture
def app():
    """Create test application."""
    return create_app()


@pytest.fixture
def client(app) -> Generator:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock data for testing
MOCK_SWAGGER_URL = "https://petstore.swagger.io/v2/swagger.json"
MOCK_MARKDOWN_URL = "https://raw.githubusercontent.com/example/repo/main/README.md"

MOCK_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0",
        "description": "A test API for documentation ingestion"
    },
    "paths": {
        "/users": {
            "get": {
                "summary": "Get all users",
                "description": "Retrieve a list of all users",
                "responses": {
                    "200": {
                        "description": "Successful response"
                    }
                }
            }
        }
    }
}

MOCK_MARKDOWN_CONTENT = """# Test API Documentation

This is a test API documentation file.

## Authentication

Use API keys for authentication.

## Endpoints

### GET /users

Returns a list of users.
"""