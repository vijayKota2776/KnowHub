# KnowHub — Production-Grade Knowledge Sharing Platform

KnowHub is an advanced, production-grade knowledge-sharing platform (combining features of Stack Overflow and Quora) built using **FastAPI** (Python) and **React** (Vite + JavaScript). 

It is designed to demonstrate full-stack software architecture, multi-database persistence (Polyglot Persistence), hybrid search, high-throughput caching, real-time message distribution (WebSockets), and observability.

---

## 🛠️ Tech Stack & Architecture

```
                       ┌─────────────────────────────────────────────────────────────┐
                       │                     FastAPI Ingress Gateway                 │
                       │               (CORS, Rate Limiting, JWT Auth)               │
                       ├────────────┬────────────┬──────────────┬────────────────────┤
                       │ UserService│ QAService  │ FeedService  │ SearchService      │
                       ├────────────┴────────────┴──────────────┴────────────────────┤
                       │  SQLite      File JSON     Graph JSON     TF-IDF Vector     │
                       │  (PostgreSQL) (Cassandra)  (Neo4j)        (Qdrant)          │
                       └─────────────────────────────────────────────────────────────┘
```

- **Backend Gateway**: FastAPI (routing, validation, middleware, rate-limiting, and lifespans).
- **Frontend App**: React (Vite, single-page router, clean CSS styling, Toast systems, dynamic rendering).
- **Databases (Polyglot Persistence)**:
  - **SQL (SQLite)**: Credentials, metadata, topics.
  - **NoSQL (JSON Store)**: Partitioned answers and comments.
  - **Graph DB (JSON List)**: Social follows and subscriptions.
  - **Vector DB (TF-IDF)**: Text vectorization and search.
- **Real-Time Layer**: Asynchronous EventBus (fan-out pub/sub) & WebSockets.
- **Monitoring**: Prometheus instrumentation & structured JSON logging (Loguru).

---

## 📂 Project Directories

- [main.py](file:///Users/vijaykota/Documents/KnowHub/main.py) — API Gateway, endpoints, and websocket connections.
- [database/](file:///Users/vijaykota/Documents/KnowHub/database/) — Database adapters (SQL, NoSQL, Graph, Vector).
- [services/](file:///Users/vijaykota/Documents/KnowHub/services/) — Business logic facades (User, QA, Feed, Search).
- [frontend/](file:///Users/vijaykota/Documents/KnowHub/frontend/) — Single-page React user interface.
- [tests/](file:///Users/vijaykota/Documents/KnowHub/tests/) — Pytest suite covering all core layers.
- [docker-compose.yml](file:///Users/vijaykota/Documents/KnowHub/docker-compose.yml) — Containerized deployment.
- [knowhub.docx](file:///Users/vijaykota/Documents/KnowHub/knowhub.docx) — Detailed Word documentation.

---

## 🚀 How to Run Locally

### 1. Prerequisite Setup
Ensure you have **Python 3.12+** and **Node.js 18+** installed.

Clone the repository locally:
```bash
git clone https://github.com/vijayKota2776/KnowHub.git
cd KnowHub
```

Configure your local environments:
```bash
cp .env.example .env
```

---

### 2. Start the Backend Server
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
2. Install python requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the uvicorn development server:
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
4. Access the API documentation at: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI).

---

### 3. Start the Frontend App
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to: [http://localhost:5173](http://localhost:5173).

---

### 4. Running the Test Suite
Ensure the backend is not running or runs on a separate database. Execute:
```bash
pytest tests/ -v
```

---

## 🐳 Run with Docker (Recommended)

To run the backend, database storage, and Prometheus sidecar collectively inside container networks:
```bash
docker compose up --build -d
```
- **Backend API**: `http://localhost:8000`
- **Prometheus Dashboard**: `http://localhost:9090`
- **Metrics Scraping endpoint**: `http://localhost:8000/metrics`
