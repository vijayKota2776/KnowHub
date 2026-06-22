import os
import re
import math
import json
from typing import Dict, List, Tuple, Set

class VectorDatabase:
    """
    Simulates a Vector Database (e.g., Qdrant) with file-backed persistence.
    Implements a pure-Python TF-IDF Vector Space Cosine Similarity search.
    """
    def __init__(self, db_path: str = "data/vector.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.documents: Dict[str, str] = {}
        self.vocabulary: List[str] = []
        self.tf_vectors: Dict[str, Dict[str, int]] = {}
        self.df_counts: Dict[str, int] = {}
        self._load_db()

    def _load_db(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", {})
                    self.vocabulary = data.get("vocabulary", [])
                    self.tf_vectors = data.get("tf_vectors", {})
                    self.df_counts = data.get("df_counts", {})
            except Exception:
                pass

    def _save_db(self):
        with open(self.db_path, "w") as f:
            json.dump({
                "documents": self.documents,
                "vocabulary": self.vocabulary,
                "tf_vectors": self.tf_vectors,
                "df_counts": self.df_counts
            }, f, indent=2)

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return [word for word in text.split() if len(word) > 2]

    def upsert(self, question_id: str, text: str) -> None:
        self.documents[question_id] = text
        tokens = self._tokenize(text)
        
        # Calculate TF
        tf: Dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
            if token not in self.vocabulary:
                self.vocabulary.append(token)
                
        # Update DF count
        for token in set(tokens):
            self.df_counts[token] = self.df_counts.get(token, 0) + 1
            
        self.tf_vectors[question_id] = tf
        self._save_db()

    def _compute_cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        dot_product = 0.0
        for word in vec_a:
            if word in vec_b:
                dot_product += vec_a[word] * vec_b[word]
                
        mag_a = math.sqrt(sum(val ** 2 for val in vec_a.values()))
        mag_b = math.sqrt(sum(val ** 2 for val in vec_b.values()))
        
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot_product / (mag_a * mag_b)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.documents:
            return []

        query_tf: Dict[str, int] = {}
        for token in query_tokens:
            query_tf[token] = query_tf.get(token, 0) + 1

        N = len(self.documents)
        idf: Dict[str, float] = {}
        for word in self.vocabulary:
            df = self.df_counts.get(word, 0)
            if df > 0:
                idf[word] = math.log1p(N / df)
            else:
                idf[word] = 0.0

        query_tfidf: Dict[str, float] = {}
        for word, count in query_tf.items():
            if word in idf:
                query_tfidf[word] = count * idf[word]

        results: List[Tuple[str, float]] = []
        for doc_id, tf in self.tf_vectors.items():
            doc_tfidf: Dict[str, float] = {}
            for word, count in tf.items():
                doc_tfidf[word] = count * idf[word]
                
            similarity = self._compute_cosine_similarity(query_tfidf, doc_tfidf)
            if similarity > 0.0:
                results.append((doc_id, similarity))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
