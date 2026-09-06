# Kashoo Connector — Connector Discovery

## Official API Landscape
Kashoo Cloud Accounting provides a RESTful API serving small businesses:
- **Root Resource:** `/api/v1/businesses/{businessId}` provides the tenant scope.
- **Contacts:** `/api/v1/businesses/{businessId}/contacts` represents customers, vendors, and partners.
- **Invoicing & Bills:** `/api/v1/businesses/{businessId}/invoices` and `/bills`.
- **Ledger Accounts:** `/api/v1/businesses/{businessId}/accounts` for bank, cash, income, and expense accounts.
- **Taxes:** `/api/v1/businesses/{businessId}/taxes` for sales tax management.

## Authentication & Headers
- `Authorization: Bearer <auth_token>`
- `Accept: application/json`
- `Content-Type: application/json`
