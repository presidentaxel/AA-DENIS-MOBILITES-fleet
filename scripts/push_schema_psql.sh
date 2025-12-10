#!/bin/bash
# Script pour pousser le schéma SQL vers Supabase via psql
# Usage: ./scripts/push_schema_psql.sh

set -e

# Charger les variables d'environnement depuis .env
if [ -f backend/.env ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "❌ Erreur: Variables DB_HOST, DB_NAME, DB_USER, DB_PASSWORD doivent être définies"
    exit 1
fi

SCHEMA_FILE="supabase/schema.sql"

if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ Erreur: Fichier $SCHEMA_FILE introuvable"
    exit 1
fi

echo "📤 Connexion à Supabase..."
echo "   Host: $DB_HOST"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"

# Construire la connection string
CONNECTION_STRING="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT:-5432}/${DB_NAME}"

echo "📝 Exécution du schéma SQL..."
psql "$CONNECTION_STRING" -f "$SCHEMA_FILE"

echo "✅ Schéma appliqué avec succès!"

