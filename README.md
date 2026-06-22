# KnowHub — Production-Grade Knowledge-Sharing Platform

A fully functional knowledge-sharing platform API (Quora/Stack Overflow hybrid) built with **FastAPI**, featuring multi-database persistence, real-time feed generation, and hybrid search.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Ingress Gateway                   │
│              (CORS, Rate Limiting, JWT Auth)                 │
├────────────┬────────────┬──────────────┬───────────────────┤
│ UserService│ QAService  │ FeedService  │ SearchService     │
├────────────┴────────────┴──────────────┴───────────────────┤
│  SQLite      File JSON     Graph JSON     TF-IDF Vector    │
│  (PostgreSQL) (Cassandra)  (Neo4j)        (Qdrant)         │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Simulates | Purpose |
|-----------|-----------|---------|
| `database/sql_db.py` | PostgreSQL | Users, Questions, Topics (ACID, FK constraints) |
| `database/nosql_db.py` | Cassandra | Answers, Comments, Feed timelines (Partition-key files) |
| `database/graph_db.py` | Neo4j | Social follows, topic follows, collaborative filtering |
| `database/vector_db.py` | Qdrant | TF-IDF vector index with Cosine similarity search |

### Key Algorithms

- **Wilson Score Interval** — Statistically robust answer ranking
- **Hybrid Push-Pull Feed** — Push for regular users, Pull for celebrities/topics
- **Hybrid Search Fusion** — Lexical (Jaccard) + Semantic (TF-IDF Cosine) with configurable weights
- **Collaborative Filtering** — Topic recommendations based on social graph

---

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn pydantic[email] requests
```

### 2. Start the Server

```bash
cd /path/to/KnowHub
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open API Documentation

Navigate to: **http://localhost:8000/docs** (Swagger UI)

### 4. Run Integration Tests

In a second terminal:

```bash
cd /path/to/KnowHub
python test_api.py
```

---

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | ❌ | Register new user |
| POST | `/api/v1/auth/login` | ❌ | Login and get token |

### Users
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/users/{user_id}` | ✅ | Get user profile |
| POST | `/api/v1/users/{user_id}/follow` | ✅ | Follow a user |

### Topics
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/topics` | ✅ | Create a topic |
| POST | `/api/v1/topics/{topic_id}/follow` | ✅ | Follow a topic |

### Q&A
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/questions` | ✅ | Post a question |
| GET | `/api/v1/questions/{question_id}` | ❌ | Get question + ranked answers |
| POST | `/api/v1/questions/{qid}/answers` | ✅ | Post an answer |
| POST | `/api/v1/questions/{qid}/answers/{aid}/vote` | ✅ | Vote on answer |
| POST | `/api/v1/questions/{qid}/comments` | ✅ | Comment on question |
| GET | `/api/v1/questions/{qid}/comments` | ❌ | Get question comments |

### Feed
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/feed` | ✅ | Get personalized feed |

### Search
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/search?q=...` | ❌ | Hybrid search |

### Recommendations
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/recommendations/topics` | ✅ | Topic recommendations |

---

## Project Structure

```
KnowHub/
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── test_api.py               # Integration test suite
├── README.md                 # This file
├── system_design_report.md   # Full architecture documentation
├── database/
│   ├── __init__.py
│   ├── sql_db.py             # SQLite adapter (PostgreSQL sim)
│   ├── nosql_db.py           # File-based JSON (Cassandra sim)
│   ├── graph_db.py           # Adjacency-list (Neo4j sim)
│   └── vector_db.py          # TF-IDF vector index (Qdrant sim)
├── models/
│   ├── __init__.py
│   └── schemas.py            # Pydantic request/response models
├── services/
│   ├── __init__.py
│   ├── user_service.py       # User registration, auth, social graph
│   ├── qa_service.py         # Questions, answers, voting, ranking
│   ├── feed_service.py       # Hybrid Push-Pull feed engine
│   └── search_service.py     # Hybrid lexical+semantic search
└── data/                     # Auto-created persistent storage
    ├── knowhub.db            # SQLite database
    ├── graph.json            # Social graph state
    ├── vector.json           # Vector index state
    └── nosql/                # Partitioned JSON files
        ├── answers/
        ├── comments/
        └── feeds/
```

---

## Design Decisions

For the full 18-section architecture report, see [`system_design_report.md`](system_design_report.md).
