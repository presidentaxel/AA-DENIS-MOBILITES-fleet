import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings

settings = get_settings()


class BoltClient:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._client = httpx.Client(base_url=settings.bolt_base_url, timeout=20)

    def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token
        resp = httpx.post(
            settings.bolt_auth_url,
            data={"grant_type": "client_credentials"},
            auth=(settings.bolt_client_id or "", settings.bolt_client_secret or ""),
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        return self._access_token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        resp = self._client.get(path, headers=self._headers(), params=params)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._client.post(path, headers=self._headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

