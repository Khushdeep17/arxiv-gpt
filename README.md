# arXiv-GPT — Production AI Research Assistant

**arXiv-GPT** is a production-grade AI research assistant that automates literature review by retrieving arXiv papers and converting unstructured research text into structured, decision-ready insights using Large Language Models.

Built as a real-world system (not a notebook), it compresses hours of paper reading into minutes.

🔗 **Live Demo:** https://arxiv-gpt.onrender.com/ &nbsp;|&nbsp;

---

## ⚙️ System Architecture

```
React Frontend
        ↓
FastAPI Gateway
        ↓
Research Orchestrator (Agent Layer)
        ↓
arXiv Retrieval → LLM Summarization → Structured Output
```

Single production service — React build served via FastAPI static mount, deployed as one unified container.

---

## 🚀 Key Features

- Intelligent arXiv paper retrieval with structured metadata parsing
- LLM-driven research summaries with **4-field deterministic schema**: TL;DR, Key Contributions, Methods, Results
- Strict **JSON schema enforcement** with Pydantic validation and fallback guards
- Research-ready PDF report generation via ReportLab
- Modular backend with clean service boundaries (agent, retrieval, summarizer, PDF)
- Retry logic via Tenacity for resilient external API calls
- Clean, research-first React frontend — no business logic on client side

---

## 🧠 Tech Stack

| Layer | Technologies |
|---|---|
| Backend | FastAPI, LangChain, Groq (Llama-3), Tenacity, ReportLab |
| Frontend | React, TailwindCSS |
| Infrastructure | Docker, Docker Compose, Render |

---

## 🐳 Deployment

- Unified Dockerized architecture — single container, single port
- React build compiled into FastAPI static folder at build time
- Environment-secured API keys via Render config
- Stateless backend — fully production-safe
- Publicly accessible at: https://arxiv-gpt.onrender.com/

---

## 📊 Production Evaluation

The system was benchmarked across **20 real-world research queries** spanning 4 complexity tiers: NLP, Vision, Agents, and Cross-domain.

### Reliability & Robustness

| Metric | Result |
|---|---|
| Pipeline Reliability | **100%** |
| Schema Validity | **100%** |
| Structured Summary Completeness | **100%** |

### Latency Benchmarks

| Metric | Value |
|---|---|
| Avg End-to-End Latency | **7.11s** |
| Median Latency | 9.01s |
| P90 Latency | 10.11s |
| P95 Latency | **10.74s** |
| Std Dev | 3.19s |
| Min / Max | 3.07s / 10.76s |
| IQR Outliers | **0** |

### Tier-wise Latency Breakdown

| Domain Tier | Queries | Avg Latency |
|---|---|---|
| A — NLP | 7 | 3.45s |
| B — Vision | 5 | 7.79s |
| C — Agents | 4 | 9.67s |
| D — Cross-domain | 4 | 10.11s |

Latency scales with query complexity — inference-dominated, not output-size-dependent (global latency-length correlation: **r = 0.005**).

### Summary Quality

- Average total summary length: ~148 words
- Average TL;DR length: ~23 words
- Average papers retrieved per query: 3

---

## 🧩 What This Project Demonstrates

- AI workflow orchestration and agentic system design
- Deterministic LLM output enforcement at scale
- Production-grade FastAPI backend engineering
- Full-stack containerized deployment
- Latency characterization and reliability benchmarking

