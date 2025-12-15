# Diagnostic : Tables vides dans Supabase

## Problème

Les endpoints retournent `[]` et les tables sont vides dans Supabase.

## Causes possibles

### 1. Le backend se connecte à PostgreSQL local au lieu de Supabase

**Symptôme** : Les données sont sauvegardées mais tu ne les vois pas dans Supabase Dashboard.

**Solution** : Configure `backend/.env` pour pointer vers Supabase :

```env
# ❌ SUPPRIME ou commente ces lignes (PostgreSQL local Docker)
# DB_HOST=db
# DB_NAME=aa_denis_fleet

# ✅ AJOUTE ces lignes (Supabase)
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe_supabase
```

**Où trouver ces infos** :
- Va sur https://supabase.com/dashboard
- Settings → Database → Connection string → URI
- Extrais l'host, le port, le user et le password

### 2. Le schéma SQL n'est pas appliqué dans Supabase

**Symptôme** : Les tables n'existent pas dans Supabase Dashboard → Table Editor.

**Solution** :
1. Va sur Supabase Dashboard → SQL Editor
2. Ouvre `supabase/schema.sql`
3. Copie-colle tout le contenu
4. Clique sur Run

### 3. Le `company_id` Bolt n'est pas défini

**Symptôme** : La synchronisation réussit mais retourne 0 drivers.

**Solution** :
1. Trouve ton `company_id` Bolt (voir `docs/BOLT_COMPANY_ID.md`)
2. Ajoute dans `backend/.env` :
   ```env
   BOLT_DEFAULT_FLEET_ID=ton_company_id
   ```

## Diagnostic étape par étape

### Étape 1 : Tester la connexion

```bash
# Depuis le container backend
docker compose exec backend python scripts/test_supabase_connection.py
```

Ou depuis ton terminal :

```bash
cd backend
python ../scripts/test_supabase_connection.py
```

**Résultat attendu** :
- ✅ Connexion à la base de données OK
- ✅ Tables existent
- ✅ Insertion fonctionne

### Étape 2 : Vérifier la configuration

```bash
# Voir la config actuelle
docker compose exec backend env | grep -E "DB_|SUPABASE"
```

**Vérifie que** :
- `DB_HOST` pointe vers Supabase (pas `db`)
- `SUPABASE_URL` est défini
- `BOLT_DEFAULT_FLEET_ID` est défini (si tu utilises Bolt)

### Étape 3 : Vérifier les tables dans Supabase

1. Va sur Supabase Dashboard
2. Table Editor
3. Tu devrais voir : `bolt_drivers`, `bolt_vehicles`, etc.

Si les tables n'existent pas → applique le schéma (voir ci-dessus).

### Étape 4 : Tester la synchronisation

```bash
# Si tu as un company_id
POST http://localhost:8000/bolt/sync/drivers?company_id=123
Authorization: Bearer <ton_jwt>
```

Puis vérifie dans Supabase Dashboard → Table Editor → `bolt_drivers` que les données sont là.

### Étape 5 : Vérifier les stats

```bash
GET http://localhost:8000/bolt/debug/stats
Authorization: Bearer <ton_jwt>
```

**Résultat attendu** :
```json
{
  "drivers": {
    "total_in_db": 5,
    "for_your_org_id": 5
  }
}
```

Si `total_in_db` est 0 mais que la sync a réussi → problème de `org_id` ou de connexion DB.

## Checklist rapide

- [ ] `DB_HOST` pointe vers Supabase (pas `db`)
- [ ] `DB_PASSWORD` est le bon mot de passe Supabase
- [ ] Le schéma SQL est appliqué dans Supabase
- [ ] `BOLT_DEFAULT_FLEET_ID` est défini (si Bolt)
- [ ] Les tables existent dans Supabase Dashboard
- [ ] La connexion fonctionne (`test_supabase_connection.py`)
- [ ] L'insertion fonctionne (`test_supabase_connection.py`)

## Commandes utiles

```bash
# Voir les logs du backend
docker compose logs backend | grep -i "bolt\|sync\|error"

# Redémarrer le backend après changement de .env
docker compose restart backend

# Tester la connexion
docker compose exec backend python scripts/test_supabase_connection.py

# Trouver le company_id Bolt
python scripts/find_bolt_company_id.py
```

## Problème persistant ?

1. Vérifie les logs : `docker compose logs backend`
2. Vérifie les permissions RLS dans Supabase
3. Vérifie que le `org_id` dans le JWT correspond à celui utilisé pour sauvegarder

