# Nexora

Nexora is a local-first AI-powered Financial Scenario Intelligence Engine built with FastAPI, Streamlit, FAISS, Ollama, RAG, multi-agent reasoning, explainability, and risk scoring.

The project analyzes financial scenarios using evidence-grounded retrieval, reasoning pipelines, risk scoring, explainability layers, and collaborative AI agents — fully locally without paid APIs or cloud dependency.

Nexora was built as a production-style end-to-end AI engineering project focused on realistic financial intelligence workflows.

---

# Core Features

* Financial data ingestion pipeline
* Document processing and chunking
* Semantic vector retrieval
* Financial RAG pipeline
* Scenario reasoning engine
* Risk scoring engine
* Explainability and evidence tracing
* Multi-agent collaboration system
* Performance benchmarking and optimization
* Enterprise deployment readiness layer
* Local-first architecture with Ollama

---

# Tech Stack

## Backend

* Python
* FastAPI
* Pydantic
* PyYAML
* Pandas

## Frontend

* Streamlit

## AI / LLM

* Ollama
* Llama 3.1
* Mistral
* DeepSeek
* Qwen
* BGE Embeddings

## Retrieval

* FAISS
* ChromaDB

## Infrastructure

* Local-first architecture
* Modular service design
* YAML configuration system
* Benchmarking & caching
* Explainability pipelines

---

# System Architecture

```text
Financial Data Ingestion
        ↓
Document Processing Pipeline
        ↓
Embedding Generation
        ↓
Vector Database & Retrieval
        ↓
Financial RAG Pipeline
        ↓
Financial Reasoning Engine
        ↓
Risk Scoring Engine
        ↓
Explainability & Evidence Layer
        ↓
AI Agent Collaboration System
        ↓
Performance Optimization Layer
        ↓
Enterprise Deployment Readiness
```

---

# Screenshots

Add screenshots later for:

* Streamlit Dashboard
* RAG Assistant
* Scenario Reasoning
* Risk Scoring
* Explainability
* AI Agent Collaboration
* Performance & Scaling
* Deployment Readiness

---

# Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/Ifthekher237/Nexora.git
cd Nexora
```

## 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Requirements

```bash
pip install -r requirements.txt
```

## 4. Start Ollama

```bash
ollama serve
```

## 5. Pull Recommended Models

```bash
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull qwen2.5:7b
ollama pull deepseek-r1:8b
```

## 6. Run Backend

```bash
./scripts/run_backend.sh
```

## 7. Run Frontend

```bash
./scripts/run_frontend.sh
```

## 8. Open Streamlit

```text
http://localhost:8503
```

---

# Example Workflow

## 1. Ingest Financial Data

```bash
python3 scripts/ingest_sec.py \
  --ticker AAPL \
  --company-name "Apple Inc." \
  --limit 3
```

## 2. Process Documents

```bash
python3 scripts/process_documents.py --limit 10
```

## 3. Build Vector Index

```bash
python3 scripts/build_vector_index.py \
  --limit 100 \
  --vector-store faiss
```

## 4. Ask Financial RAG Question

```bash
python3 scripts/ask_rag.py \
  --question "What financial risks are mentioned in the available documents?" \
  --top-k 5
```

## 5. Run Scenario Reasoning

```bash
python3 scripts/analyze_scenario.py \
  --scenario "What financial risks could appear if interest rates rise?" \
  --top-k 5
```

## 6. Run Risk Scoring

```bash
python3 scripts/score_risk.py \
  --scenario "What financial risks could appear if interest rates rise?" \
  --top-k 5
```

## 7. Run AI Agents

```bash
python3 scripts/run_agents.py \
  --scenario "What financial risks could appear if interest rates rise?" \
  --top-k 5
