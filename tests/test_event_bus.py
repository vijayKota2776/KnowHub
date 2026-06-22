"""
test_event_bus.py — Unit tests for the async EventBus.
"""

import pytest
import asyncio
from services.event_bus import EventBus


@pytest.mark.asyncio
async def test_publish_subscribe_single_event():
    """A subscriber receives an event published after it subscribes."""
    received = []

    async def consume():
        async for event in EventBus.subscribe("test_event"):
            received.append(event)
            break  # Only take first event

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)  # Yield so the subscriber can register
    await EventBus.publish("test_event", {"key": "value"})
    await asyncio.wait_for(task, timeout=2)

    assert len(received) == 1
    assert received[0]["key"] == "value"


@pytest.mark.asyncio
async def test_multiple_subscribers_same_event():
    """Multiple subscribers all receive the same published event."""
    results = [[], []]
    ready = asyncio.Event()
    ready_count = 0

    async def consumer(idx):
        nonlocal ready_count
        ready_count += 1
        if ready_count == 2:
            ready.set()
        async for event in EventBus.subscribe("multi_event"):
            results[idx].append(event)
            break

    tasks = [asyncio.create_task(consumer(i)) for i in range(2)]
    await ready.wait()  # Both consumers registered
    await EventBus.publish("multi_event", {"msg": "hello"})
    await asyncio.gather(*[asyncio.wait_for(t, timeout=3) for t in tasks])

    assert len(results[0]) == 1
    assert len(results[1]) == 1


@pytest.mark.asyncio
async def test_different_event_types_do_not_cross():
    """A subscriber for event A does NOT receive events published on event B."""
    received_b = []

    async def consume_b():
        async for event in EventBus.subscribe("type_b"):
            received_b.append(event)
            break

    task = asyncio.create_task(consume_b())
    await asyncio.sleep(0)
    # Publish to a DIFFERENT event type
    await EventBus.publish("type_a", {"should_not": "arrive"})
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert received_b == []
