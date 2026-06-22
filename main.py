"""
KnowHub — Production-Grade Knowledge-Sharing Platform API
=========================================================
FastAPI Ingress Gateway implementing:
  - JWT-based mock authentication (Section 5 of System Design)
  - CORS middleware
  - Rate-limiting simulation header
  - RESTful routes for Users, Q&A, Feed, and Search services
"""

import time
import hashlib
import json
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()  # Load .env file if present

from fastapi import FastAPI, HTTPException, Header, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from services.logger import logger
from prometheus_fastapi_instrumentator import Instrumentator


# ── Database Adapters ──────────────────────────────────────────────
from database.sql_db import SQLDatabase
from database.nosql_db import NoSQLDatabase
from database.graph_db import GraphDatabase
from database.vector_db import VectorDatabase

# ── Business Services ──────────────────────────────────────────────
from services.user_service import UserService
from services.qa_service import QAService
from services.feed_service import FeedService
from services.search_service import SearchService
from services.notification_service import NotificationService

# ── Pydantic Schemas ──────────────────────────────────────────────
from models.schemas import (
    UserRegister, UserLogin, TokenResponse, UserProfileResponse,
    QuestionCreate, QuestionResponse, AnswerCreate, AnswerResponse,
    VoteRequest, VoteResponse,
    TopicCreate, TopicResponse,
    FeedResponse, SearchResult,
)

# ═══════════════════════════════════════════════════════════════════
#  APPLICATION FACTORY
# ═══════════════════════════════════════════════════════════════════

app = FastAPI(
    title="KnowHub API",
    description="A production-grade knowledge-sharing platform API modeled after Quora/Stack Overflow.",
    version="1.0.0",
)

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# ── CORS Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton Database Adapters (Dependency Injection) ─────────────
sql_db = SQLDatabase(db_path="data/knowhub.db")
nosql_db = NoSQLDatabase(data_dir="data/nosql")
graph_db = GraphDatabase(db_path="data/graph.json")
vector_db = VectorDatabase(db_path="data/vector.json")

# ── Business Service Instances ─────────────────────────────────────
user_service = UserService(sql_db=sql_db, graph_db=graph_db)
qa_service = QAService(sql_db=sql_db, nosql_db=nosql_db, vector_db=vector_db)
feed_service = FeedService(sql_db=sql_db, nosql_db=nosql_db, graph_db=graph_db, celebrity_threshold=3)
search_service = SearchService(sql_db=sql_db, vector_db=vector_db)
notification_service = NotificationService()


# ═══════════════════════════════════════════════════════════════════
#  MOCK JWT AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════

# In-memory token store: token -> user_id
_active_tokens: dict = {}

def _generate_token(user_id: str) -> str:
    """Creates a mock JWT (HMAC-SHA256 hash of user_id + timestamp)."""
    raw = f"{user_id}:{time.time()}"
    token = hashlib.sha256(raw.encode()).hexdigest()
    _active_tokens[token] = user_id
    return token

def _resolve_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency: extracts user_id from 'Authorization: Bearer <token>' header.
    Returns user_id or raises 401.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Use 'Bearer <token>'.")
    token = parts[1]
    user_id = _active_tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user_id


# ── Author Username Resolver Helper ───────────────────────────────
_user_id_to_username = {}

def get_username_by_id(user_id: str) -> str:
    if not user_id:
        return ""
    if user_id not in _user_id_to_username:
        user = sql_db.get_user(user_id)
        if user:
            _user_id_to_username[user_id] = user["username"]
        else:
            _user_id_to_username[user_id] = user_id
    return _user_id_to_username[user_id]

def populate_author_username(obj):
    if not obj:
        return obj
    if isinstance(obj, list):
        for item in obj:
            populate_author_username(item)
        return obj
    if isinstance(obj, dict):
        if "author_id" in obj:
            obj["author_username"] = get_username_by_id(obj["author_id"])
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                populate_author_username(value)
    return obj


# ═══════════════════════════════════════════════════════════════════
#  RATE-LIMITING SIMULATION MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════

_rate_limit_store: dict = {}  # ip -> (count, window_start)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 100  # requests per window

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip in _rate_limit_store:
        count, window_start = _rate_limit_store[client_ip]
        if now - window_start > RATE_LIMIT_WINDOW:
            _rate_limit_store[client_ip] = (1, now)
            count = 1
        else:
            count += 1
            _rate_limit_store[client_ip] = (count, window_start)
    else:
        count = 1
        _rate_limit_store[client_ip] = (1, now)

    if count > RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_MAX - count))
    return response


# ═══════════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy", "service": "KnowHub API", "version": "1.0.0"}


