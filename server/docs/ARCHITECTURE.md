# Architecture du Projet - Guide Développeur

## 📁 Structure et Responsabilités

```
server/app/
├── api/                     # 🌐 ROUTES HTTP SEULEMENT
│   ├── auth_routes.py       # Login, création compte, joueurs
│   ├── city_routes.py       # Gestion des villes, bâtiments
│   ├── universe_routes.py   # Univers, îles, layouts
│   └── resource_routes.py   # Sites de ressources, production
│
├── business/                # 🧠 LOGIQUE MÉTIER
│   ├── player_service.py    # Gestion joueurs, auth
│   ├── city_service.py      # Gestion villes, bâtiments
│   └── resource_service.py  # Gestion ressources, production
│
├── core/                    # 🔧 UTILITAIRES
│   ├── exceptions.py        # Toutes les exceptions du jeu
│   ├── validators.py        # Toutes les validations
│   └── decorators.py        # Décorateurs pour les routes
│
├── data_manager.py          # 💾 ACCÈS AUX FICHIERS JSON
└── game_logic.py            # ⚙️ CALCULS ET RÈGLES DU JEU
```

## 🎯 Où ajouter du code ?

### Nouvelle fonctionnalité Joueur
- ✅ Route → `api/auth_routes.py`
- ✅ Logique → `business/player_service.py`
- ✅ Validation → `core/validators.py`

### Nouvelle fonctionnalité Ville
- ✅ Route → `api/city_routes.py`
- ✅ Logique → `business/city_service.py`
- ✅ Calculs → `game_logic.py`

### Nouvelle fonctionnalité Ressource
- ✅ Route → `api/resource_routes.py`
- ✅ Logique → `business/resource_service.py`
- ✅ Production → `game_logic.py`

## ⚠️ RÈGLES IMPORTANTES

1. **JAMAIS de logique métier dans les routes**
2. **TOUJOURS utiliser les services existants**
3. **VÉRIFIER les validators existants avant d'en créer**
4. **UNE exception = core/exceptions.py**

## 🔍 Checklist avant d'ajouter du code

- [ ] Est-ce que ça concerne les joueurs ? → `player_service.py`
- [ ] Est-ce que ça concerne les villes ? → `city_service.py`
- [ ] Est-ce que ça concerne les ressources ? → `resource_service.py`
- [ ] Ai-je besoin d'une validation ? → Vérifier `validators.py`
- [ ] Ai-je besoin d'une exception ? → Vérifier `exceptions.py`
