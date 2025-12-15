#!/usr/bin/env python3
"""
Script pour tester la résolution DNS et la connexion à l'API Bolt.
À exécuter depuis le container backend.
"""
import sys
import socket
import httpx
from urllib.parse import urlparse

def test_dns(hostname):
    """Teste la résolution DNS d'un hostname."""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS OK: {hostname} → {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS ÉCHEC: {hostname} - {e}")
        return False

def test_http(url):
    """Teste une connexion HTTP."""
    try:
        resp = httpx.get(url, timeout=5, follow_redirects=True)
        print(f"✅ HTTP OK: {url} → {resp.status_code}")
        return True
    except httpx.ConnectError as e:
        print(f"❌ HTTP ÉCHEC: {url} - {e}")
        return False
    except Exception as e:
        print(f"❌ HTTP ERREUR: {url} - {e}")
        return False

def main():
    print("🔍 Test de connexion à l'API Bolt\n")
    
    # URLs à tester
    urls_to_test = [
        "https://api.bolt.eu",
        "https://oidc.bolt.eu",
        "https://api.bolt.com",  # Au cas où
        "https://fleet-api.bolt.eu",  # Peut-être un autre sous-domaine
    ]
    
    print("1. Test DNS:")
    print("-" * 50)
    for url in urls_to_test:
        parsed = urlparse(url)
        test_dns(parsed.netloc)
    
    print("\n2. Test HTTP:")
    print("-" * 50)
    for url in urls_to_test:
        test_http(url)
    
    print("\n3. Test spécifique oidc.bolt.eu/token:")
    print("-" * 50)
    test_http("https://oidc.bolt.eu/token")
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main()

