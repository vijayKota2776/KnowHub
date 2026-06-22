"""
KnowHub API — Comprehensive Integration Test Suite
====================================================
Tests the full API lifecycle:
  1. User Registration & Authentication
  2. Topic Creation & Following
  3. User Following (Social Graph)
  4. Question Posting (with Feed Fanout)
  5. Answer Posting & Wilson Score Ranking
  6. Voting & Reputation Updates
  7. Commenting
  8. Hybrid Feed Generation (Push + Pull)
  9. Hybrid Search (Lexical + Semantic)
  10. Topic Recommendations (Collaborative Filtering)
  11. Rate Limiting Headers
  12. Error Handling (401, 404, 409)

Run:
    python test_api.py
    (Server must be running at http://localhost:8000)
"""

import requests
import sys
import time
import json

BASE_URL = "http://localhost:8000"
PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = {"passed": 0, "failed": 0, "total": 0}


def log(test_name: str, passed: bool, detail: str = ""):
    results["total"] += 1
    if passed:
        results["passed"] += 1
        print(f"  {PASS}  {test_name}")
    else:
        results["failed"] += 1
        print(f"  {FAIL}  {test_name} — {detail}")


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ═══════════════════════════════════════════════════════════════════
#  0. HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════
def test_health():
    section("0. Health Check")
    r = requests.get(f"{BASE_URL}/health")
    log("GET /health returns 200", r.status_code == 200)
    data = r.json()
    log("Response contains 'status: healthy'", data.get("status") == "healthy")


# ═══════════════════════════════════════════════════════════════════
#  1. USER REGISTRATION
# ═══════════════════════════════════════════════════════════════════
tokens = {}
user_ids = {}

def test_registration():
    section("1. User Registration")

    users = [
        {"username": "alice_eng", "email": "alice@knowhub.io", "password": "securepass1"},
        {"username": "bob_science", "email": "bob@knowhub.io", "password": "securepass2"},
        {"username": "carol_math", "email": "carol@knowhub.io", "password": "securepass3"},
        {"username": "dave_celeb", "email": "dave@knowhub.io", "password": "securepass4"},
    ]

    for u in users:
        r = requests.post(f"{BASE_URL}/api/v1/auth/register", json=u)
        passed = r.status_code == 200
        if r.status_code == 409:
            # Try to login to get token and user_id
            login_res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"email": u["email"], "password": u["password"]})
            if login_res.status_code == 200:
                passed = True
                data = login_res.json()
                tokens[u["username"]] = data["token"]["access_token"]
                user_ids[u["username"]] = data["user_id"]
        
        log(f"Register/Login '{u['username']}'", passed, f"status={r.status_code}")
        if passed and not tokens.get(u["username"]) and r.status_code == 200:
            data = r.json()
            tokens[u["username"]] = data["token"]["access_token"]
            user_ids[u["username"]] = data["user"]["user_id"]

    # Duplicate registration should fail (409)
    # We delete one user from DB or just register a new duplicate to test 409
    dup_user = {"username": "dup_alice", "email": "alice@knowhub.io", "password": "securepass1"}
    r = requests.post(f"{BASE_URL}/api/v1/auth/register", json=dup_user)
    log("Duplicate registration returns 409", r.status_code == 409, f"status={r.status_code}")


# ═══════════════════════════════════════════════════════════════════
#  2. AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════
def test_authentication():
    section("2. Authentication (Login)")

    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "alice@knowhub.io", "password": "securepass1"
    })
    log("Login with valid credentials", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        log("Token issued on login", "access_token" in data.get("token", {}))

    # Invalid password
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "alice@knowhub.io", "password": "wrongpassword"
    })
    log("Invalid password returns 401", r.status_code == 401, f"status={r.status_code}")

    # Non-existent email
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "nobody@knowhub.io", "password": "anything"
    })
    log("Non-existent email returns 401", r.status_code == 401, f"status={r.status_code}")


