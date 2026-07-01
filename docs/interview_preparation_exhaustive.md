# Exhaustive Interview Q&A Sheet

This document compiles common interview questions and answers across multiple technical dimensions.

---

## 1. DevOps & Release Management Questions

### Q: Explain the rolling update deployment strategy.
> **Answer:** In Kubernetes, `RollingUpdate` replaces pods one-by-one with new versions. We configure `maxSurge: 1` (adds one pod) and `maxUnavailable: 0` (keeps all old pods online until the new pod passes readiness checks). This ensures zero downtime.

### Q: What is GitOps, and why did you use ArgoCD?
> **Answer:** GitOps defines git as the single source of truth for infrastructure. ArgoCD monitors the repository for manifest updates and automatically applies the configurations to the target Kubernetes cluster, ensuring drift correction.

---

## 2. System Design & Database Questions

### Q: Why did you use PostgreSQL and Redis instead of a single database?
> **Answer:** PostgreSQL is a relational database ensuring strict transaction safety (ACID) for financial data and configurations. Redis is an in-memory key-value cache database used to handle Celery queue brokerage and cache complex dashboard charts.

### Q: Explain how connection pooling improves database performance.
> **Answer:** Creating database TCP connections on every query is slow. Connection pooling pre-allocates a set of active connections (using `asyncpg` pools) and reuse them, bypassing handshake overhead.

---

## 3. Kubernetes & Cloud Architecture Questions

### Q: What is the difference between HPA and VPA?
> **Answer:** Horizontal Pod Autoscaler (HPA) adds or removes pod replicas based on CPU/Memory loads. Vertical Pod Autoscaler (VPA) changes resource requests and limits parameters on existing pods.

### Q: What are Pod Disruption Budgets (PDBs)?
> **Answer:** PDBs ensure a minimum number of pod replicas remain online during node maintenance or cluster upgrades, preventing downtime.

---

## 4. AI & Agent Integration Questions

### Q: How does the AI Copilot execute tool-calling sequences?
> **Answer:** The orchestrator service parses the LLM output. If the LLM requests a tool (e.g. `list_resources`), the orchestrator calls the local tool adapter, gets the JSON data, and submits it back to the LLM to write the explanation.

### Q: How do you protect the LLM against prompt injection?
> **Answer:** We enforce strict schema formats on user inputs via Pydantic and limit the LLM context size to prevent overflow exploits.
