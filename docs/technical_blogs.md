# Technical Blogs & Project Memos

This series details the design guidelines and code lessons gathered during the development of CloudPilot.

---

## Blog 1: How I Built CloudPilot AI

Building a production-ready DevOps dashboard requires managing multiple container connections, database pings, and dashboard charts. We built **CloudPilot AI** as an asynchronous microservice stack:
* **FastAPI Backend:** Orchestrated via `asyncio` for non-blocking I/O queries.
* **Celery Workers:** Task queues process background resource discoveries and billing records scrapers.
* **React Web Frontend:** Styled with a premium dark-mode theme utilizing Recharts.

---

## Blog 2: Designing a Cloud-Agnostic DevOps Platform

To support future providers (like Oracle Cloud) without changes to core business flows, we leveraged the **Adapter Pattern**:
1. Defined `CloudProviderAdapter` class detailing expected parameters (`connect`, `discover_resources`).
2. Implemented concrete adapters registering to a central factory registry.
3. The API and service layers query only the adapter factories, meaning adding a new provider requires writing a single file.

---

## Blog 3: Building an AI DevOps Copilot

Conventional AI chat configurations often suffer from security vulnerabilities or cost hallucinations. We solved this by designing a **decoupled tool-calling sequence**:
* The LLM has **no direct cloud access**.
* The LLM parses user queries and outputs a target tool declaration (e.g. `get_billing_summary`).
* The local service layer captures this call, queries the database, and returns JSON blocks back to the LLM to format the response.
* Citations metadata are appended to the response, allowing users to verify telemetry sources.

---

## Blog 4: Lessons from Building a Multi-Cloud FinOps Platform

Building multi-cloud financial pipelines taught us three core lessons:
1. **Data Normalization:** Providers log billing items in completely different structures. Normalizing everything into a single model (`BillingRecord`) is critical.
2. **Asynchronous Scheduling:** Scraping APIs is slow. Offloading these tasks to Celery prevents API thread locks.
3. **Caching:** Users reload pages frequently. Storing aggregated charts contexts in Redis prevents database bottlenecks.