# ═══════════════════════════════════════════════════════════════════
#  3. UNAUTHORIZED ACCESS
# ═══════════════════════════════════════════════════════════════════
def test_unauthorized():
    section("3. Unauthorized Access (401)")

    # No token
    r = requests.get(f"{BASE_URL}/api/v1/users/{user_ids.get('alice_eng', 'x')}")
    log("No token returns 401", r.status_code == 401 or r.status_code == 422, f"status={r.status_code}")

    # Invalid token
    r = requests.get(
        f"{BASE_URL}/api/v1/users/{user_ids.get('alice_eng', 'x')}",
        headers={"Authorization": "Bearer fake_token_123"}
    )
    log("Invalid token returns 401", r.status_code == 401, f"status={r.status_code}")


# ═══════════════════════════════════════════════════════════════════
#  4. TOPIC CREATION
# ═══════════════════════════════════════════════════════════════════
def auth_header(username: str) -> dict:
    return {"Authorization": f"Bearer {tokens[username]}"}


def test_topics():
    section("4. Topic Creation & Following")

    topics = [
        {"topic_id": "python", "name": "Python", "description": "Python programming language"},
        {"topic_id": "ml", "name": "Machine Learning", "description": "ML algorithms and frameworks"},
        {"topic_id": "system_design", "name": "System Design", "description": "Distributed systems architecture"},
        {"topic_id": "databases", "name": "Databases", "description": "SQL, NoSQL, and Graph databases"},
    ]

    for t in topics:
        r = requests.post(f"{BASE_URL}/api/v1/topics", json=t, headers=auth_header("alice_eng"))
        log(f"Create topic '{t['name']}'", r.status_code in [200, 409], f"status={r.status_code}")

    # Follow topics
    follows = [
        ("alice_eng", "python"), ("alice_eng", "ml"),
        ("bob_science", "ml"), ("bob_science", "system_design"),
        ("carol_math", "python"), ("carol_math", "databases"),
        ("dave_celeb", "system_design"), ("dave_celeb", "databases"),
    ]

    for username, topic_id in follows:
        r = requests.post(
            f"{BASE_URL}/api/v1/topics/{topic_id}/follow",
            headers=auth_header(username),
        )
        log(f"'{username}' follows topic '{topic_id}'", r.status_code == 200, f"status={r.status_code}")


# ═══════════════════════════════════════════════════════════════════
#  5. USER FOLLOWING (SOCIAL GRAPH)
# ═══════════════════════════════════════════════════════════════════
def test_user_follows():
    section("5. User Following (Social Graph)")

    # Make dave_celeb a celebrity (>= 3 followers)
    for follower in ["alice_eng", "bob_science", "carol_math"]:
        r = requests.post(
            f"{BASE_URL}/api/v1/users/{user_ids['dave_celeb']}/follow",
            headers=auth_header(follower),
        )
        log(f"'{follower}' follows 'dave_celeb'", r.status_code == 200, f"status={r.status_code}")

    # Regular follow
    r = requests.post(
        f"{BASE_URL}/api/v1/users/{user_ids['bob_science']}/follow",
        headers=auth_header("alice_eng"),
    )
    log("'alice_eng' follows 'bob_science'", r.status_code == 200, f"status={r.status_code}")


