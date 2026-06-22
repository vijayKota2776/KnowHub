import os
import json
from typing import Dict, Set, List

class GraphDatabase:
    """
    Simulates a Neo4j Graph Database.
    Stores social graphs and topic follow maps persistently in a single JSON file.
    """
    def __init__(self, db_path: str = "data/graph.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # Maps user_id -> List of user_ids followed
        self.follows: Dict[str, List[str]] = {}
        # Maps user_id -> List of topic_ids followed
        self.followed_topics: Dict[str, List[str]] = {}
        self._load_graph()

    def _load_graph(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    self.follows = data.get("follows", {})
                    self.followed_topics = data.get("followed_topics", {})
            except Exception:
                self.follows = {}
                self.followed_topics = {}

    def _save_graph(self):
        with open(self.db_path, "w") as f:
            json.dump({
                "follows": self.follows,
                "followed_topics": self.followed_topics
            }, f, indent=2)

    def add_user(self, user_id: str) -> None:
        if user_id not in self.follows:
            self.follows[user_id] = []
        if user_id not in self.followed_topics:
            self.followed_topics[user_id] = []
        self._save_graph()

    def add_follow(self, follower_id: str, followee_id: str) -> None:
        self.add_user(follower_id)
        self.add_user(followee_id)
        if followee_id not in self.follows[follower_id]:
            self.follows[follower_id].append(followee_id)
            self._save_graph()

    def add_topic_follow(self, user_id: str, topic_id: str) -> None:
        self.add_user(user_id)
        if topic_id not in self.followed_topics[user_id]:
            self.followed_topics[user_id].append(topic_id)
            self._save_graph()

    def get_following(self, user_id: str) -> Set[str]:
        return set(self.follows.get(user_id, []))

    def get_followers(self, user_id: str) -> Set[str]:
        followers = set()
        for fer_id, f_list in self.follows.items():
            if user_id in f_list:
                followers.add(fer_id)
        return followers

    def get_followed_topics(self, user_id: str) -> Set[str]:
        return set(self.followed_topics.get(user_id, []))

    def recommend_topics_collaborative(self, user_id: str) -> List[str]:
        following = self.get_following(user_id)
        my_topics = self.get_followed_topics(user_id)
        topic_scores: Dict[str, int] = {}
        
        for friend in following:
            friend_topics = self.get_followed_topics(friend)
            for topic in friend_topics:
                if topic not in my_topics:
                    topic_scores[topic] = topic_scores.get(topic, 0) + 1
                    
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics]