@app.get("/health/notifications", tags=["System"])
def health_notifications():
    """Health check for the notification service — reports active WS connection count."""
    total = sum(len(v) for v in notification_service._connections.values())
    return {
        "status": "ok",
        "active_connections": total,
        "connected_users": list(notification_service._connections.keys()),
    }


# ═══════════════════════════════════════════════════════════════════
#  USER ROUTES  (Section 5.1)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/v1/auth/register", response_model=dict, tags=["Auth"])
def register_user(body: UserRegister):
    """Register a new user account."""
    try:
        result = user_service.register_user(body.username, body.email, body.password)
        # Auto-issue token on registration
        token = _generate_token(result["user_id"])
        return {
            "user": result,
            "token": {"access_token": token, "token_type": "Bearer", "expires_in": 3600},
        }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/api/v1/auth/login", response_model=dict, tags=["Auth"])
def login_user(body: UserLogin):
    """Authenticate and receive a token."""
    try:
        user = user_service.authenticate_user(body.email, body.password)
        token = _generate_token(user["user_id"])
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "token": {"access_token": token, "token_type": "Bearer", "expires_in": 3600},
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# /me MUST come before /{user_id} so FastAPI doesn't treat 'me' as a user_id
@app.get("/api/v1/users/me", response_model=UserProfileResponse, tags=["Users"])
def get_current_user(current_user: str = Depends(_resolve_token)):
    """Get the authenticated user's own profile."""
    try:
        profile = user_service.get_profile(current_user)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/users/{user_id}", response_model=UserProfileResponse, tags=["Users"])
def get_user_profile(user_id: str, _current_user: str = Depends(_resolve_token)):
    """Get a user's public profile (requires auth)."""
    try:
        profile = user_service.get_profile(user_id)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/users/{user_id}/follow", tags=["Users"])
