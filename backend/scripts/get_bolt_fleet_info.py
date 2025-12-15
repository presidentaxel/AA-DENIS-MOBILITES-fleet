#!/usr/bin/env python3
"""
Script pour obtenir les informations de la flotte Bolt.
Peut contenir le company_id.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.bolt_integration.bolt_client import BoltClient
from app.core.config import get_settings

settings = get_settings()


def get_fleet_info():
    """Récupère les informations de la flotte Bolt."""
    try:
        client = BoltClient()
        
        # Essayer différents endpoints qui pourraient retourner le company_id
        endpoints_to_try = [
            "/fleet",
            "/fleetIntegration/v1/getFleetInfo",
            "/fleetIntegration/v1/getCompanies",
            "/fleetIntegration/v1/me",
        ]
        
        print("🔍 Recherche d'informations sur la flotte Bolt...")
        print()
        
        for endpoint in endpoints_to_try:
            print(f"Test de {endpoint}...")
            try:
                if endpoint.startswith("/fleetIntegration"):
                    # POST pour les endpoints fleetIntegration
                    data = client.post(endpoint, {})
                else:
                    # GET pour les autres
                    data = client.get(endpoint)
                
                print(f"✅ Réponse de {endpoint}:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print()
                
                # Chercher company_id dans la réponse
                def find_company_id(obj, path=""):
                    """Recherche récursive de company_id dans la réponse."""
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if "company" in key.lower() and "id" in key.lower():
                                print(f"🎯 Trouvé: {path}.{key} = {value}")
                            find_company_id(value, f"{path}.{key}" if path else key)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            find_company_id(item, f"{path}[{i}]")
                
                find_company_id(data)
                
            except Exception as e:
                print(f"❌ Erreur avec {endpoint}: {str(e)}")
                print()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()


def main():
    if not settings.bolt_client_id or not settings.bolt_client_secret:
        print("❌ BOLT_CLIENT_ID et BOLT_CLIENT_SECRET doivent être définis")
        sys.exit(1)
    
    get_fleet_info()
    
    print("=" * 60)
    print("💡 Si aucun company_id n'a été trouvé, contacte le support Bolt")
    print("   avec tes credentials (BOLT_CLIENT_ID) pour obtenir le company_id")


if __name__ == "__main__":
    main()

