# Cahier des Charges - Système de Quêtes

## 📋 Vue d'ensemble

Système de quêtes quotidiennes et hebdomadaires avec récompenses progressives (3 étoiles) lié au niveau du joueur (1-50).

---

## 🎯 Objectifs du Système

### Quêtes Quotidiennes
- **5 quêtes par jour** sélectionnées aléatoirement parmi quêtes existantes
- **Distribution** : selon la variété des quêtes présentes dans la base de données
- **Progression à 3 paliers** : 1★ / 2★ / 3★ avec récompenses cumulatives automatiques
- **Renouvellement** : Chaque jour à minuit (00:00:00 heure serveur)

### Quêtes Hebdomadaires
- ** quêtes fixes** (non aléatoires) :  déterminées à l'avance Empire 3 villes, Empire 4 villes, Héros niveau 5, Merveille
- **Renouvellement** : Chaque dimanche à 23:59:59

### Système de Niveau de Joueur
- **Calcul simplifié** : `niveau = (construction_points * 0.5) + (quest_points * 0.5)`
- **Stockage** : Recalculé à chaque chargement (pas de cache)
- **Utilisation** : Détermine les paliers de difficulté des quêtes (1-5 → facile, 6-15 → moyen, 16+ → difficile)

### Récompenses
- **Formule progressive** : 1★ = base, 2★ = base + 20%, 3★ = base + 20% + 30%
- **Types** : Or, Points de recherche, Diamants, Ressources (bois, pierre), Population
- **Quest Points** : 1 point par étoile obtenue (classement permanent)
- **Expiration** : 3 jours pour récupérer les récompenses non réclamées

---

## 📂 Architecture Technique

### Backend (Python/Flask)

#### 1. Service Principal : `QuestService`
**Fichier** : `server/app/services/quest_service.py`

**Responsabilités** :
- Calculer le niveau du joueur
- Générer les 5 quêtes quotidiennes (aléatoires avec distribution)
- Charger les 3 quêtes hebdomadaires (fixes)
- Tracker la progression des quêtes
- Gérer l'obtention automatique des étoiles
- Distribuer les récompenses
- Gérer l'expiration des récompenses

**Méthodes clés** :
```python
def calculate_player_level(player_username) -> int
    # Formule simplifiée: (construction_points * 0.5) + (quest_points * 0.5)
    # Pas de cache, calculé à chaque appel

def generate_daily_quests(player_username, player_level) -> list
def get_weekly_quests(player_username) -> list
def load_player_quests(player_username) -> dict
    # Charge depuis player_quests.json

def save_player_quests(player_username, quest_data) -> None
    # Sauvegarde dans player_quests.json

def update_quest_progress(player_username, quest_id, progress_value)
def check_and_award_stars(player_username, quest_id)
def claim_rewards(player_username, quest_id, star_level)
def reset_daily_quests(player_username)
def reset_weekly_quests(player_username)
def cleanup_expired_rewards() -> None
    # Parcourt tous les joueurs dans player_quests.json
```

#### 2. Routes API : `quest_routes.py`
**Fichier** : `server/app/routes/quest_routes.py`

**Endpoints** :
```
GET  /api/quests/daily          # Récupérer les quêtes du jour
GET  /api/quests/weekly         # Récupérer les quêtes hebdomadaires
GET  /api/quests/progress       # État de progression de toutes les quêtes
POST /api/quests/claim-reward   # Réclamer une récompense d'étoile
GET  /api/quests/player-level   # Niveau actuel du joueur
GET  /api/quests/unclaimed      # Liste des récompenses non réclamées
```

#### 3. Modèle de Données : `player_quests.json` (FICHIER SÉPARÉ)
**Fichier** : `server/data/player_quests.json`

**Avantages** :
- ✅ Évite de surcharger `players.json`
- ✅ Isolation des données de quêtes
- ✅ Facilite la maintenance et le debug
- ✅ Permet des backups indépendants

