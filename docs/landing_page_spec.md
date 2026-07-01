# Landing Page Specifications: CloudPilot AI

This spec outlines the wireframe, copy, and styling guidelines for the CloudPilot AI marketing page.

---

## 1. Hero Section
* **Headline:** "Autonomous FinOps & Copilot for Multi-Cloud Operations."
* **Sub-headline:** "Analyze compute resources, scrape telemetry utilization, forecast spend drift, and right-size your cloud footprint safely using local AI agents."
* **Call to Action Buttons:**
  * Primary: "Get Started Free" (Links to `/register`)
  * Secondary: "Read Docs" (Links to docs hub)
* **Visual:** Premium glassmorphism screenshot of the Recharts cost explorer.

---

## 2. Feature Section
A three-column grid detailing key value propositions:
1. **Multi-Cloud Discovery:** Auto-import instances, volumes, databases across AWS, Azure, and GCP via secure API adapters.
2. **Telemetry Aggregations:** Pull CPU/Memory aggregates from Prometheus, CloudWatch, and Datadog automatically.
3. **Right-Sizing Advisor:** Deterministic optimization scans prioritizing cost spikes and unattached storages.
4. **AI DevOps Copilot:** Fully insulated chat agent utilizing local models to advise teams without exposing telemetry.

---

## 3. Pricing Tier
| Tier | Pricing | Features Included |
| :--- | :--- | :--- |
| **Developer** | $0 / mo | 1 Connected Cloud Account, Standard Scans, Chat Access |
| **Growth** | $99 / mo | 5 Cloud Accounts, Scheduled Reports, Basic WebSockets |
| **Enterprise** | Custom | Unlimited Accounts, Dedicated Celery Pools, SSO |

---

## 4. Frequently Asked Questions (FAQ)

### Q: Does the AI layer see my cloud console credentials?
> No. The LLM is completely isolated and only queries local database structures via standard tool schemas.

### Q: How often are optimization recommendations updated?
> Celery background sync tasks execute every 24 hours to refresh inventories and metrics.
