# Commandes rapides - Version courte

## RUN COMMAND #computer

- `cd frontend` → `npm run dev`
- `cd backend` → `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

## GIT COMMAND

- `git add .`
- `git commit -m "#PUSH NAME"`
- `git push`

## DOCKER COMMAND #Push online

**Prérequis:** Ouvrir Docker Desktop + `docker login` (première fois)

### DEV (docker-compose.dev.yml)

**Build/Test:**
- `docker compose -f docker-compose.dev.yml down` *(si compose up avant)*
- `docker compose -f docker-compose.dev.yml build --no-cache`
- `docker compose -f docker-compose.dev.yml up` *(test machine)*

**Push Docker Hub:**

**Frontend:**
```powershell
docker tag apiuber-frontend thelouitos/lmdcvtc-fleet-frontend:dev
if ($?) { docker push thelouitos/lmdcvtc-fleet-frontend:dev }
```

**Backend:**
```powershell
docker tag apiuber-backend thelouitos/lmdcvtc-fleet-backend:dev
if ($?) { docker push thelouitos/lmdcvtc-fleet-backend:dev }
```

### PROD (docker-compose.prod.yml)

**Build/Test:**
- `docker compose -f docker-compose.prod.yml down` *(si compose up avant)*
- `docker compose -f docker-compose.prod.yml build --no-cache`
- `docker compose -f docker-compose.prod.yml up` *(test machine)*

**Push Docker Hub:**

**Frontend:**
```powershell
docker tag apiuber-frontend thelouitos/lmdcvtc-fleet-frontend:latest
if ($?) { docker push thelouitos/lmdcvtc-fleet-frontend:latest }
```

**Backend:**
```powershell
docker tag apiuber-backend thelouitos/lmdcvtc-fleet-backend:latest
if ($?) { docker push thelouitos/lmdcvtc-fleet-backend:latest }
```

---

**💡 Astuce:** Les images sont nommées `apiuber-frontend` et `apiuber-backend` (sans tiret). Vérifier avec: `docker images`