```

---

# Major System Components

## Phase 1 — Infrastructure Foundation

* FastAPI backend
* Streamlit frontend
* Ollama integration
* YAML configuration system
* Local runtime architecture

## Phase 2 — Financial Data Ingestion

* SEC ingestion
* RSS ingestion
* Local file registration
* Metadata indexing

## Phase 3 — Document Processing Pipeline

* PDF/TXT/Markdown processing
* Text cleaning
* Chunking
* Document classification

## Phase 4 — Vector Database & Retrieval

* BGE embeddings
* FAISS indexing
* Semantic retrieval
* Retrieval benchmarking

## Phase 5 — Financial RAG Pipeline

* Retrieval-augmented generation
* Evidence grounding
* Citation support
* Hallucination guardrails

## Phase 6 — Financial Reasoning Engine

* Scenario reasoning
* Causal chain analysis
* Exposure analysis
* Multi-hop reasoning

## Phase 7 — Risk Scoring Engine

* Evidence-backed risk scoring
* Confidence estimation
* Risk breakdown analysis

## Phase 8 — Explainability & Evidence Layer

* Evidence tracing
* Citation expansion
* Confidence explanation
* Unsupported claim detection

## Phase 9 — Financial Intelligence Interface

* Unified Streamlit dashboard
* Operational UI
* Workflow orchestration

## Phase 10 — AI Agent Collaboration

* Macroeconomic Agent
* Company Analysis Agent
* Sector Analysis Agent
* News Intelligence Agent
* Risk Propagation Agent

## Phase 11 — Performance Optimization & Scaling

* Runtime caching
* Benchmarking
* Resource monitoring
* Performance tracking

## Phase 12 — Enterprise Deployment Architecture

* Deployment readiness checks
* API audit
* Security review
* Governance planning
* Production runbook
* Final reporting system

---

# API Overview

## Core Endpoint Groups

```text
/health
/models
/inference
/ingestion
/processing
/retrieval
/rag
/reasoning
/risk
/explainability
/agents
/performance
/deployment
```

---

# Performance & Optimization

Nexora includes:

* runtime caching
* retrieval caching
* metadata caching
* benchmark history
* latency tracking
* local resource monitoring
* performance status endpoints

Run benchmark:

```bash
python3 scripts/run_performance_benchmark.py \
  --queries "financial risk" "interest rate risk" \
  --top-k 5 \
  --include-rag
```

---

# Deployment Readiness

Nexora includes enterprise-planning support:

* readiness checks
* API audits
* security review
* governance planning
* observability planning
* production runbooks
* final project reporting

Run readiness check:

```bash
python3 scripts/run_deployment_readiness_check.py
```

Generate final report:

```bash
python3 scripts/generate_final_project_report.py
```

---

# Testing

Run the full test suite:

```bash
python3 -m pytest
```

Run final system validation:

```bash
python3 scripts/final_system_check.py
```

---

# Project Goals

Nexora was designed to explore:

* local-first financial AI systems
* evidence-grounded reasoning
* explainable AI pipelines
* AI agent collaboration
* practical LLM engineering
* retrieval-augmented generation
* financial scenario intelligence
* production-style AI architecture

---

# Important Notes

* Nexora is local-first.
* Nexora does not provide financial advice.
* Nexora does not predict stock prices.
* Nexora does not execute trades.
* Nexora is not a production trading system.
* Enterprise deployment is planned, not implemented.
* Ollama must run locally for LLM-powered features.

---

# Current Status

All 12 phases are complete locally.

Nexora can:

* ingest financial data
* process and chunk documents
* generate embeddings
* perform semantic retrieval
* run financial RAG
* reason about financial scenarios
* score risk
* explain outputs
* coordinate AI agents
* benchmark performance
* generate deployment readiness reports

---

# Future Improvements

Potential future directions:

* authentication and RBAC
* cloud deployment
* CI/CD pipelines
* distributed vector storage
* advanced monitoring
* structured audit logging
* portfolio comparison workflows
* multi-company scenario simulation
* enterprise secrets management

---

# Repository Structure

```text
backend/
frontend/
configs/
scripts/
docs/
data/
models/
```

---

# Author

Md Ifthekher Uddin Chy

Macquarie University
Master of Information Technology (Artificial Intelligence)

---

# License

This repository is for educational, research, and portfolio purposes.
