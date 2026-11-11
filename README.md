# arXiv-GPT — Production AI Research Assistant

[![CI](https://github.com/Khushdeep17/arxiv-gpt/actions/workflows/ci.yml/badge.svg)](https://github.com/Khushdeep17/arxiv-gpt/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon.tech-336791?logo=postgresql&logoColor=white)](https://neon.tech)
[![Groq](https://img.shields.io/badge/LLM-GPT_OSS_120B_(Groq)-F55036)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ED?logo=docker&logoColor=white)](https://www.docker.com)

**arXiv-GPT** is a full-stack, production-grade AI research assistant that automates academic literature reviews. It retrieves papers from the official arXiv repository, optimizes queries through category heuristics and domain alias expansion, extracts 6-field structured research insights via **GPT OSS 120B** on Groq, and persists user search history in a scalable **PostgreSQL (Neon)** database with **JWT-based authentication**.

Packaged as a **single, unified multi-stage Docker container**, the compiled React frontend is mounted and served directly through the FastAPI gateway, making it 100% compatible with modern container platforms like **Render**, **Railway**, or on-premise Docker hosts.

🔗 **Live Deployment:** [https://arxiv-gpt.onrender.com/](https://arxiv-gpt.onrender.com/)

---

## ⚙️ System Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │               Client Browser                 │
                    │        (React 18 + Tailwind CSS SPA)         │
                    └──────────────────────┬───────────────────────┘
                                           │ HTTP / JSON
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Unified FastAPI Gateway                              │
│                                                                                  │
│   ┌─────────────────────┐       ┌──────────────────────┐       ┌─────────────┐   │
│   │   Auth & Security   │       │  Static Asset Host   │       │ Health API  │   │
│   │ (JWT / Argon2-cffi) │       │ (SPA Fallback / CSS) │       │   /health   │   │
│   └──────────┬──────────┘       └──────────────────────┘       └─────────────┘   │
│              │                                                                   │
│              ▼                                                                   │
│   ┌────────────────────────────────────────────────────────┐                     │
│   │                 Research Agent Orchestrator            │                     │
│   └──────────┬─────────────────────────────────┬───────────┘                     │
│              │                                 │                                 │
│              ▼                                 ▼                                 │
│   ┌───────────────────────────┐     ┌────────────────────────────┐               │
│   │   arXiv Retrieval Engine  │     │   Groq LLM Inference       │               │
│   │   • Category Heuristics   │     │   • GPT OSS 120B           │               │
│   │   • Alias Expansion       │     │   • 6-Field JSON Contract  │               │
│   │   • In-Memory LRU Cache   │     │   • Pydantic V2 Validation │               │
│   │   • Tenacity Retry Logic  │     └──────────────┬─────────────┘               │
│   └───────────────────────────┘                    │                             │
│                                                    ▼                             │
│                                     ┌────────────────────────────┐               │
│                                     │   ReportLab PDF Exporter   │               │
│                                     └────────────────────────────┘               │
└──────────────────────────────────────────┬───────────────────────────────────────┘
                                           │ SQLAlchemy 2.0 (psycopg v3)
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │          PostgreSQL Database (Neon)          │
                    │   • Users (Scoped Auth)                      │
                    │   • Search Queries & Canonical Papers (M2M)  │
                    │   • Automated Alembic Migrations on Boot     │
                    └──────────────────────────────────────────────┘
```

---

## 🚀 Key Capabilities & Upgraded Features

### 1. Full-Stack JWT Authentication & Scoped Persistence
- **Secure Password Hashing:** Powered by **Argon2id** (`argon2-cffi`), the industry-standard memory-hard password derivation algorithm.
- **Stateless Session Tokens:** Cryptographically signed **HMAC-SHA256 Bearer JWTs** with configurable expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **User Scoping:** Every search query, paper association, and PDF report is securely linked to the authenticated user's account.
- **Protected Endpoints:** Strict dependency injection (`get_current_user`) guards search history and account routes.

### 2. Intelligent arXiv Retrieval & Query Expansion
- **Domain Alias Normalization:** Heuristic keyword expansion maps common research topics to specific taxonomy terms (e.g. `RAG`, `LLM`, `Vision`, `Self-Driving`, `TTS`).
- **Category-Aware Routing:** Filters queries into primary arXiv taxonomy domains (`cs.CL`, `cs.CV`, `cs.RO`, `cs.AI`, `cs.SD`, `eess.AS`, `cs.LG`).
- **In-Memory LRU Caching:** High-speed caching (`maxsize=32`) eliminates redundant arXiv network requests for identical queries.
- **Fault-Tolerant Retries:** Uses **Tenacity** exponential backoff to handle transient arXiv API rate limits and connection hiccups.

### 3. Structured LLM Summarization (GPT OSS 120B)
- **High-Throughput Inference:** Connects to Groq's low-latency inference engine utilizing `openai/gpt-oss-120b`.
- **Deterministic 6-Field Contract:**
  1. `TL;DR`: Concise one-sentence overview.
  2. `Key Contributions`: Bulleted core novelties and discoveries.
  3. `Methods`: Architectural and algorithmic techniques employed.
  4. `Results`: Quantitative metrics, benchmarks, and performance improvements.
  5. `Why It Matters`: Practical impact on machine learning and real-world deployment.
  6. `Citation`: Standardized academic citation format.
- **Guaranteed Output Schema:** Dual-layer extraction via regex pattern matching and **Pydantic V2** validation with graceful fallback handling.

### 4. Relational Data Architecture & Alembic Migrations
- **Canonical Paper De-duplication:** Papers are stored canonically by unique `arxiv_id`. Searches share paper records via a many-to-many junction table (`query_paper_association`), preventing database bloat.
- **Automated Startup Migrations:** The production container automatically runs `alembic upgrade head` upon boot, ensuring zero manual database setup on fresh cloud databases (e.g. **Neon**, **Supabase**).

### 5. Publication-Ready PDF Reports
- Built-in **ReportLab** rendering engine converts structured summaries into clean, formatted research briefs available for instant download.

### 6. Modern Redesigned UI
- **Responsive Layout:** Built with React 18, Tailwind CSS, and Lucide icons.
- **Authentication Pages:** Polished `/login` and `/register` flows with real-time field validation and human-readable API error feedback.
- **Interactive History Sidebar:** Browse past research sessions with one-click reload.

---

## 🧠 Tech Stack

| Domain | Technology / Library | Role |
| :--- | :--- | :--- |
| **Frontend** | React 18, React Router v6, Tailwind CSS, Lucide Icons, Axios | Single-Page Application (SPA) UI |
| **Backend** | FastAPI, Starlette, Uvicorn | High-performance asynchronous REST API |
| **Authentication** | PyJWT, Argon2-cffi | Password hashing & stateless JWT token validation |
| **Database** | PostgreSQL (Neon.tech / Supabase), SQLAlchemy 2.0, psycopg v3 | Relational persistence & connection pooling |
| **Migrations** | Alembic | Version-controlled declarative schema migrations |
| **LLM Inference** | Groq API (`openai/gpt-oss-120b`) | High-speed paper analysis and insight extraction |
| **PDF Generation**| ReportLab | Automated research report compilation |
| **Testing** | Python `unittest` (96 tests), Jest + React Testing Library (38 tests) | Full-suite test coverage across backend & frontend |
| **Deployment** | Docker (Multi-stage), Render (Free Web Service) | Production build & automated cloud hosting |

---

## 🗄️ Database Schema

The database model is normalized and managed through **SQLAlchemy 2.0**:

```mermaid
erDiagram
    USERS ||--o{ SEARCH_QUERIES : executes
    SEARCH_QUERIES ||--|{ QUERY_PAPER_ASSOCIATION : contains
    PAPERS ||--|{ QUERY_PAPER_ASSOCIATION : referenced_by

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        datetime created_at
    }

    SEARCH_QUERIES {
        uuid id PK
        uuid user_id FK
        string query
        datetime timestamp
        string pdf_filename
    }

    PAPERS {
        uuid id PK
        string arxiv_id UK
        string title
        text abstract
        text authors
        string published_date
        string pdf_url
        text tldr
        text key_contributions
        text methods
        text results
        text why_it_matters
        text citation
        datetime created_at
    }

    QUERY_PAPER_ASSOCIATION {
        uuid query_id PK, FK
        uuid paper_id PK, FK
        integer rank_position
    }
```

---

## 📊 Production Evaluation Benchmarks

The system was benchmarked across **20 real-world research queries** spanning 4 domain tiers: NLP, Vision, Agents, and Cross-domain.

### Reliability & Schema Integrity

| Metric | Result |
| :--- | :--- |
| Pipeline Reliability | **100%** |
| Schema Validity | **100%** |
| Structured Summary Completeness | **100%** |

### Latency Benchmarks (GPT OSS 120B on Groq)

| Metric | Value |
| :--- | :--- |
| **Avg End-to-End Latency** | **21.43s** |
| **Median Latency** | **21.89s** |
| **P90 Latency** | **25.06s** |
| **P95 Latency** | **26.66s** |
| **Min / Max Latency** | 5.21s / 29.05s |
| **Standard Deviation** | 4.53s |

### Tier-wise Latency Breakdown

| Domain Tier | Queries | Avg Latency | Median Latency | P90 Latency |
| :--- | :---: | :---: | :---: | :---: |
| **Tier A — NLP** | 7 | **21.37s** | 22.38s | 26.56s |
| **Tier B — Vision** | 5 | **20.91s** | 20.88s | 22.02s |
| **Tier C — Agents** | 4 | **22.59s** | 21.66s | 25.21s |
| **Tier D — Cross-Domain** | 4 | **21.04s** | 20.96s | 22.57s |

*Global latency-length correlation remains near-zero (**r = 0.059**), demonstrating latency is driven by model inference rather than output length.*

---

## 🛠️ API Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/auth/register` | Register a new user (`email`, `password`, `full_name`) | No |
| `POST` | `/auth/login` | Authenticate credentials and receive Bearer JWT token | No |
| `GET` | `/auth/me` | Fetch currently authenticated user profile | **Yes (Bearer)** |

### Research & Operations Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/search` | Retrieve papers, generate LLM summary, persist query & results | **Yes (Bearer)** |
| `GET` | `/history` | Fetch search history with papers scoped to current user | **Yes (Bearer)** |
| `GET` | `/download_pdf` | Download generated PDF research report by filename | No |
| `GET` | `/health` | Service uptime and health check probe (`{"status":"ok"}`) | No |

---

## 💻 Local Setup & Development

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and `npm`
- **Groq API Key** ([Free sign-up](https://console.groq.com/keys))

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/Khushdeep17/arxiv-gpt.git
cd arxiv-gpt

# Copy example environment configuration
cp .env.example .env
```

Edit `.env` and fill in your keys:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
JWT_SECRET_KEY=your_generated_random_secret_key_here_min_32_chars
# In local development, DATABASE_URL can be left blank to automatically default to SQLite!
```

---

### Option A: Docker Compose (Full-Stack + PostgreSQL)

The easiest way to run the full application with a local PostgreSQL database:

```bash
docker-compose up --build
```
- App UI & API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

---

### Option B: Manual Local Setup (Separated Dev Servers)

#### 1. Backend:
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend:
```bash
cd frontend
npm install
npm start
```
Frontend development server opens at `http://localhost:3000` with API calls automatically proxied to port `8000`.

---

## 🧪 Running Automated Tests

The repository maintains comprehensive test suites for both frontend and backend.

### Backend Test Suite (96 Tests)
Covers authentication, password hashing, JWT expiration, database safety guards, query expansion, and persistence:
```bash
cd backend
python -m unittest discover -s app/tests -v
```

### Frontend Test Suite (38 Tests)
Covers AuthContext, protected routes, form submission, error handling, and API integration:
```bash
cd frontend
npm test -- --watchAll=false
```

---

## ☁️ Deployment Guide (100% Free on Render + Neon)

This project is optimized to run **100% free with lifetime persistence**:
- **Database:** [Neon.tech](https://neon.tech/) Serverless PostgreSQL (Free tier, no 30-day expiration).
- **Web Service:** [Render.com](https://render.com/) Free Tier Web Service (Docker container).

### 1. Create Free Database on Neon
1. Go to [Neon.tech](https://neon.tech/) and sign in with GitHub.
2. Click **Create Project** (Name: `arxiv-gpt-db`).
3. Copy your connection string from the dashboard:
   ```text
   postgresql://username:password@ep-xyz.region.neon.tech/neondb?sslmode=require
   ```

### 2. Deploy Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
2. Connect your `arxiv-gpt` repository.
3. Configure the service settings:
   - **Name:** `arxiv-gpt`
   - **Region:** Any (e.g. Oregon / Frankfurt / Singapore)
   - **Branch:** `main`
   - **Root Directory:** *(Leave EMPTY / BLANK — do not specify backend)*
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `Dockerfile`
   - **Instance Type:** `Free ($0/mo)`
4. In the **Environment Variables** section, add the following 4 variables:

| Key | Example Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` | Neon PostgreSQL connection string |
| `JWT_SECRET_KEY` | `your_32_character_random_secret_string` | Secret key for JWT signature validation |
| `GROQ_API_KEY` | `gsk_...` | Groq API key for LLM summarization |
| `CORS_ORIGINS` | `https://arxiv-gpt.onrender.com` | Your service URL on Render |

5. Click **Create Web Service**.

> **Note on Migrations:** You do **not** need to run migrations manually! The multi-stage `Dockerfile` automatically executes `alembic upgrade head` before starting the web server. Tables in your Neon database are created and updated on every deployment.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
