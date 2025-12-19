# DOSSIER BUSINESS - Services Métier

## 📋 Vue d'ensemble

Ce dossier contient tous les **services métier** du jeu. Chaque service encapsule une logique métier spécifique et peut être réutilisé par les routes API ou d'autres services.

## 📁 Structure des Services

### 🔬 **research_service.py**
**Rôle** : Gestion de l'arbre technologique

**Responsabilités** :
- Vérification des prérequis (recherches préalables, coûts)
- Déverrouillage de nouvelles recherches
- Application des effets au niveau JOUEUR (bonus ressources, bâtiments débloqués)
- Gestion des points de recherche

**Points clés** :
- Les bonus s'appliquent à **TOUTES** les villes du joueur
- Stockage dans `players.json` : `player.research_effects.resource_bonuses`
- Effets supportés : `unlock_building`, `unlock_resources`, `resource_bonus`

---

### 🏛️ **building_manager.py**
**Rôle** : Gestion des bâtiments

**Responsabilités** :
- Construction et amélioration de bâtiments
- Validation des prérequis (ressources, population, recherches)
- Calcul des coûts et temps de construction
- Application des effets des bâtiments

---

### 🏙️ **city_service.py**
**Rôle** : Gestion du cycle de vie des villes

**Responsabilités** :
- Création de nouvelles villes
- Réclamation de villes (claim)
- Validation de l'état des villes
- Liaison ville ↔ joueur

---

### 🚢 **transport_service.py**
**Rôle** : Gestion des transports de ressources

**Responsabilités** :
- Création de missions de transport
- Validation des capacités (bateaux, ports)
- Calcul des temps de trajet
- Gestion des transports en cours

---

### ⏱️ **transport_timer_service.py**
**Rôle** : Gestion des timers de transport

**Responsabilités** :
- Démarrage/arrêt des timers
- Mise à jour de l'état des transports
- Complétion automatique des transports
- Gestion des transports en arrière-plan

---

### 💰 **player_resources_service.py**
**Rôle** : Gestion des ressources au niveau joueur

**Responsabilités** :
- Agrégation des ressources de toutes les villes
- Calcul des totaux (or, points de recherche, diamants)
- Gestion des ressources globales du joueur

---

### 👤 **player_service.py**
**Rôle** : Gestion des joueurs

**Responsabilités** :
- Création et mise à jour des profils joueurs
- Gestion des statistiques (batailles, XP, victoires)
- Gestion du tutoriel
- Liaison joueur ↔ villes

---

### 🏝️ **island_assignment_service.py**
**Rôle** : Attribution des îles aux joueurs

**Responsabilités** :
- Assignation d'îles disponibles
- Vérification des contraintes (distance, disponibilité)
- Gestion des îles barbares

---

### 🛒 **market_service.py**
**Rôle** : Gestion du marché (échange de ressources)

**Responsabilités** :
- Validation des échanges
- Calcul des prix
- Application des transactions

---

### 🔔 **notification_service.py**
**Rôle** : Système de notifications

**Responsabilités** :
- Création de notifications (recherche, construction, transport, etc.)
- Gestion des types de notifications
- Liaison notifications ↔ joueur

---

### 🔄 **data_consolidation_service.py**
**Rôle** : Consolidation des données de jeu

**Responsabilités** :
- Agrégation des données pour l'affichage
- Calculs de totaux et statistiques
- Préparation des données pour l'API

---

## 🏗️ Architecture des Services

```
Routes API (city_routes, research_routes, etc.)
    ↓
Services Métier (research_service, city_service, etc.)
    ↓
DataManager (Accès aux fichiers JSON)
    ↓
Fichiers de données (savegame.json, players.json, etc.)
```

## 📝 Conventions

### Initialisation
Tous les services prennent un `DataManager` en paramètre :
```python
def __init__(self, data_manager: DataManager):
    self.data_manager = data_manager
```

### Retours de fonctions
Les services retournent des dictionnaires avec un champ `success` :
```python
return {
    "success": True,
    "message": "Opération réussie",
    "data": {...}
}
```

### Gestion des erreurs
Les services lèvent des exceptions personnalisées :
```python
from ..exceptions import CityNotFoundError, GameValidationError
raise CityNotFoundError(city_id)
```

## 🔍 Points d'attention

### Bonus de Recherche
⚠️ **IMPORTANT** : Les bonus de recherche sont au niveau **JOUEUR**, pas ville.
- Stockage : `players.json` → `player.research_effects.resource_bonuses`
- Application : Automatique sur **TOUTES** les villes du joueur
- Lecture : `game_logic.py` charge depuis le joueur, pas la ville

### Séparation des Responsabilités
- Les **services** contiennent la logique métier
- Les **routes** gèrent seulement HTTP (validation, réponses)
- Le **GameLogic** contient les calculs de gameplay
- Le **DataManager** gère l'accès aux données

### Transactions
⚠️ Pas de système transactionnel sur les fichiers JSON.
- Utiliser `force_save=True` pour les opérations critiques
- Valider les données avant de sauvegarder

## 📚 Documentation Complémentaire

- Architecture globale : `/docs/ARCHITECTURE_SIMPLIFIED_FINAL.md`
- Système de recherche : `/docs/RESEARCH_BONUS_PLAYER_LEVEL.md`
- Système de transport : `/docs/CLEANUP_TRANSPORT_FIX.md`

---

**Dernière mise à jour** : Décembre 2025  
**Refonte majeure** : Bonus de recherche au niveau joueur
