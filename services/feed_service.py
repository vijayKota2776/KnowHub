from typing import List, Dict, Any
from database.sql_db import SQLDatabase
from database.nosql_db import NoSQLDatabase
from database.graph_db import GraphDatabase

class FeedService:
    """
    Implements Section 9/11 Hybrid feed engine.
    Controls writing feed IDs to timeline caches on post (Push)
    and dynamically pulling topic/celebrity posts on request (Pull).
    """
    def __init__(self, sql_db: SQLDatabase, nosql_db: NoSQLDatabase, graph_db: GraphDatabase, celebrity_threshold: int = 3, cache_db=None):
        self.sdb = sql_db
        self.ndb = nosql_db
        self.gdb = graph_db
        self.celebrity_threshold = celebrity_threshold
        self.cdb = cache_db

    def handle_new_question_fanout(self, question_id: str, author_id: str) -> None:
        followers = self.gdb.get_followers(author_id)
        is_celebrity = len(followers) >= self.celebrity_threshold
        
        # Invalidate followers' feed caches
        if self.cdb:
            for follower_id in followers:
                self.cdb.delete(f"feed:{follower_id}")

        if not is_celebrity:
            # PUSH: Write to pre-computed inbox feed of followers
            for follower_id in followers:
                self.ndb.append_to_user_feed(follower_id, question_id)

        # Invalidate users who follow the topics of the new question
        if self.cdb:
            q_data = self.sdb.get_question(question_id)
            if q_data and q_data.get("topic_ids"):
                topics = set(q_data["topic_ids"])
                for u_id in self.gdb.followed_topics.keys():
                    user_topics = set(self.gdb.followed_topics.get(u_id, []))
                    if user_topics & topics:
                        self.cdb.delete(f"feed:{u_id}")

    def generate_user_feed(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        if self.cdb:
            cached = self.cdb.get(f"feed:{user_id}")
            if cached:
                return cached[:limit]

        # 1. Fetch precomputed inbox (Push path)
        precomputed_ids = self.ndb.get_user_feed(user_id)
        
        # 2. Find followed users and topics (Graph traversal)
        followed_users = self.gdb.get_following(user_id)
        followed_topics = self.gdb.get_followed_topics(user_id)
        
        # Detect celebrity authors (followers >= threshold)
        celebrity_authors = []
        for f_id in followed_users:
            followers = self.gdb.get_followers(f_id)
            if len(followers) >= self.celebrity_threshold:
                celebrity_authors.append(f_id)
                
        # 3. Dynamic Pull: Fetch all questions from relational DB
        all_questions = self.sdb.get_all_questions()
        
        pulled_celeb_ids = []
        pulled_topic_ids = []
        
        for q in all_questions:
            q_id = q["question_id"]
            # Pull from celebrity authors
            if q["author_id"] in celebrity_authors:
                pulled_celeb_ids.append(q_id)
            # Pull from followed topics
            if set(q["topic_ids"]) & followed_topics:
                pulled_topic_ids.append(q_id)
                
        # Merge and deduplicate
        merged_ids = set(precomputed_ids + pulled_celeb_ids + pulled_topic_ids)
        
        # Hydrate questions from relational store
        feed_questions = []
        for q_id in merged_ids:
            q_data = self.sdb.get_question(q_id)
            if q_data:
                feed_questions.append(q_data)
                
        # Sort chronologically (newest first)
        feed_questions.sort(key=lambda x: x["created_at"], reverse=True)
        
        if self.cdb:
            self.cdb.set(f"feed:{user_id}", feed_questions, ttl_seconds=30)
            
        return feed_questions[:limit]
