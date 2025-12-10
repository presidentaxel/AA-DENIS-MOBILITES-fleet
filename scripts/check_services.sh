#!/bin/bash
# Script pour vérifier que tous les services sont démarrés et accessibles

echo "🔍 Vérification des services..."
echo ""

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

# Vérifier que les services sont démarrés
echo "📦 Services Docker:"
docker compose ps

echo ""
echo "🌐 Vérification des endpoints:"

# Backend
echo -n "  Backend (http://localhost:8000/health): "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Non accessible"
fi

# Backend metrics
echo -n "  Backend Metrics (http://localhost:8000/metrics): "
if curl -s http://localhost:8000/metrics > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Non accessible"
fi

# Prometheus
echo -n "  Prometheus (http://localhost:9090): "
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Non accessible"
fi

# Grafana
echo -n "  Grafana (http://localhost:3000): "
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Non accessible"
fi

echo ""
echo "💡 Si des services ne sont pas accessibles:"
echo "   1. Vérifie que Docker Compose est démarré: docker compose ps"
echo "   2. Voir les logs: docker compose logs [service]"
echo "   3. Redémarrer: docker compose restart [service]"

