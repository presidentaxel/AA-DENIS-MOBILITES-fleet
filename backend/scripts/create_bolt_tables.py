"""
Script pour créer les tables Bolt dans Supabase via l'API.
Alternative si le SQL Editor ne fonctionne pas.
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.supabase_client import get_supabase_client
from app.core.config import get_settings
from app.core import logging as app_logging

logger = app_logging.get_logger(__name__)
settings = get_settings()


def create_bolt_tables():
    """Crée les tables Bolt dans Supabase."""
    supabase = get_supabase_client()
    
    # Malheureusement, l'API REST Supabase ne permet pas d'exécuter du SQL arbitraire
    # Il faut utiliser le SQL Editor ou psql
    print("❌ L'API REST Supabase ne permet pas d'exécuter du SQL arbitraire.")
    print("\n📋 Pour créer les tables, utilise l'une des méthodes suivantes:\n")
    print("1️⃣  Via le SQL Editor Supabase (RECOMMANDÉ):")
    print("   - Va sur https://supabase.com/dashboard")
    print("   - Sélectionne ton projet")
    print("   - Va dans SQL Editor")
    print("   - Clique sur New query")
    print("   - Ouvre le fichier: supabase/schema.sql")
    print("   - Copie-colle tout le contenu")
    print("   - Clique sur Run (Ctrl+Enter)\n")
    print("2️⃣  Via psql (si installé):")
    print("   psql \"$DATABASE_URL\" -f supabase/schema.sql\n")
    print("3️⃣  Via Supabase CLI:")
    print("   supabase db push\n")
    return False


if __name__ == "__main__":
    print("🚀 Création des tables Bolt dans Supabase...\n")
    create_bolt_tables()

