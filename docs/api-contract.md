# API Contract Specification

This document details the REST API contracts for **CloudPilot AI**.

---

## 1. Global API Standards

* **Base URL:** `/api/v1`
* **Content Type:** `application/json`
* **Response Status Codes:**
  * `200 OK`: Request succeeded.
  * `201 Created`: Resource creation succeeded.
  * `202 Accepted`: Asynchronous operation accepted.
  * `400 Bad Request`: Input validation failed.
  * `401 Unauthorized`: Authentication missing or token expired.
  * `403 Forbidden`: Insufficient RBAC permission scopes.
  * `404 Not Found`: Resource does not exist.
  * `429 Too Many Requests`: Rate limit threshold exceeded.
  * `500 Internal Server Error`: Backend error.

---

## 2. Authentication Domain

### POST /auth/register
Registers a new platform user.
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "organization_name": "Acme Corp"
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "user_id": "c37b42aa-d45e-49b2-9ffb-14ab6b5862b2",
    "email": "user@example.com",
    "organization_id": "142c9823-c9a1-432d-88b9-bb230f81a7b4",
    "created_at": "2026-06-30T10:00:00Z"
  }
  ```

### POST /auth/login
Authenticates a user and issues security tokens.
* **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
* **Response (200 OK):**
  * *Headers:* `Set-Cookie: refresh_token=UUID_VALUE; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh`
  * *Body:*
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
      "token_type": "Bearer",
      "expires_in": 900
    }
    ```

### POST /auth/refresh
Refreshes an expired access token using the HTTP-Only cookie.
* **Request Body:** None (reads refresh token from HTTP-Only cookie).
* **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "Bearer",
    "expires_in": 900
  }
  ```

### POST /auth/logout
Invalidates the current session and revokes the refresh token.
* **Request Body:** None.
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Session terminated successfully."
  }
  ```

---

## 3. Cloud Accounts Domain

### POST /cloud/connect
Links a cloud integration to a workspace project.
* **Request Body:**
  ```json
  {
    "project_id": "848e02d6-4444-48f5-bcbb-b6a38ac4773c",
    "provider_id": "aws",
    "name": "Production Account",
    "account_identifier": "123456789012",
    "credentials": {
      "role_arn": "arn:aws:iam::123456789012:role/CloudPilotAccessRole",
      "external_id": "a9db58-c910-34ad-989d"
    },
    "settings": {
      "regions": ["us-east-1", "eu-west-1"]
    }
  }
  ```
* **Response (202 Accepted):**
  ```json
  {
    "cloud_account_id": "3bb609b4-b91c-4b6e-b3f5-bbad7b11c9bb",
    "status": "CONNECTING",
    "job_id": "887a02bc-b8b8-40cf-b1c1-456cb08c2a3e"
  }
  ```

### GET /cloud/accounts
Fetches registered accounts in the selected project workspace.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
* **Response (200 OK):**
  ```json
  [
    {
      "cloud_account_id": "3bb609b4-b91c-4b6e-b3f5-bbad7b11c9bb",
      "provider_id": "aws",
      "name": "Production Account",
      "account_identifier": "123456789012",
      "status": "CONNECTED",
      "created_at": "2026-06-30T10:00:00Z"
    }
  ]
  ```

