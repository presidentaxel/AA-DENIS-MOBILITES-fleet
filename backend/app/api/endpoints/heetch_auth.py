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
    Étape 1 : Envoie le SMS de validation.
    Entre le numéro de téléphone et déclenche l'envoi du SMS.
    """
    try:
        client = get_heetch_client(current_user["org_id"])
        result = client.start_login(phone)
        return {
            "status": "success",
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
    sms_code: str = Query(..., description="Code SMS reçu par téléphone"),
    password: Optional[str] = Query(None, description="Mot de passe (utilise HEETCH_PASSWORD si non fourni)"),
):
    """
    Étape 2 : Finalise la connexion.
    Valide le code SMS puis entre le mot de passe pour obtenir la session.
    """
    try:
        client = get_heetch_client(current_user["org_id"])
        # start_login doit avoir été appelé avant
        # On va le refaire si nécessaire (le client garde l'état)
        try:
            client.start_login()
        except:
            pass  # Peut déjà être fait
        
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

