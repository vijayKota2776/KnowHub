"""
conftest.py — Shared pytest fixtures for KnowHub test suite.
"""

import pytest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport

# Make the project root importable
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app


@pytest.fixture
async def client():
    """Async HTTP client wired to the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client):
    """A client registered and authenticated with a unique test user per test run."""
    uid = uuid.uuid4().hex[:10]
    payload = {
        "username": f"pytest_{uid}",
        "email": f"pytest_{uid}@testmail.com",
        "password": "TestP@ss123",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 200, f"Registration failed: {resp.text}"
    data = resp.json()
    token = data["token"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, token
