import time
from typing import Any, Dict, Optional

import httpx
from httpx import ConnectError

from app.core.config import get_settings

settings = get_settings()


class BoltClient:
    def __init__(self):
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        # Convertir AnyUrl en str pour httpx et s'assurer qu'il n'y a pas de slash final
        base_url = str(settings.bolt_base_url).rstrip("/")
        self._client = httpx.Client(base_url=base_url, timeout=20)

    def _get_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token
        # Bolt uses form-urlencoded with scope
        # Convertir AnyUrl en str pour httpx
        auth_url = str(settings.bolt_auth_url)
        if not settings.bolt_client_id or not settings.bolt_client_secret:
            raise ValueError("BOLT_CLIENT_ID and BOLT_CLIENT_SECRET must be set in environment variables")
        
        try:
            resp = httpx.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "scope": "fleet-integration:api",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=(settings.bolt_client_id, settings.bolt_client_secret),
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            # Bolt tokens expire in 10 minutes (600 seconds)
            self._token_expires_at = time.time() + data.get("expires_in", 600)
            return self._access_token
        except ConnectError as e:
            raise ConnectionError(
                f"Impossible de se connecter à {auth_url}. "
                f"Vérifie que BOLT_AUTH_URL est correct (doit être https://oidc.bolt.eu/token). "
                f"Erreur: {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Erreur lors de l'authentification Bolt vers {auth_url}: {str(e)}"
            ) from e

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        # S'assurer que le path commence par /
        if not path.startswith("/"):
            path = "/" + path
        try:
            resp = self._client.get(path, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()
        except ConnectError as e:
            base_url = str(settings.bolt_base_url).rstrip("/")
            full_url = f"{base_url}{path}"
            raise ConnectionError(
                f"Impossible de se connecter à {full_url}. "
                f"Vérifie que BOLT_BASE_URL est correct et que le réseau peut résoudre le DNS. "
                f"Erreur DNS: {str(e)}"
            ) from e

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        # S'assurer que le path commence par /
        if not path.startswith("/"):
            path = "/" + path
        try:
            resp = self._client.post(path, headers=self._headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
        except ConnectError as e:
            base_url = str(settings.bolt_base_url).rstrip("/")
            full_url = f"{base_url}{path}"
            raise ConnectionError(
                f"Impossible de se connecter à {full_url}. "
                f"Vérifie que BOLT_BASE_URL est correct et que le réseau peut résoudre le DNS. "
                f"Erreur DNS: {str(e)}. "
                f"Test depuis Docker: docker compose exec backend nslookup api.bolt.eu"
            ) from e

