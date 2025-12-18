# Configuration Digital Ocean App Platform

Ce dossier contient la configuration pour déployer l'application sur Digital Ocean App Platform.

## Fichier app.yaml

Le fichier `.do/app.yaml` contient la configuration de l'application. **IMPORTANT** : Vous devez modifier les valeurs suivantes avant le déploiement :

1. **GitHub Repository** : Remplacez `YOUR_GITHUB_USERNAME/YOUR_REPO_NAME` par votre repository GitHub
2. **Variables d'environnement** : Configurez les secrets pour la base de données dans le dashboard Digital Ocean

## Configuration des variables d'environnement

Dans le dashboard Digital Ocean App Platform, vous devez configurer les secrets suivants pour le service `backend` :

- `DB_HOST` : L'hôte de votre base de données (ex: `db.xxxxx.supabase.co` pour Supabase)
- `DB_PORT` : Le port de la base de données (généralement `5432` ou `6543` pour Supabase connection pooling)
- `DB_NAME` : Le nom de la base de données
- `DB_USER` : L'utilisateur de la base de données
- `DB_PASSWORD` : Le mot de passe de la base de données

## Build Args pour le frontend

Le frontend nécessite `VITE_API_BASE_URL` au moment du build. Digital Ocean App Platform passera automatiquement cette variable d'environnement BUILD_TIME au Dockerfile.

**Note importante** : Si Digital Ocean ne passe pas automatiquement la variable comme build arg, vous devrez peut-être ajouter un `build_command` personnalisé dans le fichier `app.yaml` pour le service frontend :

```yaml
build_command: docker build --build-arg VITE_API_BASE_URL=${VITE_API_BASE_URL} -f ./frontend/Dockerfile -t frontend ./frontend
```

Cependant, le Dockerfile actuel devrait fonctionner car il accepte les variables d'environnement directement.

## Déploiement

1. Poussez ce fichier `.do/app.yaml` dans votre repository
2. Connectez votre repository GitHub à Digital Ocean App Platform
3. Digital Ocean détectera automatiquement le fichier `.do/app.yaml` et utilisera cette configuration
4. Configurez les secrets dans le dashboard Digital Ocean
5. Déployez !

## Notes

- Traefik n'est pas nécessaire car Digital Ocean App Platform gère automatiquement le reverse proxy, le HTTPS et le load balancing
- Les health checks sont configurés pour le backend sur `/health`
- Le backend est accessible via la route `/api`
- Le frontend est accessible via la route `/`

