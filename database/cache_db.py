import time
from typing import Any, Dict, Optional

class CacheDatabase:
    """
    Simulates a Redis caching layer.
    Stores key-value pairs in memory with time-to-live (TTL) expiration.
    """
    def __init__(self):
        # Maps key -> (value, expire_timestamp)
        self._store: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            # Lazy eviction
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        expires_at = time.time() + ttl_seconds
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()
