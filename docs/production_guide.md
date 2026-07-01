# Production Deployment & Operation Guide

This document outlines standard practices to deploy and maintain **CloudPilot AI** platforms in production environments.

---

## 1. High Availability Architecture

### A. Compute Multi-Replicas
* **FastAPI APIs:** Scale stateless endpoints to at least 3 replicas across multiple availability zones using Kubernetes Horizontal Pod Autoscaler (HPA).
* **Celery Workers:** Scale workers based on background task queue sizes, mapping dedicated worker pods to heavy workflows.

### B. Probes & Health Checks
* **Liveness Probe:** Configured at `/api/v1/health/health` (FastAPI checking db/redis socket ping). Purges lockups.
* **Readiness Probe:** Configured at `/api/v1/health/health` to confirm socket connections before routing live API users.

---

## 2. Backup & Disaster Recovery

### A. Database Backup Script (cron task)
Execute a nightly snapshot of Postgres:
```bash
pg_dump -h <db_host> -U cloudpilot -d cloudpilot -F c -b -v -f /backups/cloudpilot_$(date +%F).backup
```

### B. Database Restore
Restore state to a target Postgres container:
```bash
pg_restore -h <db_host> -U cloudpilot -d cloudpilot -v /backups/cloudpilot_target.backup
```

---

## 3. Kubernetes Rolling Updates
Deployments utilize standard rolling update strategies to ensure zero-downtime releases:
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```
This guarantees a new pod is provisioned and ready before an old container is terminated.
