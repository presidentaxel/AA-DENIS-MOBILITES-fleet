@echo off
REM Script Windows pour tester la connexion à l'API Bolt depuis Docker

echo 🔍 Test de connexion à l'API Bolt...
echo.

echo 1. Test DNS pour api.bolt.eu:
docker compose exec backend nslookup api.bolt.eu
if %ERRORLEVEL% NEQ 0 echo ❌ DNS échoue

echo.
echo 2. Test DNS pour oidc.bolt.eu:
docker compose exec backend nslookup oidc.bolt.eu
if %ERRORLEVEL% NEQ 0 echo ❌ DNS échoue

echo.
echo 3. Variables d'environnement Bolt:
docker compose exec backend env | findstr BOLT

echo.
echo ✅ Tests terminés

