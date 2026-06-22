import sqlite3
import os
from typing import Dict, Any, List

class SQLDatabase:
    """
    Manages the PostgreSQL-equivalent Relational Database simulation using Python SQLite.
    Enforces ACID transactions, unique indexes, and foreign keys.
    """
    def __init__(self, db_path: str = "data/knowhub.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._initialize_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        # Enable Foreign Key enforcement in SQLite (essential for ACID referential check simulation)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        with self._get_connection() as conn:
            # 1. Create Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    reputation REAL DEFAULT 1.0 NOT NULL,
                    created_at REAL NOT NULL
                );
            """)
            
            # 2. Create Topics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    topic_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at REAL NOT NULL
                );
            """)

            # 3. Create Questions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    question_id TEXT PRIMARY KEY,
                    author_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (author_id) REFERENCES users (user_id) ON DELETE RESTRICT
                );
            """)
            
            # 4. Create Question-Topics mapping table (Relational normalization)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS question_topics (
                    question_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    PRIMARY KEY (question_id, topic_id),
                    FOREIGN KEY (question_id) REFERENCES questions (question_id) ON DELETE CASCADE,
                    FOREIGN KEY (topic_id) REFERENCES topics (topic_id) ON DELETE CASCADE
                );
            """)
            
            conn.commit()

    def insert_user(self, user_id: str, username: str, email: str, password_hash: str, created_at: float) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (user_id, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, email, password_hash, created_at)
                )
                conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Database Integrity Violation: {str(e)}")

    def get_user(self, user_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            return dict(row) if row else None

    def update_user_reputation(self, user_id: str, delta: float) -> float:
        with self._get_connection() as conn:
            row = conn.execute("SELECT reputation FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not row:
                raise ValueError(f"User '{user_id}' not found.")
            new_rep = max(0.1, row["reputation"] + delta)
            conn.execute("UPDATE users SET reputation = ? WHERE user_id = ?", (new_rep, user_id))
            conn.commit()
            return new_rep

    def insert_topic(self, topic_id: str, name: str, description: str, created_at: float) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO topics (topic_id, name, description, created_at) VALUES (?, ?, ?, ?)",
                    (topic_id, name, description, created_at)
                )
                conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Database Integrity Violation: {str(e)}")

    def get_topic(self, topic_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM topics WHERE topic_id = ?", (topic_id,)).fetchone()
            return dict(row) if row else None

    def insert_question(self, question_id: str, author_id: str, title: str, content: str, topic_ids: List[str], created_at: float) -> None:
        try:
            with self._get_connection() as conn:
                # Insert main question metadata
                conn.execute(
                    "INSERT INTO questions (question_id, author_id, title, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (question_id, author_id, title, content, created_at)
                )
                # Map topics to question
                for topic_id in topic_ids:
                    # Foreign key will automatically validate topic_id exists in topics table
                    conn.execute(
                        "INSERT INTO question_topics (question_id, topic_id) VALUES (?, ?)",
                        (question_id, topic_id)
                    )
                conn.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Database Integrity Violation: {str(e)}")

    def get_question(self, question_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            q_row = conn.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,)).fetchone()
            if not q_row:
                return None
            
            # Fetch mapped topic IDs
            t_rows = conn.execute("SELECT topic_id FROM question_topics WHERE question_id = ?", (question_id,)).fetchall()
            q_dict = dict(q_row)
            q_dict["topic_ids"] = [row["topic_id"] for row in t_rows]
            return q_dict

    def get_all_questions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            q_rows = conn.execute("SELECT * FROM questions").fetchall()
            questions = []
            for r in q_rows:
                q_id = r["question_id"]
                t_rows = conn.execute("SELECT topic_id FROM question_topics WHERE question_id = ?", (q_id,)).fetchall()
                q_dict = dict(r)
                q_dict["topic_ids"] = [t["topic_id"] for t in t_rows]
                questions.append(q_dict)
            return questions
