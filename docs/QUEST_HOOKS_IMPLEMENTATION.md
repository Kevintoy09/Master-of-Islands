# 🎯 HOOKS AUTOMATIQUES POUR LE SYSTÈME DE QUÊTES

## ✅ Implémenté

### 1. **Bouton Admin pour générer les quêtes**
- **URL** : `http://localhost:5000/admin/`
- **Fonction** : Génère automatiquement 5 quêtes aléatoires pour tous les joueurs
- **Section** : "Système de Quêtes"
- **Bouton** : "🔄 Générer des quêtes pour tous les joueurs"

### 2. **Hook pour les donations** ✅
- **Fichier** : `server/app/routes/resource_routes.py`
- **Endpoint** : `POST /api/resources/site/<island_id>/<site_type>/donate`
- **Quête trackée** : `eco_donate_sites`
- **Incrémentation** : Par le montant donné

---

## 🔄 À implémenter : Hooks pour la collecte de bois

### Contexte
La collecte de ressources (bois, pierre, marbre, verre, soufre) se fait via les **ticks automatiques** gérés par `TickService`. Les ressources sont produites périodiquement selon les bâtiments de production de chaque ville.

### Problème
Il n'y a pas d'endpoint direct pour "collecter du bois". Les ressources sont ajoutées automatiquement via les ticks. Pour tracker la collecte dans les quêtes, nous devons :

### Solution : Hook dans le TickService

**Fichier à modifier** : `server/app/services/tick_service.py`

**Méthode à modifier** : `execute_tick()` ou `process_city_production()`

**Code à ajouter** :

```python
def process_city_production(self, city_data, player_id):
    """Traite la production d'une ville"""
    # ... code existant ...
    
    # Production des ressources
    resources_produced = {
        'wood': 0,
        'stone': 0,
        'marble': 0,
        'glass': 0,
        'sulfur': 0
    }
    
    for building in city_data.get('buildings', []):
        # ... calcul de production ...
        if building['name'] == 'Scierie':
            wood_produced = calculate_wood_production(building)
            resources_produced['wood'] += wood_produced
            # Ajouter au stockage
            city_data['resources']['wood'] += wood_produced
    
    # 🎯 Hook pour les quêtes
    try:
        from app.services.quest_service import quest_service
        from app.data_manager import DataManager
        
        # Récupérer le username
        dm = DataManager()
        players = dm.load_players()
        player = next((p for p in players if p['id'] == player_id), None)
        
        if player:
            username = player.get('username')
            if username:
                # Tracker la collecte de chaque ressource
                if resources_produced['wood'] > 0:
                    quest_service.update_quest_progress(
                        username=username,
                        quest_id='eco_collect_wood',
                        increment=resources_produced['wood']
                    )
                
                if resources_produced['marble'] > 0:
                    quest_service.update_quest_progress(
                        username=username,
                        quest_id='eco_collect_marble',
                        increment=resources_produced['marble']
                    )
                
                # ... autres ressources ...
    except Exception as e:
        print(f"⚠️ Failed to update quest progress: {e}")
    
    return city_data
```

---

## 📋 Liste complète des hooks à implémenter

### 1. **Collecte de ressources** (via TickService)
- [x] `eco_donate_sites` - ✅ Implémenté dans `resource_routes.py`
- [ ] `eco_collect_wood` - À ajouter dans `TickService.process_city_production()`
- [ ] `eco_collect_stone` - À ajouter dans `TickService.process_city_production()`
- [ ] `eco_collect_marble` - À ajouter dans `TickService.process_city_production()`
- [ ] `eco_collect_glass` - À ajouter dans `TickService.process_city_production()`
- [ ] `eco_collect_sulfur` - À ajouter dans `TickService.process_city_production()`

### 2. **Construction de bâtiments**
- [ ] `eco_build_buildings` - À ajouter dans `city_routes.py` endpoint `construct_building`
- Fichier : `server/app/routes/city_routes.py`
- Endpoint : `POST /api/city/<city_id>/construct`

```python
# Dans city_routes.py
if result['success']:
    # 🎯 Hook pour les quêtes
    try:
        from app.services.quest_service import quest_service
        quest_service.update_quest_progress(
            username=username,
            quest_id='eco_build_buildings',
            increment=1
        )
    except Exception as e:
        print(f"⚠️ Quest update failed: {e}")
```

### 3. **Commerce au marché**
- [ ] `eco_trade_resources` - À ajouter dans `market_routes.py` endpoint `create_offer` ou `accept_offer`
- Fichier : `server/app/routes/market_routes.py`
- Endpoints : 
  - `POST /api/market/offers` (créer une offre)
  - `POST /api/market/offers/<offer_id>/accept` (accepter une offre)

