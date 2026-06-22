"""
test_notification.py — Unit tests for NotificationService.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from services.notification_service import NotificationService


def make_mock_ws():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_register_and_unregister_connection():
    """Connections are properly tracked and removed."""
    svc = NotificationService.__new__(NotificationService)
    svc._connections = {}

    ws = make_mock_ws()
    await svc.register_connection("user1", ws)

    assert "user1" in svc._connections
    assert ws in svc._connections["user1"]

    await svc.unregister_connection("user1", ws)
    assert "user1" not in svc._connections


@pytest.mark.asyncio
async def test_send_to_user_delivers_payload():
    """_send_to_user calls send_json on all registered connections."""
    svc = NotificationService.__new__(NotificationService)
    svc._connections = {}

    ws1 = make_mock_ws()
    ws2 = make_mock_ws()
    await svc.register_connection("user1", ws1)
    await svc.register_connection("user1", ws2)

    payload = {"type": "test", "payload": {"data": 42}}
    await svc._send_to_user("user1", payload)

    ws1.send_json.assert_awaited_once_with(payload)
    ws2.send_json.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_send_to_nonexistent_user_is_noop():
    """Sending to a user with no connections raises no error."""
    svc = NotificationService.__new__(NotificationService)
    svc._connections = {}

    # Should not raise
    await svc._send_to_user("ghost_user", {"type": "noop"})


@pytest.mark.asyncio
async def test_failed_send_unregisters_connection():
    """If send_json raises, the broken connection is removed."""
    svc = NotificationService.__new__(NotificationService)
    svc._connections = {}

    ws = make_mock_ws()
    ws.send_json = AsyncMock(side_effect=Exception("broken pipe"))
    await svc.register_connection("user1", ws)

    await svc._send_to_user("user1", {"type": "test"})

    # Connection should have been cleaned up
    assert "user1" not in svc._connections
