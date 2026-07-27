# arXiv-GPT — Production AI Research Assistant

**arXiv-GPT** is a production-grade AI research assistant that automates literature review by retrieving arXiv papers, optimizing search queries using category heuristics, and extracting 6-field structured research insights via **GPT OSS 120B**.

Built as a single unified production service (not a notebook), it compresses hours of paper reading into seconds.

🔗 **Live Demo:** [https://arxiv-gpt.onrender.com/](https://arxiv-gpt.onrender.com/)

---

## ⚙️ System Architecture

```
React Frontend
      ↓
FastAPI Gateway
      ↓
Research Orchestrator (Agent Layer)
      ↓
Optimized arXiv Retrieval (Alias + Category Mapping + LRU Cache)
      ↓
Groq LLM Engine (GPT OSS 120B)
      ↓
Structured JSON Validation (Pydantic) → ReportLab PDF Export
```

Single production container — React build served directly via FastAPI static mounting on Render.

---

## 🚀 Key Features

- **Smart arXiv Retrieval & Query Optimization**:
  - Automated keyword alias expansion (e.g. `RAG`, `LLM`, `Vision`, `Self-Driving`, `TTS`).
  - Category-aware query heuristics mapping topics to primary arXiv domains (`cs.CL`, `cs.CV`, `cs.RO`, `cs.AI`, `cs.SD`, `eess.AS`, `cs.LG`).
  - In-memory **LRU Caching** (`maxsize=32`) to serve instant results for frequent queries.
  - Resilience with exponential backoff retries via **Tenacity**.
- **GPT OSS 120B Summarization Engine**:
  - Powered by Groq's high-throughput `openai/gpt-oss-120b`.
  - Deterministic 6-field JSON schema: `TL;DR`, `Key Contributions`, `Methods`, `Results`, `Why It Matters`, and `Citation`.
- **Guaranteed Output Integrity**:
  - Strict JSON regex extraction with robust exception fallbacks.
- **Publication-Ready PDF Reports**:
  - Instant client-side download of formatted research summaries via ReportLab.
- **Production Architecture**:
  - Modular backend with clear separation of concerns (retrieval, summarization, PDF generation).
  - Clean, responsive React frontend.

---

## 🧠 Tech Stack

| Layer | Technologies |
|---|---|
| **LLM Engine** | **GPT OSS 120B** (`openai/gpt-oss-120b` via Groq) |
| **Backend** | FastAPI, LangChain, Pydantic, Tenacity, ReportLab |
| **Search & Retrieval** | arXiv API, Query Expansion, Category Heuristics, LRU Cache |
| **Frontend** | React, TailwindCSS |
| **Infrastructure** | Docker, Docker Compose, Render |

---

## 📊 Production Evaluation Benchmarks

The system was benchmarked across **20 real-world research queries** spanning 4 domain tiers: NLP, Vision, Agents, and Cross-domain.

### Reliability & Schema Integrity

| Metric | Result |
|---|---|
| Pipeline Reliability | **100%** |
| Schema Validity | **100%** |
| Structured Summary Completeness | **100%** |

### Latency Benchmarks (GPT OSS 120B)

| Metric | Value |
|---|---|
| Avg End-to-End Latency | **21.43s** |
| Median Latency | **21.89s** |
| P90 Latency | **25.06s** |
| P95 Latency | **26.66s** |
| Min / Max | 5.21s / 29.05s |
| Std Dev | 4.53s |

### Tier-wise Latency Breakdown

| Domain Tier | Queries | Avg Latency | Median Latency | P90 Latency |
|---|---|---|---|---|
| **Tier A — NLP** | 7 | **21.37s** | 22.38s | 26.56s |
| **Tier B — Vision** | 5 | **20.91s** | 20.88s | 22.02s |
| **Tier C — Agents** | 4 | **22.59s** | 21.66s | 25.21s |
| **Tier D — Cross-Domain** | 4 | **21.04s** | 20.96s | 22.57s |

*Global latency-length correlation remains near-zero (**r = 0.059**), demonstrating latency is driven by model inference rather than output length.*

### Summary Quality & Compression

- **Avg Total Summary Length**: ~127 words
- **Avg TL;DR Length**: ~16 words
- **Avg Methods Length**: ~31 words
- **Avg Results Length**: ~32 words

---

## 💻 Quickstart & Local Setup

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```
Access the application at `http://localhost:8000`.

### Option 2: Manual Local Setup

1. **Backend**:
   ```bash
   cd backend
   python -m venv venv
   # On Windows: venv\Scripts\activate | On Linux/macOS: source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend** (Development mode):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🧩 What This Project Demonstrates

- Production LLM orchestration with high-capacity models (**GPT OSS 120B**).
- Domain-specific retrieval optimization (query expansion, category filtering, caching).
- Strict schema enforcement and fault-tolerant agent design.
- Full-stack containerization & cloud deployment on Render.
- Comprehensive empirical evaluation and latency characterization.
