#!/usr/bin/env python3
"""
Script pour tester la connexion à Supabase et vérifier que les données peuvent être sauvegardées.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.db import get_db, engine
from app.models.bolt_driver import BoltDriver
from sqlalchemy.orm import Session
from sqlalchemy import text

settings = get_settings()


def test_db_connection():
    """Teste la connexion à la base de données."""
    print("🔍 Test de connexion à la base de données...")
    db_url_display = settings.database_url.replace(settings.db_password, '***')
    print(f"   URL: {db_url_display}")
    print(f"   Host: {settings.db_host}")
    print(f"   Database: {settings.db_name}")
    
    try:
        # Test de connexion simple
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connexion à la base de données OK")
            
            # Vérifier la version PostgreSQL
            version_result = conn.execute(text("SELECT version()"))
            version = version_result.scalar()
            print(f"   Version: {version.split(',')[0]}")
            return True
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("💡 Solutions possibles:")
        print("   1. Vérifie que DB_HOST, DB_NAME, DB_USER, DB_PASSWORD sont corrects")
        if settings.db_host == "db":
            print("   2. Si tu utilises Supabase, change DB_HOST vers ton host Supabase")
            print("      (ex: db.xxxxx.supabase.co)")
        return False


def test_supabase_tables():
    """Vérifie que les tables Bolt existent."""
    print("\n🔍 Vérification des tables...")
    
    tables_to_check = [
        "bolt_drivers",
        "bolt_vehicles",
        "bolt_trips",
        "bolt_earnings",
        "uber_drivers",
        "uber_vehicles",
    ]
    
    try:
        with engine.connect() as conn:
            all_exist = True
            for table_name in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table_name}'
                    );
                """))
                exists = result.scalar()
                
                if exists:
                    # Compter les lignes
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = count_result.scalar()
                    status = "✅" if count > 0 else "⚠️ "
                    print(f"{status} Table {table_name}: {count} lignes")
                    
                    # Pour bolt_drivers, lister les org_id
                    if table_name == "bolt_drivers" and count > 0:
                        org_result = conn.execute(text("SELECT DISTINCT org_id FROM bolt_drivers"))
                        org_ids = [row[0] for row in org_result]
                        print(f"      org_id uniques: {org_ids}")
                else:
                    print(f"❌ Table {table_name} n'existe pas")
                    all_exist = False
                    
            if not all_exist:
                print("\n⚠️  Certaines tables manquent")
                print("   Applique le schéma SQL: supabase/schema.sql")
                print("   Via Supabase Dashboard → SQL Editor")
                return False
                
            return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_insert_driver():
    """Teste l'insertion d'un driver de test."""
    print("\n🔍 Test d'insertion d'un driver de test...")
    
    try:
        db = next(get_db())
        
        # Créer un driver de test
        test_driver = BoltDriver(
            id="test-driver-123",
            org_id="default_org",
            first_name="Test",
            last_name="Driver",
            email="test@example.com",
            active=True,
        )
        
        db.merge(test_driver)
        db.commit()
        print("✅ Driver de test inséré avec succès")
        print(f"   ID: {test_driver.id}, org_id: {test_driver.org_id}")
        
        # Vérifier qu'il est bien là
        found = db.query(BoltDriver).filter(BoltDriver.id == "test-driver-123").first()
        if found:
            print(f"✅ Driver retrouvé: {found.first_name} {found.last_name}, org_id={found.org_id}")
            # Supprimer le driver de test
            db.delete(found)
            db.commit()
            print("✅ Driver de test supprimé")
        else:
            print("⚠️  Driver de test inséré mais non retrouvé")
            print("   Vérifie les permissions RLS dans Supabase")
            
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
        print()
        print("💡 Causes possibles:")
        print("   1. Permissions RLS trop restrictives dans Supabase")
        print("   2. Table n'existe pas ou schéma incorrect")
        print("   3. Problème de connexion")
        import traceback
        traceback.print_exc()
        return False


def check_config():
    """Vérifie la configuration."""
    print("📋 Configuration actuelle:")
    print(f"   DB_HOST: {settings.db_host}")
    print(f"   DB_NAME: {settings.db_name}")
    print(f"   DB_USER: {settings.db_user}")
    print(f"   SUPABASE_URL: {settings.supabase_url or 'Non défini'}")
    print(f"   BOLT_DEFAULT_FLEET_ID: {settings.bolt_default_fleet_id or 'Non défini'}")
    print(f"   UBER_DEFAULT_ORG_ID: {settings.uber_default_org_id or 'Non défini'}")
    print()


def main():
    print("=" * 60)
    print("Test de connexion Supabase/PostgreSQL")
    print("=" * 60)
    print()
    
    check_config()
    
    # Tests
    if not test_db_connection():
        print("\n❌ Impossible de se connecter à la base de données")
        print("   Vérifie tes variables DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    if not test_supabase_tables():
        print("\n⚠️  Les tables n'existent pas ou sont vides")
        print("   Applique le schéma SQL dans Supabase: supabase/schema.sql")
    
    if not test_insert_driver():
        print("\n❌ Impossible d'insérer des données")
        print("   Vérifie les permissions et le schéma")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Tous les tests sont passés !")
    print("=" * 60)


if __name__ == "__main__":
    main()

