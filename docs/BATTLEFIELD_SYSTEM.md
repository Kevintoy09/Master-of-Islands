# Système de Champs de Bataille

## Vue d'ensemble

Le système de champs de bataille permet de gérer les combats tactiques entre joueurs avec des positions d'unités persistantes et des combats en temps réel.

## Architecture

### Fichiers de données

- **`battlefields.json`** : Métadonnées des champs de bataille (participants, forces, statut)
- **`battles.json`** : États tactiques (positions des unités, logs de combat)

### Structure des données

#### battlefields.json
```json
{
  "active_battlefields": {
    "bf_[uuid]": {
      "id": "bf_[uuid]",
      "location": "city_id_X",
      "status": "reinforcement|combat",
      "created_at": 1757107984,
      "participants": {
        "attackers": ["player_2"],
        "defenders": ["player_3"]
      },
      "forces": {
        "attackers": {
          "player_2": {
            "units": {
              "archer": {"total": 2, "sources": [...]}
            }
          }
        },
        "defenders": {
          "player_3": {
            "units": {
              "infantry_light": {"total": 4, "sources": [...]}
            }
          }
        }
      }
    }
  }
}
```

#### battles.json
```json
{
  "bf_[uuid]": {
    "tactical_state": {
      "unit_positions": {
        "auto_archer_[timestamp]_[index]": {
          "unit_type": "archer",
          "player_id": "player_2",
          "team": "attacker",
          "position": {"q": 2, "r": 1},
          "health": 100,
          "moved": false
        }
      },
      "turn_info": {
        "current_player": "player_2",
        "turn_number": 1
      }
    }
  }
}
```

## APIs

### Backend (Flask)

- `GET /api/military/battlefields/active` : Liste des champs de bataille actifs
- `GET /api/military/city/{city_id}/battlefield_id` : ID du champ de bataille pour une ville
- `POST /api/battle/{battle_id}/move_unit` : Déplacer une unité
- `GET /api/battle/{battle_id}/state` : État tactique du champ de bataille

### Frontend (React)

- **IslandPage** : Affiche les icônes de guerre sur les villes avec champ de bataille
- **AttackPopup** : Résolution dynamique de l'ID du champ de bataille
- **NapoleonicBattlefield** : Interface tactique avec grille hexagonale
- **UnitController** : Gestion des mouvements et persistance des positions

## Fonctionnalités

### ✅ Implémentées
- Identification unique des champs de bataille (UUID)
- Séparation métadonnées/état tactique
- Persistance des positions d'unités
- Résolution dynamique des champs de bataille par ville
- Icônes visuelles sur la carte des îles
- Restauration d'état lors de la réouverture

### 🔄 En cours
- Système de combat au tour par tour
- Calcul des dégâts et élimination d'unités

### 📋 À implémenter
- Conditions de victoire
- Récompenses de bataille
- Animations de combat

## Utilisation

1. **Créer un champ de bataille** : Attaquer une ville crée automatiquement un champ de bataille
2. **Identifier le champ de bataille** : Chaque ville peut avoir au maximum un champ de bataille actif
3. **Déployer les unités** : Les unités sont automatiquement positionnées
4. **Sauvegarder les positions** : Les mouvements sont persistants entre les sessions

## Dépannage

- **Champ de bataille incorrect** : Vérifier que l'API `/api/military/city/{city_id}/battlefield_id` retourne le bon ID
- **Positions non sauvegardées** : S'assurer que `battles.json` est accessible en écriture
- **Icône manquante** : Vérifier que `barbarian_camp.png` est dans `public/assets/logos/`
