"""
Gestionnaire de clients Heetch pour conserver l'état entre les appels.
"""
from typing import Optional
from app.heetch_integration.heetch_client import HeetchClient
from threading import Lock

_client_cache: dict[str, HeetchClient] = {}
_cache_lock = Lock()


def get_heetch_client(org_id: str) -> HeetchClient:
    """
    Récupère ou crée un client Heetch pour un org_id donné.
    Le client est mis en cache pour conserver l'état (cookies, session).
    """
    with _cache_lock:
        if org_id not in _client_cache:
            _client_cache[org_id] = HeetchClient(org_id=org_id)
        return _client_cache[org_id]


def clear_client_cache(org_id: Optional[str] = None):
    """
    Vide le cache des clients Heetch.
    Si org_id est fourni, vide uniquement ce client. Sinon, vide tout.
    """
    with _cache_lock:
        if org_id:
            if org_id in _client_cache:
                try:
                    _client_cache[org_id]._close_playwright()
                except:
                    pass
                del _client_cache[org_id]
        else:
            for client in _client_cache.values():
                try:
                    client._close_playwright()
                except:
                    pass
            _client_cache.clear()

