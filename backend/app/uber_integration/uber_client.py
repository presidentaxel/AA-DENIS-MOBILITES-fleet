import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.uber_integration.uber_scopes import SUPPLIER_SCOPES

settings = get_settings()


class UberClient:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        # Convertir AnyUrl en str pour httpx
        self._client = httpx.Client(base_url=str(settings.uber_base_url), timeout=15)

    def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        # Convertir AnyUrl en str pour httpx
        response = httpx.post(
            str(settings.uber_auth_url),
            data={"grant_type": "client_credentials", "scope": " ".join(SUPPLIER_SCOPES)},
            auth=(settings.uber_client_id or "", settings.uber_client_secret or ""),
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)
        return self._access_token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        response = self._client.get(path, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(path, headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json()

