#!/bin/bash

# Script de déploiement en production
# Usage: ./scripts/deploy.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement en production..."

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

# Vérifier que le fichier .env.prod existe
if [ ! -f .env.prod ]; then
    echo "⚠️  Fichier .env.prod non trouvé"
    echo "📝 Création depuis env.prod.template..."
    if [ -f env.prod.template ]; then
        cp env.prod.template .env.prod
        echo "✅ Fichier .env.prod créé. Veuillez le configurer avant de relancer."
        exit 1
    else
        echo "❌ Fichier env.prod.template non trouvé"
        exit 1
    fi
fi

# Charger les variables d'environnement
export $(cat .env.prod | grep -v '^#' | xargs)

# Vérifier que DOMAIN est défini
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "example.com" ]; then
    echo "❌ Veuillez configurer DOMAIN dans .env.prod"
    exit 1
fi

# Vérifier que ACME_EMAIL est défini
if [ -z "$ACME_EMAIL" ] || [ "$ACME_EMAIL" = "admin@example.com" ]; then
    echo "❌ Veuillez configurer ACME_EMAIL dans .env.prod"
    exit 1
fi

# Créer le réseau Docker s'il n'existe pas
if ! docker network inspect appnet &> /dev/null; then
    echo "📦 Création du réseau Docker appnet..."
    docker network create appnet
    echo "✅ Réseau créé"
else
    echo "✅ Réseau appnet existe déjà"
fi

# Créer le répertoire pour les certificats
mkdir -p infra/traefik/letsencrypt
chmod 600 infra/traefik/letsencrypt 2>/dev/null || true

# Construire les images
echo "🔨 Construction des images Docker..."
docker compose -f docker-compose.prod.yml build

# Arrêter les services existants
echo "🛑 Arrêt des services existants..."
docker compose -f docker-compose.prod.yml down

# Lancer les services
echo "🚀 Lancement des services..."
docker compose -f docker-compose.prod.yml up -d

# Attendre que les services démarrent
echo "⏳ Attente du démarrage des services..."
sleep 5

# Vérifier l'état des services
echo "📊 État des services:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "🌐 URLs:"
echo "   - Frontend: https://app.$DOMAIN"
echo "   - Backend:  https://api.$DOMAIN"
echo "   - Grafana:  https://grafana.$DOMAIN"
echo ""
echo "📝 Vérifiez les logs avec:"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🔍 Vérifiez les certificats SSL (peuvent prendre quelques minutes):"
echo "   ls -la infra/traefik/letsencrypt/"

