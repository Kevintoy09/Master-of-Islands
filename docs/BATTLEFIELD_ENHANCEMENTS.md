# Améliorations du Système de Battlefield - Style Ikariam

## 📋 Vue d'ensemble

Ce document décrit les améliorations apportées au fichier `battlefields.json` pour suivre le modèle d'Ikariam avec des récapitulatifs détaillés, le moral des troupes, et un historique des rounds.

## 🎯 Fonctionnement Vérifié

### Cycle de Bataille Complet
✅ **1. Lancement d'attaque**
- Joueur lance attaque → `battlefields.json` créé
- Unités attaquant déduites de `savegame.json` → `battlefields.json`

✅ **2. Phase "en route"** 
- Statut "reinforcement" pendant 3 secondes (`reinforcement_end`)
- Armées affichées en transit

✅ **3. Arrivée sur place**
- Unités défenseur déduites de la ville → `battlefields.json`
- Garnison automatiquement transférée

✅ **4. Combat tactique**
- Combat géré par `battles.json` avec structure teams
- Rounds avec actions (mouvement/attaque/déploiement)

✅ **5. Fin de bataille**
- Troupes restantes renvoyées vers villes d'origine
- Données supprimées de `battles.json` et `battlefields.json`
- Rapport sauvegardé dans `battle_reports.json`

## 🆕 Nouvelles Fonctionnalités

### 1. Moral des Troupes
```json
"moral": {
  "attackers": {
    "player_2": 100
  },
  "defenders": {
    "player_4": 100
  }
}
```

### 2. Récapitulatif Global des Forces Engagées
```json
"summary": {
  "total_engaged_forces": {
    "attackers": {
      "player_2": {
        "infantry": 25,
        "ranged": 0,
        "cavalry": 0,
        "siege": 0,
        "total": 25
      }
    },
    "defenders": {
      "player_4": {
        "infantry": 0,
        "ranged": 5,
        "cavalry": 0,
        "siege": 0,
        "total": 5
      }
    }
  }
}
```

### 3. Récapitulatif Global des Pertes
```json
"total_losses": {
  "attackers": {
    "player_2": {
      "infantry": 0,
      "ranged": 0,
      "cavalry": 0,
      "siege": 0,
      "total": 0
    }
  },
  "defenders": {
    "player_4": {
      "infantry": 0,
      "ranged": 0,
      "cavalry": 0,
      "siege": 0,
      "total": 0
    }
  }
}
```

### 4. Résumé des Rounds
```json
"rounds_summary": [
  {
    "round": 1,
    "timestamp": 1757529626,
    "losses": {
      "attackers": {
        "infantry": 0,
        "ranged": 0,
        "cavalry": 0,
        "siege": 0
      },
      "defenders": {
        "infantry": 0,
        "ranged": 0,
        "cavalry": 0,
        "siege": 0
      }
    },
    "actions_count": {
      "movements": 0,
      "attacks": 0,
      "deployments": 4
    }
  }
]
```

## 🔧 Implémentation Technique

### Nouvelle API - Mise à jour des récapitulatifs
```http
POST /api/battle/{battle_id}/update_summary
```

### BattleManager - Nouvelles méthodes
- `update_battlefield_summary()` - Mise à jour complète des récapitulatifs
- `_calculate_moral_summary()` - Calcul du moral par joueur
- `_calculate_engaged_forces_by_category()` - Forces totales par catégorie
- `_calculate_total_losses_by_category()` - Pertes totales par catégorie
- `_generate_rounds_summary()` - Résumé détaillé des rounds
- `_get_unit_category()` - Mapping des types d'unités vers les catégories

### Catégories d'Unités
Mapping basé sur `unit_stats.json` :
- **infantry** : infantry_light, pikeman, etc.
- **ranged** : archer, slinger, mounted_archer
- **cavalry** : cavalry_light, cavalry_heavy
- **siege** : catapult, ballista, ram
- **hero** : comptés comme infanterie

### Mise à jour automatique
Les récapitulatifs sont automatiquement mis à jour lors de :
- ✅ Déploiement d'unités
- ✅ Mouvements d'unités  
- ✅ Actions de combat
- ✅ Fin de bataille

## 📊 Données Trackées

### Par Round
- Nombre de mouvements
- Nombre d'attaques  
- Nombre de déploiements
- Pertes par catégorie d'unité
- Timestamp des actions

### Global
- Forces initiales engagées
- Pertes cumulées
- Moral actuel des joueurs
- Statistiques de combat

## 🚀 Utilisation

### Tester la mise à jour manuelle
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/battle/bf_2d159cc5/update_summary" -Method POST -ContentType "application/json"
```

### Consulter les récapitulatifs
Les données sont disponibles dans `battlefields.json` sous :
- `active_battlefields[battle_id].moral`
- `active_battlefields[battle_id].summary`  
- `active_battlefields[battle_id].rounds_summary`

## 📈 Améliorations Futures

1. **Calcul du moral dynamique** basé sur les pertes réelles
2. **Bonus de terrain** dans le calcul des dégâts
3. **Renforts automatiques** selon les rounds
4. **Fatigue des troupes** après plusieurs rounds
5. **Héros et généraux** avec bonus spéciaux

## ✅ Status d'implémentation

- [x] Structure de base `battlefields.json` améliorée
- [x] API de mise à jour des récapitulatifs
- [x] Calcul automatique des forces et pertes par catégorie
- [x] Résumé des rounds avec compteurs d'actions
- [x] Mise à jour automatique lors des actions
- [x] Moral de base (100) pour tous les joueurs
- [ ] Calcul dynamique du moral basé sur les pertes
- [ ] Intégration complète avec le client React

Le système est maintenant prêt et fonctionnel selon les spécifications Ikariam !
