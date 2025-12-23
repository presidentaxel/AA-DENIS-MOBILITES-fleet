import time
import asyncio
import random
from typing import Any, Dict, Optional
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor
import threading
from threading import Lock

_cache_lock = Lock()

import httpx
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.core.config import get_settings
from app.core import logging as app_logging
from app.heetch_integration.heetch_auth_api import HeetchAuthAPI

settings = get_settings()
logger = app_logging.get_logger(__name__)

# ThreadPoolExecutor pour exécuter Playwright dans un thread séparé
# Utiliser un seul worker pour s'assurer que les sessions sont réutilisées
_playwright_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="heetch_playwright")

# Cache global pour les clients Heetch (un par org_id)
_client_cache: Dict[str, 'HeetchClient'] = {}

# Stockage global pour les sessions Playwright par client_id
# Format: {client_id: {"playwright": ..., "browser": ..., "context": ..., "page": ..., "loop": ...}}
_playwright_sessions: Dict[str, Dict[str, Any]] = {}
_session_lock = Lock()


class HeetchClient:
    """
    Client pour scraper les données Heetch via le site driver.heetch.com.
    Utilise Playwright pour gérer la session et les cookies.
    """
    
    def __init__(self, org_id: Optional[str] = None):
        self._cookies: Optional[list[Dict[str, Any]]] = None
        self._cookies_expires_at: float = 0.0
        # ID unique pour ce client (pour stocker la session Playwright)
        import uuid
        self._client_id = str(uuid.uuid4())
        self.org_id = org_id or "default_org"
        self.base_url = "https://driver.heetch.com"
        self.auth_url = "https://auth.heetch.com/?client_id=driver-portal&redirect_uri=https://driver.heetch.com/api/callback?requestURL=/dashboard"
        self._phone_number: Optional[str] = None
        self._auth_api = HeetchAuthAPI()
        self._token: Optional[str] = None
    
    def _get_session_key(self, phone: Optional[str] = None) -> str:
        """Génère une clé de session basée sur org_id + phone_number."""
        phone_to_use = phone or self._phone_number or "unknown"
        return f"{self.org_id}:{phone_to_use}"
    
    def _normalize_cookies_for_playwright(self, cookies: list) -> list:
        """
        Normalise les cookies pour qu'ils soient compatibles avec Playwright storage_state.
        Assure que tous les cookies ont les champs requis et au bon format.
        """
        normalized = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                logger.warning(f"[HEETCH] Cookie ignoré car ce n'est pas un dict: {type(cookie)}")
                continue
            
            # Créer un cookie normalisé avec les champs requis
            normalized_cookie = {
                "name": str(cookie.get("name", "")),
                "value": str(cookie.get("value", "")),
                "domain": str(cookie.get("domain", "")),
                "path": str(cookie.get("path", "/")),
            }
            
            # Ajouter expires si présent (doit être un timestamp Unix en secondes)
            if "expires" in cookie:
                expires = cookie["expires"]
                if isinstance(expires, (int, float)):
                    normalized_cookie["expires"] = int(expires)
                elif isinstance(expires, str):
                    try:
                        # Si c'est une chaîne, essayer de la convertir en timestamp
                        from datetime import datetime
                        dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
                        normalized_cookie["expires"] = int(dt.timestamp())
                    except:
                        logger.debug(f"[HEETCH] Impossible de convertir expires '{expires}' pour cookie {normalized_cookie.get('name')}")
            
            # Ajouter httpOnly si présent
            if "httpOnly" in cookie:
                normalized_cookie["httpOnly"] = bool(cookie["httpOnly"])
            
            # Ajouter secure si présent
            if "secure" in cookie:
                normalized_cookie["secure"] = bool(cookie["secure"])
            
            # Ajouter sameSite si présent (doit être "Strict", "Lax", ou "None")
            if "sameSite" in cookie and cookie["sameSite"]:
                same_site = cookie["sameSite"]
                if same_site in ["Strict", "Lax", "None"]:
                    normalized_cookie["sameSite"] = same_site
                elif same_site.lower() in ["strict", "lax", "none"]:
                    normalized_cookie["sameSite"] = same_site.capitalize() if same_site.lower() != "none" else "None"
            
            normalized.append(normalized_cookie)
        
        return normalized
        
    def _close_playwright(self):
        """Ferme Playwright et libère les ressources."""
        # Pour l'API async, la fermeture se fait dans les fonctions async
        pass
    
    def _load_cookies_from_db(self, phone_number: str) -> bool:
        """
        Charge les cookies depuis la base de données pour un numéro de téléphone donné.
        
        Returns:
            True si des cookies valides ont été trouvés et chargés
        """
        try:
            from app.core.supabase_db import SupabaseDB
            from app.models.heetch_session_cookies import HeetchSessionCookies
            from datetime import datetime
            
            db = SupabaseDB()
            # Rechercher par org_id + phone_number, en excluant les cookies marqués comme invalides
            session_cookies = db.query(HeetchSessionCookies).filter(
                HeetchSessionCookies.org_id == self.org_id,
                HeetchSessionCookies.phone_number == phone_number,
                HeetchSessionCookies.invalid_at.is_(None)  # Ne prendre que les cookies non marqués comme invalides
            ).first()
            
            if session_cookies and session_cookies.expires_at > datetime.utcnow():
                cookies_raw = session_cookies.cookies
                logger.debug(f"[HEETCH] Cookies bruts chargés de la DB, type: {type(cookies_raw)}")
                
                # Gérer différents formats de désérialisation JSONB
                if isinstance(cookies_raw, str):
                    # Si c'est une chaîne JSON, la désérialiser
                    try:
                        import json
                        cookies_raw = json.loads(cookies_raw)
                        logger.debug("[HEETCH] Cookies désérialisés depuis chaîne JSON")
                    except Exception as e:
                        logger.error(f"[HEETCH] Erreur lors de la désérialisation JSON: {e}")
                        return False
                
                self._cookies = cookies_raw
                
                # Vérifier le type des cookies (devrait être une liste)
                if not isinstance(self._cookies, list):
                    logger.warning(f"[HEETCH] Les cookies chargés ne sont pas une liste, type: {type(self._cookies)}, tentative de conversion...")
                    # Si c'est un dict avec une clé 'cookies', extraire la liste
                    if isinstance(self._cookies, dict) and 'cookies' in self._cookies:
                        self._cookies = self._cookies['cookies']
                        logger.info("[HEETCH] Cookies extraits depuis dict avec clé 'cookies'")
                    elif isinstance(self._cookies, dict):
                        # Si c'est directement un dict, convertir en liste
                        self._cookies = [self._cookies] if self._cookies else []
                        logger.info("[HEETCH] Cookie unique converti en liste")
                    else:
                        logger.error(f"[HEETCH] Format de cookies inattendu et non convertible: {type(self._cookies)}")
                        return False
                
                # Convertir expires_at en timestamp
                expires_timestamp = session_cookies.expires_at.timestamp()
                self._cookies_expires_at = expires_timestamp
                logger.info(f"[HEETCH] {len(self._cookies) if self._cookies else 0} cookies chargés depuis la DB pour {phone_number} (expire: {session_cookies.expires_at})")
                # Log du premier cookie pour vérifier le format
                if self._cookies and len(self._cookies) > 0:
                    first_cookie = self._cookies[0]
                    logger.debug(f"[HEETCH] Exemple de cookie chargé: name={first_cookie.get('name')}, domain={first_cookie.get('domain')}, keys={list(first_cookie.keys())}")
                return True
            elif session_cookies:
                logger.info(f"[HEETCH] Cookies expirés dans la DB pour {phone_number} (expiré le: {session_cookies.expires_at})")
                # Marquer comme invalides au lieu de supprimer (pour garder l'historique)
                session_cookies.invalid_at = datetime.utcnow()
                db.merge(session_cookies)
                db.commit()
            
            return False
        except Exception as e:
            logger.debug(f"[HEETCH] Erreur lors du chargement des cookies depuis la DB: {e}")
            return False
    
    def _save_cookies_to_db(self, phone_number: str) -> None:
        """
        Sauvegarde les cookies dans la base de données pour un numéro de téléphone donné.
        """
        try:
            from app.core.supabase_db import SupabaseDB
            from app.models.heetch_session_cookies import HeetchSessionCookies
            from datetime import datetime, timedelta
            import uuid
            
            if not self._cookies:
                return
            
            db = SupabaseDB()
            
            # Vérifier si une entrée existe déjà pour cet org_id + phone_number (même si marquée comme invalide)
            existing = db.query(HeetchSessionCookies).filter(
                HeetchSessionCookies.org_id == self.org_id,
                HeetchSessionCookies.phone_number == phone_number
            ).first()
            
            # Calculer expires_at depuis le timestamp
            expires_at = datetime.fromtimestamp(self._cookies_expires_at)
            
            if existing:
                # Mettre à jour l'entrée existante avec de nouveaux cookies valides
                existing.cookies = self._cookies
                existing.expires_at = expires_at
                existing.invalid_at = None  # Réinitialiser invalid_at car les nouveaux cookies sont valides
                db.merge(existing)
            else:
                # Créer une nouvelle entrée avec un UUID généré
                session_cookies = HeetchSessionCookies(
                    id=uuid.uuid4(),
                    org_id=self.org_id,
                    phone_number=phone_number,
                    cookies=self._cookies,
                    expires_at=expires_at,
                    invalid_at=None  # Nouveaux cookies sont valides
                )
                db.merge(session_cookies)
            
            db.commit()
            # Log des domaines de cookies sauvegardés pour debugging
            cookie_domains = {}
            for cookie in self._cookies:
                domain = cookie.get('domain', 'N/A')
                if domain not in cookie_domains:
                    cookie_domains[domain] = 0
                cookie_domains[domain] += 1
            domains_summary = ", ".join([f"{domain}: {count}" for domain, count in cookie_domains.items()])
            logger.info(f"[HEETCH] {len(self._cookies)} cookies sauvegardés dans la DB pour {phone_number} (domaines: {domains_summary})")
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la sauvegarde des cookies dans la DB: {e}", exc_info=True)
            # Ne pas lever d'exception, la sauvegarde des cookies n'est pas critique
    
    def _get_cookies(self, phone: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        Récupère les cookies de session. Essaie de les charger depuis la DB si non présents en mémoire.
        Si expirés ou absents, lève une exception.
        La connexion doit être faite explicitement via start_login() puis complete_login() ou auto_login().
        
        Args:
            phone: Numéro de téléphone pour charger les cookies depuis la DB si nécessaire
        """
        # Si on a des cookies en mémoire et qu'ils sont valides, les retourner
        if self._cookies and time.time() < self._cookies_expires_at:
            return self._cookies
        
        # Sinon, essayer de charger depuis la DB si on a un numéro de téléphone
        if phone:
            cookies_loaded = self._load_cookies_from_db(phone)
            if cookies_loaded and self._cookies and time.time() < self._cookies_expires_at:
                logger.info(f"[HEETCH] Cookies chargés depuis la DB pour {phone}")
                return self._cookies
        
        # Sinon, lever une exception pour indiquer qu'une connexion est nécessaire
        raise RuntimeError(
            "Session expirée ou absente. "
            "Utilisez /heetch/auth/start puis /heetch/auth/complete pour vous connecter, "
            "ou laissez le système se connecter automatiquement."
        )
    
    def ensure_authenticated(self, phone: Optional[str] = None) -> bool:
        """
        S'assure que la session est authentifiée, sans faire le flux complet si les cookies sont valides.
        Cette méthode est plus légère que auto_login car elle ne teste pas avec une requête API.
        
        Args:
            phone: Numéro de téléphone (utilise HEETCH_LOGIN si non fourni)
        
        Returns:
            True si authentifié, False si besoin de connexion
        """
        if not phone:
            phone = getattr(settings, 'heetch_login', None)
        
        if not phone:
            return False
        
        # Essayer de charger les cookies depuis la DB si non présents en mémoire
        if not self._cookies or time.time() >= self._cookies_expires_at:
            cookies_loaded = self._load_cookies_from_db(phone)
            if cookies_loaded and self._cookies and time.time() < self._cookies_expires_at:
                logger.info("[HEETCH] Cookies chargés depuis la DB, session valide")
                return True
        
        # Si on a des cookies valides en mémoire
        if self._cookies and time.time() < self._cookies_expires_at:
            logger.info("[HEETCH] Cookies valides en mémoire, session active")
            return True
        
        return False
    
    def auto_login(self, phone: Optional[str] = None, password: Optional[str] = None, sms_code: Optional[str] = None) -> bool:
        """
        Connexion automatique : essaie d'abord avec les cookies sauvegardés,
        puis fait le flux complet (téléphone → SMS → code → mot de passe) si nécessaire.
        
        Args:
            phone: Numéro de téléphone (utilise HEETCH_LOGIN si non fourni)
            password: Mot de passe (utilise HEETCH_PASSWORD si non fourni)
            sms_code: Code SMS (utilise HEETCH_2FA_CODE si non fourni, requis si flux complet nécessaire)
        
        Returns:
            True si la connexion réussit
        """
        if not phone:
            phone = getattr(settings, 'heetch_login', None)
        if not password:
            password = getattr(settings, 'heetch_password', None)
        if not sms_code:
            sms_code = getattr(settings, 'heetch_2fa_code', None)
        
        if not phone or not password:
            raise ValueError("HEETCH_LOGIN et HEETCH_PASSWORD doivent être définis pour la connexion automatique")
        
        # Vérifier d'abord si on a déjà une session valide (sans tester avec une requête)
        if self.ensure_authenticated(phone):
            logger.info("[HEETCH] Session déjà authentifiée, pas besoin de reconnexion")
            return True
        
        # Si on n'a pas de cookies valides, charger depuis la DB et vérifier
        cookies_loaded = self._load_cookies_from_db(phone)
        if cookies_loaded and self._cookies and time.time() < self._cookies_expires_at:
            logger.info("[HEETCH] Cookies chargés depuis la DB, session valide (pas de reconnexion nécessaire)")
            return True
        
        # Si les cookies ne fonctionnent pas, faire le flux complet
        logger.info("[HEETCH] Démarrage du flux de connexion complet (téléphone → SMS → code → mot de passe)")
        
        # Étape 1 : Envoyer le SMS
        try:
            result = self.start_login(phone)
            if result.get("status") == "already_logged_in":
                logger.info("[HEETCH] Déjà connecté après start_login")
                return True
            if result.get("status") == "phone_remembered":
                logger.info("[HEETCH] Numéro mémorisé, tentative de connexion directe avec mot de passe")
                # Si le numéro est mémorisé, on peut essayer de se connecter directement
                # Mais pour l'instant, on continue avec le flux SMS normal
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de start_login: {e}", exc_info=True)
            raise
        
        # Étape 2 : Compléter avec le code SMS et le mot de passe
        if not sms_code:
            raise ValueError(
                "Code SMS requis pour la connexion. "
                "Configurez HEETCH_2FA_CODE dans les variables d'environnement "
                "ou utilisez /heetch/auth/start puis /heetch/auth/complete manuellement."
            )
        
        logger.info("[HEETCH] Finalisation de la connexion avec code SMS et mot de passe")
        return self.complete_login(sms_code, password)
    
    def _run_async_in_thread(self, async_func, *args, session_key: Optional[str] = None, **kwargs):
        """
        Exécute une fonction async Playwright dans un thread séparé.
        Si session_key est fourni et qu'une session existe, réutilise le même event loop.
        """
        def run_with_loop():
            import sys
            import threading
            
            # Si on a une session_key, essayer de réutiliser le même event loop
            loop_to_use = None
            if session_key:
                with _session_lock:
                    if session_key in _playwright_sessions:
                        session = _playwright_sessions[session_key]
                        stored_loop = session.get("event_loop")
                        stored_thread_id = session.get("thread_id")
                        current_thread_id = threading.current_thread().ident
                        
                        # Si c'est le même thread, on peut réutiliser le loop
                        if stored_thread_id == current_thread_id and stored_loop and not stored_loop.is_closed():
                            try:
                                # Vérifier que le loop est toujours actif
                                asyncio.set_event_loop(stored_loop)
                                loop_to_use = stored_loop
                                logger.info(f"[HEETCH] Réutilisation du même event loop pour la session {session_key}")
                            except Exception as e:
                                logger.debug(f"[HEETCH] Impossible de réutiliser le loop: {e}")
            
            # Si pas de loop réutilisable, en créer un nouveau
            if not loop_to_use:
                # Configurer la politique d'event loop pour Windows
                if sys.platform == 'win32':
                    policy = asyncio.WindowsProactorEventLoopPolicy()
                    asyncio.set_event_loop_policy(policy)
                    loop_to_use = asyncio.new_event_loop()
                else:
                    loop_to_use = asyncio.new_event_loop()
                asyncio.set_event_loop(loop_to_use)
                logger.info(f"[HEETCH] Nouvel event loop créé (platform: {sys.platform})")
            
            try:
                result = loop_to_use.run_until_complete(async_func(*args, **kwargs))
                logger.info("[HEETCH] Exécution async terminée avec succès")
                return result
            except Exception as e:
                logger.error(f"[HEETCH] Erreur dans l'exécution async: {e}", exc_info=True)
                raise
            finally:
                # Ne pas fermer le loop si on a une session active
                # Le loop sera réutilisé pour complete_login
                pass
        
        logger.info("[HEETCH] Soumission de la tâche au thread pool")
        future = _playwright_executor.submit(run_with_loop)
        try:
            result = future.result(timeout=120)  # Augmenter le timeout à 120 secondes
            logger.info("[HEETCH] Tâche terminée avec succès")
            return result
        except TimeoutError:
            logger.error("[HEETCH] Timeout lors de l'exécution de la tâche Playwright")
            raise RuntimeError("Timeout lors de l'initialisation de Playwright. Vérifiez que Playwright est installé avec 'playwright install chromium'")
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de l'exécution: {e}", exc_info=True)
            raise
    
    async def _handle_captcha_with_mouse_movement(self, page: Page) -> bool:
        """
        Détecte et gère le captcha en simulant un mouvement de souris aléatoire avant de cliquer dessus.
        Gère les captchas dans des iframes (reCAPTCHA, hCaptcha).
        
        Args:
            page: La page Playwright
            
        Returns:
            True si un captcha a été détecté et géré, False sinon
        """
        try:
            # Sélecteurs possibles pour le captcha (reCAPTCHA, hCaptcha, etc.)
            # D'abord chercher les iframes (cas le plus courant)
            captcha_iframe_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                'iframe[title*="reCAPTCHA"]',
                'iframe[title*="hCaptcha"]',
            ]
            
            # Sélecteurs pour les éléments de captcha directs
            captcha_direct_selectors = [
                '[class*="recaptcha"]',
                '[class*="hcaptcha"]',
                '[id*="recaptcha"]',
                '[id*="hcaptcha"]',
                '.g-recaptcha',
                '#g-recaptcha',
                '[data-sitekey]',
                '.h-captcha',
            ]
            
            captcha_element = None
            captcha_frame = None
            iframe_element = None
            is_iframe = False
            
            # D'abord chercher dans les iframes
            for selector in captcha_iframe_selectors:
                try:
                    iframe_el = await page.query_selector(selector)
                    if iframe_el and await iframe_el.is_visible():
                        logger.info(f"[HEETCH] Iframe captcha détecté avec sélecteur: {selector}")
                        # Garder la référence à l'iframe
                        iframe_element = iframe_el
                        # Obtenir le frame
                        captcha_frame = await iframe_el.content_frame()
                        if captcha_frame:
                            # Chercher le bouton/checkbox dans l'iframe
                            checkbox_selectors = [
                                '.recaptcha-checkbox-border',
                                '#recaptcha-anchor',
                                '.hcaptcha-box',
                                '[role="checkbox"]',
                                '.checkbox',
                            ]
                            for checkbox_selector in checkbox_selectors:
                                try:
                                    checkbox = await captcha_frame.query_selector(checkbox_selector)
                                    if checkbox:
                                        captcha_element = checkbox
                                        is_iframe = True
                                        logger.info(f"[HEETCH] Élément captcha trouvé dans iframe: {checkbox_selector}")
                                        break
                                except:
                                    continue
                            if captcha_element:
                                break
                except:
                    continue
            
            # Si pas trouvé dans iframe, chercher directement dans la page
            if not captcha_element:
                for selector in captcha_direct_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element and await element.is_visible():
                            captcha_element = element
                            logger.info(f"[HEETCH] Captcha détecté avec sélecteur direct: {selector}")
                            break
                    except:
                        continue
            
            if not captcha_element:
                logger.debug("[HEETCH] Aucun captcha détecté")
                return False
            
            # Obtenir la position du captcha (depuis l'iframe si nécessaire)
            if is_iframe and captcha_frame and iframe_element:
                # Pour les iframes, utiliser la position de l'iframe + position relative dans l'iframe
                iframe_box = await iframe_element.bounding_box()
                checkbox_box = await captcha_element.bounding_box()
                if iframe_box and checkbox_box:
                    captcha_x = iframe_box['x'] + checkbox_box['x'] + checkbox_box['width'] / 2
                    captcha_y = iframe_box['y'] + checkbox_box['y'] + checkbox_box['height'] / 2
                else:
                    logger.warning("[HEETCH] Impossible d'obtenir la position du captcha dans l'iframe")
                    return False
            else:
                box = await captcha_element.bounding_box()
                if not box:
                    logger.warning("[HEETCH] Impossible d'obtenir la position du captcha")
                    return False
                captcha_x = box['x'] + box['width'] / 2
                captcha_y = box['y'] + box['height'] / 2
            
            logger.info(f"[HEETCH] Position du captcha: x={captcha_x}, y={captcha_y}")
            
            # Simuler un mouvement de souris aléatoire vers le captcha
            # Commencer depuis une position aléatoire (dans une zone autour de la page)
            start_x = random.randint(100, 500)
            start_y = random.randint(100, 500)
            
            # Déplacer la souris vers le captcha avec des points intermédiaires aléatoires
            # pour simuler un mouvement naturel
            num_steps = random.randint(3, 7)  # Nombre de points intermédiaires
            
            for step in range(num_steps):
                # Calculer la position intermédiaire
                progress = (step + 1) / num_steps
                # Ajouter de l'aléatoire pour rendre le mouvement plus naturel
                target_x = start_x + (captcha_x - start_x) * progress + random.randint(-30, 30)
                target_y = start_y + (captcha_y - start_y) * progress + random.randint(-30, 30)
                
                # Déplacer la souris vers cette position
                await page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
                # Petite pause aléatoire entre les mouvements
                await page.wait_for_timeout(random.randint(50, 150))
            
            # Arriver finalement sur le captcha avec un petit mouvement aléatoire
            final_x = captcha_x + random.randint(-5, 5)
            final_y = captcha_y + random.randint(-5, 5)
            await page.mouse.move(final_x, final_y, steps=random.randint(3, 8))
            await page.wait_for_timeout(random.randint(100, 300))
            
            logger.info(f"[HEETCH] Mouvement de souris simulé vers le captcha")
            
            # Cliquer sur le captcha
            try:
                if is_iframe and captcha_frame:
                    # Cliquer dans l'iframe
                    await captcha_element.click(timeout=5000)
                    logger.info("[HEETCH] Captcha cliqué avec succès dans l'iframe")
                else:
                    # Cliquer directement sur l'élément
                    await captcha_element.click(timeout=5000)
                    logger.info("[HEETCH] Captcha cliqué avec succès")
            except Exception as e:
                logger.warning(f"[HEETCH] Impossible de cliquer sur le captcha via l'élément: {e}")
                # Essayer de cliquer directement aux coordonnées
                try:
                    await page.mouse.click(final_x, final_y)
                    logger.info("[HEETCH] Captcha cliqué via coordonnées de souris")
                except Exception as e2:
                    logger.warning(f"[HEETCH] Impossible de cliquer sur le captcha via coordonnées: {e2}")
            
            # Attendre un peu pour que le captcha se résolve
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            return True
            
        except Exception as e:
            logger.debug(f"[HEETCH] Erreur lors de la gestion du captcha: {e}")
            return False
    
    def start_login(self, phone: Optional[str] = None) -> Dict[str, Any]:
        """
        Étape 1 : Entre le numéro de téléphone et déclenche l'envoi du SMS.
        
        Args:
            phone: Numéro de téléphone (utilise HEETCH_LOGIN si non fourni)
        
        Returns:
            Dict avec status et message indiquant que le SMS a été envoyé
        """
        if not phone:
            phone = getattr(settings, 'heetch_login', None)
        
        if not phone:
            raise ValueError("HEETCH_LOGIN doit être défini dans les variables d'environnement")
        
        async def _do_start_login_async():
            """Version async de start_login."""
            logger.info("[HEETCH] Démarrage de l'initialisation Playwright")
            
            # Stocker le numéro de téléphone pour pouvoir réutiliser la session
            self._phone_number = phone
            
            # AVANT de créer le contexte Playwright, charger les cookies depuis la DB
            # Cela permet de restaurer la session et éviter de redemander le numéro/SMS
            if phone:
                cookies_loaded = self._load_cookies_from_db(phone)
                if cookies_loaded and self._cookies:
                    logger.info(f"[HEETCH] {len(self._cookies)} cookies chargés depuis la DB, tentative de restauration de session")
                else:
                    logger.info("[HEETCH] Aucun cookie trouvé en DB, connexion complète nécessaire")
            
            try:
                # Créer une nouvelle session Playwright (sera réutilisée dans complete_login via le cache)
                logger.info("[HEETCH] Démarrage de async_playwright()...")
                playwright = await async_playwright().start()
                logger.info("[HEETCH] Playwright démarré, lancement de Chromium...")
                # Mode headless contrôlé par variable d'environnement (par défaut False pour voir le navigateur)
                headless_mode = getattr(settings, 'heetch_headless', False)
                browser = await playwright.chromium.launch(
                    headless=headless_mode,
                    slow_mo=500  # Ralentir les actions de 500ms pour voir ce qui se passe
                )
                logger.info(f"[HEETCH] Chromium lancé (headless={headless_mode}), création du contexte...")
                
                # Préparer les options du contexte
                context_options = {
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
                }
                
                # Restaurer les cookies depuis la DB (chargés plus haut) pour éviter de redemander le numéro
                if self._cookies:
                    logger.info(f"[HEETCH] Injection de {len(self._cookies)} cookies dans le contexte Playwright")
                    # Normaliser les cookies pour Playwright
                    normalized_cookies = self._normalize_cookies_for_playwright(self._cookies)
                    logger.info(f"[HEETCH] {len(normalized_cookies)} cookies normalisés pour injection")
                    
                    # Log des domaines de cookies injectés pour debugging
                    cookie_domains = {}
                    for cookie in normalized_cookies:
                        domain = cookie.get('domain', 'N/A')
                        if domain not in cookie_domains:
                            cookie_domains[domain] = 0
                        cookie_domains[domain] += 1
                    domains_summary = ", ".join([f"{domain}: {count}" for domain, count in cookie_domains.items()])
                    logger.info(f"[HEETCH] Cookies injectés par domaine: {domains_summary}")
                    # Log des cookies d'authentification pour debugging
                    auth_cookies = [c for c in normalized_cookies if c.get('name') in ['heetch_auth_token', 'heetch_driver_session']]
                    if auth_cookies:
                        for cookie in auth_cookies:
                            logger.info(f"[HEETCH] Cookie d'auth injecté: {cookie.get('name')} (domaine: {cookie.get('domain', 'N/A')})")
                    context_options["storage_state"] = {
                        "cookies": normalized_cookies
                    }
                
                context = await browser.new_context(**context_options)
                logger.info("[HEETCH] Contexte créé, création de la page...")
                page = await context.new_page()
                logger.info("[HEETCH] Page créée avec succès")
                
                # Stocker la session pour complete_login (utiliser org_id + phone comme clé)
                session_key = self._get_session_key(phone)
                current_loop = asyncio.get_event_loop()
                with _session_lock:
                    _playwright_sessions[session_key] = {
                        "playwright": playwright,
                        "browser": browser,
                        "context": context,
                        "page": page,
                        "event_loop": current_loop,
                        "thread_id": threading.current_thread().ident
                    }
                logger.info(f"[HEETCH] Session stockée dans le cache avec la clé: {session_key} (thread_id: {threading.current_thread().ident})")
            except Exception as e:
                logger.error(f"[HEETCH] Erreur lors de l'initialisation Playwright: {e}", exc_info=True)
                raise RuntimeError(f"Erreur lors de l'initialisation de Playwright: {e}. Vérifiez que Playwright est installé avec 'playwright install chromium'")
            
            logger.info(f"[HEETCH] Démarrage connexion pour {phone}")
            
            # Normaliser le format du numéro de téléphone pour Heetch
            # Heetch attend le format international avec +33
            normalized_phone = phone
            
            # Si le numéro commence par 0, le convertir en +33
            if phone.startswith('0') and len(phone) == 10:
                # Format français: 0612345678 -> +33612345678
                normalized_phone = '+33' + phone[1:]
            elif phone.startswith('33') and len(phone) == 11:
                # Format: 33612345678 -> +33612345678
                normalized_phone = '+' + phone
            elif not phone.startswith('+'):
                # Si pas de +, essayer d'ajouter +33
                if len(phone) == 9:
                    # 9 chiffres sans indicatif -> +33 + numéro
                    normalized_phone = '+33' + phone
                elif len(phone) == 10 and phone.startswith('0'):
                    # 10 chiffres commençant par 0 -> +33 + numéro sans le 0
                    normalized_phone = '+33' + phone[1:]
            
            logger.info(f"[HEETCH] Numéro normalisé: {normalized_phone} (original: {phone})")
            
            # Aller sur la page de login
            # Utiliser "load" au lieu de "networkidle" car certaines pages chargent des ressources en continu
            logger.info(f"[HEETCH] Navigation vers {self.auth_url}...")
            await page.goto(self.auth_url, wait_until="load", timeout=60000)
            logger.info("[HEETCH] Page chargée, vérification de l'état...")
            # Attendre que les redirections potentielles soient terminées
            await page.wait_for_timeout(3000)
            # Attendre que la navigation soit stable (pas de redirections en cours)
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass  # Si networkidle timeout, continuer quand même
            
            # Vérifier si les cookies sont bien présents dans le contexte après navigation
            cookies_after_nav = await context.cookies()
            logger.info(f"[HEETCH] Cookies présents dans le contexte après navigation: {len(cookies_after_nav)} cookies")
            if cookies_after_nav:
                cookie_domains_after = {}
                for cookie in cookies_after_nav:
                    domain = cookie.get('domain', 'N/A')
                    if domain not in cookie_domains_after:
                        cookie_domains_after[domain] = 0
                    cookie_domains_after[domain] += 1
                domains_summary_after = ", ".join([f"{domain}: {count}" for domain, count in cookie_domains_after.items()])
                logger.info(f"[HEETCH] Cookies après navigation par domaine: {domains_summary_after}")
            
            # Vérifier si on est déjà connecté (grâce aux cookies restaurés depuis la DB)
            current_url = page.url
            logger.info(f"[HEETCH] URL après chargement: {current_url}")
            
            # On considère la session comme déjà connectée UNIQUEMENT si :
            # 1. L'hôte est driver.heetch.com (pas auth.heetch.com)
            # 2. L'URL ne contient pas /login
            # 3. ET on a vraiment des cookies valides (test avec une requête API légère)
            from urllib.parse import urlparse
            parsed_url = urlparse(current_url)
            host = parsed_url.netloc or ""
            is_driver_host = "driver.heetch.com" in host
            is_login_path = "/login" in current_url.lower()
            is_auth_host = "auth.heetch.com" in host
            
            # Si on est sur auth.heetch.com/login, vérifier quel type de formulaire apparaît
            if is_auth_host and is_login_path:
                # Attendre un peu pour que le formulaire se charge
                await page.wait_for_timeout(2000)
                
                # Vérifier si on voit un champ mot de passe (numéro mémorisé) ou un champ téléphone (connexion complète nécessaire)
                try:
                    password_input = await page.query_selector('input[type="password"]')
                    phone_input = await page.query_selector('input.f-FormEl, input[type="tel"], input[name="phone"], input[placeholder*="téléphone" i], input[placeholder*="phone" i]')
                    
                    if password_input and await password_input.is_visible() and (not phone_input or not await phone_input.is_visible()):
                        # Champ mot de passe présent mais pas de champ téléphone = numéro mémorisé, cookies de "mémorisation" valides
                        logger.info("[HEETCH] ✅ Numéro déjà mémorisé (champ mot de passe détecté), les cookies de mémorisation sont valides")
                        logger.info("[HEETCH] Pas besoin de SMS, seule la connexion avec mot de passe est nécessaire")
                        # NE PAS marquer les cookies comme invalides car ils permettent de bypasser le SMS
                        # Les cookies seront mis à jour après complete_login avec le mot de passe
                        # Sauvegarder les cookies actuels (qui permettent de bypasser le SMS) pour les réutiliser
                        cookies = await context.cookies()
                        self._cookies = cookies  # Garder les cookies en mémoire pour complete_login
                        logger.info(f"[HEETCH] {len(cookies)} cookies conservés (permettent de bypasser le SMS)")
                        return {"status": "phone_remembered", "message": "Numéro déjà mémorisé grâce aux cookies, mot de passe requis (pas de SMS nécessaire)"}
                    else:
                        # Champ téléphone présent = même la mémorisation ne fonctionne plus, connexion complète nécessaire
                        logger.warning("[HEETCH] Champ téléphone détecté, les cookies de mémorisation sont également invalides")
                        if self._cookies:
                            # Marquer les cookies comme invalides dans la DB car même la mémorisation ne fonctionne plus
                            try:
                                from app.core.supabase_db import SupabaseDB
                                from app.models.heetch_session_cookies import HeetchSessionCookies
                                from datetime import datetime
                                db = SupabaseDB()
                                session_cookies = db.query(HeetchSessionCookies).filter(
                                    HeetchSessionCookies.org_id == self.org_id,
                                    HeetchSessionCookies.phone_number == phone,
                                    HeetchSessionCookies.invalid_at.is_(None)
                                ).first()
                                if session_cookies:
                                    session_cookies.invalid_at = datetime.utcnow()
                                    db.merge(session_cookies)
                                    db.commit()
                                    logger.info(f"[HEETCH] Cookies marqués comme invalides dans la DB pour {phone} (même la mémorisation ne fonctionne plus)")
                            except Exception as e:
                                logger.debug(f"[HEETCH] Erreur lors du marquage des cookies invalides: {e}")
                            # Réinitialiser les cookies en mémoire
                            self._cookies = None
                            self._cookies_expires_at = 0.0
                        # Continuer avec le processus de connexion complet (phone + SMS + password)
                except Exception as e:
                    logger.debug(f"[HEETCH] Erreur lors de la vérification du type de formulaire: {e}, continuation avec le processus normal")
                    # En cas d'erreur, continuer avec le processus normal (phone + SMS + password)
            
            # Si on est sur driver.heetch.com (pas sur /login), tester avec une requête API pour confirmer
            elif is_driver_host and not is_login_path:
                # Vérifier que les cookies d'authentification sont présents
                # Ces cookies sont critiques : heetch_auth_token (sur .heetch.com) et heetch_driver_session (sur driver.heetch.com)
                cookies = await context.cookies()
                cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
                cookie_domains = {cookie['name']: cookie.get('domain', '') for cookie in cookies}
                
                has_auth_token = 'heetch_auth_token' in cookie_dict
                has_driver_session = 'heetch_driver_session' in cookie_dict
                
                # Log détaillé pour debugging
                logger.info(f"[HEETCH] Cookies trouvés: {len(cookies)} cookies au total")
                if has_auth_token:
                    logger.info(f"[HEETCH] heetch_auth_token présent (domaine: {cookie_domains.get('heetch_auth_token', 'N/A')})")
                if has_driver_session:
                    logger.info(f"[HEETCH] heetch_driver_session présent (domaine: {cookie_domains.get('heetch_driver_session', 'N/A')})")
                
                if has_auth_token or has_driver_session:
                    logger.info("[HEETCH] ✅ Déjà connecté grâce aux cookies restaurés depuis la DB (bypass du numéro et SMS)")
                    # Récupérer tous les cookies (peut-être rafraîchis)
                    self._cookies = cookies
                    self._cookies_expires_at = time.time() + (24 * 60 * 60)
                    # Sauvegarder les cookies mis à jour dans la DB
                    self._save_cookies_to_db(phone)
                    logger.info(f"[HEETCH] {len(cookies)} cookies mis à jour et sauvegardés dans la DB")
                    return {"status": "already_logged_in", "message": "Session restaurée depuis la DB, déjà connecté (cookies rafraîchis sans SMS)"}
                else:
                    logger.warning("[HEETCH] Sur driver.heetch.com mais pas de token d'authentification dans les cookies, connexion nécessaire")
                    # Marquer les cookies comme invalides si on en avait chargés depuis la DB
                    if self._cookies:
                        logger.warning("[HEETCH] Les cookies chargés depuis la DB ne sont pas valides (pas de token après navigation)")
                        try:
                            from app.core.supabase_db import SupabaseDB
                            from app.models.heetch_session_cookies import HeetchSessionCookies
                            from datetime import datetime
                            db = SupabaseDB()
                            session_cookies = db.query(HeetchSessionCookies).filter(
                                HeetchSessionCookies.org_id == self.org_id,
                                HeetchSessionCookies.phone_number == phone,
                                HeetchSessionCookies.invalid_at.is_(None)
                            ).first()
                            if session_cookies:
                                session_cookies.invalid_at = datetime.utcnow()
                                db.merge(session_cookies)
                                db.commit()
                                logger.info(f"[HEETCH] Cookies marqués comme invalides dans la DB pour {phone}")
                        except Exception as e:
                            logger.debug(f"[HEETCH] Erreur lors du marquage des cookies invalides: {e}")
                        self._cookies = None
                        self._cookies_expires_at = 0.0
                    # Continuer avec le processus de connexion normal
            
            # Attendre que le formulaire soit chargé avec un timeout plus long
            # Essayer d'abord le sélecteur spécifique Heetch
            try:
                await page.wait_for_selector('input.f-FormEl, input[type="tel"], input[type="text"], input[name="phone"], input[placeholder*="téléphone" i], input[placeholder*="phone" i]', timeout=10000)
                logger.info("[HEETCH] Formulaire téléphone détecté")
                # Pause pour permettre à l'utilisateur de voir le formulaire
                await page.wait_for_timeout(1000)
            except Exception:
                # Le formulaire téléphone n'est pas présent, peut-être qu'on doit entrer directement le mot de passe
                logger.info("[HEETCH] Formulaire téléphone non détecté, peut-être que le numéro est déjà mémorisé")
                # Vérifier s'il y a un champ mot de passe
                try:
                    await page.wait_for_selector('input[type="password"]', timeout=5000)
                    logger.info("[HEETCH] Champ mot de passe détecté, le numéro est déjà mémorisé")
                    # Ne pas sauvegarder les cookies ici car on n'est pas encore authentifié
                    # Les cookies seront sauvegardés après complete_login avec le mot de passe
                    return {"status": "phone_remembered", "message": "Numéro déjà mémorisé, mot de passe requis"}
                except:
                    pass
            
            # Chercher le champ téléphone/login
            phone_selectors = [
                'input.f-FormEl',  # Classe spécifique Heetch
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="login"]',
                'input[placeholder*="téléphone" i]',
                'input[placeholder*="phone" i]',
                'input[placeholder*="numéro" i]',
                'input[id*="phone" i]',
                'input[id*="login" i]',
                'input[type="text"]',
                '.f-FormEl input',  # Alternative si c'est un conteneur
                'input[class*="f-FormEl"]'  # Si la classe est combinée avec d'autres
            ]
            
            phone_filled = False
            for selector in phone_selectors:
                try:
                    phone_input = await page.query_selector(selector)
                    if phone_input:
                        # Vérifier si l'élément est visible et éditable
                        is_visible = await phone_input.is_visible()
                        is_enabled = await phone_input.is_enabled()
                        if is_visible and is_enabled:
                            logger.info(f"[HEETCH] Tentative de remplissage avec sélecteur: {selector}")
                            # Essayer de cliquer d'abord pour s'assurer que l'input est focus
                            await phone_input.click()
                            await page.wait_for_timeout(300)  # Petite pause après le clic
                            
                            # Méthode 1: Utiliser fill() avec le numéro normalisé
                            try:
                                # Vider le champ au cas où il y aurait déjà quelque chose
                                await phone_input.fill('')
                                await page.wait_for_timeout(200)
                                # Remplir avec le numéro normalisé
                                await phone_input.fill(normalized_phone)
                                await page.wait_for_timeout(500)  # Attendre que la valeur soit mise à jour
                                # Déclencher les événements input et change pour que le formulaire détecte la valeur
                                await phone_input.evaluate('(element) => { element.dispatchEvent(new Event("input", { bubbles: true })); element.dispatchEvent(new Event("change", { bubbles: true })); }')
                                await page.wait_for_timeout(300)
                            except Exception as e1:
                                logger.debug(f"[HEETCH] fill() a échoué, tentative avec type(): {e1}")
                                # Méthode 2: Utiliser type() si fill() ne fonctionne pas
                                try:
                                    await phone_input.clear()
                                    await page.wait_for_timeout(200)
                                    await phone_input.type(normalized_phone, delay=100)  # Taper caractère par caractère avec délai
                                    await page.wait_for_timeout(500)
                                except Exception as e2:
                                    logger.warning(f"[HEETCH] type() a aussi échoué: {e2}")
                                    continue
                            
                            # Vérifier que le texte a bien été rempli
                            value = await phone_input.input_value()
                            logger.info(f"[HEETCH] Valeur dans l'input après remplissage: '{value}'")
                            
                            # Normaliser les valeurs pour la comparaison (enlever espaces, tirets, parenthèses, etc.)
                            def normalize_phone(phone_str: str) -> str:
                                """Normalise un numéro de téléphone en enlevant tous les caractères non numériques sauf + au début."""
                                if not phone_str:
                                    return ""
                                # Garder le + s'il est au début
                                has_plus = phone_str.startswith('+')
                                # Enlever tous les caractères non numériques
                                cleaned = ''.join(c for c in phone_str if c.isdigit())
                                # Remettre le + au début si présent
                                return ('+' + cleaned) if has_plus else cleaned
                            
                            normalized_phone_clean = normalize_phone(normalized_phone)
                            normalized_value_clean = normalize_phone(value)
                            original_phone_clean = normalize_phone(phone)
                            
                            logger.info(f"[HEETCH] Comparaison: original={original_phone_clean}, normalized={normalized_phone_clean}, value_normalized={normalized_value_clean}")
                            
                            # Vérifier si les numéros normalisés correspondent
                            if (normalized_value_clean == normalized_phone_clean or 
                                normalized_value_clean == original_phone_clean or
                                normalized_phone_clean in normalized_value_clean or
                                original_phone_clean in normalized_value_clean or
                                normalized_phone in value or 
                                phone in value or
                                # Vérifier aussi si les derniers chiffres correspondent (au cas où le formatage ajoute des espaces)
                                (len(normalized_value_clean) >= 8 and normalized_phone_clean[-8:] in normalized_value_clean)):
                                
                                # Vérifier s'il y a des messages d'erreur affichés
                                await page.wait_for_timeout(500)  # Attendre que la validation se fasse
                                
                                # Chercher les messages d'erreur
                                error_selectors = [
                                    '[class*="error"]',
                                    '[class*="invalid"]',
                                    '[role="alert"]',
                                    '.error-message',
                                    '[data-error]',
                                    'text=/Numéro de téléphone invalide/i',
                                    'text=/invalid/i',
                                    'text=/erreur/i'
                                ]
                                
                                has_error = False
                                error_message = None
                                for error_selector in error_selectors:
                                    try:
                                        error_element = await page.query_selector(error_selector)
                                        if error_element:
                                            is_visible = await error_element.is_visible()
                                            if is_visible:
                                                error_text = await error_element.inner_text()
                                                if error_text and len(error_text.strip()) > 0:
                                                    has_error = True
                                                    error_message = error_text
                                                    logger.warning(f"[HEETCH] Message d'erreur détecté: {error_text}")
                                                    break
                                    except:
                                        continue
                                
                                if has_error:
                                    logger.error(f"[HEETCH] Le formulaire indique une erreur: {error_message}")
                                    logger.error(f"[HEETCH] Numéro saisi: {normalized_phone}, Valeur dans l'input: {value}")
                                    # Essayer avec un format différent
                                    if normalized_phone.startswith('+33'):
                                        # Essayer sans le +33, juste avec 0
                                        alternative_phone = '0' + normalized_phone[3:]
                                        logger.info(f"[HEETCH] Tentative avec format alternatif: {alternative_phone}")
                                        try:
                                            await phone_input.fill('')
                                            await page.wait_for_timeout(200)
                                            await phone_input.fill(alternative_phone)
                                            await page.wait_for_timeout(500)
                                            await phone_input.evaluate('(element) => { element.dispatchEvent(new Event("input", { bubbles: true })); element.dispatchEvent(new Event("change", { bubbles: true })); }')
                                            await page.wait_for_timeout(1000)
                                            # Vérifier à nouveau les erreurs
                                            has_error = False
                                            for error_selector in error_selectors:
                                                try:
                                                    error_element = await page.query_selector(error_selector)
                                                    if error_element and await error_element.is_visible():
                                                        error_text = await error_element.inner_text()
                                                        if error_text and len(error_text.strip()) > 0:
                                                            has_error = True
                                                            break
                                                except:
                                                    continue
                                        except Exception as e:
                                            logger.debug(f"[HEETCH] Erreur lors de la tentative avec format alternatif: {e}")
                                
                                if not has_error:
                                    phone_filled = True
                                    logger.info(f"[HEETCH] Numéro de téléphone rempli avec succès (sélecteur: {selector}, valeur: {value})")
                                    # Pause pour permettre à l'utilisateur de voir le numéro rempli
                                    await page.wait_for_timeout(1000)
                                    break
                                else:
                                    logger.warning(f"[HEETCH] Le numéro n'a pas été accepté par le formulaire. Erreur: {error_message}")
                            else:
                                logger.warning(f"[HEETCH] Le numéro n'a pas été correctement rempli. Attendu: {phone}, Obtenu: {value}")
                                # Essayer une dernière fois avec une méthode différente
                                try:
                                    # Échapper les guillemets pour JavaScript
                                    escaped_phone = normalized_phone.replace('"', '\\"').replace("'", "\\'")
                                    await phone_input.evaluate(f'(element) => {{ element.value = "{escaped_phone}"; element.dispatchEvent(new Event("input", {{ bubbles: true }})); element.dispatchEvent(new Event("change", {{ bubbles: true }})); element.dispatchEvent(new Event("blur", {{ bubbles: true }})); }}')
                                    await page.wait_for_timeout(500)
                                    value = await phone_input.input_value()
                                    
                                    # Re-normaliser pour la comparaison
                                    def normalize_phone(phone_str: str) -> str:
                                        if not phone_str:
                                            return ""
                                        has_plus = phone_str.startswith('+')
                                        cleaned = ''.join(c for c in phone_str if c.isdigit())
                                        return ('+' + cleaned) if has_plus else cleaned
                                    
                                    normalized_value_clean = normalize_phone(value)
                                    normalized_phone_clean = normalize_phone(normalized_phone)
                                    original_phone_clean = normalize_phone(phone)
                                    
                                    if (normalized_phone_clean in normalized_value_clean or 
                                        original_phone_clean in normalized_value_clean or
                                        normalized_phone in value or 
                                        phone in value or
                                        (len(normalized_value_clean) >= 8 and normalized_phone_clean[-8:] in normalized_value_clean)):
                                        phone_filled = True
                                        logger.info(f"[HEETCH] Numéro rempli avec evaluate() (valeur: {value})")
                                        await page.wait_for_timeout(1000)
                                        break
                                except Exception as e3:
                                    logger.debug(f"[HEETCH] evaluate() a échoué: {e3}")
                        else:
                            logger.debug(f"[HEETCH] Sélecteur {selector} trouvé mais non visible/enabled (visible={is_visible}, enabled={is_enabled})")
                except Exception as e:
                    logger.debug(f"[HEETCH] Sélecteur {selector} non trouvé: {e}")
                    continue
            
            if not phone_filled:
                raise RuntimeError("Impossible de trouver le champ téléphone/login sur la page de login")
            
            # Cliquer sur le bouton pour envoyer le SMS (Continuer)
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Continuer")',
                'button:has-text("Envoyer")',
                'button:has-text("Connexion")',
                'button:has-text("Se connecter")',
                'button:has-text("Suivant")',
                'button:has-text("Next")',
                'input[type="submit"]',
                'form button',  # N'importe quel bouton dans un formulaire
                'button[class*="submit"]',  # Bouton avec "submit" dans la classe
                'button[class*="continue"]',  # Bouton avec "continue" dans la classe
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = await page.query_selector(selector)
                    if submit_button:
                        is_visible = await submit_button.is_visible()
                        is_enabled = await submit_button.is_enabled()
                        button_text = await submit_button.inner_text() if await submit_button.is_visible() else ""
                        logger.info(f"[HEETCH] Bouton trouvé avec sélecteur {selector}: visible={is_visible}, enabled={is_enabled}, text='{button_text}'")
                        
                        if is_visible and is_enabled:
                            # Essayer plusieurs méthodes de clic
                            try:
                                await submit_button.click()
                                logger.info(f"[HEETCH] Clic réussi avec click() sur {selector}")
                            except Exception as e1:
                                logger.debug(f"[HEETCH] click() a échoué, tentative avec JavaScript: {e1}")
                                try:
                                    await submit_button.evaluate('(element) => element.click()')
                                    logger.info(f"[HEETCH] Clic réussi avec evaluate() sur {selector}")
                                except Exception as e2:
                                    logger.debug(f"[HEETCH] evaluate() a aussi échoué: {e2}")
                                    # Essayer de presser Enter sur l'input
                                    try:
                                        await phone_input.press('Enter')
                                        logger.info(f"[HEETCH] Enter pressé sur l'input")
                                    except Exception as e3:
                                        logger.debug(f"[HEETCH] Enter press a échoué: {e3}")
                                        continue
                            
                            submitted = True
                            logger.info(f"[HEETCH] Bouton cliqué avec sélecteur: {selector}")
                            # Attendre un peu pour que le captcha apparaisse
                            await page.wait_for_timeout(2000)
                            break
                except Exception as e:
                    logger.debug(f"[HEETCH] Sélecteur {selector} non trouvé: {e}")
                    continue
            
            if not submitted:
                # Dernière tentative: appuyer sur Enter dans l'input
                try:
                    logger.info("[HEETCH] Tentative avec Enter sur l'input comme dernier recours")
                    await phone_input.press('Enter')
                    await page.wait_for_timeout(2000)
                    submitted = True
                except Exception as e:
                    logger.error(f"[HEETCH] Impossible de soumettre le formulaire: {e}")
                    raise RuntimeError("Impossible de trouver le bouton pour envoyer le SMS")
            
            # Après avoir cliqué sur "Continuer", le captcha apparaît - le gérer maintenant
            logger.info("[HEETCH] Vérification et gestion du captcha après clic sur Continuer...")
            captcha_handled = await self._handle_captcha_with_mouse_movement(page)
            
            if captcha_handled:
                # Attendre un peu après avoir résolu le captcha
                await page.wait_for_timeout(1000)
                
                # Cliquer à nouveau sur "Continuer" après avoir résolu le captcha
                logger.info("[HEETCH] Clic sur Continuer après résolution du captcha...")
                submit_selectors_after_captcha = [
                    'button[type="submit"]',
                    'button:has-text("Continuer")',
                    'button:has-text("Envoyer")',
                    'button:has-text("Valider")',
                    'button:has-text("Vérifier")',
                    'button:has-text("Confirmer")',
                    'button[class*="submit"]',
                    'button[class*="continue"]',
                    'form button',
                ]
                
                submitted_after_captcha = False
                for selector in submit_selectors_after_captcha:
                    try:
                        submit_button = await page.query_selector(selector)
                        if submit_button:
                            is_visible = await submit_button.is_visible()
                            is_enabled = await submit_button.is_enabled()
                            button_text = await submit_button.inner_text() if await submit_button.is_visible() else ""
                            
                            if is_visible and is_enabled:
                                try:
                                    await submit_button.click()
                                    logger.info(f"[HEETCH] Bouton cliqué après captcha avec sélecteur: {selector} (text: {button_text})")
                                    submitted_after_captcha = True
                                    await page.wait_for_timeout(2000)  # Attendre que la page réagisse
                                    break
                                except Exception as e:
                                    logger.debug(f"[HEETCH] Impossible de cliquer avec {selector}: {e}")
                                    continue
                    except:
                        continue
                
                if not submitted_after_captcha:
                    logger.warning("[HEETCH] Impossible de trouver le bouton Continuer après le captcha, peut-être que le SMS a déjà été envoyé")
                else:
                    logger.info("[HEETCH] Bouton Continuer cliqué avec succès après résolution du captcha")
            
            # Attendre que la page suivante apparaisse (SMS ou mot de passe)
            logger.info("[HEETCH] Attente de la page suivante (SMS ou mot de passe)...")
            
            # Sélecteurs pour le champ code SMS
            sms_input_selectors = [
                'input[type="tel"]',
                'input[name*="code" i]',
                'input[placeholder*="code" i]',
                'input[id*="code" i]',
                'input[placeholder*="sms" i]',
                'input[class*="code" i]',
                'input[class*="sms" i]',
                'input.f-FormEl',  # Même classe que l'input téléphone mais pour le code
            ]
            
            # Sélecteurs pour le champ mot de passe
            password_input_selectors = [
                'input[type="password"]',
                'input[name*="password" i]',
                'input[id*="password" i]',
            ]
            
            # Attendre jusqu'à 15 secondes que la page suivante apparaisse
            next_page_detected = False
            page_type = None  # "sms" ou "password"
            max_wait_time = 15000  # 15 secondes
            check_interval = 500  # Vérifier toutes les 500ms
            elapsed_time = 0
            
            while elapsed_time < max_wait_time and not next_page_detected:
                # Vérifier l'URL actuelle
                current_url = page.url
                logger.debug(f"[HEETCH] URL actuelle: {current_url}, temps écoulé: {elapsed_time}ms")
                
                # Vérifier si on est sur une page différente (pas la page d'auth/login)
                if ("/login" not in current_url and "auth.heetch.com" not in current_url) or "sms" in current_url.lower() or "code" in current_url.lower() or "verify" in current_url.lower() or "/dashboard" in current_url:
                    logger.info(f"[HEETCH] Page changée vers: {current_url}")
                    next_page_detected = True
                    break
                
                # Vérifier d'abord si on voit un champ mot de passe (bypass du SMS grâce aux cookies)
                password_input = None
                for selector in password_input_selectors:
                    try:
                        found_input = await page.query_selector(selector)
                        if found_input and await found_input.is_visible():
                            password_input = found_input
                            break
                    except:
                        continue
                
                # Chercher les sélecteurs SMS
                sms_input = None
                for selector in sms_input_selectors:
                    try:
                        found_input = await page.query_selector(selector)
                        if found_input:
                            is_visible = await found_input.is_visible()
                            if is_visible:
                                # Vérifier que ce n'est pas le même input que le téléphone
                                input_value = await found_input.input_value()
                                if input_value != normalized_phone and input_value != phone:
                                    sms_input = found_input
                                    break
                    except:
                        continue
                
                # Si on voit un champ mot de passe mais PAS de champ SMS, les cookies permettent de bypasser le SMS
                if password_input and not sms_input:
                    logger.info("[HEETCH] ✅ Champ mot de passe détecté sans champ SMS : les cookies permettent de bypasser le SMS")
                    next_page_detected = True
                    page_type = "password"
                    break
                elif sms_input:
                    logger.info(f"[HEETCH] Page de validation SMS détectée")
                    next_page_detected = True
                    page_type = "sms"
                    break
                
                await page.wait_for_timeout(check_interval)
                elapsed_time += check_interval
            
            # Gérer le cas où on arrive directement sur la page de mot de passe (bypass du SMS)
            if page_type == "password":
                logger.info("[HEETCH] ✅ Les cookies permettent de bypasser le SMS, passage direct au mot de passe")
                # Sauvegarder les cookies actuels (qui permettent de bypasser le SMS)
                cookies = await context.cookies()
                self._cookies = cookies
                self._cookies_expires_at = time.time() + (24 * 60 * 60)
                logger.info(f"[HEETCH] {len(cookies)} cookies sauvegardés (permettent de bypasser le SMS)")
                # Les cookies seront sauvegardés dans la DB après complete_login avec le mot de passe
                return {"status": "phone_filled_password_needed", "message": "Numéro rempli, les cookies permettent de bypasser le SMS. Mot de passe requis (pas de code SMS nécessaire)"}
            
            if not next_page_detected or page_type != "sms":
                # Prendre une capture d'écran pour debug
                try:
                    await page.screenshot(path="heetch_sms_error.png")
                    logger.error("[HEETCH] Capture d'écran sauvegardée dans heetch_sms_error.png")
                except:
                    pass
                logger.error(f"[HEETCH] URL finale: {page.url}")
                raise RuntimeError(f"La page de validation SMS n'a pas été détectée après {max_wait_time}ms. URL actuelle: {page.url}")
            
            # Stocker les cookies après avoir entré le numéro (pour les restaurer la prochaine fois)
            cookies = await context.cookies()
            self._cookies = cookies
            self._cookies_expires_at = time.time() + (24 * 60 * 60)
            logger.info(f"[HEETCH] {len(cookies)} cookies sauvegardés après saisie du numéro")
            
            # Extraire le token reCAPTCHA depuis la page si disponible
            recaptcha_token = None
            try:
                # Méthode 1: Chercher dans window.grecaptcha
                recaptcha_token = await page.evaluate("""
                    () => {
                        // Chercher dans window.grecaptcha
                        if (window.grecaptcha && window.grecaptcha.getResponse) {
                            try {
                                const response = window.grecaptcha.getResponse();
                                if (response && response.length > 0) {
                                    return response;
                                }
                            } catch(e) {
                                console.log('Erreur grecaptcha.getResponse:', e);
                            }
                        }
                        // Chercher dans grecaptcha.enterprise si disponible
                        if (window.grecaptcha && window.grecaptcha.enterprise && window.grecaptcha.enterprise.getResponse) {
                            try {
                                const response = window.grecaptcha.enterprise.getResponse();
                                if (response && response.length > 0) {
                                    return response;
                                }
                            } catch(e) {
                                console.log('Erreur grecaptcha.enterprise.getResponse:', e);
                            }
                        }
                        return null;
                    }
                """)
                
                # Méthode 2: Intercepter les requêtes réseau pour capturer le token reCAPTCHA
                if not recaptcha_token:
                    # Attendre un peu pour que reCAPTCHA se charge
                    await page.wait_for_timeout(2000)
                    # Chercher dans les éléments de la page
                    recaptcha_elements = await page.query_selector_all('[data-sitekey], [class*="recaptcha"], [id*="recaptcha"]')
                    if recaptcha_elements:
                        logger.info(f"[HEETCH] Éléments reCAPTCHA trouvés, tentative d'extraction du token...")
                        # Attendre que reCAPTCHA soit résolu
                        await page.wait_for_timeout(3000)
                        recaptcha_token = await page.evaluate("""
                            () => {
                                if (window.grecaptcha && window.grecaptcha.getResponse) {
                                    try {
                                        return window.grecaptcha.getResponse();
                                    } catch(e) {}
                                }
                                return null;
                            }
                        """)
                
                if recaptcha_token:
                    logger.info(f"[HEETCH] Token reCAPTCHA extrait: {recaptcha_token[:30]}...")
                else:
                    logger.warning("[HEETCH] Token reCAPTCHA non trouvé, la requête API pourrait échouer")
            except Exception as e:
                logger.debug(f"[HEETCH] Impossible d'extraire le token reCAPTCHA: {e}")
            
            # Créer une session via l'API avec le numéro de téléphone
            try:
                session_info = self._auth_api.create_session(phone, recaptcha_token)
                logger.info(f"[HEETCH] Session API créée: state={session_info.get('state')}, phone_number={session_info.get('phone_number')}")
                
                # Extraire l'access_token depuis la réponse
                if "access_token" in session_info:
                    self._token = session_info["access_token"]
                    self._auth_api._token = self._token
                    logger.info(f"[HEETCH] Access token obtenu: {self._token[:20]}...")
                    
                    # Vérifier l'état de la session
                    session_state = self._auth_api.check_session()
                    logger.info(f"[HEETCH] État de session vérifié: {session_state.get('state')}")
            except Exception as e:
                logger.warning(f"[HEETCH] Impossible de créer la session via API (continuons avec Playwright): {e}")
            
            # Sauvegarder les cookies dans la base de données
            self._save_cookies_to_db(phone)
            
            # Garder la session ouverte pour complete_login
            return {"status": "sms_sent", "message": "SMS envoyé avec succès"}
        
        try:
            session_key = self._get_session_key(phone)
            return self._run_async_in_thread(_do_start_login_async, session_key=session_key)
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de l'envoi du SMS: {e}", exc_info=True)
            raise
    
    def complete_login(self, sms_code: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Étape 2 : Valide le code SMS (si nécessaire) puis entre le mot de passe pour finaliser la connexion.
        
        Args:
            sms_code: Code SMS reçu par téléphone (optionnel si le numéro est déjà mémorisé, dans ce cas le SMS est bypassé)
            password: Mot de passe (utilise HEETCH_PASSWORD si non fourni)
        
        Returns:
            True si la connexion réussit
        """
        if not password:
            password = getattr(settings, 'heetch_password', None)
        
        if not password:
            raise ValueError("HEETCH_PASSWORD doit être défini dans les variables d'environnement")
        
        async def _do_complete_login_async():
            """Version async de complete_login."""
            # Récupérer la session Playwright créée dans start_login
            # Utiliser org_id + phone_number comme clé
            if not self._phone_number:
                raise RuntimeError("start_login() doit être appelé avant complete_login() avec un numéro de téléphone")
            
            session_key = self._get_session_key(self._phone_number)
            with _session_lock:
                if session_key not in _playwright_sessions:
                    raise RuntimeError(f"Session Playwright introuvable avec la clé {session_key}. Veuillez d'abord appeler start_login()")
                
                session = _playwright_sessions[session_key]
                playwright = session.get("playwright")
                browser = session.get("browser")
                context = session.get("context")
                page = session.get("page")
                
                if not page:
                    raise RuntimeError("Session Playwright invalide, veuillez refaire start_login()")
                
                logger.info(f"[HEETCH] Session Playwright récupérée avec la clé: {session_key}")
            
            # Vérifier que la page est toujours valide et ouverte
            try:
                # Vérifier si la page est fermée
                if page.is_closed():
                    logger.warning("[HEETCH] La page était fermée, tentative de récupération d'une page existante")
                    pages = context.pages
                    if pages:
                        page = pages[0]
                        logger.info("[HEETCH] Première page du contexte récupérée")
                    else:
                        # Créer une nouvelle page dans le même contexte
                        page = await context.new_page()
                        logger.info("[HEETCH] Nouvelle page créée dans le contexte existant")
                        # Mettre à jour la session
                        with _session_lock:
                            if session_key in _playwright_sessions:
                                _playwright_sessions[session_key]["page"] = page
                
                # Vérifier l'URL actuelle
                current_url = page.url
                logger.info(f"[HEETCH] URL actuelle de la page: {current_url}")
                
                # Si on n'est pas sur une page de validation SMS, essayer de naviguer
                if "code" not in current_url.lower() and "sms" not in current_url.lower() and "verify" not in current_url.lower():
                    logger.warning(f"[HEETCH] La page n'est pas sur la page de validation SMS. URL: {current_url}")
                    # On va quand même essayer de continuer, peut-être que le champ SMS est déjà visible
                    
            except Exception as e:
                logger.warning(f"[HEETCH] Erreur lors de la vérification de la page: {e}")
                # Continuer quand même, peut-être que la page fonctionne
            
            logger.info("[HEETCH] Validation du code SMS (si nécessaire) et connexion")
            
            # Vérifier si on est déjà sur la page de mot de passe (numéro mémorisé, pas besoin de SMS)
            password_input = await page.query_selector('input[type="password"]')
            phone_input = await page.query_selector('input.f-FormEl, input[type="tel"], input[name="phone"], input[placeholder*="téléphone" i], input[placeholder*="phone" i]')
            sms_input = None
            
            # Chercher le champ SMS
            sms_input_selectors = [
                'input[type="tel"]',
                'input[name*="code" i]',
                'input[placeholder*="code" i]',
                'input[id*="code" i]',
                'input[placeholder*="sms" i]'
            ]
            
            for selector in sms_input_selectors:
                try:
                    found_input = await page.query_selector(selector)
                    if found_input and await found_input.is_visible():
                        sms_input = found_input
                        break
                except:
                    continue
            
            # Déterminer si on doit remplir le SMS ou si on passe directement au mot de passe
            skip_sms = False
            if password_input and await password_input.is_visible():
                if not sms_input or not await sms_input.is_visible():
                    # Champ mot de passe présent mais pas de champ SMS = numéro mémorisé
                    logger.info("[HEETCH] ✅ Numéro déjà mémorisé, pas besoin de code SMS (passage direct au mot de passe)")
                    skip_sms = True
                elif phone_input and await phone_input.is_visible():
                    # Les deux sont présents, on doit vérifier lequel est visible en premier
                    logger.info("[HEETCH] Formulaire complet détecté, traitement normal avec SMS")
                else:
                    # Seulement le mot de passe = skip SMS
                    logger.info("[HEETCH] ✅ Numéro déjà mémorisé, pas besoin de code SMS")
                    skip_sms = True
            
            if not skip_sms:
                # Remplir le code SMS
                if not sms_input:
                    raise RuntimeError("Impossible de trouver le champ code SMS")
                
                if not sms_code:
                    raise ValueError("Code SMS requis pour finaliser la connexion (le numéro n'est pas mémorisé)")
                
                await sms_input.fill(sms_code)
                logger.info("[HEETCH] Code SMS rempli")
                
                # Cliquer sur le bouton de validation du code
                validate_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Valider")',
                    'button:has-text("Vérifier")',
                    'button:has-text("Confirmer")',
                    'button:has-text("Continuer")'
                ]
                
                validated = False
                for selector in validate_selectors:
                    try:
                        validate_button = await page.query_selector(selector)
                        if validate_button and await validate_button.is_visible():
                            await validate_button.click()
                            validated = True
                            logger.info(f"[HEETCH] Code SMS validé avec sélecteur: {selector}")
                            break
                    except:
                        continue
                
                if not validated:
                    raise RuntimeError("Impossible de trouver le bouton de validation du code SMS")
                
                # Attendre la redirection vers la page de mot de passe
                await page.wait_for_timeout(3000)
            else:
                logger.info("[HEETCH] Étape SMS ignorée, passage direct au mot de passe")
            
            # Maintenant, chercher le champ mot de passe
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="mot de passe" i]',
                'input[id*="password" i]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_input = await page.query_selector(selector)
                    if password_input and await password_input.is_visible():
                        await password_input.fill(password)
                        password_filled = True
                        logger.info(f"[HEETCH] Mot de passe rempli avec sélecteur: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"[HEETCH] Sélecteur {selector} non trouvé: {e}")
                    continue
            
            if not password_filled:
                raise RuntimeError("Impossible de trouver le champ mot de passe après validation du SMS")
            
            # Cliquer sur le bouton de connexion final
            final_submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Connexion")',
                'button:has-text("Se connecter")',
                'button:has-text("Login")',
                'input[type="submit"]'
            ]
            
            submitted = False
            for selector in final_submit_selectors:
                try:
                    submit_button = await page.query_selector(selector)
                    if submit_button and await submit_button.is_visible():
                        await submit_button.click()
                        submitted = True
                        logger.info(f"[HEETCH] Connexion finale avec sélecteur: {selector}")
                        break
                except:
                    continue
            
            if not submitted:
                raise RuntimeError("Impossible de trouver le bouton de connexion final")
            
            # Attendre la redirection finale
            await page.wait_for_timeout(3000)
            
            # Vérifier que la connexion a réussi
            current_url = page.url
            if "/login" in current_url or ("auth.heetch.com" in current_url and "/dashboard" not in current_url):
                try:
                    await page.screenshot(path="heetch_login_error.png")
                    logger.error(f"[HEETCH] Toujours sur la page de login: {current_url}")
                except:
                    pass
                raise RuntimeError("La connexion a échoué, toujours sur la page de login")
            
            logger.info(f"[HEETCH] Connexion réussie, URL actuelle: {current_url}")
            
            # Récupérer les cookies
            cookies = await context.cookies()
            self._cookies = cookies
            self._cookies_expires_at = time.time() + (24 * 60 * 60)
            
            logger.info(f"[HEETCH] {len(self._cookies)} cookies récupérés")
            
            # Extraire le token depuis les cookies
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            token = cookie_dict.get('heetch_auth_token') or cookie_dict.get('auth_token')
            if token:
                self._token = token
                logger.info(f"[HEETCH] Token extrait depuis les cookies: {token[:20]}...")
            
            # Vérifier l'état de la session via l'API
            try:
                # Configurer le token dans l'API client
                if self._token:
                    self._auth_api._token = self._token
                session_info = self._auth_api.check_session()
                logger.info(f"[HEETCH] État de session API: {session_info.get('state')}")
                if session_info.get('state') != 'authentication_required':
                    logger.info(f"[HEETCH] Session authentifiée via API: {session_info}")
            except Exception as e:
                logger.debug(f"[HEETCH] Impossible de vérifier la session via API: {e}")
            
            # Sauvegarder les cookies dans la base de données si on a le numéro de téléphone
            if self._phone_number:
                self._save_cookies_to_db(self._phone_number)
            
            # Fermer les ressources maintenant qu'on a les cookies
            session_key = self._get_session_key(self._phone_number)
            try:
                await page.close()
                await context.close()
                await browser.close()
                await playwright.stop()
                # Nettoyer la session
                with _session_lock:
                    if session_key in _playwright_sessions:
                        del _playwright_sessions[session_key]
                        logger.info(f"[HEETCH] Session {session_key} nettoyée")
            except Exception as e:
                logger.debug(f"[HEETCH] Erreur lors de la fermeture: {e}")
                # Nettoyer quand même la session
                with _session_lock:
                    if session_key in _playwright_sessions:
                        del _playwright_sessions[session_key]
                        logger.info(f"[HEETCH] Session {session_key} nettoyée après erreur")
            
            return True
        
        try:
            if not self._phone_number:
                raise RuntimeError("start_login() doit être appelé avant complete_login()")
            session_key = self._get_session_key(self._phone_number)
            return self._run_async_in_thread(_do_complete_login_async, session_key=session_key)
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la finalisation de la connexion: {e}", exc_info=True)
            raise
    
    def login(self, login: Optional[str] = None, password: Optional[str] = None, sms_code: Optional[str] = None) -> bool:
        """
        Méthode de compatibilité : effectue le login complet en deux étapes.
        Utilise start_login() puis complete_login() automatiquement.
        
        Args:
            login: Numéro de téléphone (utilise HEETCH_LOGIN si non fourni)
            password: Mot de passe (utilise HEETCH_PASSWORD si non fourni)
            sms_code: Code SMS (requis)
        
        Returns:
            True si la connexion réussit
        """
        if not sms_code:
            sms_code = getattr(settings, 'heetch_2fa_code', None)
        
        if not sms_code:
            # Si pas de code SMS, on démarre juste l'envoi du SMS
            self.start_login(login)
            raise ValueError(
                "Code SMS requis. Veuillez appeler start_login() puis complete_login(sms_code, password) "
                "ou fournir HEETCH_2FA_CODE dans les variables d'environnement."
            )
        
        # Effectuer les deux étapes
        self.start_login(login)
        return self.complete_login(sms_code, password)
    
    def get_earnings(self, date_param: date, period: str = "weekly") -> Dict[str, Any]:
        """
        Récupère les earnings depuis l'API Heetch.
        
        Args:
            date_param: Date de début de la période (format date)
            period: Période (weekly, monthly, etc.)
        
        Returns:
            Données JSON des earnings
        """
        # S'assurer d'avoir les cookies de session (essayer de charger depuis DB si nécessaire)
        phone = self._phone_number or getattr(settings, 'heetch_login', None)
        cookies = self._get_cookies(phone)  # _get_cookies charge déjà depuis la DB si nécessaire
        
        # Convertir les cookies Playwright en format httpx
        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie['name']] = cookie['value']
        
        # Construire le header Cookie
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
        
        # Format de date: YYYY-MM-DD
        date_str = date_param.strftime("%Y-%m-%d")
        
        url = f"{self.base_url}/api/earnings"
        params = {
            "date": date_str,
            "period": period
        }
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": cookie_header,
            "referer": f"{self.base_url}/earnings",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
        }
        
        # Si on a un token d'authentification (depuis l'API auth-gw), l'utiliser aussi
        # Note: Le token peut être dans les cookies (heetch_auth_token) ou on peut l'extraire
        if "heetch_auth_token" in cookie_dict:
            # Le token est déjà dans les cookies, c'est bon
            pass
        
        logger.info(f"[HEETCH] Récupération des earnings: date={date_str}, period={period}, cookies_count={len(cookies)}")
        
        # Log des noms de cookies pour debug
        cookie_names = [c.get('name', '') for c in cookies]
        logger.debug(f"[HEETCH] Cookies envoyés: {', '.join(cookie_names)}")
        
        try:
            with httpx.Client(timeout=30.0, follow_redirects=False) as client:
                resp = client.get(url, params=params, headers=headers)
                
                # Si 307 (redirect vers auth), les cookies ne sont plus valides
                if resp.status_code == 307:
                    redirect_location = resp.headers.get('location', '')
                    logger.warning(f"[HEETCH] Session expirée (307 redirect vers auth): {redirect_location}")
                    # Marquer les cookies comme invalides et expirés
                    self._cookies = None
                    self._cookies_expires_at = 0.0
                    # Marquer les cookies comme invalides dans la DB (au lieu de les supprimer pour garder l'historique)
                    if phone:
                        try:
                            from app.core.supabase_db import SupabaseDB
                            from app.models.heetch_session_cookies import HeetchSessionCookies
                            from datetime import datetime
                            db = SupabaseDB()
                            session_cookies = db.query(HeetchSessionCookies).filter(
                                HeetchSessionCookies.org_id == self.org_id,
                                HeetchSessionCookies.phone_number == phone,
                                HeetchSessionCookies.invalid_at.is_(None)  # Seulement si pas déjà marqué invalide
                            ).first()
                            if session_cookies:
                                session_cookies.invalid_at = datetime.utcnow()
                                db.merge(session_cookies)
                                db.commit()
                                logger.info(f"[HEETCH] Cookies marqués comme invalides dans la DB pour {phone} (invalid_at={session_cookies.invalid_at})")
                        except Exception as e:
                            logger.debug(f"[HEETCH] Erreur lors du marquage des cookies comme invalides: {e}")
                    raise RuntimeError(
                        f"Session expirée (HTTP 307). Les cookies sauvegardés ne sont plus valides côté serveur Heetch. "
                        f"Veuillez vous reconnecter via /heetch/auth/start puis /heetch/auth/complete."
                    )
                
                # Si 401 ou 403, la session a expiré
                if resp.status_code in [401, 403]:
                    logger.warning(f"[HEETCH] Session expirée (HTTP {resp.status_code})")
                    self._cookies = None
                    self._cookies_expires_at = 0.0
                    raise RuntimeError(
                        f"Session expirée (HTTP {resp.status_code}). Veuillez vous reconnecter via /heetch/auth/start puis /heetch/auth/complete."
                    )
                
                resp.raise_for_status()
                data = resp.json()
                
                logger.info(f"[HEETCH] Earnings récupérés avec succès: {len(data.get('drivers', []))} drivers")
                return data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 307:
                # Déjà géré plus haut, mais au cas où
                raise RuntimeError(
                    f"Session expirée (HTTP 307). Les cookies sauvegardés ne sont plus valides. "
                    f"Veuillez vous reconnecter via /heetch/auth/start puis /heetch/auth/complete."
                )
            logger.error(f"[HEETCH] Erreur HTTP {e.response.status_code}: {e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la récupération des earnings: {e}", exc_info=True)
            raise
    
    def __del__(self):
        """Nettoyage lors de la destruction de l'objet."""
        self._close_playwright()

