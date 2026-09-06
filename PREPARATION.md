# Kashoo Connector — Preparation

## Product Scope
Build a comprehensive Imperal connector for **Kashoo** (C27. Accounting & Bookkeeping). The integration connects directly to the official **Kashoo REST API** (`https://api.kashoo.com`), providing accounting management across business contacts/customers, sales invoices, vendor bills, ledger accounts, and sales tax rates.

## Official API Specifications
- **API Architecture:** RESTful JSON API
- **Endpoint:** `https://api.kashoo.com`
- **Core Endpoints:**
  - `GET /api/users/me/businesses` — discover authenticated user businesses
  - `GET /api/v1/businesses/{businessId}/contacts` — contacts (filtered by type `CUSTOMER` or `VENDOR`)
  - `GET /api/v1/businesses/{businessId}/invoices` — sales invoices
  - `GET /api/v1/businesses/{businessId}/bills` — vendor bills
  - `GET /api/v1/businesses/{businessId}/payments` — incoming and outgoing payments
  - `GET /api/v1/businesses/{businessId}/accounts` — general ledger and bank accounts
  - `GET /api/v1/businesses/{businessId}/taxes` — sales tax codes and rates
- **Authentication Model:** Bearer token via `Authorization: Bearer <auth_token>`
- **Mandatory Requirements:**
  - Scoping all business operations by `business_id` (Standard B7).
  - Explicit rate limit detection (HTTP 429) and auth classification (HTTP 401/403).
  - Sanitization of Bearer tokens and API keys in exception traces (Standard B8).
  - Multi-tenant connection tracking via `connection_id` (Standard B9).

## Delivery Gates
1. [x] Official API discovery completed with Kashoo REST API specifications.
2. [x] Scoping by business_id and authentication mechanisms verified.
3. [x] Five mandatory specification documents authored.
4. [x] Client implemented with B7-B10 compliance, secret redaction, and 429/401 classification.
5. [x] Panel sidebar implemented conforming to UI_INTERFACE_STANDARD.md.
6. [x] Action prices calibrated per PRICING_POLICY.md.