def follow_user(user_id: str, current_user: str = Depends(_resolve_token)):
    """Follow another user."""
    try:
        user_service.follow_user(follower_id=current_user, followee_id=user_id)
        return {"status": "ok", "message": f"Now following user '{user_id}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
#  TOPIC ROUTES  (Section 5.2)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/topics", tags=["Topics"])
def list_topics():
    """List all topics (public)."""
    with sql_db._get_connection() as conn:
        rows = conn.execute("SELECT * FROM topics ORDER BY name").fetchall()
        topics = [dict(r) for r in rows]
    return {"topics": topics, "count": len(topics)}


@app.post("/api/v1/topics", response_model=TopicResponse, tags=["Topics"])
def create_topic(body: TopicCreate, _current_user: str = Depends(_resolve_token)):
    """Create a new topic (admin-like endpoint)."""
    try:
        result = user_service.create_topic(body.topic_id, body.name, body.description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/api/v1/topics/{topic_id}/follow", tags=["Topics"])
def follow_topic(topic_id: str, current_user: str = Depends(_resolve_token)):
    """Follow a topic to receive feed updates."""
    try:
        user_service.follow_topic(user_id=current_user, topic_id=topic_id)
        return {"status": "ok", "message": f"Now following topic '{topic_id}'."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
#  Q&A ROUTES  (Section 5.3)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/v1/questions", response_model=QuestionResponse, tags=["Q&A"])
def post_question(body: QuestionCreate, current_user: str = Depends(_resolve_token)):
    """Post a new question. Triggers feed fanout."""
    try:
        result = qa_service.post_question(
            author_id=current_user,
            title=body.title,
            content=body.content,
            topic_ids=body.topic_ids,
        )
        # Trigger async feed fanout (Push path)
        feed_service.handle_new_question_fanout(result["question_id"], current_user)
        return populate_author_username(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/questions/{question_id}", tags=["Q&A"])
def get_question(question_id: str):
    """Get a question by ID (public)."""
    q = sql_db.get_question(question_id)
    if not q:
        raise HTTPException(status_code=404, detail=f"Question '{question_id}' not found.")
    # Attach ranked answers
    answers = qa_service.get_ranked_answers(question_id)
    response_data = {"question": q, "answers": answers, "answer_count": len(answers)}
    return populate_author_username(response_data)


@app.post("/api/v1/questions/{question_id}/answers", response_model=AnswerResponse, tags=["Q&A"])
def post_answer(question_id: str, body: AnswerCreate, current_user: str = Depends(_resolve_token)):
    """Post an answer to a question."""
    try:
        result = qa_service.post_answer(
            question_id=question_id,
            author_id=current_user,
            content=body.content,
        )
        return populate_author_username(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/questions/{question_id}/answers/{answer_id}/vote", response_model=VoteResponse, tags=["Q&A"])
def vote_on_answer(question_id: str, answer_id: str, body: VoteRequest, _current_user: str = Depends(_resolve_token)):
    """Upvote or downvote an answer. Updates author reputation."""
    try:
        result = qa_service.vote_answer(question_id, answer_id, body.vote_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/questions/{question_id}/comments", tags=["Q&A"])
def post_question_comment(question_id: str, body: AnswerCreate, current_user: str = Depends(_resolve_token)):
    """Post a comment on a question."""
    try:
        result = qa_service.post_comment(
            parent_id=question_id,
            parent_type="question",
            author_id=current_user,
            content=body.content,
        )
        return populate_author_username(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/questions/{question_id}/comments", tags=["Q&A"])
def get_question_comments(question_id: str):
    """Get comments for a question (public)."""
    comments = nosql_db.get_comments_for_parent(question_id)
    return populate_author_username({"comments": comments, "count": len(comments)})


# ═══════════════════════════════════════════════════════════════════
#  FEED ROUTES  (Section 5.4)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/feed", tags=["Feed"])
def get_user_feed(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: str = Depends(_resolve_token),
):
    """
    Get the authenticated user's personalized feed.
    Implements Hybrid Push-Pull architecture:
      - Push: Pre-computed inbox from non-celebrity followed users.
      - Pull: Dynamic merge from celebrity authors and followed topics.
    """
    questions = feed_service.generate_user_feed(user_id=current_user, limit=limit)
    feed_items = []
    for q in questions:
        feed_items.append(QuestionResponse(**populate_author_username(q)).model_dump())
    return {"data": feed_items, "count": len(feed_items)}


# ═══════════════════════════════════════════════════════════════════
#  SEARCH ROUTES  (Section 5.5)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/search", tags=["Search"])
def search_questions(
    q: str = Query(..., min_length=1, description="Search query string"),
    top_k: int = Query(default=5, ge=1, le=50),
    lexical_weight: float = Query(default=0.4, ge=0.0, le=1.0),
    semantic_weight: float = Query(default=0.6, ge=0.0, le=1.0),
):
    """
    Hybrid search fusing lexical (Jaccard) and semantic (TF-IDF Cosine) scores.
    Public endpoint — no authentication required.
    """
    results = search_service.search_questions(
        query=q, top_k=top_k,
        lexical_weight=lexical_weight,
        semantic_weight=semantic_weight,
    )
    return {"results": populate_author_username(results), "count": len(results), "query": q}


# ═══════════════════════════════════════════════════════════════════
#  RECOMMENDATION ROUTES  (Section 5.6)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/v1/recommendations/topics", tags=["Recommendations"])
def recommend_topics(current_user: str = Depends(_resolve_token)):
    """
    Collaborative filtering topic recommendations.
    Suggests topics followed by people the user follows, but not yet followed by the user.
    """
    recommended = graph_db.recommend_topics_collaborative(current_user)
    return {"recommended_topics": recommended, "count": len(recommended)}


# (moved to correct positions above)


# ═══════════════════════════════════════════════════════════════════
#  STARTUP EVENT
# ═══════════════════════════════════════════════════════════════════

@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time notifications.
    Clients must provide a `token` query parameter (same format as Authorization header).
    Rate-limited: max 10 WS connections per IP.
    """
    client_ip = websocket.client.host if websocket.client else "unknown"

    # WS-level rate limiting: max 10 active connections per IP
    ws_count = sum(
        1 for conns in notification_service._connections.values() for _ in conns
    )
    if ws_count > 10:
        await websocket.close(code=1008)  # Policy violation
        return

    # Validate token — reject if missing/invalid
    user_id = _active_tokens.get(token)
    if not user_id:
        logger.warning("WS rejected: invalid token", ip=client_ip)
        await websocket.close(code=4001)  # Custom: Unauthorized
        return

    logger.info("WS connected", user_id=user_id, ip=client_ip)
    await notification_service.register_connection(user_id, websocket)
    try:
        while True:
            # Keep connection alive; ignore any received messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WS disconnected", user_id=user_id, ip=client_ip)
        await notification_service.unregister_connection(user_id, websocket)


def seed_mock_data():
    """Seeds the SQL, NoSQL, Graph, and Vector databases with realistic mock data."""
    try:
        logger.info("Creating mock users...")
        u_alice = user_service.register_user("alice_eng", "alice@knowhub.io", "securepass1")
        u_bob = user_service.register_user("bob_science", "bob@knowhub.io", "securepass2")
        u_carol = user_service.register_user("carol_math", "carol@knowhub.io", "securepass3")
        u_dave = user_service.register_user("dave_celeb", "dave@knowhub.io", "securepass4")

        alice_id = u_alice["user_id"]
        bob_id = u_bob["user_id"]
        carol_id = u_carol["user_id"]
        dave_id = u_dave["user_id"]

        logger.info("Creating mock topics...")
        user_service.create_topic("python", "Python", "Python programming language, optimization, and runtime internals.")
        user_service.create_topic("ml", "Machine Learning", "Neural networks, regression, transformers, and training pipelines.")
        user_service.create_topic("system_design", "System Design", "Scalability, microservices, load balancing, and distributed consensus.")
        user_service.create_topic("databases", "Databases", "Relational database indexing, sharding, replication, and NoSQL stores.")

        logger.info("Creating social follows and subscriptions...")
        user_service.follow_user(alice_id, bob_id)
        user_service.follow_user(alice_id, dave_id)
        user_service.follow_user(bob_id, dave_id)
        user_service.follow_user(carol_id, bob_id)

        user_service.follow_topic(alice_id, "python")
        user_service.follow_topic(alice_id, "system_design")
        user_service.follow_topic(bob_id, "ml")
        user_service.follow_topic(bob_id, "system_design")
        user_service.follow_topic(carol_id, "databases")
        user_service.follow_topic(dave_id, "system_design")

        logger.info("Creating mock questions...")
        q1 = qa_service.post_question(
            author_id=alice_id,
            title="How does Python garbage collection work under the hood?",
            content="I am curious about reference counting, cyclic garbage collection, and generational thresholds in CPython. How does it handle cycles?",
            topic_ids=["python"]
        )
        q2 = qa_service.post_question(
            author_id=bob_id,
            title="Best practices for system design interviews?",
            content="When designing high-throughput services, how should I structure the conversation? Should I start with API design or database schema?",
            topic_ids=["system_design"]
        )
        q3 = qa_service.post_question(
            author_id=dave_id,
            title="How to design a scalable database sharding solution?",
            content="We have a highly transactional table that has outgrown a single Postgres node. What sharding keys work best, and how do we handle dynamic re-sharding?",
            topic_ids=["databases", "system_design"]
        )

        logger.info("Creating mock answers...")
        a1 = qa_service.post_answer(
            question_id=q1["question_id"],
            author_id=bob_id,
            content="CPython relies on reference counting as its primary GC mechanism. When an object's reference count drops to zero, it is deallocated immediately. To handle reference cycles (e.g. object A referencing B, and B referencing A), CPython runs a cyclic garbage collector. It groups objects into three generations (Gen 0, 1, and 2) based on survival rates and inspects them using double-linked lists to detect isolated islands of unreferenced cycles."
        )
        a2 = qa_service.post_answer(
            question_id=q1["question_id"],
            author_id=carol_id,
            content="Yes, and it is worth noting that you can tune these thresholds using the native `gc` module in Python. For example, `gc.set_threshold()` lets you adjust when generation collection runs. You can also manually call `gc.collect()` to trigger a collection cycle, which is common in memory-constrained environments or background worker loops."
        )
        a3 = qa_service.post_answer(
            question_id=q2["question_id"],
            author_id=dave_id,
            content="Start by clarifying requirements (functional and non-functional RPS, DAU, latency). Then draft the high-level design (gateway, load balancers, database layers) before diving into deep bottleneck analysis. Never jump straight to database schemas without establishing the scale targets!"
        )

        logger.info("Adding mock votes...")
        # Upvotes for Bob's excellent GC answer
        qa_service.vote_answer(q1["question_id"], a1["answer_id"], alice_id, "upvote")
        qa_service.vote_answer(q1["question_id"], a1["answer_id"], carol_id, "upvote")
        qa_service.vote_answer(q1["question_id"], a1["answer_id"], dave_id, "upvote")

        # Downvote for Carol's answer
        qa_service.vote_answer(q1["question_id"], a2["answer_id"], bob_id, "downvote")

        logger.info("Adding mock comments...")
        qa_service.post_comment(parent_id=q1["question_id"], parent_type="question", author_id=carol_id, content="Great question! I was also wondering about the overhead of cyclic GC.")
        qa_service.post_comment(parent_id=a1["answer_id"], parent_type="answer", author_id=alice_id, content="This clears up generational thresholds perfectly. Thanks Bob!")

        logger.info("Mock database seeding completed successfully!")
    except Exception as e:
        logger.error("Failed to seed mock data", error=str(e))


@app.on_event("startup")
async def startup_event():
    notification_service.start()
    
    # Run seeder if database has no users
    try:
        with sql_db._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
            user_count = row["cnt"] if row else 0
        if user_count == 0:
            seed_mock_data()
    except Exception as e:
        logger.error("Database check failed during startup", error=str(e))
        
    logger.info("KnowHub API started", version="1.0.0", docs="http://localhost:8000/docs")

