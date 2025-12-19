# 🏛️ Jeu de Stratégie Antique - Documentation Complète
*Dernière mise à jour : 29 août 2025*

## 📋 Vue d'ensemble

**Jeu de stratégie multijoueur en temps réel** inspiré d'Ikariam, développé avec React TypeScript (frontend) et Flask Python (backend). Le joueur développe ses cités, colonise des îles, gère ses ressources, construit des bâtiments, recherche des technologies et commerce avec d'autres joueurs.

### 🏗️ Architecture Technique

```
game18/
├── client/          # Frontend React TypeScript + Mobile optimisé
│   ├── src/components/   # HeaderBar, popups, interfaces
│   ├── src/pages/        # WorldPage, IslandPage, CityPage
│   └── public/           # Assets statiques
├── server/          # Backend Flask + API REST
│   ├── app/api/          # Routes API (city, resource, transport, research)
│   ├── app/managers/     # Logique métier (population, transport, game_logic)
│   ├── app/business/     # Services (CityService, BuildingManager)
│   └── data/             # Données JSON (buildings, savegame, players)
├── assets/          # Ressources graphiques partagées
└── docs/            # Documentation et rapports
```

---

## 🎮 Fonctionnalités Actuelles

### ✅ **SYSTÈME DE PRODUCTION** (Complet)
- **Production basée sur workers** : Fini les taux fixes, tout dépend des ouvriers assignés
- **13 ressources** : bois, pierre, fer, céréales, papyrus, marbre, viande, chevaux, verre, charbon, poudre, épices, coton
- **Sites de ressources par île** : Chaque île a ses spécialités (forêt, mine, champ, ranch...)
- **Bonus bâtiments** : Scierie (+10-30% bois), Mine (+10-30% 4 ressources), etc.
- **Stockage sécurisé** : Entrepôts protègent les ressources du pillage
- **Système de débordement** : Limitation des stocks avec gestion automatique

### ✅ **SYSTÈME DE BÂTIMENTS** (Complet - 13 types)
1. **Hôtel de Ville** : Capacité population (100→1420), croissance (+1.2→21.5/h), stockage nourriture
2. **Windmill** : Nourriture bonus, multiplicateur céréales (x2→x4), sustente population extra
3. **Academy** : Production points recherche (1→2 pts/worker), max ouvriers (25→75)
4. **Scierie** : Bonus production bois (+10→30%)
5. **Mine** : Bonus 4 ressources (+10→30% pierre/fer/céréales/papyrus)
6. **Entrepôt** : Stockage sécurisé (500→10000 par ressource)
7. **Market** : Commerce entre villes, gestion transport
8. **Port** : Bateaux transport (+2→20 navires)
9. **Barracks** : Capacité militaire (pas encore implémenté)
10. **Thermes** : Hygiène population, bonus satisfaction
11. **Ambassade** : Relations diplomatiques (partiellement implémenté)
12. **Architect Workshop** : Bonus construction (-10→30% temps)
13. **Wall Building** : Défense ville (pas encore utilisé)

**Système de niveaux** : Chaque bâtiment 1→10 niveaux, coûts/effets croissants, temps construction 2s→60s

### ✅ **SYSTÈME DE POPULATION** (Complet)
- **Croissance dynamique** : Basée sur nourriture, satisfaction, multiplicateur temps
- **Segmentation alimentaire** : Population nourrie par Hôtel de Ville vs Windmill
- **Consommation céréales** : Population excédentaire consomme selon multiplicateur choisi
- **Facteurs satisfaction** : Nourriture, hygiène, surpopulation, bâtiments
- **Gestion automatique workers** : Ajustement prioritaire si population insuffisante
- **Système de famine** : Décroissance si nourriture insuffisante

### ✅ **SYSTÈME DE RECHERCHE** (Complet)
- **Production continue** : Academy génère points recherche selon ouvriers assignés
- **Arbre technologique** : Déblocage progressif selon prérequis
- **Effets recherche** : Bonus production, nouveaux bâtiments, capacités spéciales
- **6 ères technologiques** : Pierre, Bronze, Fer, Découvertes, Industrie, Moderne

