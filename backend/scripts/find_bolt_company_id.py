#!/usr/bin/env python3
"""
Script pour trouver le company_id Bolt en testant différentes valeurs.
À exécuter depuis le container backend.
"""
import sys
from pathlib import Path

# Ajouter le répertoire app au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.bolt_integration.bolt_client import BoltClient
from app.core.config import get_settings

settings = get_settings()


def test_company_id(company_id: int):
    """Teste un company_id donné."""
    try:
        client = BoltClient()
        payload = {
            "company_id": company_id,
            "limit": 10,
            "offset": 0,
        }
        
        data = client.post("/fleetIntegration/v1/getDrivers", payload)
        
        code = data.get("code")
        message = data.get("message", "Unknown error")
        
        if code == 0:
            drivers = data.get("data", {}).get("drivers", [])
            return True, len(drivers), message
        elif code == 702:
            # INVALID_REQUEST - company_id incorrect ou requête mal formée
            return False, 0, f"INVALID_REQUEST: {message}"
        elif "COMPANY_NOT_FOUND" in message or code == 404:
            # Company not found - ce company_id n'existe pas
            return False, 0, f"COMPANY_NOT_FOUND: {message}"
        else:
            return False, 0, f"Code {code}: {message}"
    except Exception as e:
        return False, 0, f"Exception: {str(e)}"


def main():
    print("🔍 Recherche du company_id Bolt...")
    print()
    
    if not settings.bolt_client_id or not settings.bolt_client_secret:
        print("❌ BOLT_CLIENT_ID et BOLT_CLIENT_SECRET doivent être définis")
        sys.exit(1)
    
    print("Test de différents company_id...")
    print("(Cela peut prendre du temps, appuyez sur Ctrl+C pour arrêter)")
    print()
    
    found_ids = []
    invalid_count = 0
    
    print("Test de company_id de 1 à 100...")
    print("(Si tous retournent INVALID_REQUEST, le company_id n'est probablement pas dans cette plage)")
    print()
    
    # Tester les IDs de 1 à 100 (ou jusqu'à trouver)
    for company_id in range(1, 101):
        success, count, msg = test_company_id(company_id)
        
        if success:
            print(f"✅ company_id={company_id}: {count} drivers trouvés - {msg}")
            found_ids.append((company_id, count))
            # Arrêter après le premier trouvé (optionnel)
            break
        elif "INVALID_REQUEST" in msg:
            invalid_count += 1
            # Afficher seulement tous les 10 pour ne pas spammer
            if company_id % 10 == 0:
                print(f"   Testé jusqu'à company_id={company_id}... (tous INVALID_REQUEST)")
        elif "COMPANY_NOT_FOUND" in msg:
            # Company not found, continue silencieusement
            pass
        else:
            print(f"⚠️  company_id={company_id}: {msg}")
    
    print()
    print("=" * 60)
    if found_ids:
        print("✅ Company IDs trouvés:")
        for cid, count in found_ids:
            print(f"   company_id={cid}: {count} drivers")
        print()
        print("Ajoute dans backend/.env:")
        print(f"BOLT_DEFAULT_FLEET_ID={found_ids[0][0]}")
    else:
        print("❌ Aucun company_id valide trouvé dans la plage testée (1-100)")
        if invalid_count == 100:
            print()
            print("💡 Tous les company_id testés retournent INVALID_REQUEST.")
            print("   Cela signifie probablement que :")
            print("   1. Le company_id n'est pas un nombre séquentiel (1, 2, 3...)")
            print("   2. Le company_id est un nombre plus grand (> 100)")
            print("   3. Le company_id doit être obtenu d'une autre manière")
        print()
        print("📋 Solutions:")
        print("1. Contacte le support Bolt et demande ton company_id")
        print("   (Ils devraient te le fournir avec tes credentials)")
        print("2. Vérifie dans le Bolt Fleet Owner Portal → Settings → Fleet Integration API")
        print("3. Regarde dans la documentation Bolt si un endpoint liste les companies")
        print("4. Le company_id peut être dans l'email de bienvenue Bolt")
        print()
        print("📖 Voir docs/BOLT_COMPANY_ID_FIND.md pour plus de détails")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompu par l'utilisateur")
        sys.exit(0)

