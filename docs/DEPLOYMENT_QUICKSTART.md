# Déploiement rapide en production

## Résumé des changements

✅ **Nouveau fichier** : `docker-compose.prod.yml` - Configuration complète de production avec Traefik et HTTPS

✅ **Fichier mis à jour** : `docker-compose.traefik.yml` - Corrigé avec HTTPS et redirections

✅ **Script de déploiement** : `scripts/deploy.sh` - Automatise le déploiement

✅ **Documentation** : `docs/DEPLOYMENT.md` - Guide complet

## Déploiement en 5 étapes

### 1. Sur votre serveur (DigitalOcean, OVH, etc.)

```bash
# Cloner/transférer le projet
cd /opt
git clone <votre-repo> api-uber
cd api-uber
```

### 2. Configurer les variables d'environnement

```bash
# Créer le fichier de configuration
cp env.prod.template .env.prod
nano .env.prod
```

**À modifier :**
- `DOMAIN=mon-domaine.com` (votre domaine)
- `ACME_EMAIL=votre@email.com` (pour Let's Encrypt)
- `DB_PASSWORD=mot_de_passe_fort` (sécurité)

### 3. Configurer les DNS OVH

Dans votre interface OVH, ajoutez :
```
Type A | app.mon-domaine.com  | IP_du_serveur
Type A | api.mon-domaine.com  | IP_du_serveur
```

### 4. Lancer le déploiement

```bash
# Option 1 : Script automatique
./scripts/deploy.sh

# Option 2 : Manuel
docker network create appnet
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 5. Vérifier

```bash
# Vérifier les services
docker compose -f docker-compose.prod.yml ps

# Vérifier les logs
docker logs traefik
docker logs backend
docker logs frontend

# Tester (les certificats SSL peuvent prendre 2-3 minutes)
curl -I https://app.mon-domaine.com
curl -I https://api.mon-domaine.com
```

## Ce qui a été corrigé

### ✅ HTTPS activé
- Routers HTTPS configurés avec Let's Encrypt
- Redirection automatique HTTP → HTTPS

### ✅ Hostnames configurés
- `app.domaine.tld` → Frontend
- `api.domaine.tld` → Backend
- `grafana.domaine.tld` → Grafana (optionnel)

### ✅ Ports non exposés directement
- Plus de `5173:80` ou `8000:8000` sur l'hôte
- Seul Traefik expose 80/443
- Tout passe par Traefik avec HTTPS

### ✅ Réseau Docker
- Le script crée automatiquement le réseau `appnet`
- Ou création manuelle : `docker network create appnet`

### ✅ Grafana sécurisé
- Plus de port 3000 exposé directement
- Accessible via Traefik sur `grafana.domaine.tld` avec HTTPS

## Structure des fichiers

```
.
├── docker-compose.prod.yml      # ← Configuration production complète
├── docker-compose.traefik.yml    # ← Mis à jour (HTTPS)
├── docker-compose.yml            # ← Dev local (inchangé)
├── env.prod.template             # ← Template de configuration
├── scripts/
│   └── deploy.sh                 # ← Script de déploiement
└── docs/
    ├── DEPLOYMENT.md             # ← Guide complet
    └── DEPLOYMENT_QUICKSTART.md  # ← Ce fichier
```

## Commandes utiles

```bash
# Voir les logs
docker compose -f docker-compose.prod.yml logs -f

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart backend

# Mettre à jour
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Arrêter
docker compose -f docker-compose.prod.yml down
```

## Problèmes courants

### "network appnet not found"
```bash
docker network create appnet
```

### "port already in use"
Vérifier qu'aucun autre service n'utilise 80/443 :
```bash
sudo lsof -i :80
sudo lsof -i :443
```

### Certificats SSL ne se génèrent pas
1. Vérifier les DNS : `dig app.mon-domaine.com`
2. Vérifier que les ports 80/443 sont ouverts
3. Attendre 2-3 minutes pour Let's Encrypt

## Support

Voir `docs/DEPLOYMENT.md` pour le guide complet avec tous les détails.

