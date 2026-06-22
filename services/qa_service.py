import time
import math
import asyncio
from typing import Dict, Any, List
from database.sql_db import SQLDatabase
from database.nosql_db import NoSQLDatabase
from database.vector_db import VectorDatabase
from services.event_bus import EventBus


def _fire_event(event_type: str, payload: Dict[str, Any]):
    """Schedule an EventBus.publish coroutine on the running event loop from a sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.call_soon_threadsafe(lambda: asyncio.ensure_future(EventBus.publish(event_type, payload)))
    except RuntimeError:
        pass  # No event loop — skip publishing (e.g. during CLI/tests that don't need notifications)


class QAService:
    """
    Manages questions posting, answer writing, voting counters, and reputation increments.
    Implements the core Wilson Score + Reputation + Time Decay ranking system.
    """
    def __init__(self, sql_db: SQLDatabase, nosql_db: NoSQLDatabase, vector_db: VectorDatabase):
        self.sdb = sql_db
        self.ndb = nosql_db
        self.vdb = vector_db
        self.z = 1.96 # 95% confidence critical value
        self.decay_lambda = 0.005 # decay per hour

    def post_question(self, author_id: str, title: str, content: str, topic_ids: List[str]) -> Dict[str, Any]:
        # Validate author exists
        if not self.sdb.get_user(author_id):
            raise ValueError(f"Author '{author_id}' does not exist.")
            
        question_id = f"q_{int(time.time() * 1000)}"
        created_at = time.time()
        
        # 1. SQL Write
        self.sdb.insert_question(question_id, author_id, title, content, topic_ids, created_at)
        
        # 2. Vector DB Write (Index searchable payload)
        payload = f"{title} {content}"
        self.vdb.upsert(question_id, payload)
        
        result = {
            "question_id": question_id,
            "author_id": author_id,
            "title": title,
            "content": content,
            "topic_ids": topic_ids,
            "created_at": created_at
        }
        # Publish event for new question
        _fire_event('question_posted', result)
        return result

    def post_answer(self, question_id: str, author_id: str, content: str) -> Dict[str, Any]:
        if not self.sdb.get_question(question_id):
            raise ValueError(f"Question '{question_id}' does not exist.")
        if not self.sdb.get_user(author_id):
            raise ValueError(f"User '{author_id}' does not exist.")
            
        answer_id = f"a_{int(time.time() * 1000)}"
        created_at = time.time()
        
        answer_data = {
            "answer_id": answer_id,
            "question_id": question_id,
            "author_id": author_id,
            "content": content,
            "upvotes": 0,
            "downvotes": 0,
            "created_at": created_at
        }
        
        # NoSQL Write
        self.ndb.insert_answer(answer_data)
        # Publish answer posted event
        _fire_event('answer_posted', answer_data)
        return answer_data

    def post_comment(self, parent_id: str, parent_type: str, author_id: str, content: str) -> Dict[str, Any]:
        if not self.sdb.get_user(author_id):
            raise ValueError(f"User '{author_id}' does not exist.")
            
        comment_id = f"c_{int(time.time() * 1000)}"
        created_at = time.time()
        
        comment_data = {
            "comment_id": comment_id,
            "parent_id": parent_id,
            "parent_type": parent_type, # "question" or "answer"
            "author_id": author_id,
            "content": content,
            "created_at": created_at
        }
        
        # NoSQL Write
        self.ndb.insert_comment(comment_data)
        return comment_data

    def vote_answer(self, question_id: str, answer_id: str, vote_type: str) -> Dict[str, Any]:
        answers = self.ndb.get_answers_for_question(question_id)
        target_answer = None
        for ans in answers:
            if ans["answer_id"] == answer_id:
                target_answer = ans
                break
                
        if not target_answer:
            raise ValueError(f"Answer '{answer_id}' not found under question '{question_id}'.")
            
        author_id = target_answer["author_id"]
        
        if vote_type == "upvote":
            upvotes = target_answer.get("upvotes", 0) + 1
            downvotes = target_answer.get("downvotes", 0)
            # Upvote increases reputation
            self.sdb.update_user_reputation(author_id, 0.10)
        elif vote_type == "downvote":
            upvotes = target_answer.get("upvotes", 0)
            downvotes = target_answer.get("downvotes", 0) + 1
            # Downvote decreases reputation
            self.sdb.update_user_reputation(author_id, -0.05)
        else:
            raise ValueError("Invalid vote_type.")
            
        # Update partition record
        self.ndb.update_answer_votes(question_id, answer_id, upvotes, downvotes)
        
        return {
            "answer_id": answer_id,
            "upvotes": upvotes,
            "downvotes": downvotes
        }

    def calculate_wilson_score(self, upvotes: int, downvotes: int) -> float:
        n = upvotes + downvotes
        if n == 0:
            return 0.0
        p = upvotes / n
        numerator = p + (self.z**2) / (2 * n) - self.z * math.sqrt((p * (1 - p) + (self.z**2) / (4 * n)) / n)
        denominator = 1 + (self.z**2) / n
        return numerator / denominator

    def get_ranked_answers(self, question_id: str) -> List[Dict[str, Any]]:
        raw_answers = self.ndb.get_answers_for_question(question_id)
        ranked = []
        now = time.time()
        
        for ans in raw_answers:
            ans_copy = dict(ans)
            upvotes = ans_copy.get("upvotes", 0)
            downvotes = ans_copy.get("downvotes", 0)
            created_at = ans_copy.get("created_at", now)
            author_id = ans_copy.get("author_id")
            
            # Wilson Score
            wilson = self.calculate_wilson_score(upvotes, downvotes)
            
            # Author reputation factor
            author = self.sdb.get_user(author_id)
            reputation = author["reputation"] if author else 1.0
            reputation_factor = math.log10(reputation + 10)
            
            # Time decay
            age_hours = (now - created_at) / 3600.0
            decay = math.exp(-self.decay_lambda * age_hours)
            
            final_score = wilson * reputation_factor * decay
            
            ans_copy["ranking_score"] = final_score
            ans_copy["author_reputation"] = reputation
            ranked.append(ans_copy)
            
        # Sort desc
        ranked.sort(key=lambda x: x["ranking_score"], reverse=True)
        return ranked
