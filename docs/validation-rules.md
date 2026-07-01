# Input & Field Validation Rules

This document specifies the validation rules applied across the APIs, domain models, and databases of **CloudPilot AI**.

---

## 1. Core Field Types

### Email Address
* **Regex Rule:** `^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$`
* **Additional Rules:**
  * Must be lowercased before validation or insertion.
  * Maximum length of 255 characters.

### Password
* **Minimum Length:** 12 characters.
* **Maximum Length:** 128 characters.
* **Complexity Rules:** Must contain at least:
  * One uppercase letter (`A-Z`)
  * One lowercase letter (`a-z`)
  * One numeric character (`0-9`)
  * One special character (e.g. `!@#$%^&*()_+=-[]{}|;:',.<>?/`)

### UUID
* **Standard:** UUID Version 4.
* **Regex Rule:** `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`
* **Applicability:** Applies to all generated identifiers (`user_id`, `project_id`, `resource_id`, etc.).

### Dates & Timestamps
* **Standard:** ISO 8601 format (`YYYY-MM-DDTHH:mm:ssZ`).
* **Timezone:** Enforce UTC (`Z` offset suffix).
* **Logical Checks:**
  * For ranges, `end_date` must be greater than or equal to `start_date`.
  * Collection ranges cannot exceed 366 days in a single query.

### Currency
* **Standard:** ISO 4217 Three-letter Alphabetic Code.
* **Constraint:** Must belong to a validated list. Default: `USD`.
* **Regex Rule:** `^[A-Z]{3}$`

### Cost & Values
* **Numeric Format:** Decimal / float values.
* **Constraint:** Must be non-negative (`value >= 0.0`).
* **Scale:** Retain up to 6 decimal places for raw billing inputs (`NUMERIC(15, 6)`).

---

## 2. Cloud Credentials Validation Schemas

When adding integrations, incoming payload configurations are validated against these strict Pydantic/JSON structures:

### 2.1 Amazon Web Services (AWS)
* **Auth Method:** IAM Role Delegation (External ID validation pattern).
* **Validation Structure:**
  ```json
  {
    "role_arn": {
      "type": "string",
      "regex": "^arn:aws:iam::[0-9]{12}:role/[A-Za-z0-9+=,.@_-]{1,64}$"
    },
    "external_id": {
      "type": "string",
      "regex": "^[A-Za-z0-9-]{12,64}$"
    }
  }
  ```

### 2.2 Microsoft Azure
* **Auth Method:** Service Principal (Active Directory credentials).
* **Validation Structure:**
  ```json
  {
    "tenant_id": { "type": "string", "format": "uuid" },
    "subscription_id": { "type": "string", "format": "uuid" },
    "client_id": { "type": "string", "format": "uuid" },
    "client_secret": { "type": "string", "minLength": 16, "maxLength": 128 }
  }
  ```

### 2.3 Google Cloud Platform (GCP)
* **Auth Method:** Service Account Key JSON.
* **Validation Structure:**
  ```json
  {
    "type": { "type": "string", "enum": ["service_account"] },
    "project_id": { "type": "string", "regex": "^[a-z0-9-]{6,30}$" },
    "private_key_id": { "type": "string", "regex": "^[a-f0-9]{40}$" },
    "private_key": { "type": "string", "contains": "-----BEGIN PRIVATE KEY-----" },
    "client_email": { "type": "string", "format": "email" }
  }
  ```

---

## 3. Metadata & Infrastructure Parameters

### Resource IDs
* **AWS:** Amazon Resource Names (ARNs). Regex: `^arn:aws:[a-z0-9:-]+$`
* **Azure:** Resource Manager URI. Regex: `^/subscriptions/[^/]+/resourceGroups/[^/]+/providers/[^/]+$`
* **GCP:** Compute Resource URI. Regex: `^https://www.googleapis.com/compute/[^/]+$`

### Regions
* **AWS:** Regex `^[a-z]{2}-[a-z]+-[0-9]$` (e.g. `us-east-1`).
* **Azure:** Regex `^[a-z0-9]+$` (e.g. `eastus`, `westeurope`).
* **GCP:** Regex `^[a-z]+-[a-z0-9]+-[a-z]$` (e.g. `us-central1-a`).

### Tags
* **Keys:** Max 128 characters, letters/numbers and `_`, `.`, `-` only.
* **Values:** Max 256 characters.
* **Size Limit:** A maximum of 50 tags per resource.
