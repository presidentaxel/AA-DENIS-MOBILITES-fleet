# Structure du Frontend - AA Denis Fleet

## Architecture

Le frontend est organisé selon une structure modulaire inspirée de Rollee, avec un design moderne et une navigation claire.

## Arborescence

```
frontend/src/
├── api/
│   └── fleetApi.ts           # Toutes les appels API
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx       # Sidebar de navigation (style Rollee)
│   │   └── MainLayout.tsx    # Layout principal avec sidebar
│   ├── StatCard.tsx          # Cartes de statistiques
│   ├── DriverStats.tsx       # Statistiques détaillées d'un chauffeur (12 KPIs)
│   ├── DriverTableModern.tsx # Tableau moderne des chauffeurs
│   └── OrdersList.tsx        # Liste des commandes avec filtres
├── pages/
│   ├── LoginPage.tsx         # Page de connexion
│   ├── OverviewPage.tsx      # Dashboard principal
│   ├── DriversPage.tsx       # Gestion des chauffeurs
│   ├── VehiclesPage.tsx      # Gestion des véhicules
│   ├── OrdersPage.tsx        # Liste et stats des commandes
│   ├── AnalyticsPage.tsx     # Analytics et insights
│   └── SettingsPage.tsx      # Paramètres
├── styles/
│   └── global.css            # Styles globaux (design system)
├── App.tsx                   # Router principal
└── main.tsx                  # Point d'entrée
```

## Pages et Fonctionnalités

### 1. Overview (/)
- Vue d'ensemble avec statistiques principales
- Cartes de stats : Chauffeurs totaux, Véhicules, Commandes, Revenus
- Quick actions vers les autres sections
- **Données disponibles :** ✓

### 2. Chauffeurs (/drivers)
- Liste des chauffeurs avec sélection
- Statistiques détaillées par chauffeur (12 KPIs)
- Liste des commandes par chauffeur
- Filtres par période
- **Données disponibles :** ✓ (orders, earnings, stats)

### 3. Véhicules (/vehicles)
- Liste des véhicules
- Statistiques par véhicule (commandes, distance, revenus)
- **Données disponibles :** ✓ (partiel - stats calculées depuis orders)

### 4. Commandes (/orders)
- Tableau complet de toutes les commandes
- Filtres par période et chauffeur
- Statistiques agrégées (total, complétées, annulées, revenus)
- **Données disponibles :** ✓

### 5. Analytics (/analytics)
- Métriques clés (utilisateurs connectés, actifs, revenus)
- Top 10 des chauffeurs par revenus
- **Données disponibles :** ✓
- **Graphiques :** ⚠️ Non implémentés (nécessite Chart.js ou Recharts)

### 6. Paramètres (/settings)
- Gestion des accès dashboard
- Configuration de la synchronisation
- **Données disponibles :** ⚠️ Partiel (sync config visible, gestion accès non implémentée)

## Design System

### Couleurs
- Primary: `#3b82f6` (Bleu)
- Success: `#10b981` (Vert)
- Warning: `#f59e0b` (Orange)
- Error: `#ef4444` (Rouge)
- Info: `#06b6d4` (Cyan)

### Sidebar
- Fond sombre : `#1e293b`
- Largeur fixe : `260px`
- Navigation avec icônes
- Style inspiré de Rollee

### Composants
- Cards avec ombres et bordures
- Tableaux avec hover effects
- Boutons avec transitions
- Badges colorés pour les statuts

## Fonctionnalités Non Disponibles

1. **Graphiques d'évolution temporelle** : Nécessite une bibliothèque de graphiques (Chart.js, Recharts)
2. **Distribution des revenus** : Peut être calculée mais nécessite graphiques
3. **Gestion des utilisateurs/accès** : Nécessite une table users dans Supabase avec permissions
4. **Comparaison semaine/mois** : Données disponibles, mais graphiques manquants
5. **Export de données** : Non implémenté

## Prochaines Étapes

Pour compléter l'interface comme Rollee :

1. **Installer une bibliothèque de graphiques** :
   ```bash
   cd frontend
   npm install recharts
   ```

2. **Ajouter les graphiques** :
   - Évolution des revenus dans le temps
   - Distribution des revenus par tranche
   - Comparaison semaine/mois

3. **Gestion des utilisateurs** :
   - Table `users` dans Supabase
   - Permissions et RLS
   - Invitation d'utilisateurs

4. **Export de données** :
   - Export CSV des commandes
   - Export PDF des rapports

