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
            # Bolt attend client_id et client_secret dans le body, pas en HTTP Basic Auth
            resp = httpx.post(
                auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.bolt_client_id,
                    "client_secret": settings.bolt_client_secret,
                    "scope": "fleet-integration:api",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
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
        base_url = str(settings.bolt_base_url).rstrip("/")
        full_url = f"{base_url}{path}"
        headers = self._headers()
        
        # Logs de debug détaillés
        print(f"[BOLT DEBUG] ===== GET REQUEST =====")
        print(f"[BOLT] URL: {full_url}")
        print(f"[BOLT] METHOD: GET")
        print(f"[BOLT] PARAMS: {params}")
        print(f"[BOLT] HEADERS: { {k: (v[:20] + '...' if k.lower() == 'authorization' else v) for k, v in headers.items()} }")
        
        try:
            resp = self._client.get(path, headers=headers, params=params)
            
            # Logs de réponse
            print(f"[BOLT] STATUS: {resp.status_code}")
            print(f"[BOLT] RESPONSE HEADERS: {dict(resp.headers)}")
            response_text = resp.text[:800] if resp.text else "(empty)"
            print(f"[BOLT] BODY: {response_text}")
            print(f"[BOLT DEBUG] =====================")
            
            resp.raise_for_status()
            return resp.json()
        except ConnectError as e:
            print(f"[BOLT] CONNECTION ERROR: {str(e)}")
            raise ConnectionError(
                f"Impossible de se connecter à {full_url}. "
                f"Vérifie que BOLT_BASE_URL est correct (doit être https://node.bolt.eu/fleet-integration-gateway). "
                f"Erreur DNS: {str(e)}"
            ) from e
        except Exception as e:
            print(f"[BOLT] ERROR: {str(e)}")
            print(f"[BOLT DEBUG] =====================")
            raise

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        # S'assurer que le path commence par /
        if not path.startswith("/"):
            path = "/" + path
        base_url = str(settings.bolt_base_url).rstrip("/")
        full_url = f"{base_url}{path}"
        
        # Headers selon la documentation Bolt
        headers = {
            **self._headers(),
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        
        # Logs de debug détaillés
        print(f"[BOLT DEBUG] ===== POST REQUEST =====")
        print(f"[BOLT] URL: {full_url}")
        print(f"[BOLT] METHOD: POST")
        print(f"[BOLT] PARAMS: (none - using JSON body)")
        print(f"[BOLT] JSON BODY: {payload}")
        print(f"[BOLT] HEADERS: { {k: (v[:20] + '...' if k.lower() == 'authorization' else v) for k, v in headers.items()} }")
        
        try:
            resp = self._client.post(path, headers=headers, json=payload)
            
            # Logs de réponse (TOUJOURS afficher, même en cas d'erreur)
            print(f"[BOLT] STATUS: {resp.status_code}")
            print(f"[BOLT] RESPONSE HEADERS: {dict(resp.headers)}")
            response_text = resp.text[:800] if resp.text else "(empty)"
            print(f"[BOLT] BODY: {response_text}")
            
            # Si erreur HTTP, essayer de parser le JSON pour voir le message d'erreur Bolt
            if resp.status_code >= 400:
                try:
                    error_json = resp.json()
                    print(f"[BOLT] ERROR JSON: {error_json}")
                except:
                    pass
            
            print(f"[BOLT DEBUG] =====================")
            
            resp.raise_for_status()
            return resp.json()
        except ConnectError as e:
            print(f"[BOLT] CONNECTION ERROR: {str(e)}")
            print(f"[BOLT DEBUG] =====================")
            raise ConnectionError(
                f"Impossible de se connecter à {full_url}. "
                f"Vérifie que BOLT_BASE_URL est correct (doit être https://node.bolt.eu/fleet-integration-gateway). "
                f"Erreur DNS: {str(e)}"
            ) from e
        except Exception as e:
            print(f"[BOLT] ERROR: {str(e)}")
            print(f"[BOLT DEBUG] =====================")
            raise

