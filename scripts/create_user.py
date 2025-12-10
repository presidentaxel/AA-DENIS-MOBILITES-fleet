#!/usr/bin/env python3
"""
Script pour créer un utilisateur Supabase via l'API.

Usage:
    python scripts/create_user.py email@example.com password123
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.supabase_client import get_supabase_client

settings = get_settings()


def create_user(email: str, password: str, auto_confirm: bool = True):
    """Crée un utilisateur dans Supabase."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans .env")
        sys.exit(1)

    try:
        supabase = get_supabase_client()
        
        # Utiliser l'admin API pour créer un utilisateur
        from supabase import create_client as create_supabase_client
        
        admin_client = create_supabase_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        
        response = admin_client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": auto_confirm,
        })
        
        if response.user:
            print(f"✅ Utilisateur créé avec succès !")
            print(f"   Email: {response.user.email}")
            print(f"   ID: {response.user.id}")
            if auto_confirm:
                print(f"   ✅ Email confirmé automatiquement")
            else:
                print(f"   ⚠️  L'utilisateur doit confirmer son email")
        else:
            print("❌ Erreur: Impossible de créer l'utilisateur")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_user.py <email> <password> [--no-confirm]")
        print("\nExemple:")
        print("  python scripts/create_user.py admin@example.com password123")
        print("  python scripts/create_user.py user@example.com password123 --no-confirm")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    auto_confirm = "--no-confirm" not in sys.argv
    
    create_user(email, password, auto_confirm)

