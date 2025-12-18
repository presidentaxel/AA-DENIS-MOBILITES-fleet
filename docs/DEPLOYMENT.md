# Guide de déploiement en production

Ce guide explique comment déployer l'application en production avec Traefik, HTTPS et Let's Encrypt.

## Architecture de production

- **Traefik** : Reverse proxy et gestionnaire SSL (ports 80/443)
- **Frontend** : Accessible sur `app.domaine.tld` (HTTPS)
- **Backend** : Accessible sur `api.domaine.tld` (HTTPS)
- **Grafana** : Optionnel, accessible sur `grafana.domaine.tld` (HTTPS)
- **PostgreSQL** : Base de données (non exposée publiquement)
- **Prometheus** : Monitoring (optionnel, non exposé par défaut)

## Prérequis

1. **Serveur** (DigitalOcean, OVH, etc.) avec :
   - Docker et Docker Compose installés
   - Ports 80 et 443 ouverts
   - Accès root/sudo

2. **Domaines configurés** :
   - `app.domaine.tld` → IP du serveur
   - `api.domaine.tld` → IP du serveur
   - (Optionnel) `grafana.domaine.tld` → IP du serveur

3. **DNS OVH** (ou autre provider) :
   ```
   Type A | app.domaine.tld  | IP_du_serveur
   Type A | api.domaine.tld  | IP_du_serveur
   ```

## Étapes de déploiement

### 1. Préparer l'environnement

```bash
# Sur le serveur, cloner ou transférer le projet
cd /opt  # ou votre répertoire préféré
git clone <votre-repo> api-uber
cd api-uber

# Créer le réseau Docker partagé
docker network create appnet

# Créer le répertoire pour les certificats Let's Encrypt
mkdir -p infra/traefik/letsencrypt
chmod 600 infra/traefik/letsencrypt  # Sécurité
```

### 2. Configurer les variables d'environnement

```bash
# Copier le fichier d'exemple
cp .env.prod.example .env.prod

# Éditer .env.prod avec vos valeurs
nano .env.prod
```

**Variables importantes :**
- `DOMAIN` : Votre domaine principal (ex: `mon-domaine.com`)
- `ACME_EMAIL` : Email pour Let's Encrypt (obligatoire)
- `DB_PASSWORD` : Mot de passe PostgreSQL fort
- `DB_HOST` : `db` (local) ou URL Supabase si vous utilisez Supabase

### 3. Configurer le backend

```bash
# Créer/éditer backend/.env
cd backend
cp .env.example .env  # Si vous avez un exemple
nano .env
```

Assurez-vous que les variables correspondent à celles de `.env.prod`.

### 4. Construire et lancer les services

```bash
# Revenir à la racine
cd ..

# Construire les images
docker compose -f docker-compose.prod.yml build

# Lancer les services
docker compose -f docker-compose.prod.yml up -d
```

### 5. Vérifier le déploiement

```bash
# Vérifier que tous les conteneurs sont en cours d'exécution
docker compose -f docker-compose.prod.yml ps

# Vérifier les logs Traefik
docker logs traefik

# Vérifier les logs backend
docker logs backend

# Vérifier les logs frontend
docker logs frontend
```

### 6. Tester l'accès

```bash
# Tester le backend (devrait rediriger vers HTTPS)
curl -I http://api.domaine.tld/health

# Tester le frontend (devrait rediriger vers HTTPS)
curl -I http://app.domaine.tld

# Tester HTTPS (les certificats peuvent prendre quelques minutes à être générés)
curl -I https://api.domaine.tld/health
curl -I https://app.domaine.tld
```

### 7. Vérifier les certificats SSL

```bash
# Vérifier que les certificats Let's Encrypt sont générés
ls -la infra/traefik/letsencrypt/

# Vous devriez voir un fichier acme.json
```

## Configuration avancée

### Exposer Grafana via Traefik

Grafana est déjà configuré dans `docker-compose.prod.yml` pour être accessible sur `grafana.domaine.tld`.

1. Ajouter un enregistrement DNS : `grafana.domaine.tld` → IP du serveur
2. Redémarrer les services :
   ```bash
   docker compose -f docker-compose.prod.yml restart grafana traefik
   ```

### Exposer Prometheus via Traefik

Décommentez les labels Traefik dans la section `prometheus` de `docker-compose.prod.yml` :

```yaml
prometheus:
  # ...
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.prometheus.rule=Host(`prometheus.${DOMAIN:-example.com}`)"
    - "traefik.http.routers.prometheus.entrypoints=websecure"
    - "traefik.http.routers.prometheus.tls.certresolver=le"
    - "traefik.http.services.prometheus.loadbalancer.server.port=9090"
```

### Utiliser Supabase au lieu de PostgreSQL local

1. Dans `.env.prod`, définir :
   ```env
   DB_HOST=db.xxxxx.supabase.co
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=votre_mot_de_passe_supabase
   ```

2. Dans `backend/.env`, définir les mêmes valeurs.

3. **Important** : Retirer ou commenter le service `db` dans `docker-compose.prod.yml` si vous utilisez Supabase.

### Mise à jour de l'application

```bash
# Arrêter les services
docker compose -f docker-compose.prod.yml down

# Récupérer les dernières modifications
git pull

# Reconstruire les images
docker compose -f docker-compose.prod.yml build

# Relancer les services
docker compose -f docker-compose.prod.yml up -d
```

## Dépannage

### Les certificats SSL ne se génèrent pas

1. Vérifier que les DNS pointent bien vers le serveur :
   ```bash
   dig app.domaine.tld
   dig api.domaine.tld
   ```

2. Vérifier que les ports 80 et 443 sont ouverts :
   ```bash
   sudo ufw status
   # ou
   sudo iptables -L -n
   ```

3. Vérifier les logs Traefik :
   ```bash
   docker logs traefik | grep -i acme
   ```

### Le frontend ne peut pas accéder au backend

1. Vérifier que `VITE_API_BASE_URL` dans `docker-compose.prod.yml` pointe vers `https://api.domaine.tld`
2. Reconstruire le frontend :
   ```bash
   docker compose -f docker-compose.prod.yml build frontend
   docker compose -f docker-compose.prod.yml up -d frontend
   ```

### Erreur "network appnet not found"

```bash
# Créer le réseau
docker network create appnet
```

### Erreur "port already in use"

Vérifier qu'aucun autre service n'utilise les ports 80, 443 :
```bash
sudo netstat -tulpn | grep -E ':(80|443)'
# ou
sudo lsof -i :80
sudo lsof -i :443
```

## Sécurité

1. **Ne jamais exposer PostgreSQL** : Le port 5432 n'est pas exposé publiquement.
2. **Utiliser des mots de passe forts** : Changez `DB_PASSWORD` dans `.env.prod`.
3. **Protéger Grafana** : Configurez l'authentification dans Grafana.
4. **Firewall** : Configurez un firewall (UFW, iptables) pour limiter l'accès.
5. **Backups** : Configurez des backups réguliers de la base de données.

## Monitoring

- **Traefik Dashboard** : `http://traefik.domaine.tld:8080` (si configuré)
- **Grafana** : `https://grafana.domaine.tld` (si configuré)
- **Logs** : `docker logs <container_name>`

## Support

En cas de problème, vérifiez :
1. Les logs des conteneurs : `docker logs <container_name>`
2. Les logs Traefik : `docker logs traefik`
3. La configuration DNS
4. Les certificats SSL : `ls -la infra/traefik/letsencrypt/`

