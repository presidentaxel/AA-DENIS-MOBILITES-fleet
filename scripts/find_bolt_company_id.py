#!/usr/bin/env python3
"""
Script pour trouver le company_id Bolt en testant différentes valeurs.

Usage:
    # Depuis Windows (hors Docker)
    cd backend
    python -m app.scripts.find_bolt_company_id
    
    # Depuis Docker
    docker compose exec backend python scripts/find_bolt_company_id.py
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire backend au path
backend_dir = Path(__file__).parent.parent / "backend"
if backend_dir.exists():
    sys.path.insert(0, str(backend_dir))
else:
    # Si on est déjà dans backend/
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Charger les variables d'environnement depuis backend/.env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)

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
        
        if data.get("code") == 0:
            drivers = data.get("data", {}).get("drivers", [])
            return True, len(drivers), data.get("message", "OK")
        else:
            error_code = data.get("code")
            error_msg = data.get("message", "Unknown error")
            return False, 0, f"Code {error_code}: {error_msg}"
    except Exception as e:
        return False, 0, str(e)


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
    
    # Tester les IDs de 1 à 100 (ou jusqu'à trouver)
    for company_id in range(1, 101):
        success, count, msg = test_company_id(company_id)
        
        if success:
            print(f"✅ company_id={company_id}: {count} drivers trouvés - {msg}")
            found_ids.append((company_id, count))
        elif "COMPANY_NOT_FOUND" in msg or "498807" in msg:
            # Company not found, continue
            if company_id % 10 == 0:
                print(f"   Testé jusqu'à company_id={company_id}...")
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
        print("❌ Aucun company_id valide trouvé dans la plage testée")
        print()
        print("Solutions:")
        print("1. Vérifie dans la documentation Bolt quel est ton company_id")
        print("2. Contacte le support Bolt pour obtenir ton company_id")
        print("3. Le company_id peut être un nombre plus grand (> 100)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompu par l'utilisateur")
        sys.exit(0)