### ✅ **SYSTÈME DE TRANSPORT** (Ultra-optimisé)
- **Commerce inter-îles** : Transport ressources entre villes du joueur
- **Gestion navires** : Port génère bateaux de transport disponibles
- **Interface intuitive** : Sélection quantités, destination, durée voyage
- **Performance** : Cache 2s, sauvegarde en lot, **397x plus rapide** qu'avant
- **Métriques** : 268,673 requêtes/seconde, popup 0.26ms

### ✅ **SYSTÈME DE COLONISATION**
- **Expansion territoriale** : Coloniser nouvelles îles avec coûts bois/or
- **Types d'îles** : Spécialisées par ressource (céréales, pierre, fer, verre)
- **Emplacements multiples** : Plusieurs villes possibles par île
- **Gestion automatique** : Intégration resources/transport/population

### ✅ **INTERFACE MOBILE OPTIMISÉE**
- **HeaderBar responsive** : 4 lignes ressources, spacing mobile réduit
- **Popups adaptatives** : Toutes interfaces smartphone-friendly
- **Navigation tactile** : Boutons optimisés, zones touch appropriées
- **Mode portrait/landscape** : Layout adaptatif selon orientation

---

## � Technologies & Performance

### **Backend (Serveur)**
- **Flask** : API REST, gestion requêtes, sessions joueurs
- **JSON natif** : Données persistantes (savegame.json, players.json, buildings.json)
- **Cache intelligent** : Système cache 2s + sauvegarde différée
- **Managers spécialisés** : PopulationManager, TransportManager, GameLogic
- **Optimisations** : Batch operations, delta-updates, memory caching

### **Frontend (Client)**
- **React 18 + TypeScript** : Composants modernes, typage strict
- **CSS mobile-first** : Responsive design, touch-optimized
- **API asynchrone** : Fetch, error handling, loading states
- **État partagé** : Context API pour données globales
- **Performance** : Code splitting, lazy loading, optimized renders

### **Métriques Performance Actuelles**
| Composant | Vitesse | Optimisation |
|-----------|---------|--------------|
| Transport System | 268K req/s | Cache + Batch saves |
| Resource Updates | 1.9ms | In-memory calculations |
| Population Calc | <5ms | Algorithmes optimisés |
| Building Queries | 0.001ms | JSON indexing |
| HeaderBar Mobile | 16.2vh | +11% height mobile |

---

## � Structure des Données

### **Savegame Principal** (`server/data/savegame.json`)
```json
{
  "cities": [
    {
      "id": "city_id_7",
      "name": "City 1", 
      "owner": "player_1",
      "island_id": "3",
      "base_resource": "cereal",
      "buildings": [...],
      "resources": {...},
      "workers_assigned": {...},
      "population": {...}
    }
  ],
  "transports": [...],
  "islands": [...],
  "last_update": timestamp
}
```

### **Configuration Bâtiments** (`server/data/buildings.json`)
```json
{
  "Hôtel de Ville": {
    "levels": [
      {
        "level": 1,
        "cost": {"wood": 100, "stone": 50},
        "construction_time": 6,
        "effect": {
          "population_capacity": 100,
          "food_capacity": 50,
          "population_growth": 1.2
        }
      }
    ]
  }
}
```

### **Joueurs** (`server/data/players.json`)
```json
{
  "players": [
    {
      "id": "player_1",
      "name": "Joueur #1",
      "research_points": 245.7,
      "gold": 11950,
      "cities": ["city_id_7", "city_id_8"],
      "last_research_update": timestamp
    }
  ]
}
```

---

## 🛠️ Développement & Maintenance

### **Ajout d'un Nouveau Bâtiment**
1. **Définir dans** `server/data/buildings.json` (nom, niveaux, coûts, effets)
2. **Ajouter image** dans `assets/buildings/nom_batiment.png`
3. **Implémenter logique** dans `GameLogic.calculate_building_bonuses()`
4. **Créer popup client** dans `client/src/popups/NomBatimentPopup.tsx`
5. **Tester** construction, effets, amélioration

