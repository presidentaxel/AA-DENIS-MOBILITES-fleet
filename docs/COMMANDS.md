# Commandes rapides

> **Note:** Remplacez `VOTRE_USERNAME` par votre nom d'utilisateur Docker Hub

---

## RUN COMMAND #computer

### Développement local (sans Docker)

**Frontend:**
```bash
cd frontend
npm run dev
```

**Backend:**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## GIT COMMAND

```bash
git add .
git commit -m "#PUSH NAME"
git push
```

## DOCKER COMMAND #Push online

### Prérequis
- Ouvrir Docker Desktop
- Se connecter à Docker Hub : `docker login` (première utilisation)

---

### Version DEV (docker-compose.dev.yml)

**Build et test local:**
```bash
docker compose -f docker-compose.dev.yml down          # Si compose up utilisé avant
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up           # Test machine
```

**Push vers Docker Hub:**

**Frontend:**
```bash
docker tag apiuber-frontend thelouitos/lmdcvtc-fleet-frontend:dev
if ($?) { docker push thelouitos/lmdcvtc-fleet-frontend:dev }
```

**Backend:**
```bash
docker tag apiuber-backend thelouitos/lmdcvtc-fleet-backend:dev
if ($?) { docker push thelouitos/lmdcvtc-fleet-backend:dev }
```

---

### Version PROD (docker-compose.prod.yml)

**Build et test local:**
```bash
docker compose -f docker-compose.prod.yml down        # Si compose up utilisé avant
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up          # Test machine
```

**Push vers Docker Hub:**

**Frontend:**
```bash
docker tag apiuber-frontend thelouitos/lmdcvtc-fleet-frontend:latest
if ($?) { docker push thelouitos/lmdcvtc-fleet-frontend:latest }
```

**Backend:**
```bash
docker tag apiuber-backend thelouitos/lmdcvtc-fleet-backend:latest
if ($?) { docker push thelouitos/lmdcvtc-fleet-backend:latest }
```

**Traefik (optionnel):**
```bash
docker tag apiuber-traefik thelouitos/lmdcvtc-fleet-traefik:latest
if ($?) { docker push thelouitos/lmdcvtc-fleet-traefik:latest }
```

---

## Notes

- **Noms d'images Docker** : Les images sont nommées `apiuber-frontend` et `apiuber-backend` (sans tiret, format Docker Compose)
- **Docker Hub** : `thelouitos` (nom d'utilisateur Docker Hub)
- Les images sont taggées avec `:dev` pour la version développement et `:latest` pour la production
- Les commandes `if ($?) { ... }` sont pour PowerShell (Windows)
- Pour Linux/Mac, utilisez : `docker tag ... && docker push ...`

**Trouver le nom réel de l'image après build:**
```bash
docker images
# Les images sont nommées: apiuber-frontend, apiuber-backend
# Format Docker Compose: nom-du-dossier-nom-du-service (sans tirets dans le nom final)
```

## Commandes utiles

**Voir les images Docker:**
```bash
docker images
```

**Voir les conteneurs en cours:**
```bash
docker ps
```

**Voir tous les conteneurs:**
```bash
docker ps -a
```

**Arrêter tous les conteneurs:**
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.dev.yml down
```

**Voir les logs:**
```bash
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.dev.yml logs -f
```

