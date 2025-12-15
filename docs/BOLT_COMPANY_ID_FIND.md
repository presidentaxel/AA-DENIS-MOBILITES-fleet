# Comment trouver le Company ID Bolt

## ⚠️ Le company_id est REQUIS

**Non, tu ne peux pas t'en passer** pour les endpoints suivants :
- `/fleetIntegration/v1/getDrivers` → **requiert `company_id`**
- `/fleetIntegration/v1/getVehicles` → **requiert `company_id`**

L'API Bolt retourne `INVALID_REQUEST` (code 702) si le `company_id` est manquant ou incorrect.

## 🔍 Où trouver le company_id ?

### Méthode 1 : Dans l'URL du portail Bolt (⭐ LA PLUS SIMPLE)

1. Connecte-toi au **Bolt Fleet Portal** : https://fleets.bolt.eu
2. Navigue vers n'importe quelle page (ex: Settings)
3. **Regarde l'URL dans la barre d'adresse**

**Exemple** :
```
https://fleets.bolt.eu/218016/settings/companySettings
```

Le nombre **`218016`** dans l'URL est ton **`company_id`** ! ✅

Voir `docs/BOLT_COMPANY_ID_URL.md` pour plus de détails.

### Méthode 2 : Dans le portail Bolt Fleet (alternative)

1. Connecte-toi au **Bolt Fleet Owner Portal**
2. Va dans **Settings** → **Fleet Integration API**
3. Le `company_id` devrait être affiché là
4. Ou contacte le **support Bolt** et demande ton `company_id` pour l'API Fleet Integration

### Méthode 2 : Via l'API Bolt (si disponible)

Utilise le script pour chercher le `company_id` dans les réponses de l'API :

```bash
docker compose exec backend python scripts/get_bolt_fleet_info.py
```

Ce script teste plusieurs endpoints Bolt et cherche le `company_id` dans les réponses.

Ou teste manuellement :

```bash
# Teste l'endpoint /fleet qui pourrait retourner le company_id
curl -X GET 'https://node.bolt.eu/fleet-integration-gateway/fleet' \
  -H 'Authorization: Bearer TON_TOKEN_BOLT'
```

Regarde dans les réponses des autres endpoints que tu appelles - le `company_id` peut être inclus.

### Méthode 3 : Dans les credentials Bolt

Le `company_id` peut être fourni avec tes credentials Bolt (`BOLT_CLIENT_ID` / `BOLT_CLIENT_SECRET`). Vérifie :
- L'email de bienvenue Bolt
- Les documents d'intégration Bolt
- Le support Bolt

### Méthode 4 : Tester avec des valeurs courantes

Le script `find_bolt_company_id.py` teste automatiquement les IDs de 1 à 100. Si tu obtiens `INVALID_REQUEST` pour tous, c'est que :
- Le `company_id` est un nombre plus grand (> 100)
- Le `company_id` n'est pas un nombre séquentiel
- Il faut le demander au support Bolt

## 🔧 Améliorer le script de recherche

Le script actuel teste seulement 1-100. Tu peux :

1. **Étendre la plage** : Modifie `range(1, 101)` pour tester plus de valeurs
2. **Tester des valeurs spécifiques** : Si tu as une idée du `company_id` (ex: basé sur ton client_id), teste ces valeurs
3. **Vérifier les logs** : Les erreurs `INVALID_REQUEST` signifient que la requête est mal formée ou que le `company_id` n'existe pas

## 📋 Structure de la requête

La requête doit être :

```json
{
  "company_id": 12345,  // ← Nombre entier, REQUIS
  "limit": 10,
  "offset": 0
}
```

**Erreurs possibles** :
- `INVALID_REQUEST` (702) : `company_id` manquant, incorrect, ou requête mal formée
- `COMPANY_NOT_FOUND` : Le `company_id` n'existe pas
- `UNAUTHORIZED` : Problème d'authentification

## ✅ Solution rapide

**Contacte le support Bolt** et demande :
> "Bonjour, j'ai besoin de mon `company_id` pour utiliser l'API Fleet Integration. Mes credentials sont [BOLT_CLIENT_ID]. Pouvez-vous me fournir le `company_id` associé ?"

Ils devraient te le fournir rapidement.

## 🚀 Alternative : Endpoint sans company_id ?

Si l'API Bolt a des endpoints qui ne requièrent pas de `company_id`, on peut les utiliser. Mais pour `getDrivers` et `getVehicles`, c'est **obligatoire**.

Vérifie la documentation Bolt pour voir s'il y a d'autres endpoints disponibles.

