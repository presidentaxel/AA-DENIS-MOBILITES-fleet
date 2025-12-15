from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH pour que les imports fonctionnent
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.models import Base

# Importer tous les modèles pour qu'Alembic les détecte dans Base.metadata
from app.models.org import UberOrganization  # noqa: F401
from app.models.driver import UberDriver  # noqa: F401
from app.models.vehicle import UberVehicle  # noqa: F401
from app.models.driver_metrics import DriverDailyMetrics  # noqa: F401
from app.models.driver_payments import DriverPayment  # noqa: F401
from app.models.bolt_org import BoltOrganization  # noqa: F401
from app.models.bolt_driver import BoltDriver  # noqa: F401
from app.models.bolt_vehicle import BoltVehicle  # noqa: F401
from app.models.bolt_trip import BoltTrip  # noqa: F401
from app.models.bolt_earning import BoltEarning  # noqa: F401

settings = get_settings()

config = context.config

# Vérifier que la configuration est correctement chargée
try:
    script_location = config.get_main_option("script_location")
    if not script_location:
        raise ValueError("script_location non trouvé dans alembic.ini")
    print(f"[Alembic] script_location: {script_location}")
except Exception as e:
    print(f"[Alembic] Erreur lors du chargement de la config: {e}")
    print(f"[Alembic] config_file_name: {config.config_file_name}")
    raise

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Vérifier que les variables de base de données sont configurées
if not settings.db_host or not settings.db_name or not settings.db_user:
    raise ValueError(
        f"Variables de base de données manquantes. "
        f"DB_HOST={settings.db_host}, DB_NAME={settings.db_name}, DB_USER={settings.db_user}, DB_PORT={settings.db_port}"
    )

database_url = settings.database_url
print(f"[Alembic] Connexion à la base de données: {settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}")
# Ne pas afficher le mot de passe complet, juste vérifier qu'il est présent
print(f"[Alembic] Mot de passe défini: {'Oui' if settings.db_password else 'Non'} (longueur: {len(settings.db_password) if settings.db_password else 0})")
# Afficher l'URL sans le mot de passe pour debug
url_parts = database_url.split("@")
if len(url_parts) > 1:
    safe_url = url_parts[0].split(":")[0] + ":***@" + "@".join(url_parts[1:])
    print(f"[Alembic] URL (masquée): {safe_url}")

# Désactiver l'interpolation pour éviter les problèmes avec les caractères spéciaux dans le mot de passe
# Utiliser set_main_option avec interpolation désactivée
config.attributes["sqlalchemy.url"] = database_url
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # Récupérer l'URL depuis les attributs si disponible, sinon depuis la config
    url = config.attributes.get("sqlalchemy.url") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Si l'URL est dans les attributs, l'utiliser directement
    database_url = config.attributes.get("sqlalchemy.url")
    if database_url:
        from sqlalchemy import create_engine
        connectable = create_engine(database_url, poolclass=pool.NullPool)
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section) or {},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