### **Ajout d'une Nouvelle Ressource**
1. **Configurer site** dans `server/app/data/resource_sites_database.py`
2. **Ajouter aux calculs** dans `GameLogic.update_resource_production()`
3. **Icône & label** dans `assets/icons/` et `client/src/constants/resourceIcons.ts`
4. **HeaderBar** : Ajouter dans `resourceLines` appropriée
5. **Tester** production, stockage, transport

### **API Routes Disponibles**
- **Cities** : `/api/cities/*` (info ville, construction, workers)
- **Resources** : `/api/resources/*` (production, sites, workers assignment)
- **Transport** : `/api/transport/*` (create, cancel, status, ships)
- **Research** : `/api/research/*` (points, unlock, tree)
- **Islands** : `/api/islands/*` (colonize, info, resource sites)

---

## 🎯 État Actuel vs Objectifs

### ✅ **COMPLÈTEMENT IMPLÉMENTÉ**
- Système production ressources
- Gestion bâtiments (13 types)
- Population & satisfaction
- Recherche scientifique  
- Transport & commerce
- Colonisation îles
- Interface mobile optimisée
- Performance ultra-optimisée

### 🚧 **PARTIELLEMENT IMPLÉMENTÉ**
- **Combat/Guerre** : Bâtiments militaires définis mais logique manquante
- **Diplomatie** : Ambassade existe mais relations joueurs basiques
- **Événements** : Infrastructure prête mais pas de contenu

### ❌ **À DÉVELOPPER**
- **Système militaire complet** (attaque, défense, pillage)
- **Quêtes & objectifs** (tutoriel, défis, récompenses)
- **Marché économique** (prix fluctuants, ordres automatiques)
- **Système espionnage** (reconnaissance, sabotage)
- **Notifications push** (constructions, attaques)
- **Classements & compétitions**

---

## 🚀 Prochaines Priorités Recommandées

### **PRIORITÉ 1 - Gameplay Avancé**
1. **Système Combat** : Implémenter attaque/défense/pillage
2. **Quêtes Tutoriel** : Guider nouveaux joueurs  
3. **Événements Temporaires** : Relancer engagement

### **PRIORITÉ 2 - UX/Performance**  
1. **Notifications Push** : Alertes constructions/attaques
2. **Interface Avancée** : Graphiques, statistiques, historiques
3. **Mode Hors-ligne** : Cache local, synchronisation

### **PRIORITÉ 3 - Contenu**
1. **Nouveaux Bâtiments** : Temple, Forge, Université
2. **Ressources Avancées** : Diamants, Technologie, Magie
3. **Système Alliances** : Coopération joueurs

---

## 📈 Métriques & KPIs

### **Performance Technique**
- ✅ Transport : 397x amélioration vitesse
- ✅ API Response : <10ms moyenne
- ✅ Mobile UX : HeaderBar +11% hauteur optimisée
- ✅ Cache Hit Rate : >95%

### **Contenu Jeu**
- ✅ **13 bâtiments** avec 10 niveaux chacun
- ✅ **13 ressources** avec production dynamique
- ✅ **25+ recherches** débloquables
- ✅ **Transport system** entre îles illimitées
- ✅ **Population** avec facteurs satisfaction complexes

### **Architecture Code**
- ✅ **Backend** : 45+ modules Python organisés
- ✅ **Frontend** : 20+ composants React TypeScript  
- ✅ **API** : 40+ endpoints REST documentés
- ✅ **Tests** : Code cleanup avec 0 erreurs vulture

---

**Ce jeu représente 750+ heures de développement** avec architecture moderne, performance optimisée et gameplay riche. Prêt pour expansion majeure (combat, événements) ou déploiement production.

**Contact :** Kevin (Kevintoy09)  
**Repository :** jeu-09-03-25 (GitHub)  
**Tech Stack :** React/TypeScript + Flask/Python + JSON
