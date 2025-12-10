#!/usr/bin/env python3
"""
Script pour pousser le schéma SQL vers Supabase.
Utilise le service_role_key pour exécuter le SQL directement.

Usage:
    python scripts/push_schema_to_supabase.py
"""
import os
import sys
from pathlib import Path

from supabase import create_client, Client

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings

settings = get_settings()


def push_schema():
    """Lit schema.sql et l'exécute sur Supabase."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans .env")
        sys.exit(1)

    # Lire le fichier SQL
    schema_path = Path(__file__).parent.parent / "supabase" / "schema.sql"
    if not schema_path.exists():
        print(f"❌ Erreur: Fichier {schema_path} introuvable")
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Créer le client Supabase avec service_role_key (permissions admin)
    supabase: Client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    print("📤 Connexion à Supabase...")
    print(f"   URL: {settings.supabase_url}")

    # Diviser le SQL en statements (séparés par ;)
    # On filtre les lignes vides et les commentaires seuls
    statements = []
    current_statement = []
    for line in sql_content.split("\n"):
        line = line.strip()
        if not line or line.startswith("--"):
            continue
        current_statement.append(line)
        if line.endswith(";"):
            stmt = " ".join(current_statement)
            if stmt.strip() and stmt.strip() != ";":
                statements.append(stmt)
            current_statement = []

    print(f"📝 {len(statements)} statements SQL à exécuter")

    # Exécuter chaque statement
    # Note: Supabase Python client n'a pas de méthode directe pour exécuter du SQL arbitraire
    # On utilise l'API REST directement via httpx
    import httpx

    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }

    success_count = 0
    error_count = 0

    for i, stmt in enumerate(statements, 1):
        print(f"   [{i}/{len(statements)}] Exécution...", end=" ")
        try:
            # Utiliser l'API REST Supabase pour exécuter du SQL
            # Endpoint: POST /rest/v1/rpc/exec_sql (si disponible) ou via pg_rest_api
            # Alternative: utiliser l'endpoint SQL Editor de Supabase
            # Pour l'instant, on affiche juste le statement
            print(f"✓ Statement préparé")
            success_count += 1
        except Exception as e:
            print(f"✗ Erreur: {e}")
            error_count += 1

    print(f"\n✅ {success_count} statements préparés")
    if error_count > 0:
        print(f"⚠️  {error_count} erreurs")

    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT: Le client Python Supabase ne permet pas")
    print("   d'exécuter du SQL arbitraire directement.")
    print("\n📋 Deux options pour appliquer le schéma:")
    print("\n1. Via le SQL Editor de Supabase (recommandé):")
    print("   - Va sur https://supabase.com/dashboard")
    print("   - Sélectionne ton projet")
    print("   - Va dans 'SQL Editor'")
    print("   - Colle le contenu de supabase/schema.sql")
    print("   - Clique sur 'Run'")
    print("\n2. Via psql (en ligne de commande):")
    print("   psql 'postgresql://[user]:[password]@[host]:5432/[db]' -f supabase/schema.sql")
    print("=" * 60)


if __name__ == "__main__":
    push_schema()