**Structure complète** :
```json
{
  "player1": {
    "quest_points_total": 45,
    "daily_quests": {
      "generated_date": "2025-12-05",
      "player_level_snapshot": 12,
      "quests": [
        {
          "id": "eco_collect_wood",
          "progress": 75,
          "stars_earned": [1, 2],
          "rewards_claimed": [1, 2],
          "started_at": "2025-12-05T08:00:00"
        },
        {
          "id": "eco_build_buildings",
          "progress": 1,
          "stars_earned": [1],
          "rewards_claimed": [],
          "started_at": "2025-12-05T08:00:00"
        }
      ]
    },
    "weekly_quests": {
      "week_start": "2025-12-01",
      "quests": [
        {
          "id": "week_1_three_cities",
          "progress": 2,
          "completed": false,
          "reward_claimed": false,
          "started_at": "2025-12-01T00:00:00"
        }
      ]
    },
    "unclaimed_rewards": [
      {
        "quest_id": "eco_collect_wood",
        "star_level": 3,
        "rewards": {"gold": 30, "research_points": 5, "quest_points": 1},
        "awarded_at": "2025-12-05T14:30:00",
        "expires_at": "2025-12-08T00:00:00"
      }
    ]
  },
  "player2": {
    "quest_points_total": 12,
    "daily_quests": { ... },
    "weekly_quests": { ... },
    "unclaimed_rewards": []
  }
}
```

**Note** : `players.json` garde uniquement `quest_points_total` pour le calcul du niveau

#### 4. Système de Tracking Automatique
**Note importante** : Chaque type de quête nécessite son propre système de tracking. L'implémentation sera progressive selon les priorités.

**Priorité 1 (Essentielles - Phase 1)** :
- ✅ Construction de bâtiments (déjà existant)
- ✅ Collecte de ressources (système de tick existant)
- ✅ Recrutement d'unités (déjà existant)

**Priorité 2 (Importantes - Phase 2)** :
- 🔶 Combat et victoires (système bataille existant)
- 🔶 Recherche (système recherche existant)
- 🔶 Commerce (marché existant)

**Priorité 3 (Avancées - Phase 3)** :
- 🔷 Transport de ressources (à vérifier)
- 🔷 Population (calcul existant)
- 🔷 Dons aux sites (NOUVEAU - à créer)

**Intégration dans les systèmes existants** :

**Construction** (`city_routes.py`) :
```python
# Après construction/amélioration réussie
QuestService.update_quest_progress(username, 'eco_build_buildings', increment=1)
```

**Collecte de ressources** (`city_routes.py`) :
```python
# Lors du tick de ressources
QuestService.update_quest_progress(username, 'eco_collect_wood', amount_collected)
```

**Commerce** (`trade_routes.py`) :
```python
# Après transaction au marché
QuestService.update_quest_progress(username, 'eco_trade_resources', increment=1)
```

**Transport** (`transport_routes.py`) :
```python
# Après envoi réussi
total_quantity = sum(resources.values())
QuestService.update_quest_progress(username, 'eco_transport_resources', total_quantity)
```

**Dons** (nouveau système) :
```python
# Nouveau endpoint pour les dons aux sites
QuestService.update_quest_progress(username, 'eco_donate_sites', gold_donated)
```

**Combat** (`battle_routes.py`) :
```python
# Après victoire
QuestService.update_quest_progress(username, 'mil_win_battles', increment=1)
QuestService.update_quest_progress(username, 'mil_kill_units', units_killed)
if is_barbarian:
    QuestService.update_quest_progress(username, 'mil_attack_barbarians', increment=1)
```

**Recrutement** (`army_routes.py`) :
```python
# Après recrutement d'unités
QuestService.update_quest_progress(username, 'mil_recruit_units', units_recruited)
```

**Recherche** (`research_routes.py`) :
```python
# Après déblocage de recherche
QuestService.update_quest_progress(username, 'sci_unlock_research', increment=1)
# Sur accumulation de points
QuestService.update_quest_progress(username, 'sci_accumulate_research_points', points)
```

#### 5. Tâches Planifiées (Cron)
**Fichier** : `server/app/tasks/quest_scheduler.py`

