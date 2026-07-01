# Security, Credential Storage & RBAC Matrix

This document outlines the security architecture, credentials encryption design, and Role-Based Access Control (RBAC) schemas for **CloudPilot AI**.

---

## 1. Secrets Management & Envelope Encryption

### Credential Encryption Flow
To prevent unauthorized access to cloud integration credentials, CloudPilot AI employs **Envelope Encryption** via AES-256-GCM.

```
       Plaintext Cloud Credentials
                  │
                  ▼
        ┌───────────────────┐
        │  Encrypt with DEK │<─── Data Encryption Key (DEK, unique per account)
        └─────────┬─────────┘
                  │
                  ├─── Ciphertext Payload ───> Save to DB (cloud_credentials)
                  │
        ┌─────────┴─────────┐
        │  Encrypt with KEK │<─── Key Encryption Key (KEK, managed in KMS/Vault)
        └─────────┬─────────┘
                  │
                  ▼
        Encrypted DEK Payload ───────────────> Save to DB (cloud_credentials)
```

1. **Instantiation:** For every new integration, the backend generates a cryptographically secure, random 256-bit **Data Encryption Key (DEK)**.
2. **Data Encrypt:** The credentials payload is encrypted using the DEK with AES-256-GCM.
3. **Key Encrypt:** The DEK is encrypted using a **Key Encryption Key (KEK)** retrieved from AWS KMS or HashiCorp Vault.
4. **Storage:** The encrypted credentials payload, the encrypted DEK, and the initialization vector (IV) are stored together in the `cloud_credentials` table.
5. **Decryption:** At runtime, Celery workers decrypt the DEK using the KEK from KMS, then decrypt the credentials payload using the recovered DEK. Plaintext credentials exist only in volatile process memory and are never written to disk or logs.

---

## 2. Sensitive Fields & Masking Strategy

### Database Sensitive Fields
* `users.password_hash`
* `api_keys.key_hash`
* `refresh_tokens.token_hash`
* `cloud_credentials.encrypted_payload`
* `monitoring_sources.encrypted_credentials`

### Logging & UI Masking Strategy
* **Logging Filter Middleware:** A custom Python logging formatter strips out fields named `password`, `secret`, `api_key`, `credentials`, `private_key`, `token` using regular expression search-replace patterns.
* **IP Addresses:** Masked in logs and activity streams to the class-C block level (e.g. `192.168.1.XXX`).
* **Cloud Credentials UI Display:** In API responses and UI configuration views, credentials inputs are masked completely. The client only receives metadata confirming integration:
  * AWS: Returns `{"role_arn": "arn:aws:iam::123456789012:role/CloudPilotAccessRole", "external_id": "********"}`
  * Tenant Secrets: Retained as `{"status": "CONFIGURED", "last_updated": "2026-06-30T10:00:00Z"}`

---

## 3. Session Security & Token Storage

### Access Tokens (JWT)
* **Encryption Type:** Signed via HMAC-SHA256 using a key rotated every 30 days.
* **Expiration Time:** 15 minutes.
* **Storage:** Volatile React frontend state memory. It is never stored in `localStorage` or `sessionStorage` to mitigate Cross-Site Scripting (XSS) extraction risks.

### Refresh Tokens
* **Format:** Cryptographically secure random UUID string stored in the database.
* **Expiration Time:** 7 days (with sliding expiration).
* **Storage:** Saved in a secure, HTTP-Only, Secure, SameSite=Strict cookie.
* **Rotation:** When a new access token is requested via `/auth/refresh`, the old refresh token is deleted and a new one is issued (Refresh Token Rotation).

---

## 4. RBAC Permission Matrix

Users are assigned to distinct Roles within their target Organization.

### Defined Roles
* **`Admin`:** Complete administrative control over the organization workspace, settings, users, and credentials.
* **`Operator`:** Technical lead responsible for maintaining infrastructure syncs, monitoring connections, and applying recommendations.
* **`BillingAdmin`:** Financial officer responsible for analyzing costs, auditing invoices, and reviewing forecast projections.
* **`Viewer`:** Read-only access to optimization logs and infrastructure inventories.

### RBAC Permission Allocation Table

| Permission | Admin | Operator | BillingAdmin | Viewer |
| :--- | :---: | :---: | :---: | :---: |
| `connect_provider` | **Yes** | **Yes** | No | No |
| `disconnect_provider` | **Yes** | No | No | No |
| `view_costs` | **Yes** | **Yes** | **Yes** | **Yes** |
| `view_inventory` | **Yes** | **Yes** | **Yes** | **Yes** |
| `apply_optimization` | **Yes** | **Yes** | No | No |
| `dismiss_optimization` | **Yes** | **Yes** | No | No |
| `read_chat` | **Yes** | **Yes** | **Yes** | **Yes** |
| `write_chat` | **Yes** | **Yes** | **Yes** | No |
| `export_reports` | **Yes** | **Yes** | **Yes** | **Yes** |
| `manage_users` | **Yes** | No | No | No |
| `view_audit_logs` | **Yes** | No | No | No |
