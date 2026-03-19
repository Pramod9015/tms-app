"""
HTTP Client for connecting the PyQt6 desktop app to the FastAPI backend.
Handles JWT token management and automatic refresh.
"""
import requests
from typing import Optional, Dict, Any
import os

# Load backend URL from env or default to localhost
BASE_URL = os.getenv("TMS_API_URL", "http://localhost:8000")


class APIClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.username: Optional[str] = None
        self.role: Optional[str] = None
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", self._headers())
        resp = self.session.request(method, url, **kwargs)
        # Try token refresh on 401
        if resp.status_code == 401 and self.refresh_token:
            refreshed = self._do_refresh()
            if refreshed:
                kwargs["headers"] = self._headers()
                resp = self.session.request(method, url, **kwargs)
        return resp

    def _do_refresh(self) -> bool:
        try:
            r = self.session.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": self.refresh_token},
            )
            if r.status_code == 200:
                data = r.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                return True
        except Exception:
            pass
        return False

    def login(self, username: str, password: str) -> Dict[str, Any]:
        r = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password},
        )
        if r.status_code == 200:
            data = r.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.username = data["username"]
            self.role = data["role"]
        return r

    def logout(self):
        self.access_token = None
        self.refresh_token = None
        self.username = None
        self.role = None

    def is_admin(self) -> bool:
        return self.role == "admin"

    # ─── Dashboard ──────────────────────────────────────────────────────────
    def get_summary(self): return self._request("GET", "/api/dashboard/summary")
    def get_daily_chart(self, days=30): return self._request("GET", f"/api/dashboard/daily-chart?days={days}")
    def get_app_usage(self): return self._request("GET", "/api/dashboard/app-usage")
    def get_bank_wise(self): return self._request("GET", "/api/dashboard/bank-wise")
    def get_monthly_trend(self): return self._request("GET", "/api/dashboard/monthly-trend")
    def get_recent_transactions(self, limit=10): return self._request("GET", f"/api/dashboard/recent-transactions?limit={limit}")

    # ─── Transactions ────────────────────────────────────────────────────────
    def list_transactions(self, **params): return self._request("GET", "/api/transactions", params=params)
    def create_transaction(self, data): return self._request("POST", "/api/transactions", json=data)
    def update_transaction(self, txn_id, data): return self._request("PUT", f"/api/transactions/{txn_id}", json=data)
    def delete_transaction(self, txn_id): return self._request("DELETE", f"/api/transactions/{txn_id}")

    # ─── Banks ───────────────────────────────────────────────────────────────
    def list_banks(self): return self._request("GET", "/api/banks")
    def create_bank(self, data): return self._request("POST", "/api/banks", json=data)
    def update_bank(self, bank_id, data): return self._request("PUT", f"/api/banks/{bank_id}", json=data)
    def delete_bank(self, bank_id): return self._request("DELETE", f"/api/banks/{bank_id}")
    def get_default_banks(self): return self._request("GET", "/api/banks/defaults")
    def import_bank_list(self, names: list): return self._request("POST", "/api/banks/import/list", json={"bank_names": names})
    def import_banks_txt(self, file_bytes: bytes, filename: str):
        return self.session.post(
            f"{self.base_url}/api/banks/import/txt",
            files={"file": (filename, file_bytes, "text/plain")},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
    def import_banks_excel(self, file_bytes: bytes, filename: str):
        return self.session.post(
            f"{self.base_url}/api/banks/import/excel",
            files={"file": (filename, file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers={"Authorization": f"Bearer {self.access_token}"},
        )

    # ─── Beneficiaries ───────────────────────────────────────────────────────
    def list_beneficiaries(self): return self._request("GET", "/api/beneficiaries")
    def get_beneficiaries_by_mobile(self, mobile: str): return self._request("GET", "/api/beneficiaries/by-mobile", params={"mobile": mobile})
    def create_beneficiary(self, data): return self._request("POST", "/api/beneficiaries", json=data)
    def delete_beneficiary(self, ben_id): return self._request("DELETE", f"/api/beneficiaries/{ben_id}")

    # ─── Reports ─────────────────────────────────────────────────────────────
    def export_csv(self, **params): return self._request("GET", "/api/reports/export/csv", params=params)
    def export_excel(self, **params): return self._request("GET", "/api/reports/export/excel", params=params)
    def export_pdf(self, **params): return self._request("GET", "/api/reports/export/pdf", params=params)

    # ─── Users (Admin) ───────────────────────────────────────────────────────
    def list_users(self): return self._request("GET", "/api/users")
    def create_user(self, data): return self._request("POST", "/api/auth/register", json=data)
    def update_user(self, user_id, data): return self._request("PUT", f"/api/users/{user_id}", json=data)
    def delete_user(self, user_id): return self._request("DELETE", f"/api/users/{user_id}")

    # ─── Audit ────────────────────────────────────────────────────────────────
    def list_audit_logs(self): return self._request("GET", "/api/audit")


# Singleton
api = APIClient()