```python
# Reset quotidien à 00:00:00
@scheduler.task('cron', hour=0, minute=0)
def reset_daily_quests():
    for player in all_players:
        QuestService.reset_daily_quests(player)

# Reset hebdomadaire dimanche 23:59:59
@scheduler.task('cron', day_of_week='sun', hour=23, minute=59, second=59)
def reset_weekly_quests():
    for player in all_players:
        QuestService.reset_weekly_quests(player)

# Nettoyage des récompenses expirées (quotidien)
@scheduler.task('cron', hour=1, minute=0)
def cleanup_expired_rewards():
    QuestService.cleanup_expired_rewards()
```

---

### Frontend (React/TypeScript)

#### 1. Page Principale : `QuestsPage.tsx`
**Fichier** : `client/src/pages/QuestsPage.tsx`

**Composants** :
- **Onglets** : Quotidiennes (5) / Hebdomadaires (3)
- **Niveau du joueur** : Badge avec niveau calculé
- **Liste de quêtes** : Cartes avec progression
- **Panneau récompenses** : Non réclamées avec expiration

**Structure** :
```tsx
interface Quest {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: 'economic' | 'military' | 'research';
  stars: {
    targets: number[];
    rewards: Reward[][];
    earned: number[];
    claimed: number[];
  };
  progress: number;
}

const QuestsPage = () => {
  const [activeTab, setActiveTab] = useState<'daily' | 'weekly'>('daily');
  const [dailyQuests, setDailyQuests] = useState<Quest[]>([]);
  const [weeklyQuests, setWeeklyQuests] = useState<Quest[]>([]);
  const [playerLevel, setPlayerLevel] = useState<number>(1);
  const [unclaimedRewards, setUnclaimedRewards] = useState<UnclaimedReward[]>([]);
  
  // Logique de chargement et mise à jour
}
```

#### 2. Composant Carte de Quête : `QuestCard.tsx`
**Fichier** : `client/src/components/quests/QuestCard.tsx`

