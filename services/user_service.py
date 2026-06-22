import time
import hashlib
import asyncio
from typing import Dict, Any, List
from database.sql_db import SQLDatabase
from database.graph_db import GraphDatabase
from services.event_bus import EventBus


def _fire_event(event_type: str, payload: Dict[str, Any]):
    """Schedule an EventBus.publish coroutine on the running event loop from a sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.call_soon_threadsafe(lambda: asyncio.ensure_future(EventBus.publish(event_type, payload)))
    except RuntimeError:
        pass  # No event loop — skip publishing


class UserService:
    """
    Manages accounts, registration authentication hash validations,
    and Graph relation modifications (user and topic follows).
    """
    def __init__(self, sql_db: SQLDatabase, graph_db: GraphDatabase, cache_db=None):
        self.sdb = sql_db
        self.gdb = graph_db
        self.cdb = cache_db

    def _hash_password(self, password: str) -> str:
        # Standard SHA-256 password hashing (simulates bcrypt/argon2 hashing at production)
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        user_id = f"u_{int(time.time() * 1000)}"
        pw_hash = self._hash_password(password)
        created_at = time.time()
        
        # SQL Insert (enforces unique email and username)
        self.sdb.insert_user(user_id, username, email, pw_hash, created_at)
        
        # Graph init
        self.gdb.add_user(user_id)
        
        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "created_at": created_at
        }

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        user = self.sdb.get_user_by_email(email)
        if not user:
            raise ValueError("Invalid email or password.")
            
        hashed_input = self._hash_password(password)
        if user["password_hash"] != hashed_input:
            raise ValueError("Invalid email or password.")
            
        return user

    def follow_user(self, follower_id: str, followee_id: str) -> None:
        if not self.sdb.get_user(follower_id):
            raise ValueError(f"Follower '{follower_id}' does not exist.")
        if not self.sdb.get_user(followee_id):
            raise ValueError(f"Followee '{followee_id}' does not exist.")
        self.gdb.add_follow(follower_id, followee_id)
        if self.cdb:
            self.cdb.delete(f"profile:{follower_id}")
            self.cdb.delete(f"profile:{followee_id}")
        # Publish follow event
        _fire_event('user_followed', {
            'follower_id': follower_id,
            'followee_id': followee_id
        })

    def follow_topic(self, user_id: str, topic_id: str) -> None:
        if not self.sdb.get_user(user_id):
            raise ValueError(f"User '{user_id}' does not exist.")
        if not self.sdb.get_topic(topic_id):
            raise ValueError(f"Topic '{topic_id}' does not exist.")
        self.gdb.add_topic_follow(user_id, topic_id)
        if self.cdb:
            self.cdb.delete(f"profile:{user_id}")

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        if self.cdb:
            cached = self.cdb.get(f"profile:{user_id}")
            if cached:
                return cached

        user = self.sdb.get_user(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found.")
            
        # Enrich profile metadata from Graph DB
        user_dict = dict(user)
        user_dict["following_count"] = len(self.gdb.get_following(user_id))
        user_dict["followers_count"] = len(self.gdb.get_followers(user_id))
        user_dict["followed_topics"] = list(self.gdb.get_followed_topics(user_id))
        
        if self.cdb:
            self.cdb.set(f"profile:{user_id}", user_dict, ttl_seconds=60)
            
        return user_dict

    def create_topic(self, topic_id: str, name: str, description: str) -> Dict[str, Any]:
        created_at = time.time()
        self.sdb.insert_topic(topic_id, name, description, created_at)
        return {
            "topic_id": topic_id,
            "name": name,
            "description": description,
            "created_at": created_at
        }
