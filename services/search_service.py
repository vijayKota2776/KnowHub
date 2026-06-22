import re
from typing import List, Dict, Any, Tuple, Set
from database.sql_db import SQLDatabase
from database.vector_db import VectorDatabase

class SearchService:
    """
    Implements Section 6 Search Engine.
    Fuses lexical overlap queries (Jaccard similarity) with
    semantic similarity metrics (Cosine similarity from the Vector DB).
    """
    def __init__(self, sql_db: SQLDatabase, vector_db: VectorDatabase):
        self.sdb = sql_db
        self.vdb = vector_db

    def _tokenize(self, text: str) -> Set[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return {word for word in text.split() if len(word) > 2}

    def _calculate_lexical_score(self, query: str, document_text: str) -> float:
        query_words = self._tokenize(query)
        doc_words = self._tokenize(document_text)
        
        if not query_words or not doc_words:
            return 0.0
            
        intersection = query_words.intersection(doc_words)
        union = query_words.union(doc_words)
        return len(intersection) / len(union)

    def search_questions(self, query: str, top_k: int = 5, lexical_weight: float = 0.4, semantic_weight: float = 0.6) -> List[Dict[str, Any]]:
        all_questions = self.sdb.get_all_questions()
        scores: Dict[str, Dict[str, float]] = {}
        
        for q in all_questions:
            q_id = q["question_id"]
            scores[q_id] = {"lexical": 0.0, "semantic": 0.0}

        # 1. Lexical Scoring
        for q in all_questions:
            q_id = q["question_id"]
            doc_text = f"{q['title']} {q['content']}"
            scores[q_id]["lexical"] = self._calculate_lexical_score(query, doc_text)

        # 2. Semantic Scoring
        vector_results = self.vdb.search(query, top_k=len(all_questions))
        for q_id, vector_score in vector_results:
            if q_id in scores:
                scores[q_id]["semantic"] = vector_score

        # 3. Score Fusion
        hybrid_results = []
        for q_id, score_dict in scores.items():
            l_score = score_dict["lexical"]
            s_score = score_dict["semantic"]
            
            final_score = (lexical_weight * l_score) + (semantic_weight * s_score)
            
            if final_score > 0.0:
                hybrid_results.append((q_id, final_score, l_score, s_score))

        # Sort desc
        hybrid_results.sort(key=lambda x: x[1], reverse=True)

        # Hydrate
        search_results = []
        for q_id, final_score, l_score, s_score in hybrid_results[:top_k]:
            q_data = self.sdb.get_question(q_id)
            if q_data:
                enriched = {
                    **q_data,
                    "search_score": final_score,
                    "lexical_score": l_score,
                    "semantic_score": s_score
                }
                search_results.append(enriched)

        return search_results
