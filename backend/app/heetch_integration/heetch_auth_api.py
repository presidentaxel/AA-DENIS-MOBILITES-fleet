"""
Client d'authentification Heetch via l'API auth-gw.heetch.com
Utilise l'API officielle au lieu du scraping Playwright.
"""
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings
from app.core import logging as app_logging

settings = get_settings()
logger = app_logging.get_logger(__name__)


class HeetchAuthAPI:
    """
    Client pour l'authentification Heetch via l'API auth-gw.heetch.com.
    """
    
    def __init__(self):
        self.auth_base_url = "https://auth-gw.heetch.com"
        self.driver_base_url = "https://driver.heetch.com"
        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._device_id: Optional[str] = None
        self._session_cookies: Optional[Dict[str, str]] = None
        
    def _get_device_id(self) -> str:
        """Génère ou récupère un device_id unique."""
        if not self._device_id:
            import uuid
            self._device_id = str(uuid.uuid4())
        return self._device_id
    
    def check_session(self) -> Dict[str, Any]:
        """
        Vérifie l'état de la session actuelle.
        
        Returns:
            Dict avec l'état de la session (state, phone_number, etc.)
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "device-id": self._get_device_id(),
            "origin": "https://auth.heetch.com",
            "referer": "https://auth.heetch.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        
        if self._token:
            headers["authorization"] = f"Token {self._token}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(f"{self.auth_base_url}/session", headers=headers)
                resp.raise_for_status()
                data = resp.json()
                
                # Extraire le token depuis les headers de réponse si disponible
                auth_header = resp.headers.get("authorization")
                if auth_header and not self._token:
                    # Le token peut être dans le header Authorization de la réponse
                    token = auth_header.replace("Token ", "").replace("Bearer ", "")
                    if token:
                        self._token = token
                        logger.info(f"[HEETCH AUTH] Token extrait depuis les headers de réponse")
                
                # Extraire access_token depuis la réponse si présent
                if "access_token" in data and not self._token:
                    self._token = data["access_token"]
                    logger.info(f"[HEETCH AUTH] Access token extrait depuis la réponse")
                
                return data
        except Exception as e:
            logger.error(f"[HEETCH AUTH] Erreur lors de la vérification de session: {e}", exc_info=True)
            raise
    
    def create_session(self, phone_number: str, recaptcha_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée une nouvelle session web avec le numéro de téléphone.
        
        Args:
            phone_number: Numéro de téléphone
            recaptcha_token: Token reCAPTCHA (optionnel, peut être extrait depuis Playwright)
        
        Returns:
            Dict avec access_token et état de la session
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "device-id": self._get_device_id(),
            "origin": "https://auth.heetch.com",
            "referer": "https://auth.heetch.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        
        payload = {
            "client": "web",
            "phone_number": phone_number,
            "action": "login",
            "challenge": "score"
        }
        
        if recaptcha_token:
            payload["recaptcha_token"] = recaptcha_token
        
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{self.auth_base_url}/web/session", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                
                # Extraire l'access_token depuis la réponse
                if "access_token" in data:
                    self._token = data["access_token"]
                    # Les tokens expirent généralement après 24h
                    self._token_expires_at = time.time() + (24 * 60 * 60)
                    logger.info(f"[HEETCH AUTH] Session créée avec access_token: {self._token[:20]}...")
                
                return data
        except Exception as e:
            logger.error(f"[HEETCH AUTH] Erreur lors de la création de session: {e}", exc_info=True)
            raise
    
    def authenticate(self, phone: str, password: str) -> Dict[str, Any]:
        """
        Authentifie l'utilisateur avec téléphone et mot de passe.
        
        Args:
            phone: Numéro de téléphone
            password: Mot de passe
        
        Returns:
            Dict avec le token et les informations de session
        """
        # D'abord, vérifier l'état de la session
        session_info = self.check_session()
        logger.info(f"[HEETCH AUTH] État de session: {session_info.get('state')}")
        
        # Préparer les headers
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "device-id": self._get_device_id(),
            "origin": "https://auth.heetch.com",
            "referer": "https://auth.heetch.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        
        # Essayer de s'authentifier
        # L'endpoint exact peut varier, mais généralement c'est POST /authenticate ou /login
        auth_endpoints = [
            "/authenticate",
            "/login",
            "/session/authenticate",
            "/auth/login"
        ]
        
        payload = {
            "phone_number": phone,
            "password": password,
            "authentication_provider": "phone_number-password"
        }
        
        for endpoint in auth_endpoints:
            try:
                with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                    resp = client.post(
                        f"{self.auth_base_url}{endpoint}",
                        json=payload,
                        headers=headers
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        # Extraire le token de la réponse ou des headers
                        token = data.get("token") or data.get("access_token") or data.get("auth_token")
                        
                        # Si pas dans le body, chercher dans les headers
                        if not token:
                            auth_header = resp.headers.get("authorization") or resp.headers.get("x-auth-token")
                            if auth_header:
                                token = auth_header.replace("Token ", "").replace("Bearer ", "")
                        
                        if token:
                            self._token = token
                            # Les tokens expirent généralement après 24h
                            self._token_expires_at = time.time() + (24 * 60 * 60)
                            
                            # Récupérer les cookies de session
                            self._session_cookies = {}
                            for cookie in resp.cookies.jar:
                                self._session_cookies[cookie.name] = cookie.value
                            
                            logger.info(f"[HEETCH AUTH] Authentification réussie avec endpoint: {endpoint}")
                            return {
                                "token": token,
                                "session": data,
                                "cookies": self._session_cookies
                            }
                    
                    logger.debug(f"[HEETCH AUTH] Endpoint {endpoint} retourné {resp.status_code}")
            except Exception as e:
                logger.debug(f"[HEETCH AUTH] Erreur avec endpoint {endpoint}: {e}")
                continue
        
        raise RuntimeError("Impossible de s'authentifier avec aucun des endpoints testés")
    
    def get_token(self) -> Optional[str]:
        """Récupère le token actuel s'il est encore valide."""
        if self._token and time.time() < self._token_expires_at:
            return self._token
        return None
    
    def get_cookies(self) -> Dict[str, str]:
        """Récupère les cookies de session."""
        return self._session_cookies or {}

