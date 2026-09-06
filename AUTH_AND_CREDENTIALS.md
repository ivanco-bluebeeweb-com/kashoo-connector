# Kashoo Connector — Auth and Credentials Standard

## Provider Authentication
- **Protocol:** Bearer Token (OAuth 2.0 / API Token)
- **Credential Storage:** `ctx.secrets.set("kashoo_connections", ...)`
- **Fields:** `auth_token`, `business_id`, optional `base_url`
- **Sanitization:** All tokens masked in logs and exception messages per Standard B8.
