import time
import asyncio
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
        self._phone_number: Optional[str] = None
        
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
            # ID composite: org_id + phone_number
            cookie_id = f"{self.org_id}_{phone_number}"
            
            session_cookies = db.query(HeetchSessionCookies).filter(
                HeetchSessionCookies.id == cookie_id
            ).first()
            
            if session_cookies and session_cookies.expires_at > datetime.utcnow():
                self._cookies = session_cookies.cookies
                # Convertir expires_at en timestamp
                expires_timestamp = session_cookies.expires_at.timestamp()
                self._cookies_expires_at = expires_timestamp
                logger.info(f"[HEETCH] {len(self._cookies)} cookies chargés depuis la DB pour {phone_number}")
                return True
            elif session_cookies:
                logger.info(f"[HEETCH] Cookies expirés dans la DB pour {phone_number}")
                # Supprimer les cookies expirés
                db.delete(session_cookies)
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
            
            if not self._cookies:
                return
            
            db = SupabaseDB()
            # ID composite: org_id + phone_number
            cookie_id = f"{self.org_id}_{phone_number}"
            
            # Calculer expires_at depuis le timestamp
            expires_at = datetime.fromtimestamp(self._cookies_expires_at)
            
            session_cookies = HeetchSessionCookies(
                id=cookie_id,
                org_id=self.org_id,
                phone_number=phone_number,
                cookies=self._cookies,
                expires_at=expires_at
            )
            
            db.merge(session_cookies)
            db.commit()
            logger.info(f"[HEETCH] {len(self._cookies)} cookies sauvegardés dans la DB pour {phone_number}")
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la sauvegarde des cookies dans la DB: {e}", exc_info=True)
            # Ne pas lever d'exception, la sauvegarde des cookies n'est pas critique
    
    def _get_cookies(self) -> list[Dict[str, Any]]:
        """
        Récupère les cookies de session. Si expirés ou absents, lève une exception.
        La connexion doit être faite explicitement via start_login() puis complete_login() ou auto_login().
        """
        # Vérifier si les cookies sont encore valides (expire après 24h par sécurité)
        if self._cookies and time.time() < self._cookies_expires_at:
            return self._cookies
        
        # Sinon, lever une exception pour indiquer qu'une connexion est nécessaire
        raise RuntimeError(
            "Session expirée ou absente. "
            "Utilisez /heetch/auth/start puis /heetch/auth/complete pour vous connecter, "
            "ou laissez le système se connecter automatiquement."
        )
    
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
        
        # Essayer d'abord de charger les cookies depuis la DB
        cookies_loaded = self._load_cookies_from_db(phone)
        
        # Si on a des cookies valides, essayer de les utiliser directement
        if cookies_loaded and self._cookies and time.time() < self._cookies_expires_at:
            logger.info("[HEETCH] Tentative de connexion automatique avec cookies sauvegardés")
            try:
                # Vérifier si les cookies sont encore valides en testant une requête
                # On va essayer de récupérer les earnings pour voir si la session est valide
                from datetime import date, timedelta
                test_date = date.today() - timedelta(days=7)
                try:
                    self.get_earnings(test_date, "weekly")
                    logger.info("[HEETCH] Cookies valides, connexion automatique réussie")
                    return True
                except Exception as e:
                    logger.info(f"[HEETCH] Cookies invalides ou expirés: {e}, passage au flux complet")
                    # Les cookies ne sont plus valides, continuer avec le flux complet
                    self._cookies = None
                    self._cookies_expires_at = 0.0
            except Exception as e:
                logger.info(f"[HEETCH] Erreur lors de la vérification des cookies: {e}, passage au flux complet")
                self._cookies = None
                self._cookies_expires_at = 0.0
        
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
    
    def _run_async_in_thread(self, async_func, *args, **kwargs):
        """Exécute une fonction async Playwright dans un thread séparé avec un nouvel event loop."""
        def run_with_new_loop():
            # Créer un nouvel event loop dans ce thread
            # Utiliser ProactorEventLoop sur Windows pour éviter les problèmes avec subprocess
            import sys
            import platform
            
            # Configurer la politique d'event loop pour Windows
            if sys.platform == 'win32':
                # Utiliser ProactorEventLoopPolicy sur Windows
                policy = asyncio.WindowsProactorEventLoopPolicy()
                asyncio.set_event_loop_policy(policy)
                loop = asyncio.new_event_loop()
            else:
                loop = asyncio.new_event_loop()
            
            asyncio.set_event_loop(loop)
            
            try:
                logger.info(f"[HEETCH] Démarrage de l'exécution async dans le thread (platform: {sys.platform})")
                result = loop.run_until_complete(async_func(*args, **kwargs))
                logger.info("[HEETCH] Exécution async terminée avec succès")
                return result
            except Exception as e:
                logger.error(f"[HEETCH] Erreur dans l'exécution async: {e}", exc_info=True)
                raise
            finally:
                # Ne pas fermer le loop immédiatement si on a une session active
                # Le loop sera réutilisé pour complete_login
                pass
        
        logger.info("[HEETCH] Soumission de la tâche au thread pool")
        future = _playwright_executor.submit(run_with_new_loop)
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
            try:
                # Créer une nouvelle session Playwright (sera réutilisée dans complete_login via le cache)
                logger.info("[HEETCH] Démarrage de async_playwright()...")
                playwright = await async_playwright().start()
                logger.info("[HEETCH] Playwright démarré, lancement de Chromium...")
                browser = await playwright.chromium.launch(headless=True)
                logger.info("[HEETCH] Chromium lancé, création du contexte...")
                
                # Préparer les options du contexte
                context_options = {
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
                }
                
                # Restaurer les cookies si on en a déjà (pour éviter de redemander le numéro)
                if self._cookies and time.time() < self._cookies_expires_at:
                    logger.info(f"[HEETCH] Restauration de {len(self._cookies)} cookies de session existants")
                    context_options["storage_state"] = {
                        "cookies": self._cookies
                    }
                
                context = await browser.new_context(**context_options)
                logger.info("[HEETCH] Contexte créé, création de la page...")
                page = await context.new_page()
                logger.info("[HEETCH] Page créée avec succès")
                
                # Stocker la session pour complete_login
                with _session_lock:
                    _playwright_sessions[self._client_id] = {
                        "playwright": playwright,
                        "browser": browser,
                        "context": context,
                        "page": page
                    }
                logger.info("[HEETCH] Session stockée dans le cache")
            except Exception as e:
                logger.error(f"[HEETCH] Erreur lors de l'initialisation Playwright: {e}", exc_info=True)
                raise RuntimeError(f"Erreur lors de l'initialisation de Playwright: {e}. Vérifiez que Playwright est installé avec 'playwright install chromium'")
            
            logger.info(f"[HEETCH] Démarrage connexion pour {phone}")
            
            # Aller sur la page de login
            # Utiliser "load" au lieu de "networkidle" car certaines pages chargent des ressources en continu
            logger.info(f"[HEETCH] Navigation vers {self.base_url}/login...")
            await page.goto(f"{self.base_url}/login", wait_until="load", timeout=60000)
            logger.info("[HEETCH] Page chargée, vérification de l'état...")
            
            # Vérifier si on est déjà connecté (grâce aux cookies restaurés)
            current_url = page.url
            if "/login" not in current_url:
                logger.info("[HEETCH] Déjà connecté grâce aux cookies restaurés")
                cookies = await context.cookies()
                self._cookies = cookies
                self._cookies_expires_at = time.time() + (24 * 60 * 60)
                # Sauvegarder les cookies mis à jour
                self._save_cookies_to_db(phone)
                return {"status": "already_logged_in", "message": "Session restaurée, déjà connecté"}
            
            # Attendre que le formulaire soit chargé avec un timeout plus long
            try:
                await page.wait_for_selector('input[type="tel"], input[type="text"], input[name="phone"], input[placeholder*="téléphone" i], input[placeholder*="phone" i]', timeout=10000)
                logger.info("[HEETCH] Formulaire téléphone détecté")
            except Exception:
                # Le formulaire téléphone n'est pas présent, peut-être qu'on doit entrer directement le mot de passe
                logger.info("[HEETCH] Formulaire téléphone non détecté, peut-être que le numéro est déjà mémorisé")
                # Vérifier s'il y a un champ mot de passe
                try:
                    await page.wait_for_selector('input[type="password"]', timeout=5000)
                    logger.info("[HEETCH] Champ mot de passe détecté, le numéro est déjà mémorisé")
                    # Sauvegarder les cookies actuels
                    cookies = await context.cookies()
                    self._cookies = cookies
                    self._cookies_expires_at = time.time() + (24 * 60 * 60)
                    self._save_cookies_to_db(phone)
                    return {"status": "phone_remembered", "message": "Numéro déjà mémorisé, mot de passe requis"}
                except:
                    pass
            
            # Chercher le champ téléphone/login
            phone_selectors = [
                'input[type="tel"]',
                'input[name="phone"]',
                'input[name="login"]',
                'input[placeholder*="téléphone" i]',
                'input[placeholder*="phone" i]',
                'input[placeholder*="numéro" i]',
                'input[id*="phone" i]',
                'input[id*="login" i]',
                'input[type="text"]'
            ]
            
            phone_filled = False
            for selector in phone_selectors:
                try:
                    phone_input = await page.query_selector(selector)
                    if phone_input and await phone_input.is_visible():
                        await phone_input.fill(phone)
                        phone_filled = True
                        logger.info(f"[HEETCH] Numéro de téléphone rempli avec sélecteur: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"[HEETCH] Sélecteur {selector} non trouvé: {e}")
                    continue
            
            if not phone_filled:
                raise RuntimeError("Impossible de trouver le champ téléphone/login sur la page de login")
            
            # Cliquer sur le bouton pour envoyer le SMS
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Continuer")',
                'button:has-text("Envoyer")',
                'button:has-text("Connexion")',
                'button:has-text("Se connecter")',
                'input[type="submit"]'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    submit_button = await page.query_selector(selector)
                    if submit_button and await submit_button.is_visible():
                        await submit_button.click()
                        submitted = True
                        logger.info(f"[HEETCH] Bouton cliqué avec sélecteur: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"[HEETCH] Sélecteur {selector} non trouvé: {e}")
                    continue
            
            if not submitted:
                raise RuntimeError("Impossible de trouver le bouton pour envoyer le SMS")
            
            # Attendre que le SMS soit envoyé (on devrait voir un champ pour le code SMS)
            await page.wait_for_timeout(3000)
            
            # Vérifier qu'on est sur la page de validation SMS
            sms_input_selectors = [
                'input[type="tel"]',
                'input[name*="code" i]',
                'input[placeholder*="code" i]',
                'input[id*="code" i]',
                'input[placeholder*="sms" i]'
            ]
            
            sms_page_detected = False
            for selector in sms_input_selectors:
                try:
                    sms_input = await page.query_selector(selector)
                    if sms_input and await sms_input.is_visible():
                        sms_page_detected = True
                        logger.info(f"[HEETCH] Page de validation SMS détectée")
                        break
                except:
                    continue
            
            if not sms_page_detected:
                raise RuntimeError("La page de validation SMS n'a pas été détectée après l'envoi du SMS")
            
            # Stocker les cookies après avoir entré le numéro (pour les restaurer la prochaine fois)
            cookies = await context.cookies()
            self._cookies = cookies
            self._cookies_expires_at = time.time() + (24 * 60 * 60)
            logger.info(f"[HEETCH] {len(cookies)} cookies sauvegardés après saisie du numéro")
            
            # Sauvegarder les cookies dans la base de données
            self._save_cookies_to_db(phone)
            
            # Garder la session ouverte pour complete_login
            return {"status": "sms_sent", "message": "SMS envoyé avec succès"}
        
        try:
            return self._run_async_in_thread(_do_start_login_async)
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de l'envoi du SMS: {e}", exc_info=True)
            raise
    
    def complete_login(self, sms_code: str, password: Optional[str] = None) -> bool:
        """
        Étape 2 : Valide le code SMS puis entre le mot de passe pour finaliser la connexion.
        
        Args:
            sms_code: Code SMS reçu par téléphone
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
            # Note: Les objets doivent être dans le même thread/event loop
            # On va les récupérer depuis le cache global
            with _session_lock:
                if self._client_id not in _playwright_sessions:
                    raise RuntimeError("start_login() doit être appelé avant complete_login()")
                
                session = _playwright_sessions[self._client_id]
                playwright = session.get("playwright")
                browser = session.get("browser")
                context = session.get("context")
                page = session.get("page")
                
                if not page:
                    raise RuntimeError("Session Playwright invalide, veuillez refaire start_login()")
            
            logger.info("[HEETCH] Validation du code SMS et connexion")
            
            # Remplir le code SMS
            sms_input_selectors = [
                'input[type="tel"]',
                'input[name*="code" i]',
                'input[placeholder*="code" i]',
                'input[id*="code" i]',
                'input[placeholder*="sms" i]'
            ]
            
            sms_filled = False
            for selector in sms_input_selectors:
                try:
                    sms_input = await page.query_selector(selector)
                    if sms_input and await sms_input.is_visible():
                        await sms_input.fill(sms_code)
                        sms_filled = True
                        logger.info("[HEETCH] Code SMS rempli")
                        break
                except:
                    continue
            
            if not sms_filled:
                raise RuntimeError("Impossible de trouver le champ code SMS")
            
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
            if "/login" in current_url:
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
            
            # Sauvegarder les cookies dans la base de données si on a le numéro de téléphone
            if self._phone_number:
                self._save_cookies_to_db(self._phone_number)
            
            # Fermer les ressources maintenant qu'on a les cookies
            try:
                await page.close()
                await context.close()
                await browser.close()
                await playwright.stop()
                # Nettoyer la session
                with _session_lock:
                    if self._client_id in _playwright_sessions:
                        del _playwright_sessions[self._client_id]
            except Exception as e:
                logger.debug(f"[HEETCH] Erreur lors de la fermeture: {e}")
                # Nettoyer quand même la session
                with _session_lock:
                    if self._client_id in _playwright_sessions:
                        del _playwright_sessions[self._client_id]
            
            return True
        
        try:
            return self._run_async_in_thread(_do_complete_login_async)
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
        # S'assurer d'avoir les cookies de session
        cookies = self._get_cookies()
        
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
        
        logger.info(f"[HEETCH] Récupération des earnings: date={date_str}, period={period}")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params=params, headers=headers)
                
                # Si 401 ou 403, la session a expiré, se reconnecter
                if resp.status_code in [401, 403]:
                    logger.warning("[HEETCH] Session expirée, reconnexion nécessaire")
                    self._cookies = None  # Forcer la reconnexion
                    cookies = self._get_cookies()
                    cookie_dict = {c['name']: c['value'] for c in cookies}
                    cookie_header = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
                    headers["cookie"] = cookie_header
                    resp = client.get(url, params=params, headers=headers)
                
                resp.raise_for_status()
                data = resp.json()
                
                logger.info(f"[HEETCH] Earnings récupérés avec succès: {len(data.get('drivers', []))} drivers")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[HEETCH] Erreur HTTP {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"[HEETCH] Erreur lors de la récupération des earnings: {e}", exc_info=True)
            raise
    
    def __del__(self):
        """Nettoyage lors de la destruction de l'objet."""
        self._close_playwright()

