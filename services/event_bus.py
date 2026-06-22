import asyncio
from typing import Dict, Any, AsyncIterator, List

class EventBus:
    """In-memory async event bus with fan-out: every subscriber gets every event.

    Usage:
        await EventBus.publish('question_posted', {'question_id': 'q_123'})
        async for event in EventBus.subscribe('question_posted'):
            ...
    """
    # event_type -> list of per-subscriber queues
    _subscribers: Dict[str, List[asyncio.Queue]] = {}

    @classmethod
    async def publish(cls, event_type: str, payload: Dict[str, Any]):
        """Fan-out payload to all active subscribers for this event type."""
        queues = cls._subscribers.get(event_type, [])
        for q in queues:
            await q.put(payload)

    @classmethod
    async def subscribe(cls, event_type: str) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe to an event type. Each subscriber gets its own queue (fan-out).

        The iterator runs forever; callers should break when needed.
        """
        queue: asyncio.Queue = asyncio.Queue()
        cls._subscribers.setdefault(event_type, []).append(queue)
        try:
            while True:
                payload = await queue.get()
                yield payload
        finally:
            # Clean up on generator close / break
            try:
                cls._subscribers[event_type].remove(queue)
            except (KeyError, ValueError):
                pass
