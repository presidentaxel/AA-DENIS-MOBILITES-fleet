# Script PowerShell pour tester la connexion à l'API Bolt depuis Windows

Write-Host "🔍 Test de connexion à l'API Bolt depuis Windows" -ForegroundColor Cyan
Write-Host ""

# Test DNS
Write-Host "1. Test DNS pour api.bolt.eu:" -ForegroundColor Yellow
try {
    $result = Resolve-DnsName -Name "api.bolt.eu" -ErrorAction Stop
    Write-Host "✅ DNS OK: api.bolt.eu → $($result[0].IPAddress)" -ForegroundColor Green
} catch {
    Write-Host "❌ DNS ÉCHEC: api.bolt.eu - $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. Test DNS pour oidc.bolt.eu:" -ForegroundColor Yellow
try {
    $result = Resolve-DnsName -Name "oidc.bolt.eu" -ErrorAction Stop
    Write-Host "✅ DNS OK: oidc.bolt.eu → $($result[0].IPAddress)" -ForegroundColor Green
} catch {
    Write-Host "❌ DNS ÉCHEC: oidc.bolt.eu - $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. Test HTTP vers api.bolt.eu:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://api.bolt.eu" -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ HTTP OK: https://api.bolt.eu → Status $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ HTTP ÉCHEC: https://api.bolt.eu - $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Test HTTP vers oidc.bolt.eu/token:" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://oidc.bolt.eu/token" -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ HTTP OK: https://oidc.bolt.eu/token → Status $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  HTTP: https://oidc.bolt.eu/token - $_" -ForegroundColor Yellow
    Write-Host "   (C'est normal si ça retourne 405 Method Not Allowed, l'endpoint nécessite POST)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Tests terminés" -ForegroundColor Cyan
Write-Host ""
Write-Host "Si les tests DNS/HTTP fonctionnent depuis Windows mais pas depuis Docker," -ForegroundColor Yellow
Write-Host "c'est un problème de réseau Docker. Redémarre Docker Compose après avoir" -ForegroundColor Yellow
Write-Host "ajouté les serveurs DNS dans docker-compose.yml." -ForegroundColor Yellow