# ═══════════════════════════════════════════════════════════════════
#  6. USER PROFILE
# ═══════════════════════════════════════════════════════════════════
def test_profile():
    section("6. User Profile")

    r = requests.get(
        f"{BASE_URL}/api/v1/users/{user_ids['alice_eng']}",
        headers=auth_header("alice_eng"),
    )
    log("Get alice profile", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        log("Profile has following_count", "following_count" in data)
        log("Profile has followers_count", "followers_count" in data)
        log("Profile has followed_topics", "followed_topics" in data)
        log(f"  following_count={data.get('following_count')}", data.get("following_count", 0) > 0)

    # Non-existent user
    r = requests.get(
        f"{BASE_URL}/api/v1/users/nonexistent_user",
        headers=auth_header("alice_eng"),
    )
    log("Non-existent user returns 404", r.status_code == 404, f"status={r.status_code}")


# ═══════════════════════════════════════════════════════════════════
#  7. QUESTION POSTING
# ═══════════════════════════════════════════════════════════════════
question_ids = {}

def test_questions():
    section("7. Question Posting (with Feed Fanout)")

    questions = [
        {
            "user": "alice_eng",
            "body": {
                "title": "How does Python garbage collection work?",
                "content": "I want to understand the reference counting and generational GC in CPython. How does the cyclic garbage collector detect unreachable objects?",
                "topic_ids": ["python"],
            },
        },
        {
            "user": "bob_science",
            "body": {
                "title": "Best practices for system design interviews?",
                "content": "What are the key components to cover when designing distributed systems? I'm preparing for FAANG interviews and want to understand capacity estimation and data partitioning.",
                "topic_ids": ["system_design"],
            },
        },
        {
            "user": "dave_celeb",
            "body": {
                "title": "How to design a scalable database sharding strategy?",
                "content": "Consistent hashing vs range-based partitioning for distributed databases. What are the trade-offs and when should each be used?",
                "topic_ids": ["databases", "system_design"],
            },
        },
        {
            "user": "carol_math",
            "body": {
                "title": "Understanding neural network backpropagation",
                "content": "Can someone explain the chain rule and gradient descent optimization in the context of multi-layer perceptrons? I need help with the mathematical derivation.",
                "topic_ids": ["ml"],
            },
        },
    ]

    for q in questions:
        time.sleep(0.05)  # Ensure unique timestamps
        r = requests.post(
            f"{BASE_URL}/api/v1/questions",
            json=q["body"],
            headers=auth_header(q["user"]),
        )
        passed = r.status_code == 200
        log(f"'{q['user']}' posts: '{q['body']['title'][:40]}...'", passed, f"status={r.status_code}")
        if passed:
            data = r.json()
            question_ids[q["user"]] = data["question_id"]


# ═══════════════════════════════════════════════════════════════════
#  8. ANSWER POSTING & RANKING
# ═══════════════════════════════════════════════════════════════════
answer_ids = {}

def test_answers():
    section("8. Answer Posting & Wilson Score Ranking")

    target_q = question_ids.get("alice_eng")
    if not target_q:
        log("SKIP: No question ID for alice_eng", False, "question not created")
        return

    answers = [
        {
            "user": "bob_science",
            "content": "Python uses reference counting as its primary GC mechanism. When an object's reference count drops to zero, it is deallocated immediately. For cyclic references, the generational garbage collector runs periodically.",
        },
        {
            "user": "carol_math",
            "content": "The CPython garbage collector uses three generations. New objects start in Gen 0. After surviving a collection cycle, they move to Gen 1, then Gen 2. The threshold for each generation determines collection frequency.",
        },
        {
            "user": "dave_celeb",
            "content": "Key insight: Python's gc module lets you control the collector. Use gc.get_threshold() to see generation thresholds and gc.collect() to force a collection. In production, you can tune gc.set_threshold() for your workload.",
        },
    ]

    for i, a in enumerate(answers):
        time.sleep(0.05)
        r = requests.post(
            f"{BASE_URL}/api/v1/questions/{target_q}/answers",
            json={"content": a["content"]},
            headers=auth_header(a["user"]),
        )
        passed = r.status_code == 200
        log(f"'{a['user']}' answers alice's question", passed, f"status={r.status_code}")
        if passed:
            data = r.json()
            answer_ids[a["user"]] = data["answer_id"]


# ═══════════════════════════════════════════════════════════════════
#  9. VOTING & REPUTATION
# ═══════════════════════════════════════════════════════════════════
def test_voting():
    section("9. Voting & Reputation Updates")

    target_q = question_ids.get("alice_eng")
    if not target_q or not answer_ids:
        log("SKIP: No question/answer IDs", False, "prerequisites missing")
        return

    # Upvote bob's answer 3 times (different users)
    bob_ans = answer_ids.get("bob_science")
    if bob_ans:
        for voter in ["alice_eng", "carol_math", "dave_celeb"]:
            r = requests.post(
                f"{BASE_URL}/api/v1/questions/{target_q}/answers/{bob_ans}/vote",
                json={"vote_type": "upvote"},
                headers=auth_header(voter),
            )
            log(f"'{voter}' upvotes bob's answer", r.status_code == 200, f"status={r.status_code}")

    # Upvote carol's answer once
    carol_ans = answer_ids.get("carol_math")
    if carol_ans:
        r = requests.post(
            f"{BASE_URL}/api/v1/questions/{target_q}/answers/{carol_ans}/vote",
            json={"vote_type": "upvote"},
            headers=auth_header("alice_eng"),
        )
        log("'alice_eng' upvotes carol's answer", r.status_code == 200, f"status={r.status_code}")

    # Downvote dave's answer once
    dave_ans = answer_ids.get("dave_celeb")
    if dave_ans:
        r = requests.post(
            f"{BASE_URL}/api/v1/questions/{target_q}/answers/{dave_ans}/vote",
            json={"vote_type": "downvote"},
            headers=auth_header("bob_science"),
        )
        log("'bob_science' downvotes dave's answer", r.status_code == 200, f"status={r.status_code}")

    # Verify ranked order
    r = requests.get(f"{BASE_URL}/api/v1/questions/{target_q}")
    if r.status_code == 200:
        data = r.json()
        answers = data.get("answers", [])
        if len(answers) >= 2:
            scores = [a.get("ranking_score", 0) for a in answers]
            log("Answers sorted by Wilson score (descending)", scores == sorted(scores, reverse=True),
                f"scores={[round(s, 4) for s in scores]}")
            log(f"Top answer is bob's (most upvotes)", 
                answers[0].get("author_id") == user_ids.get("bob_science"),
                f"top_author={answers[0].get('author_id')}")
        else:
            log("At least 2 ranked answers", False, f"got {len(answers)}")

    # Check reputation increase for bob
    r = requests.get(
        f"{BASE_URL}/api/v1/users/{user_ids['bob_science']}",
        headers=auth_header("bob_science"),
    )
    if r.status_code == 200:
        rep = r.json().get("reputation", 0)
        log(f"Bob's reputation increased (={rep:.2f})", rep > 1.0)


# ═══════════════════════════════════════════════════════════════════
#  10. COMMENTING
# ═══════════════════════════════════════════════════════════════════
def test_comments():
    section("10. Comments")

    target_q = question_ids.get("alice_eng")
    if not target_q:
        log("SKIP: No question ID", False)
        return

    r = requests.post(
        f"{BASE_URL}/api/v1/questions/{target_q}/comments",
        json={"content": "Great question! I was wondering the same thing about cyclic references."},
        headers=auth_header("bob_science"),
    )
    log("Post comment on question", r.status_code == 200, f"status={r.status_code}")

    r = requests.get(f"{BASE_URL}/api/v1/questions/{target_q}/comments")
    log("Get comments for question", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        log(f"Comment count={data.get('count', 0)}", data.get("count", 0) >= 1)


# ═══════════════════════════════════════════════════════════════════
#  11. FEED (HYBRID PUSH-PULL)
# ═══════════════════════════════════════════════════════════════════
def test_feed():
    section("11. Feed — Hybrid Push-Pull Architecture")

    # Alice follows bob (regular) and dave (celebrity, 3+ followers)
    r = requests.get(f"{BASE_URL}/api/v1/feed", headers=auth_header("alice_eng"))
    log("Get alice's feed", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        feed_items = data.get("data", [])
        count = data.get("count", 0)
        log(f"Feed contains items (count={count})", count > 0)

        # Alice should see:
        # - bob's question (PUSH path — alice follows bob, bob is NOT celebrity)
        # - dave's question (PULL path — dave IS celebrity, alice follows dave)
        # - topic-based pulls for topics alice follows (python, ml)
        feed_author_ids = [item.get("author_id") for item in feed_items]
        log("Feed contains bob's question (Push path)",
            user_ids.get("bob_science") in feed_author_ids,
            f"authors in feed: {feed_author_ids}")
        log("Feed contains dave's question (Pull: celebrity)",
            user_ids.get("dave_celeb") in feed_author_ids,
            f"authors in feed: {feed_author_ids}")


# ═══════════════════════════════════════════════════════════════════
#  12. SEARCH (HYBRID LEXICAL + SEMANTIC)
# ═══════════════════════════════════════════════════════════════════
def test_search():
    section("12. Search — Hybrid Lexical + Semantic Fusion")

    # Exact match search
    r = requests.get(f"{BASE_URL}/api/v1/search", params={"q": "Python garbage collection"})
    log("Search for 'Python garbage collection'", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])
        log(f"Search returned results (count={len(results)})", len(results) > 0)
        if results:
            top_result = results[0]
            log("Top result has search_score", "search_score" in top_result)
            log("Top result has lexical_score", "lexical_score" in top_result)
            log("Top result has semantic_score", "semantic_score" in top_result)
            log("Top result is about Python GC",
                "python" in top_result.get("title", "").lower() or "garbage" in top_result.get("title", "").lower(),
                f"title='{top_result.get('title', '')}'")

    # Semantic search (related concept, not exact words)
    r = requests.get(f"{BASE_URL}/api/v1/search", params={"q": "distributed systems partitioning"})
    log("Semantic search for 'distributed systems partitioning'", r.status_code == 200)
    if r.status_code == 200:
        data = r.json()
        results = data.get("results", [])
        log(f"Semantic results count={len(results)}", len(results) > 0)


# ═══════════════════════════════════════════════════════════════════
#  13. TOPIC RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════
def test_recommendations():
    section("13. Topic Recommendations (Collaborative Filtering)")

    r = requests.get(
        f"{BASE_URL}/api/v1/recommendations/topics",
        headers=auth_header("alice_eng"),
    )
    log("Get topic recommendations for alice", r.status_code == 200, f"status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        recommended = data.get("recommended_topics", [])
        log(f"Recommendations returned (count={len(recommended)})", len(recommended) > 0)
        # Alice follows python, ml. Follows bob (system_design, ml) and dave (system_design, databases)
        # Should recommend: system_design, databases
        log("Recommends 'system_design' (followed by bob & dave)",
            "system_design" in recommended,
            f"recommended={recommended}")
        log("Recommends 'databases' (followed by dave)",
            "databases" in recommended,
            f"recommended={recommended}")


# ═══════════════════════════════════════════════════════════════════
#  14. RATE-LIMIT HEADERS
# ═══════════════════════════════════════════════════════════════════
def test_rate_limit_headers():
    section("14. Rate-Limiting Headers")

    r = requests.get(f"{BASE_URL}/health")
    log("X-RateLimit-Limit header present", "X-RateLimit-Limit" in r.headers,
        f"headers={dict(r.headers)}")
    log("X-RateLimit-Remaining header present", "X-RateLimit-Remaining" in r.headers)


# ═══════════════════════════════════════════════════════════════════
#  RUNNER
# ═══════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  KnowHub API — Integration Test Suite")
    print("=" * 60)

    try:
        requests.get(f"{BASE_URL}/health", timeout=3)
    except requests.ConnectionError:
        print(f"\n  {FAIL}  Cannot connect to {BASE_URL}")
        print("  Make sure the server is running: uvicorn main:app --reload")
        sys.exit(1)

    test_health()
    test_registration()
    test_authentication()
    test_unauthorized()
    test_topics()
    test_user_follows()
    test_profile()
    test_questions()
    test_answers()
    test_voting()
    test_comments()
    test_feed()
    test_search()
    test_recommendations()
    test_rate_limit_headers()

    # Summary
    print(f"\n{'═' * 60}")
    print(f"  RESULTS: {results['passed']}/{results['total']} passed, {results['failed']} failed")
    print(f"{'═' * 60}")

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
