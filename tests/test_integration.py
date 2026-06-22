"""
test_integration.py — End-to-end integration tests for the KnowHub API.
"""

import pytest
import pytest_asyncio


# ─── Health Endpoints ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "KnowHub API"


@pytest.mark.asyncio
async def test_health_notifications(client):
    resp = await client.get("/health/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "active_connections" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert b"http_requests_total" in resp.content or b"python_gc" in resp.content


# ─── Auth Flow ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_and_login(client):
    import uuid
    uid = uuid.uuid4().hex[:8]
    register_resp = await client.post("/api/v1/auth/register", json={
        "username": f"user_{uid}",
        "email": f"{uid}@test.com",
        "password": "SecureP@ss1",
    })
    assert register_resp.status_code == 200
    data = register_resp.json()
    assert "token" in data
    assert data["token"]["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


# ─── Authenticated Routes ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_own_profile(auth_client):
    ac, _ = auth_client
    resp = await ac.get("/api/v1/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data


@pytest.mark.asyncio
async def test_post_question_and_retrieve(auth_client):
    ac, _ = auth_client
    resp = await ac.post("/api/v1/questions", json={
        "title": "What is system design?",
        "content": "Explain system design in simple terms.",
        "topic_ids": [],
    })
    assert resp.status_code == 200
    q = resp.json()
    assert "question_id" in q

    # Retrieve the question
    get_resp = await ac.get(f"/api/v1/questions/{q['question_id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["question"]["question_id"] == q["question_id"]


@pytest.mark.asyncio
async def test_post_answer(auth_client):
    ac, _ = auth_client
    # First post a question
    q_resp = await ac.post("/api/v1/questions", json={
        "title": "What is CAP theorem?",
        "content": "Please explain CAP theorem.",
        "topic_ids": [],
    })
    q_id = q_resp.json()["question_id"]

    # Post answer
    a_resp = await ac.post(f"/api/v1/questions/{q_id}/answers", json={
        "content": "CAP theorem states you can only have 2 of 3: Consistency, Availability, Partition Tolerance.",
    })
    assert a_resp.status_code == 200
    assert "answer_id" in a_resp.json()


# ─── Rate Limiting ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_public(client):
    resp = await client.get("/api/v1/search?q=system+design")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data


# ─── Unauthorized Access ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(client):
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert resp.status_code == 401