**Éléments** :
- **En-tête** : Icône + Titre + Catégorie (badge coloré)
- **Description** : Texte explicatif
- **Barre de progression** : 3 sections pour les 3 étoiles
- **Indicateurs d'étoiles** :
  - 🌟 Étoile gagnée + récompense réclamée
  - ⭐ Étoile gagnée + récompense non réclamée (bouton "Réclamer")
  - ☆ Étoile non gagnée (affichage de l'objectif)

**Exemple visuel** :
```
┌─────────────────────────────────────────────┐
│ 🪵 Bûcheron                    [Économique] │
│ Récoltez du bois dans vos forêts            │
├─────────────────────────────────────────────┤
│ Progression: 75 / 100                       │
│ ▓▓▓▓▓▓▓▓▓▓▓▓░░░                            │
│                                              │
│ 🌟 50 bois     ⭐ 75 bois      ☆ 100 bois  │
│ ✓ Réclamé      [Réclamer]     25 restants  │
│ 100 or         20 or           30 or + 5 📚 │
└─────────────────────────────────────────────┘
```

#### 3. Composant Récompenses Non Réclamées : `UnclaimedRewardsPanel.tsx`
**Fichier** : `client/src/components/quests/UnclaimedRewardsPanel.tsx`

**Affichage** :
- Liste déroulante avec nombre de récompenses
- Compteur d'expiration (ex: "Expire dans 2j 5h")
- Bouton "Tout réclamer"
- Animation lors de la réclamation

#### 4. Styles : `QuestsPage.css`
**Fichier** : `client/src/styles/QuestsPage.css`

**Thème** :
- **Économique** : Vert (#4CAF50)
- **Militaire** : Rouge (#F44336)
- **Recherche** : Bleu (#2196F3)
- **Étoiles** : Doré (#FFD700)

---

## 🔄 Flux de Données

### 1. Chargement Initial
```
User accède à /quests
  ↓
Frontend appelle GET /api/quests/daily + /api/quests/weekly + /api/quests/player-level
  ↓
Backend:
  - Vérifie si quêtes quotidiennes existent pour aujourd'hui
  - Si non : génère 5 nouvelles quêtes aléatoires
  - Si oui : charge depuis players.json
  - Calcule le niveau du joueur
  - Retourne les données
  ↓
Frontend affiche les quêtes avec progression
```

### 2. Progression Automatique
```
User effectue une action (ex: construire un bâtiment)
  ↓
Backend traite l'action (ex: POST /api/city/build)
  ↓
Après succès:
  QuestService.update_quest_progress('eco_build_buildings', +1)
    ↓
    - Met à jour le compteur de progression
    - Vérifie si un palier d'étoile est atteint
    - Si oui: marque l'étoile comme gagnée
    - Ajoute la récompense dans unclaimed_rewards
    - Enregistre l'horodatage d'expiration (+3 jours)
  ↓
Frontend reçoit mise à jour (polling ou WebSocket)
  ↓
Animation "⭐ Étoile obtenue !" + notification
```

### 3. Réclamation de Récompense
```
User clique sur "Réclamer" pour une étoile
  ↓
Frontend appelle POST /api/quests/claim-reward
  Body: {quest_id: "eco_collect_wood", star_level: 2}
  ↓
Backend:
  - Vérifie que l'étoile est gagnée
  - Vérifie que la récompense n'est pas expirée
  - Ajoute les ressources au joueur (or, recherche, etc.)
  - Marque la récompense comme réclamée
  - Incrémente quest_points_total
  ↓
Frontend:
  - Animation de réclamation
  - Mise à jour des ressources du joueur
  - Mise à jour du statut de l'étoile (🌟)
```

### 4. Reset Quotidien
```
00:00:00 serveur
  ↓
Tâche planifiée: reset_daily_quests()
  ↓
Pour chaque joueur:
  - Supprime les anciennes quêtes quotidiennes
  - Marque les récompenses non réclamées comme expirées
  - Génère 5 nouvelles quêtes aléatoires
  - Réinitialise les compteurs de progression
```

---

## 🎨 Détails d'Implémentation

### Génération de Quêtes Quotidiennes

**Algorithme de sélection** :
```python
def generate_daily_quests(player_level):
    # Pool de 18 quêtes: 10 eco, 6 mil, 4 sci
    economic_pool = [...10 quêtes...]
    military_pool = [...6 quêtes...]
    research_pool = [...4 quêtes...]
    
    # Sélection aléatoire respectant la distribution 50/30/20
    selected = []
    selected += random.sample(economic_pool, k=3)  # 3/5 = 60% ≈ 50%
    selected += random.sample(military_pool, k=1)   # 1/5 = 20% ≈ 30%
    selected += random.sample(research_pool, k=1)   # 1/5 = 20%
    
    # Alternative plus précise avec 10 quêtes affichées:
    # 5 eco, 3 mil, 2 sci
    
    # Pour chaque quête, déterminer les paliers selon le niveau
    for quest in selected:
        quest['targets'] = get_targets_for_level(quest['id'], player_level)
        quest['rewards'] = get_rewards_for_level(quest['id'], player_level)
    
    return selected
```

### Interpolation des Niveaux

**Pour les niveaux intermédiaires (basé sur le calcul simplifié)** :
```python
def get_targets_for_level(quest_id, player_level):
    # player_level = (construction_points * 0.5) + (quest_points * 0.5)
    # On utilise 3 paliers définis dans quests_config.json
    
    if player_level <= 5:
        return config['quest_progression'][quest_id][0]['targets']  # Level 1 (débutant)
    elif player_level <= 15:
        return config['quest_progression'][quest_id][1]['targets']  # Level 2 (intermédiaire)
    else:
        return config['quest_progression'][quest_id][2]['targets']  # Level 3 (avancé)
    
    # Exemple concret:
    # Joueur avec 10 constructions (5 points) + 20 quest_points (10 points) = niveau 15 → Level 2
    # Joueur avec 50 constructions (25 points) + 40 quest_points (20 points) = niveau 45 → Level 3
```

### Détection Automatique des Étoiles

**À chaque mise à jour de progression** :
```python
def check_and_award_stars(player_username, quest_id):
    quest_data = get_player_quest(player_username, quest_id)
    progress = quest_data['progress']
    targets = quest_data['targets']  # [50, 75, 100]
    earned_stars = quest_data['stars_earned']  # [1, 2]
    
    for i, target in enumerate(targets):
        star_level = i + 1
        if progress >= target and star_level not in earned_stars:
            # Nouvelle étoile obtenue !
            earned_stars.append(star_level)
            
            # Ajouter la récompense aux non réclamées
            reward = quest_data['rewards'][i]
            add_unclaimed_reward(player_username, quest_id, star_level, reward)
            
            # Notification
            send_notification(player_username, f"⭐ Étoile {star_level}/3 obtenue !")
```

---

## 📊 Classement Quest Points

**Intégration avec le système de leaderboard existant** :

1. **Ajouter une nouvelle catégorie** dans `leaderboard_routes.py` :
```python
@leaderboard_bp.route('/leaderboard/quest_points', methods=['GET'])
def get_quest_points_leaderboard():
    players = load_all_players()
    ranked = sorted(players, 
                   key=lambda p: p.get('quests', {}).get('quest_points_total', 0),
                   reverse=True)
    return jsonify(ranked[:100])  # Top 100
```

2. **Affichage** dans `LeaderboardPage.tsx` :
- Nouvel onglet "Points de Quêtes"
- Badge avec étoiles pour le top 3
- Affichage permanent (pas de reset)

---

## ⚙️ Configuration et Paramètres

### Variables d'Environnement
```env
QUEST_RESET_TIME=00:00:00
QUEST_REWARD_EXPIRATION_DAYS=3
QUEST_DAILY_COUNT=5
QUEST_WEEKLY_COUNT=3
ENABLE_QUEST_NOTIFICATIONS=true
```

### Paramètres de Génération
```python
# Dans quests_config.json
"settings": {
  "daily_selection": {
    "total": 5,
    "distribution": {
      "economic": 3,   # 60%
      "military": 1,   # 20%
      "research": 1    # 20%
    }
  },
  "level_brackets": {
    "1-5": "level_1_data",
    "6-15": "level_2_data",
    "16-50": "level_3_data"
  }
}
```

---

## 🧪 Tests à Effectuer

### Tests Unitaires

1. **QuestService**
   - Calcul du niveau joueur
   - Génération de 5 quêtes aléatoires avec distribution correcte
   - Mise à jour de progression
   - Détection des étoiles
   - Réclamation de récompenses
   - Gestion de l'expiration

2. **Routes API**
   - GET /api/quests/daily retourne 5 quêtes
   - POST /api/quests/claim-reward valide et distribue
   - Gestion des erreurs (quête inexistante, déjà réclamée, expirée)

### Tests d'Intégration

1. **Scénario complet** :
   - Nouveau joueur → génération de 5 quêtes quotidiennes
   - Construction de bâtiment → progression de eco_build_buildings
   - Atteinte de 50/75/100 → 3 étoiles obtenues
   - Réclamation → ressources ajoutées
   - Reset à minuit → nouvelles quêtes

2. **Edge cases** :
   - Récompense non réclamée pendant 3 jours → expiration
   - Joueur niveau 50 → quêtes avec paliers maximaux
   - Multiple quêtes mises à jour simultanément

### Tests Frontend

1. **UI/UX** :
   - Affichage correct des 3 étoiles par quête
   - Animation de progression fluide
   - Bouton "Réclamer" actif/inactif selon statut
   - Compteur d'expiration mis à jour en temps réel

2. **Performance** :
   - Chargement rapide de la page quêtes
   - Mise à jour en temps réel sans lag
   - Gestion de 5 quêtes quotidiennes + 3 hebdomadaires

---

## 📅 Planning de Développement

### Phase 1 : Backend Core (3-4 jours)
- [ ] Créer `QuestService` avec calcul de niveau
- [ ] Implémenter génération de quêtes quotidiennes
- [ ] Implémenter tracking de progression
- [ ] Créer routes API de base
- [ ] Tests unitaires QuestService

### Phase 2 : Intégration Tracking Priorité 1 (2-3 jours)
- [ ] Intégrer dans `city_routes.py` (construction de bâtiments)
- [ ] Intégrer dans `city_routes.py` (collecte de ressources via tick)
- [ ] Intégrer dans `army_routes.py` (recrutement d'unités)
- [ ] Tests d'intégration priorité 1

### Phase 2.5 : Tracking Priorité 2 (optionnel - 2 jours)
- [ ] Intégrer dans `battle_routes.py` (victoires, unités tuées)
- [ ] Intégrer dans `research_routes.py` (déblocage, accumulation)
- [ ] Intégrer dans marché (transactions commerciales)
- [ ] Tests d'intégration priorité 2

### Phase 3 : Frontend UI (3-4 jours)
- [ ] Créer `QuestsPage.tsx` avec onglets
- [ ] Créer `QuestCard.tsx` avec 3 étoiles
- [ ] Créer `UnclaimedRewardsPanel.tsx`
- [ ] Ajouter navigation menu → Quêtes
- [ ] Créer `QuestsPage.css` avec thème
- [ ] Tests UI

### Phase 4 : Reset & Cron (1-2 jours)
- [ ] Implémenter reset quotidien (00:00:00)
- [ ] Implémenter reset hebdomadaire (dimanche)
- [ ] Implémenter nettoyage des récompenses expirées
- [ ] Tests de planification

### Phase 5 : Leaderboard & Polish (1-2 jours)
- [ ] Ajouter catégorie Quest Points au leaderboard
- [ ] Animations et notifications
- [ ] Documentation
- [ ] Tests finaux et déploiement

**Durée totale estimée** : 10-15 jours de développement

---

## 🚀 Évolutions Futures

### Version 2.0
- **Quêtes par niveau** : 20 quêtes pour levels 1-5, 15 pour 5-10, etc.
- **Quêtes spéciales** : Événements saisonniers
- **Chaînes de quêtes** : Quêtes multi-étapes (saga)
- **Achievements** : Récompenses permanentes pour milestones
- **Quêtes guildes** : Objectifs collaboratifs

### Optimisations
- **WebSocket** : Mise à jour en temps réel sans polling
- **Cache Redis** : Stockage temporaire des quêtes actives
- **Compression** : Réduire la taille des données JSON

---

## 📝 Notes Importantes

1. **Progression passive** : Les quêtes progressent automatiquement, le joueur n'a pas besoin de les "accepter"
2. **Récompenses cumulatives** : 1★ donne reward[0], 2★ donne reward[0]+reward[1], 3★ donne tout
3. **Fichier séparé** : `player_quests.json` indépendant de `players.json` pour éviter la surcharge
4. **Niveau simplifié** : `(construction_points * 0.5) + (quest_points * 0.5)` - recalculé à la volée
5. **Implémentation progressive** : Les trackers de quêtes seront ajoutés au fur et à mesure selon priorité
6. **Balance économique** : Surveiller les récompenses pour éviter l'inflation d'or/ressources
7. **Rétrocompatibilité** : Les anciens joueurs sans données de quêtes doivent être initialisés proprement

---

## ✅ Critères de Validation

Le système de quêtes est considéré comme fonctionnel si :

- ✅ 5 quêtes quotidiennes générées chaque jour avec distribution correcte
- ✅ 3 quêtes hebdomadaires fixes accessibles
- ✅ Progression automatique sans action du joueur
- ✅ 3 étoiles par quête avec récompenses cumulatives
- ✅ Réclamation manuelle des récompenses
- ✅ Expiration après 3 jours
- ✅ Reset quotidien et hebdomadaire fonctionnels
- ✅ Niveau joueur calculé dynamiquement
- ✅ UI intuitive et responsive
- ✅ Classement Quest Points intégré

---

**Document préparé le** : 5 décembre 2025  
**Version** : 1.0  
**Statut** : Prêt pour implémentation
