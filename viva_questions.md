# KnowHub — System Design Viva Questions & Answers

This document provides a comprehensive set of viva / technical interview questions based on the **System Design Syllabus** and maps them to the actual implementations in **KnowHub**.

---

## Module 1: Fundamentals (Network Protocols, Storage, Metrics)

### Q1: What is the difference between HTTP and WebSockets, and when would you use each?
* **Answer**: HTTP is a stateless, half-duplex request-response protocol over TCP. The client always initiates the connection. WebSockets provide a stateful, full-duplex, persistent TCP connection allowing bidirectional real-time data transfer.
* **KnowHub Mapping**: 
  * HTTP (`main.py` REST endpoints) is used for standard CRUD operations (registration, posting questions, voting).
  * WebSockets (`/api/v1/notifications/ws`) are used for real-time instant notifications (pushing live events when a question or answer is posted).

### Q2: Explain Latency, Throughput, and Availability. How do you measure them in a system?
* **Answer**:
  * **Latency**: The time taken for a single request to be processed (measured in milliseconds).
  * **Throughput**: The number of requests a system can handle per second (RPS) or data processed per second.
  * **Availability**: The percentage of time the system is operational (e.g., 99.9% / "three nines").
* **KnowHub Mapping**: 
  * Measured using Prometheus metrics exposed via `/metrics` using `prometheus_fastapi_instrumentator`.
  * Middleware tracks latency per endpoint (`http_request_duration_seconds_bucket`).

---

## Module 2: Scalability & Caching

### Q3: What is the difference between Horizontal and Vertical scaling?
* **Answer**:
  * **Vertical Scaling (Scale-Up)**: Adding more power (CPU, RAM) to an existing server. It has a hard hardware ceiling and introduces a single point of failure (SPOF).
  * **Horizontal Scaling (Scale-Out)**: Adding more machines to the resource pool. It requires a load balancer but supports linear scaling and high availability.
* **KnowHub Mapping**: Docker and `docker-compose.yml` enable horizontal scaling by spinning up multiple instances of the FastAPI container behind a load balancer (like Nginx/HAProxy).

### Q4: What is Cache Invalidation, and what strategies exist?
* **Answer**: Cache invalidation is the process of updating or clearing cached data when the source database changes. Strategies include:
  * **Write-Through**: Write to cache and DB simultaneously.
  * **Write-Back (Write-Behind)**: Write to cache immediately, write to DB asynchronously.
  * **Cache-Aside (Lazy Loading)**: Read from cache; if miss, read from DB and write to cache.
* **KnowHub Mapping**: `user_service.py` uses the **Cache-Aside** strategy. Profiles are loaded from Cache (`self.cdb.get`). On update (e.g. following a user/topic), the cache is explicitly invalidated (`self.cdb.delete(f"profile:{user_id}")`).

---

## Module 3: Databases & Sharding

### Q5: How do you choose between SQL and NoSQL databases? What are the trade-offs?
* **Answer**:
  * **SQL**: Relational, schema-enforced, supports ACID transactions and complex joins. Best for structured, transactional data (users, billing).
  * **NoSQL**: Schema-less, highly scalable, optimized for key-value, document, column-family, or graph access. Best for unstructured or high-write volume data.
* **KnowHub Mapping**:
  * **SQL (SQLite/PostgreSQL)**: Stores user credentials and topics where schema integrity is critical.
  * **NoSQL (Document Store)**: Answers and comments (highly dynamic structure).
  * **Graph DB**: Follow networks and topics relationships.
  * **Vector DB**: Vector indexing for high-dimensional search.

### Q6: What is Database Sharding? Explain the difference between Horizontal Partitioning and Sharding.
* **Answer**: Horizontal partitioning splits tables inside a single database instance. Sharding distributes partitions across multiple independent database nodes.
* **KnowHub Mapping**: The simulated Cassandra layer (`nosql_db.py`) implements partitioning using a folder-based hash of the partition key (`question_id` or `user_id`) to store data across isolated files.

---

## Module 4: Distributed Systems & Message Queues

