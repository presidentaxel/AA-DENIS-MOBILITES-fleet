# Mode Développement avec Hot-Reload

Ce guide explique comment utiliser le mode développement avec hot-reload pour éviter de rebuild l'image Docker à chaque modification de code.

## 🚀 Démarrage rapide

```bash
# Démarrer en mode développement (avec hot-reload)
docker compose -f docker-compose.dev.yml up --build
```

## ✨ Avantages du mode développement

- **Hot-reload automatique** : Les modifications de code sont détectées automatiquement
- **Pas de rebuild** : Plus besoin de rebuild l'image à chaque changement
- **Développement rapide** : Les changements sont visibles immédiatement

## 📝 Comment ça fonctionne

1. **Volumes montés** : Le code backend (`./backend/app`) est monté en volume dans le container
2. **Uvicorn avec --reload** : Le serveur surveille les changements et redémarre automatiquement
3. **Modifications instantanées** : Dès que vous sauvegardez un fichier, le serveur redémarre

## 🔧 Utilisation

### Démarrer les services

```bash
# Mode développement (avec hot-reload)
docker compose -f docker-compose.dev.yml up

# Ou en arrière-plan
docker compose -f docker-compose.dev.yml up -d
```

### Voir les logs

```bash
# Logs du backend
docker compose -f docker-compose.dev.yml logs -f backend

# Tous les logs
docker compose -f docker-compose.dev.yml logs -f
```

### Arrêter les services

```bash
docker compose -f docker-compose.dev.yml down
```

## 📂 Fichiers modifiables sans rebuild

Avec le mode développement, vous pouvez modifier ces fichiers et voir les changements immédiatement :

- ✅ `backend/app/**/*.py` - Tous les fichiers Python du backend
- ✅ `backend/scripts/**/*.py` - Les scripts Python

## ⚠️ Fichiers nécessitant un rebuild

Ces fichiers nécessitent toujours un rebuild :

- ❌ `backend/requirements.txt` - Ajout de nouvelles dépendances
- ❌ `backend/Dockerfile.dev` - Modification du Dockerfile
- ❌ `docker-compose.dev.yml` - Modification de la configuration Docker

Pour ces cas, utilisez :

```bash
docker compose -f docker-compose.dev.yml up --build
```

## 🔄 Comparaison des modes

| Fonctionnalité | Mode Production | Mode Développement |
|----------------|-----------------|-------------------|
| Hot-reload | ❌ Non | ✅ Oui |
| Rebuild nécessaire | ✅ Oui | ❌ Non (sauf dépendances) |
| Volumes montés | ❌ Non | ✅ Oui |
| Performance | ✅ Optimale | ⚠️ Légèrement plus lent |

## 💡 Astuces

### Vérifier que le hot-reload fonctionne

1. Modifiez un fichier dans `backend/app/` (par exemple, ajoutez un `print("test")`)
2. Sauvegardez le fichier
3. Regardez les logs : vous devriez voir `Reloading...` puis `Application startup complete`

### Problèmes courants

**Le hot-reload ne fonctionne pas :**
- Vérifiez que vous utilisez `docker-compose.dev.yml` et non `docker-compose.yml`
- Vérifiez que les volumes sont bien montés : `docker compose -f docker-compose.dev.yml ps`
- Vérifiez les logs pour voir les erreurs : `docker compose -f docker-compose.dev.yml logs backend`

**Les changements ne sont pas détectés :**
- Assurez-vous que le fichier est bien sauvegardé
- Vérifiez que le fichier est dans `backend/app/` (pas dans un sous-dossier ignoré)
- Redémarrez le container : `docker compose -f docker-compose.dev.yml restart backend`

## 🎯 Workflow recommandé

1. **Démarrage** : `docker compose -f docker-compose.dev.yml up`
2. **Développement** : Modifiez le code, sauvegardez, les changements sont automatiquement appliqués
3. **Tests** : Testez vos modifications via l'API ou le frontend
4. **Arrêt** : `docker compose -f docker-compose.dev.yml down` quand vous avez terminé

## 📚 Ressources

- [Documentation Uvicorn --reload](https://www.uvicorn.org/settings/#reload)
- [Documentation Docker Compose volumes](https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes)

