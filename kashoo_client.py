"""Official Kashoo REST API client aligned with api.kashoo.com schema."""
from __future__ import annotations
import httpx
from typing import Any, Optional

DEFAULT_KASHOO_BASE = "https://api.kashoo.com"

class KashooClient:
    def __init__(self, auth_token: str, business_id: str, base_url: str = ""):
        self.auth_token = auth_token.strip()
        self.business_id = str(business_id).strip()
        self.base_url = (base_url.strip() if base_url else DEFAULT_KASHOO_BASE).rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Imperal-Kashoo/0.1.0"
        }
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _sanitize_msg(self, msg: str) -> str:
        if not msg:
            return ""
        if self.auth_token and len(self.auth_token) > 6:
            msg = msg.replace(self.auth_token, self.auth_token[:3] + "..." + self.auth_token[-3:])
        return msg

    def _classify_error(self, resp: httpx.Response, action_name: str) -> dict[str, Any]:
        status = resp.status_code
        err_msg = ""
        try:
            data = resp.json()
            if "message" in data:
                err_msg = data["message"]
            elif "error" in data:
                err_msg = str(data["error"])
        except Exception:
            err_msg = resp.text[:200]
        err_msg = self._sanitize_msg(err_msg)

        if status == 429:
            retry_after = resp.headers.get("Retry-After", "60")
            return {
                "status": "error",
                "code": "RATE_LIMITED",
                "message": f"Kashoo rate limit reached during {action_name}. Retry after {retry_after}s.",
                "retry_after": int(retry_after) if retry_after.isdigit() else 60
            }
        elif status == 401:
            return {
                "status": "error",
                "code": "UNAUTHORIZED",
                "message": f"Kashoo authentication failed (HTTP 401) during {action_name}. Token expired or invalid: {err_msg}"
            }
        elif status == 403:
            return {
                "status": "error",
                "code": "FORBIDDEN",
                "message": f"Kashoo permission denied (HTTP 403) for business {self.business_id} during {action_name}: {err_msg}"
            }
        elif status == 404:
            return {"status": "error", "code": "NOT_FOUND", "message": f"Resource not found in Kashoo: {err_msg}"}
        return {"status": "error", "code": "REQUEST_FAILED", "message": f"Kashoo API returned HTTP {status}: {err_msg}"}

    async def verify_auth(self) -> dict[str, Any]:
        url = f"{self.base_url}/api/users/me/businesses"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "message": "Authenticated"}
                return self._classify_error(resp, "verify_auth")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def list_customers(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/contacts"
        params = {"type": "CUSTOMER", "limit": limit}
        if cursor.isdigit():
            params["offset"] = int(cursor)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("contacts", [])
                    return {"status": "ok", "items": items, "total": len(items)}
                return self._classify_error(resp, "list_customers")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/contacts/{customer_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "get_customer")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def create_customer(self, payload: dict[str, Any] = None, name: str = '', details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if payload is None: payload = {'name': name, **(details or {})}
        url = f"{self.base_url}/api/businesses/{self.business_id}/contacts"
        req_payload = dict(payload)
        req_payload["type"] = "CUSTOMER"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, headers=self.headers, json=req_payload)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "create_customer")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def update_customer(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/contacts/{customer_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.put(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 204):
                    data = resp.json() if resp.text else {"id": customer_id}
                    return {"status": "ok", "data": data}
                return self._classify_error(resp, "update_customer")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def delete_customer(self, customer_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/contacts/{customer_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.delete(url, headers=self.headers)
                if resp.status_code in (200, 204):
                    return {"status": "ok", "id": customer_id, "deleted": True}
                return self._classify_error(resp, "delete_customer")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def list_invoices(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/invoices"
        params = {"limit": limit}
        if cursor.isdigit():
            params["offset"] = int(cursor)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("invoices", [])
                    return {"status": "ok", "items": items, "total": len(items)}
                return self._classify_error(resp, "list_invoices")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def get_invoice(self, invoice_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/invoices/{invoice_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "get_invoice")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def create_invoice(self, payload: dict[str, Any] = None, name: str = '', details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if payload is None: payload = {'name': name, **(details or {})}
        url = f"{self.base_url}/api/businesses/{self.business_id}/invoices"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "create_invoice")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def update_invoice(self, invoice_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/invoices/{invoice_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.put(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 204):
                    data = resp.json() if resp.text else {"id": invoice_id}
                    return {"status": "ok", "data": data}
                return self._classify_error(resp, "update_invoice")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def delete_invoice(self, invoice_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/invoices/{invoice_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.delete(url, headers=self.headers)
                if resp.status_code in (200, 204):
                    return {"status": "ok", "id": invoice_id, "deleted": True}
                return self._classify_error(resp, "delete_invoice")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def list_bills(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/bills"
        params = {"limit": limit}
        if cursor.isdigit():
            params["offset"] = int(cursor)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("bills", [])
                    return {"status": "ok", "items": items, "total": len(items)}
                return self._classify_error(resp, "list_bills")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def get_bill(self, bill_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/bills/{bill_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "get_bill")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def create_bill(self, payload: dict[str, Any] = None, name: str = '', details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if payload is None: payload = {'name': name, **(details or {})}
        url = f"{self.base_url}/api/businesses/{self.business_id}/bills"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "create_bill")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def update_bill(self, bill_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/bills/{bill_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.put(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 204):
                    data = resp.json() if resp.text else {"id": bill_id}
                    return {"status": "ok", "data": data}
                return self._classify_error(resp, "update_bill")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def delete_bill(self, bill_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/bills/{bill_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.delete(url, headers=self.headers)
                if resp.status_code in (200, 204):
                    return {"status": "ok", "id": bill_id, "deleted": True}
                return self._classify_error(resp, "delete_bill")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def list_payments(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/payments"
        params = {"limit": limit}
        if cursor.isdigit():
            params["offset"] = int(cursor)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("payments", [])
                    return {"status": "ok", "items": items, "total": len(items)}
                return self._classify_error(resp, "list_payments")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def get_payment(self, payment_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/payments/{payment_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "get_payment")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def create_payment(self, payload: dict[str, Any] = None, name: str = '', details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if payload is None: payload = {'name': name, **(details or {})}
        url = f"{self.base_url}/api/businesses/{self.business_id}/payments"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "create_payment")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def update_payment(self, payment_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/payments/{payment_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.put(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 204):
                    data = resp.json() if resp.text else {"id": payment_id}
                    return {"status": "ok", "data": data}
                return self._classify_error(resp, "update_payment")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def delete_payment(self, payment_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/payments/{payment_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.delete(url, headers=self.headers)
                if resp.status_code in (200, 204):
                    return {"status": "ok", "id": payment_id, "deleted": True}
                return self._classify_error(resp, "delete_payment")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def list_bank_accounts(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/accounts"
        params = {"type": "BANK", "limit": limit}
        if cursor.isdigit():
            params["offset"] = int(cursor)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("accounts", [])
                    return {"status": "ok", "items": items, "total": len(items)}
                return self._classify_error(resp, "list_bank_accounts")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def get_bank_account(self, bank_account_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/accounts/{bank_account_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "get_bank_account")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def create_bank_account(self, payload: dict[str, Any] = None, name: str = '', details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if payload is None: payload = {'name': name, **(details or {})}
        url = f"{self.base_url}/api/businesses/{self.business_id}/accounts"
        req_payload = dict(payload)
        req_payload.setdefault("type", "BANK")
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, headers=self.headers, json=req_payload)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "create_bank_account")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def update_bank_account(self, bank_account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/accounts/{bank_account_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.put(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 204):
                    data = resp.json() if resp.text else {"id": bank_account_id}
                    return {"status": "ok", "data": data}
                return self._classify_error(resp, "update_bank_account")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def delete_bank_account(self, bank_account_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/accounts/{bank_account_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.delete(url, headers=self.headers)
                if resp.status_code in (200, 204):
                    return {"status": "ok", "id": bank_account_id, "deleted": True}
                return self._classify_error(resp, "delete_bank_account")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def list_tax_rates(self, limit: int = 50, cursor: str = "") -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/taxes"
        params = {"limit": limit}
        if cursor.isdigit():
            params["offset"] = int(cursor)
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("taxes", [])
                    return {"status": "ok", "items": items, "total": len(items)}
                return self._classify_error(resp, "list_tax_rates")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def get_tax_rate(self, tax_rate_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/taxes/{tax_rate_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "get_tax_rate")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def create_tax_rate(self, payload: dict[str, Any] = None, name: str = '', details: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if payload is None: payload = {'name': name, **(details or {})}
        url = f"{self.base_url}/api/businesses/{self.business_id}/taxes"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 201):
                    return {"status": "ok", "data": resp.json()}
                return self._classify_error(resp, "create_tax_rate")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def update_tax_rate(self, tax_rate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/taxes/{tax_rate_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.put(url, headers=self.headers, json=payload)
                if resp.status_code in (200, 204):
                    data = resp.json() if resp.text else {"id": tax_rate_id}
                    return {"status": "ok", "data": data}
                return self._classify_error(resp, "update_tax_rate")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def delete_tax_rate(self, tax_rate_id: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/businesses/{self.business_id}/taxes/{tax_rate_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.delete(url, headers=self.headers)
                if resp.status_code in (200, 204):
                    return {"status": "ok", "id": tax_rate_id, "deleted": True}
                return self._classify_error(resp, "delete_tax_rate")
            except Exception as exc:
                return {"status": "error", "code": "NETWORK_ERROR", "message": self._sanitize_msg(str(exc))}

    async def audit_accounting_health(self) -> dict[str, Any]:
        inv_res = await self.list_invoices(limit=100)
        bills_res = await self.list_bills(limit=100)
        overdue_invoices = 0
        unpaid_bills = 0
        if inv_res.get("status") == "ok":
            for inv in inv_res.get("items", []):
                if inv.get("status") == "overdue" or (inv.get("balanceDue", 0) > 0 and not inv.get("paid", False)):
                    overdue_invoices += 1
        if bills_res.get("status") == "ok":
            for b in bills_res.get("items", []):
                if not b.get("paid", False):
                    unpaid_bills += 1
        return {
            "status": "ok",
            "overdue_invoices_count": overdue_invoices,
            "unpaid_bills_count": unpaid_bills,
            "reconciliation_pending": 0,
            "overall_status": "warning" if (overdue_invoices > 0 or unpaid_bills > 0) else "healthy"
        }

    async def get_cash_flow_summary(self) -> dict[str, Any]:
        inv_res = await self.list_invoices(limit=100)
        bills_res = await self.list_bills(limit=100)
        acc_res = await self.list_bank_accounts(limit=100)
        rec = sum(inv.get("totalDue", inv.get("amount", 0)) for inv in inv_res.get("items", [])) if inv_res.get("status") == "ok" else 0
        pay = sum(b.get("totalDue", b.get("amount", 0)) for b in bills_res.get("items", [])) if bills_res.get("status") == "ok" else 0
        cash = sum(a.get("balance", 0) for a in acc_res.get("items", [])) if acc_res.get("status") == "ok" else 0
        return {
            "status": "ok",
            "receivables_total": float(rec),
            "payables_total": float(pay),
            "cash_balance": float(cash),
            "currency": "USD"
        }
