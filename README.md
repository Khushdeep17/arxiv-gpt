
# arXiv-GPT — Production AI Research Assistant

**arXiv-GPT** is a production-grade AI research assistant that automates literature review by retrieving arXiv papers and converting unstructured research text into structured, decision-ready insights using Large Language Models.

Built as a real-world system (not a notebook), it compresses hours of paper reading into minutes.

---

## 🚀 Key Features

- Intelligent arXiv paper retrieval with metadata parsing  
- Structured LLM-driven research summaries (TL;DR, methods, contributions, results, impact)  
- Automated generation of research-ready PDF reports  
- Clean, research-first web interface  
- Modular, production-ready backend architecture  
- Fully containerized with Docker and deployed on Render  

---

## 🧠 Tech Stack

### Backend
- FastAPI  
- LangChain  
- Groq (Llama-3)  
- ReportLab  
- Tenacity  

### Frontend
- React  
- TailwindCSS  

### Infrastructure
- Docker  
- Docker Compose  
- Render (Production Deployment)  

---

## ⚙️ System Architecture

```

React Frontend
↓
FastAPI Gateway
↓
Research Orchestrator
↓
arXiv Retrieval → LLM Summarization → PDF Generation
↓
Structured Research Output

```

Single production service serving both API and frontend with unified deployment.