### 4. **Transport de ressources**
- [ ] `eco_transport_resources` - À ajouter dans l'endpoint de transport
- Fichier : probablement `transport_routes.py` ou `city_routes.py`
- Endpoint : À identifier

### 5. **Production d'or**
- [ ] `eco_produce_gold` - À ajouter dans `TickService` (production d'or via taxes)

### 6. **Population**
- [ ] `eco_reach_population` - À ajouter dans `TickService` ou lors de la construction de bâtiments de logement

### 7. **Recrutement d'unités**
- [ ] `mil_recruit_units` - À ajouter dans `army_routes.py` ou `barracks_routes.py`
- Fichier : probablement dans les routes militaires
- Endpoint : À identifier (production d'unités)

---

## 🛠️ Méthode générique pour ajouter un hook

### Template de code :

```python
# Après une action réussie (construction, recrutement, commerce, etc.)
if result['success']:
    try:
        from app.services.quest_service import quest_service
        from app.data_manager import DataManager
        
        # Récupérer le username depuis player_id
        dm = DataManager()
        players = dm.load_players()
        player = next((p for p in players if p['id'] == player_id), None)
        
        if player:
            username = player.get('username')
            if username:
                quest_service.update_quest_progress(
                    username=username,
                    quest_id='QUEST_ID_ICI',
                    increment=QUANTITE_ICI
                )
                print(f"🎯 Quest updated: {username} - QUEST_ID_ICI +{QUANTITE_ICI}")
    except Exception as e:
        # Ne jamais bloquer l'action principale si la mise à jour des quêtes échoue
        print(f"⚠️ Failed to update quest progress: {e}")
```

### Paramètres à adapter :
- **`QUEST_ID_ICI`** : ID de la quête (`eco_collect_wood`, `mil_recruit_units`, etc.)
- **`QUANTITE_ICI`** : Quantité à incrémenter
  - 1 pour les actions unitaires (construction, commerce)
  - Quantité produite/collectée pour les ressources
  - Nombre d'unités pour le recrutement

---

## 🔍 Comment trouver les endpoints à modifier

### 1. Recherche par mots-clés
```bash
grep -r "construct" server/app/routes/
grep -r "recruit" server/app/routes/
grep -r "transport" server/app/routes/
```

### 2. Identifier les routes
- Chercher `@resource_bp.route` ou `@city_bp.route`
- Chercher les fonctions qui retournent `jsonify(result)`
- Vérifier que `result['success']` existe

### 3. Tester les hooks
- Faire l'action dans le jeu
- Vérifier les logs serveur pour `🎯 Quest updated`
- Ouvrir la Maison du Chef pour voir la progression

---

## 📊 Priorités d'implémentation

### Phase 1 (Urgent) :
1. ✅ eco_donate_sites (déjà fait)
2. ⏳ eco_collect_wood (via TickService)
3. ⏳ eco_build_buildings (via city_routes)

### Phase 2 (Important) :
4. eco_recruit_units (militaire)
5. eco_transport_resources (commerce)
6. eco_trade_resources (marché)

### Phase 3 (Optionnel) :
7. eco_collect_marble, eco_collect_stone, etc.
8. eco_produce_gold
9. eco_reach_population

---

## 🧪 Test des hooks

### 1. Générer les quêtes
- Aller sur `http://localhost:5000/admin/`
- Cliquer sur "🔄 Générer des quêtes pour tous les joueurs"

### 2. Faire une action trackée
- Exemple : Donner 100 bois à un site de production

### 3. Vérifier la progression
- Ouvrir le Journal des Quêtes (cliquer sur la Maison du Chef)
- Vérifier que la barre de progression a augmenté

### 4. Logs serveur
```
🎯 Quest updated: Kevin donated 100 wood
🎯 Quest updated: Kevin - eco_donate_sites +100
```

---

## 📝 Notes importantes

### ⚠️ Gestion des erreurs
- **TOUJOURS** wrapper les hooks dans un `try/except`
- **NE JAMAIS** bloquer l'action principale si le hook échoue
- Logger les erreurs avec `print()` pour debug

### 🔄 Performance
- Les hooks sont légers (juste un incrément dans un JSON)
- Pas d'impact notable sur les performances
- Exécution asynchrone possible si nécessaire

### 🎯 Flexibilité
- Facile d'ajouter/supprimer des quêtes
- Pas besoin de modifier les hooks si on change les récompenses
- Structure séparée config/progression

---

## 🚀 Prochaine action recommandée

**Implémenter le hook pour `eco_collect_wood` dans le TickService** pour tracker automatiquement la collecte de bois pendant les ticks de production.

**Fichier** : `server/app/services/tick_service.py`
**Méthode** : `execute_tick()` ou la méthode qui gère la production de ressources

Ce sera le plus impactant car la collecte de bois est l'action la plus fréquente dans le jeu ! 🪵
