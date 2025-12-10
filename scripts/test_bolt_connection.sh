#!/bin/bash
# Script pour tester la connexion à l'API Bolt depuis Docker

echo "🔍 Test de connexion à l'API Bolt..."
echo ""

echo "1. Test DNS pour api.bolt.eu:"
docker compose exec backend nslookup api.bolt.eu || echo "❌ DNS échoue"

echo ""
echo "2. Test DNS pour oidc.bolt.eu:"
docker compose exec backend nslookup oidc.bolt.eu || echo "❌ DNS échoue"

echo ""
echo "3. Test ping api.bolt.eu:"
docker compose exec backend ping -c 3 api.bolt.eu || echo "❌ Ping échoue"

echo ""
echo "4. Test HTTP vers api.bolt.eu:"
docker compose exec backend curl -I https://api.bolt.eu || echo "❌ HTTP échoue"

echo ""
echo "5. Test HTTP vers oidc.bolt.eu:"
docker compose exec backend curl -I https://oidc.bolt.eu/token || echo "❌ HTTP échoue"

echo ""
echo "6. Variables d'environnement Bolt:"
docker compose exec backend env | grep BOLT

echo ""
echo "✅ Tests terminés"

