# Traefik (optionnel, OVH)

1. Créer le réseau partagé : `docker network create appnet` (si absent).
2. Copier `docker-compose.traefik.yml` et remplacer `backend.example.com` / `front.example.com` par tes domaines.
3. Activer Let's Encrypt : décommente les lignes ACME et renseigne ton email.
4. Lancer : `docker compose -f docker-compose.yml -f docker-compose.traefik.yml up -d`.
5. Vérifie : `curl -I https://backend.example.com/health`.

