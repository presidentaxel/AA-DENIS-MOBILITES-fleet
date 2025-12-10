# Déploiement OVH (guide rapide)

## Pré-requis
- Un projet Supabase (ou Postgres géré) avec RLS activé sur chaque table et politiques configurées.
- Un registre d'images (Docker Hub, GHCR ou registry OVH).
- Un serveur OVH (VPS ou Public Cloud) avec Docker / Docker Compose installés.

## Variables d'environnement
- Backend : copier `backend/.env.example` en `backend/.env` et renseigner :
  - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
  - `UBER_CLIENT_ID`, `UBER_CLIENT_SECRET`, `UBER_*`
  - DB : soit la chaîne Supabase, soit une base Postgres OVH.
- Frontend : copier `frontend/.env.example` en `frontend/.env` et renseigner `VITE_API_BASE_URL` (URL publique du backend).

## Build & push des images
```bash
docker build -t <registry>/aa-fleet-backend:latest backend
docker build -t <registry>/aa-fleet-frontend:latest frontend
docker push <registry>/aa-fleet-backend:latest
docker push <registry>/aa-fleet-frontend:latest
```

## Déploiement sur le serveur OVH
1. SSH sur le serveur.
2. Créer un dossier projet et y placer `docker-compose.yml`, `monitoring/prometheus.yml`, et les `.env` remplis.
3. Mettre à jour `docker-compose.yml` pour utiliser les images poussées :
   ```yaml
   image: <registry>/aa-fleet-backend:latest
   image: <registry>/aa-fleet-frontend:latest
   ```
   et configurer les variables (`env_file` / `environment`) pour pointer vers Supabase.
4. Lancer : `docker compose up -d`.
5. Vérifier :
   - Backend: `/health`, `/metrics`
   - Frontend: page de login/dashboard
   - Grafana: configurer la datasource Prometheus (`http://prometheus:9090`).

## Traefik (TLS / reverse proxy) — optionnel
- Créer un réseau partagé : `docker network create appnet` (si absent).
- Utiliser `docker-compose.traefik.yml` en complément : `docker compose -f docker-compose.yml -f docker-compose.traefik.yml up -d`.
- Remplacer `backend.example.com` / `front.example.com` par tes domaines ; décommenter ACME et renseigner l'email pour Let's Encrypt.

## Sécurité / RLS
- RLS doit être activé sur toutes les tables et des politiques doivent limiter les accès par organisation/utilisateur. Garder la clé service role uniquement côté backend.
- Configurer TLS (reverse proxy Nginx/Traefik ou OVH Load Balancer) pour exposer les ports 80/443.

## Mises à jour
- Rebuild + push les images.
- Sur le serveur : `docker compose pull && docker compose up -d`.