### DELETE /cloud/account/{id}
Removes a cloud integration.
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Cloud account integration removed successfully."
  }
  ```

### GET /cloud/providers
Lists supported cloud platforms.
* **Response (200 OK):**
  ```json
  [
    { "id": "aws", "name": "Amazon Web Services", "is_active": true },
    { "id": "azure", "name": "Microsoft Azure", "is_active": true },
    { "id": "gcp", "name": "Google Cloud Platform", "is_active": true }
  ]
  ```

---

## 4. Monitoring Domain

### POST /monitoring/connect
Links a monitoring integration to a workspace project.
* **Request Body:**
  ```json
  {
    "project_id": "848e02d6-4444-48f5-bcbb-b6a38ac4773c",
    "provider_id": "datadog",
    "name": "Datadog US Production",
    "endpoint_url": "https://api.datadoghq.com",
    "credentials": {
      "api_key": "dd_api_key_plaintext",
      "application_key": "dd_app_key_plaintext"
    }
  }
  ```
* **Response (201 Created):**
  ```json
  {
    "monitoring_source_id": "fbc8110b-88a2-4a0b-99d8-c9ab7b09b11b",
    "status": "ACTIVE"
  }
  ```

### GET /monitoring/providers
Lists supported metrics platforms.
* **Response (200 OK):**
  ```json
  [
    { "id": "prometheus", "name": "Prometheus", "is_active": true },
    { "id": "cloudwatch", "name": "AWS CloudWatch", "is_active": true },
    { "id": "azure_monitor", "name": "Azure Monitor", "is_active": true },
    { "id": "datadog", "name": "Datadog", "is_active": true }
  ]
  ```

### GET /monitoring/status
Returns health check status values for monitoring integrations.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
* **Response (200 OK):**
  ```json
  [
    {
      "monitoring_source_id": "fbc8110b-88a2-4a0b-99d8-c9ab7b09b11b",
      "name": "Datadog US Production",
      "status": "ACTIVE",
      "last_health_check": "2026-06-30T10:15:00Z"
    }
  ]
  ```

---

## 5. Resources Domain

### GET /resources
Lists discovered resources.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
  * `provider` `VARCHAR` (Optional, e.g. aws)
  * `type` `VARCHAR` (Optional, e.g. virtual_machine)
  * `limit` `INT` (Default: 50)
  * `offset` `INT` (Default: 0)
* **Response (200 OK):**
  ```json
  {
    "total_count": 1,
    "resources": [
      {
        "id": "e331c923-3b10-4aa1-bb99-db0b91ab4aa3",
        "cloud_account_id": "3bb609b4-b91c-4b6e-b3f5-bbad7b11c9bb",
        "external_id": "arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789abcdef0",
        "name": "prod-api-server",
        "resource_type": "virtual_machine",
        "region": "us-east-1",
        "status": "running",
        "tags": {
          "Environment": "Production",
          "Owner": "DevOps"
        },
        "specification": {
          "instance_type": "m6g.xlarge",
          "vcpu_count": 4,
          "memory_gb": 16.0
        }
      }
    ]
  }
  ```

### GET /resources/{id}
Retrieves detailed information for a single resource.
* **Response (200 OK):**
  ```json
  {
    "id": "e331c923-3b10-4aa1-bb99-db0b91ab4aa3",
    "cloud_account_id": "3bb609b4-b91c-4b6e-b3f5-bbad7b11c9bb",
    "external_id": "arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789abcdef0",
    "name": "prod-api-server",
    "resource_type": "virtual_machine",
    "region": "us-east-1",
    "status": "running",
    "tags": {
      "Environment": "Production"
    },
    "specification": {
      "instance_type": "m6g.xlarge",
      "vcpu_count": 4,
      "memory_gb": 16.0,
      "operating_system": "linux",
      "lifecycle": "ON_DEMAND"
    },
    "created_at": "2026-06-25T12:00:00Z"
  }
  ```

### GET /resources/filter
Executes complex tag or query logic on resource attributes.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
  * `query_string` `VARCHAR` (Required, e.g. "tags.Environment=Production AND specification.vcpu_count>=4")
* **Response (200 OK):** Same list structure as `GET /resources`.

---

## 6. Billing Domain

### GET /billing/summary
Returns aggregated cost data for dashboards.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
  * `start_date` `DATE` (Required)
  * `end_date` `DATE` (Required)
* **Response (200 OK):**
  ```json
  {
    "total_cost": 4500.50,
    "currency": "USD",
    "by_provider": {
      "aws": 3000.20,
      "azure": 1500.30
    },
    "by_category": {
      "Compute": 2500.00,
      "Storage": 1200.50,
      "Database": 800.00
    }
  }
  ```

### GET /billing/history
Returns cost trends over time.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
  * `interval` `VARCHAR` (Required, options: `daily`, `monthly`)
  * `start_date` `DATE` (Required)
  * `end_date` `DATE` (Required)
* **Response (200 OK):**
  ```json
  {
    "interval": "daily",
    "history": [
      {
        "date": "2026-06-01",
        "cost": 150.00,
        "currency": "USD"
      },
      {
        "date": "2026-06-02",
        "cost": 152.50,
        "currency": "USD"
      }
    ]
  }
  ```

### GET /billing/resource/{id}
Retrieves billing history records mapped to a specific resource.
* **Query Parameters:**
  * `start_date` `DATE` (Required)
  * `end_date` `DATE` (Required)
* **Response (200 OK):**
  ```json
  {
    "resource_id": "e331c923-3b10-4aa1-bb99-db0b91ab4aa3",
    "total_accumulated_cost": 254.30,
    "currency": "USD",
    "records": [
      {
        "usage_start": "2026-06-01T00:00:00Z",
        "cost": 8.47
      }
    ]
  }
  ```

---

## 7. Metrics Domain

### GET /metrics/resource/{id}
Fetches metric details for a single resource.
* **Query Parameters:**
  * `metric_type` `VARCHAR` (Required, e.g. cpu_utilization)
  * `start_time` `INT` (Required, Unix Timestamp)
  * `end_time` `INT` (Required, Unix Timestamp)
  * `resolution` `INT` (Optional, Step seconds)
* **Response (200 OK):**
  ```json
  {
    "resource_id": "e331c923-3b10-4aa1-bb99-db0b91ab4aa3",
    "metric_type": "cpu_utilization",
    "unit": "percent",
    "data_points": [
      { "timestamp": 1782806400, "value": 14.5 },
      { "timestamp": 1782806700, "value": 18.2 }
    ]
  }
  ```

### GET /metrics/dashboard
Aggregates high-level utilization values across all servers.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
* **Response (200 OK):**
  ```json
  {
    "average_cpu_utilization": 24.3,
    "idle_instances_count": 8,
    "total_monitored_nodes": 45
  }
  ```

---

## 8. Optimization Domain

### GET /recommendations
Retrieves active recommendations.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
  * `status` `VARCHAR` (Optional, Default: ACTIVE)
  * `type` `VARCHAR` (Optional, e.g. rightsize)
* **Response (200 OK):**
  ```json
  [
    {
      "recommendation_id": "8bb911cb-c8a8-48b2-9df9-cbab7801be1b",
      "resource_id": "e331c923-3b10-4aa1-bb99-db0b91ab4aa3",
      "resource_name": "prod-api-server",
      "rule_id": "oversized_vm",
      "recommendation_type": "rightsize",
      "savings_potential_monthly": 120.00,
      "current_configuration": {
        "instance_type": "m6g.xlarge",
        "monthly_cost": 240.00
      },
      "target_configuration": {
        "instance_type": "m6g.large",
        "monthly_cost": 120.00
      },
      "reasoning": "Peak CPU utilization was below 12% over the last 14 days.",
      "created_at": "2026-06-30T10:00:00Z"
    }
  ]
  ```

### POST /recommendations/run
Manually triggers optimization engine checks.
* **Request Body:**
  ```json
  {
    "project_id": "848e02d6-4444-48f5-bcbb-b6a38ac4773c"
  }
  ```
* **Response (202 Accepted):**
  ```json
  {
    "job_id": "67a911bc-c8b8-4cda-92c2-89cc098acab1",
    "status": "RUNNING"
  }
  ```

### GET /recommendations/{id}
Retrieves details for a single recommendation.
* **Response (200 OK):** Same structure as the items in `GET /recommendations`.

---

## 9. Forecast Domain

### GET /forecast
Retrieves cost predictions.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
  * `months` `INT` (Default: 3, Max: 12)
* **Response (200 OK):**
  ```json
  {
    "baseline_cost": 4500.00,
    "prediction_start": "2026-07-01",
    "prediction_end": "2026-09-30",
    "predictions": [
      {
        "month": "2026-07",
        "baseline": 4650.00,
        "optimistic": 4100.00,
        "pessimistic": 5200.00
      }
    ]
  }
  ```

---

## 10. AI Chat Domain

### POST /chat
Sends a prompt to the assistant.
* **Request Body:**
  ```json
  {
    "project_id": "848e02d6-4444-48f5-bcbb-b6a38ac4773c",
    "conversation_id": "f5b611a2-c8a8-444d-88b9-cba89801bcba", // Optional
    "message": "Which databases are cost-inefficient in US-East?"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "conversation_id": "f5b611a2-c8a8-444d-88b9-cba89801bcba",
    "message": {
      "id": "e88b911c-c901-44ab-bc9d-cba78b0c8b2a",
      "role": "assistant",
      "content": "Based on my analysis, database 'rds-prod-postgres' in us-east-1 is running at 4% average CPU utilization...",
      "created_at": "2026-06-30T10:17:00Z"
    }
  }
  ```

### GET /chat/history
Lists conversations associated with the current project workspace.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
* **Response (200 OK):**
  ```json
  [
    {
      "conversation_id": "f5b611a2-c8a8-444d-88b9-cba89801bcba",
      "title": "US-East Resource Optimizations",
      "updated_at": "2026-06-30T10:17:00Z"
    }
  ]
  ```

### GET /chat/{conversationId}
Retrieves the messages of a chat session.
* **Response (200 OK):**
  ```json
  {
    "conversation_id": "f5b611a2-c8a8-444d-88b9-cba89801bcba",
    "title": "US-East Resource Optimizations",
    "messages": [
      {
        "role": "user",
        "content": "Which databases are cost-inefficient in US-East?",
        "created_at": "2026-06-30T10:16:30Z"
      },
      {
        "role": "assistant",
        "content": "Based on my analysis...",
        "created_at": "2026-06-30T10:17:00Z"
      }
    ]
  }
  ```

---

## 11. Reports Domain

### GET /reports
Lists generated PDF/CSV reports.
* **Query Parameters:**
  * `project_id` `UUID` (Required)
* **Response (200 OK):**
  ```json
  [
    {
      "report_id": "997b88aa-d45a-4933-88bc-cba78b091f2c",
      "name": "monthly-cost-report-2026-06.pdf",
      "report_type": "billing_summary",
      "created_at": "2026-06-30T09:00:00Z"
    }
  ]
  ```

### POST /reports/export
Generates an export report task.
* **Request Body:**
  ```json
  {
    "project_id": "848e02d6-4444-48f5-bcbb-b6a38ac4773c",
    "report_type": "billing_summary",
    "format": "pdf",
    "parameters": {
      "start_date": "2026-06-01",
      "end_date": "2026-06-30"
    }
  }
  ```
* **Response (202 Accepted):**
  ```json
  {
    "report_id": "a9db58-c910-34ad-989d",
    "status": "PROCESSING"
  }
  ```
