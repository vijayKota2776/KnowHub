import os
import json
from typing import Dict, List, Any

class NoSQLDatabase:
    """
    Simulates a wide-column Cassandra database.
    Stores partitions (Answers, Comments, and timelines) in separate JSON files on disk.
    Allows O(1) reads by loading the matching partition file directly without searching tables.
    """
    def __init__(self, data_dir: str = "data/nosql"):
        self.data_dir = data_dir
        os.makedirs(os.path.join(data_dir, "answers"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "comments"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "feeds"), exist_ok=True)

    def _get_partition_path(self, table_name: str, partition_key: str) -> str:
        # Safe filename hashing or mapping
        safe_key = "".join([c if c.isalnum() else "_" for c in partition_key])
        return os.path.join(self.data_dir, table_name, f"{safe_key}.json")

    def _read_partition(self, table_name: str, partition_key: str) -> List[Dict[str, Any]]:
        path = self._get_partition_path(table_name, partition_key)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_partition(self, table_name: str, partition_key: str, data: List[Dict[str, Any]]) -> None:
        path = self._get_partition_path(table_name, partition_key)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def insert_answer(self, answer_data: Dict[str, Any]) -> None:
        question_id = answer_data.get("question_id")
        partition = self._read_partition("answers", question_id)
        
        # Append answer (simulate wide-column clustering append)
        partition.append(dict(answer_data))
        self._write_partition("answers", question_id, partition)

    def get_answers_for_question(self, question_id: str) -> List[Dict[str, Any]]:
        return self._read_partition("answers", question_id)

    def update_answer_votes(self, question_id: str, answer_id: str, upvotes: int, downvotes: int) -> None:
        partition = self._read_partition("answers", question_id)
        for ans in partition:
            if ans.get("answer_id") == answer_id:
                ans["upvotes"] = upvotes
                ans["downvotes"] = downvotes
                break
        self._write_partition("answers", question_id, partition)

    def insert_comment(self, comment_data: Dict[str, Any]) -> None:
        parent_id = comment_data.get("parent_id")
        partition = self._read_partition("comments", parent_id)
        partition.append(dict(comment_data))
        self._write_partition("comments", parent_id, partition)

    def get_comments_for_parent(self, parent_id: str) -> List[Dict[str, Any]]:
        return self._read_partition("comments", parent_id)

    def append_to_user_feed(self, user_id: str, question_id: str) -> None:
        path = self._get_partition_path("feeds", user_id)
        feed = self._read_partition("feeds", user_id)
        
        # Prepend question_id (reverse chronological)
        feed_ids = [item.get("question_id") for item in feed if isinstance(item, dict)]
        if not feed_ids:
            # Fallback if partition was simple array of strings historically
            feed_ids = [item for item in feed if isinstance(item, str)]
            
        if question_id not in feed_ids:
            feed.insert(0, {"question_id": question_id})
            self._write_partition("feeds", user_id, feed)

    def get_user_feed(self, user_id: str) -> List[str]:
        feed = self._read_partition("feeds", user_id)
        # Parse output safely
        q_ids = []
        for item in feed:
            if isinstance(item, dict):
                q_ids.append(item["question_id"])
            elif isinstance(item, str):
                q_ids.append(item)
        return q_ids