### Q7: Explain the CAP Theorem. Which guarantees does KnowHub prioritize?
* **Answer**: CAP states that a distributed database can only guarantee two out of three: Consistency, Availability, and Partition Tolerance.
* **KnowHub Mapping**:
  * The SQL layer (`database/sql_db.py`) enforces strict **Consistency (ACID)**.
  * The NoSQL layer (`database/nosql_db.py`) and Event Bus prioritize **Availability** and **Partition Tolerance (AP)**, settling for eventual consistency via pub/sub events.

### Q8: What is the difference between a Message Queue (e.g. RabbitMQ) and a Message Stream (e.g. Kafka)?
* **Answer**: 
  * **Message Queue**: Message is deleted once consumed (one-to-one). Best for task workers.
  * **Message Stream**: Messages are appended to a log and persisted; consumers maintain their own offsets (replayable, pub/sub).
* **KnowHub Mapping**: `EventBus` (`services/event_bus.py`) implements a **fan-out pub/sub stream architecture**. Multiple subscribers (like WebSocket notification tasks) get their own queues to receive every message.

---

## Module 5: API Design & Microservices

### Q9: Compare REST, GraphQL, and gRPC.
* **Answer**:
  * **REST**: Resource-based (JSON over HTTP/1.1), standardized, caching-friendly, but can suffer from over/under-fetching.
  * **GraphQL**: Single endpoint, client defines the schema. Prevents over-fetching but adds query-parsing overhead.
  * **gRPC**: Protobuf over HTTP/2, contract-first, bi-directional streaming, high performance. Best for inter-service communication.
* **KnowHub Mapping**: External APIs are **RESTful** (using FastAPI). Internal event distribution is asynchronous and event-driven via `EventBus`.

### Q10: What is the Saga Pattern, and why is it used instead of 2PC in Microservices?
* **Answer**: Two-Phase Commit (2PC) is a blocking protocol that reduces availability in distributed systems. The Saga Pattern coordinates local transactions across multiple microservices using compensation events to roll back state if a step fails.
* **KnowHub Mapping**: When a question is posted, `qa_service.py` performs local database writes (SQL + vector + local EventBus pub/sub). If the vector insert fails, a compensation transaction could remove the SQL record.

---

## Module 6: Security

### Q11: How does JWT Authentication work? How do you secure it?
* **Answer**: A JWT contains a Header, Payload, and Signature. It is cryptographically signed (using a secret key) so the client cannot alter its contents.
* **KnowHub Mapping**: In `main.py`, the `_resolve_token` dependency verifies JWTs using `SECRET_KEY` and extracts the `user_id`. WebSockets inspect the `token` query param to authorize connections.

### Q12: How do you implement Rate Limiting?
* **Answer**: Using algorithms like Token Bucket, Leaky Bucket, or Fixed/Sliding Window.
* **KnowHub Mapping**:
  * **HTTP Rate Limiting**: `rate_limit_middleware` in `main.py` uses a sliding window (simulated via in-memory timestamps per IP) to limit requests.
  * **WebSocket Rate Limiting**: Enforces a max of 10 concurrent WebSocket connections per IP to prevent DDoS.

---

## Module 7: Monitoring & Observability

### Q13: What is the difference between Logs, Metrics, and Tracing?
* **Answer**:
  * **Logs**: Timestamped text records of discrete events (good for debugging *why* an error occurred).
  * **Metrics**: Aggregatable numeric data (CPU, memory, request rates) to measure system health.
  * **Tracing**: Tracks the end-to-end path of a request across microservices.
* **KnowHub Mapping**:
  * **Logs**: Structured JSON logging using Loguru in `services/logger.py`.
  * **Metrics**: Prometheus instrumentation exposes `/metrics` for scraping.

---

## Module 8: Design Patterns

### Q14: Identify Design Patterns used in the codebase.
* **Answer**:
  * **Facade Pattern**: Service classes (`UserService`, `QAService`) act as a facade over database engines (SQL, NoSQL, Vector, Graph).
  * **Observer Pattern**: `EventBus` implements the Observer pattern, notifying subscribers when questions or answers are posted.
  * **Singleton Pattern**: The databases (SQL, NoSQL, Vector, Graph) and `EventBus` are managed as singletons or classmethods.
