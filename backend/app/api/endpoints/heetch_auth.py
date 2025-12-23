from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.heetch_integration.client_manager import get_heetch_client

router = APIRouter(prefix="/heetch", tags=["heetch"])


@router.post("/auth/start")
def start_heetch_login(
    current_user: dict = Depends(get_current_user),
    phone: Optional[str] = Query(None, description="Numéro de téléphone (utilise HEETCH_LOGIN si non fourni)"),
):
    """
    Étape 1 : Démarre le processus de connexion.
    - Si des cookies valides sont trouvés en DB, la session est restaurée automatiquement (pas de SMS nécessaire)
    - Sinon, envoie le SMS de validation et attend le code
    """
    try:
        client = get_heetch_client(current_user["org_id"])
        result = client.start_login(phone)
        
        # Si déjà connecté grâce aux cookies, retourner un message différent
        if isinstance(result, dict) and result.get("status") == "already_logged_in":
            return {
                "status": "success",
                "already_logged_in": True,
                "message": result.get("message", "Session déjà active, cookies restaurés et mis à jour depuis la DB"),
                "next_step": "Aucune action nécessaire, vous pouvez utiliser les endpoints de synchronisation directement",
            }
        elif isinstance(result, dict) and result.get("status") == "phone_remembered":
            return {
                "status": "success",
                "phone_remembered": True,
                "message": result.get("message", "Numéro déjà mémorisé grâce aux cookies, mot de passe requis (pas de SMS nécessaire)"),
                "next_step": "Appelez /heetch/auth/complete avec uniquement le mot de passe (pas de code SMS nécessaire)",
            }
        elif isinstance(result, dict) and result.get("status") == "phone_filled_password_needed":
            return {
                "status": "success",
                "phone_filled": True,
                "message": result.get("message", "Numéro rempli, les cookies permettent de bypasser le SMS. Mot de passe requis (pas de code SMS nécessaire)"),
                "next_step": "Appelez /heetch/auth/complete avec uniquement le mot de passe (pas de code SMS nécessaire)",
            }
        else:
            # Flux normal : SMS envoyé
            return {
                "status": "success",
                "already_logged_in": False,
                "message": "SMS envoyé avec succès. Vérifiez votre téléphone pour le code.",
                "next_step": "Appelez /heetch/auth/complete avec le code SMS et le mot de passe",
            }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/auth/complete")
def complete_heetch_login(
    current_user: dict = Depends(get_current_user),
    sms_code: Optional[str] = Query(None, description="Code SMS reçu par téléphone (optionnel si numéro déjà mémorisé)"),
    password: Optional[str] = Query(None, description="Mot de passe (utilise HEETCH_PASSWORD si non fourni)"),
):
    """
    Étape 2 : Finalise la connexion.
    - Si le numéro est déjà mémorisé (phone_remembered), seul le mot de passe est requis (pas de SMS)
    - Sinon, valide le code SMS puis entre le mot de passe pour obtenir la session.
    """
    try:
        client = get_heetch_client(current_user["org_id"])
        # start_login doit avoir été appelé avant
        # On va le refaire si nécessaire (le client garde l'état)
        try:
            client.start_login()
        except:
            pass  # Peut déjà être fait
        
        # Si sms_code n'est pas fourni, utiliser une valeur vide (complete_login gérera le cas)
        if not sms_code:
            sms_code = ""
        
        success = client.complete_login(sms_code, password)
        
        if success:
            return {
                "status": "success",
                "message": "Connexion réussie. Vous pouvez maintenant utiliser les endpoints de synchronisation.",
            }
        else:
            return {
                "status": "error",
                "message": "La connexion a échoué",
            }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }

