# Système de Classement (Leaderboard)

## Vue d'ensemble

Le système de classement permet aux joueurs de comparer leurs performances à travers plusieurs catégories. Il est accessible via le menu principal sous "Statistiques" (🏆).

## Architecture

### Backend

**Fichier**: `server/app/routes/leaderboard_routes.py`

**Endpoint principal**: `GET /api/leaderboard/<category>`

**Catégories disponibles**:

1. **general** - Score général combiné
   - Formule : `construction_points + research_points + (victories * 10)`
   - Affiche les détails de chaque composant

2. **construction** - Points de construction
   - Calculé via `PlayerProgressionService.calculate_construction_points()`
   - Formule triangulaire : Σ(level * (level + 1) / 2)

3. **research** - Points de recherche investis
   - Calculé via `PlayerProgressionService.calculate_research_points_invested()`
   - Somme des coûts de toutes les recherches débloquées + points actuels

4. **military_xp** - Expérience militaire
   - Directement depuis `player['military_experience']`

5. **units_killed** - Unités ennemies éliminées
   - Total des unités détruites en combat

6. **units_lost** - Unités perdues
   - Total des unités perdues en combat

7. **victories** - Victoires militaires
   - Nombre de batailles gagnées

**Dépendances**:
- `PlayerProgressionService` pour les calculs de score
- `DataManager` pour l'accès aux données des joueurs

### Frontend

**Fichier**: `client/src/pages/LeaderboardPage.tsx`

**Caractéristiques**:

1. **Filtres de catégorie**
   - 7 boutons pour changer de catégorie
   - Catégorie active mise en surbrillance

2. **Affichage du classement**
   - Tableau avec rang, nom de joueur et score
   - Badges spéciaux pour les 3 premiers :
     - 🥇 1er place - Or (#FFD700)
     - 🥈 2ème place - Argent (#C0C0C0)
     - 🥉 3ème place - Bronze (#CD7F32)

3. **Mise en évidence du joueur actuel**
   - Ligne du joueur actuel avec fond doré
   - Barre latérale "Vous" pour faciliter la localisation

4. **Affichage des détails (catégorie "general")**
   - Construction, Recherche, Victoires affichées séparément
   - Total calculé automatiquement

**Styles**: `client/src/styles/LeaderboardPage.css`
- Design responsive
- Typographie Trajan Pro
- Dégradés subtils pour les badges
- Animation de survol

### Navigation

**Menu Principal** (`client/src/components/MenuPopup.tsx`):
- Bouton "Statistiques" avec icône 🏆
- Situé entre "Recherche" et "Messages"

**Bottom Nav Bar** (`client/src/components/BottomNavBar.tsx`):
- Handler `handleLeaderboard()` qui navigue vers `/leaderboard`
- Ferme le menu automatiquement après navigation

**Routing** (`client/src/App.tsx`):
```tsx
<Route path="/leaderboard" element={
  <GameShell>
    <LeaderboardPage />
  </GameShell>
} />
```

## Flux de données

1. **Chargement initial**
   - LeaderboardPage monte
   - Appel API vers `/api/leaderboard/general` (catégorie par défaut)
   - Affichage du classement

2. **Changement de catégorie**
   - Clic sur bouton de filtre
   - Nouvel appel API vers `/api/leaderboard/<nouvelle_catégorie>`
   - Mise à jour du tableau

3. **Calcul en temps réel**
   - Les scores sont recalculés à chaque appel API
   - Garantit que les données sont toujours à jour
   - Pas de cache côté serveur

## Intégration avec le système de progression

Le classement utilise les services de progression existants :

**Construction Points**:
```python
PlayerProgressionService.calculate_construction_points(player_id)
```

**Research Points**:
```python
PlayerProgressionService.calculate_research_points_invested(player_id)
```

**Données militaires**:
- Directement depuis les champs du joueur
- `military_experience`, `units_killed`, `units_lost`, `victories`

## Format de réponse API

```json
{
  "success": true,
  "category": "general",
  "leaderboard": [
    {
      "player_id": "player_1",
      "username": "Joueur 1",
      "score": 1250,
      "construction_points": 450,    // Seulement pour "general"
      "research_points": 300,        // Seulement pour "general"
      "victories": 50                // Seulement pour "general"
    },
    ...
  ]
}
```

## Améliorations futures possibles

1. **Pagination**
   - Pour gérer de nombreux joueurs
   - Limiter à 50-100 joueurs par page

2. **Filtres temporels**
   - Classement du jour/semaine/mois
   - Nécessite l'ajout de timestamps

3. **Classements par île**
   - Comparaison locale entre voisins

4. **Historique**
   - Évolution du rang au fil du temps
   - Graphiques de progression

5. **Récompenses**
   - Prix pour les premiers rangs
   - Titres honorifiques

6. **Mise à jour en temps réel**
   - WebSocket pour notifications de changement de rang
   - Animations de montée/descente

## Notes techniques

- **Performance**: Les calculs sont O(n*m) où n = nombre de joueurs, m = nombre de bâtiments/recherches
  - Acceptable pour <1000 joueurs
  - Envisager la mise en cache pour scale-up

- **Cohérence des données**: 
  - Les scores sont recalculés dynamiquement
  - Pas de désynchronisation possible entre `players.json` et les scores affichés

- **Sécurité**:
  - Endpoint public, pas d'authentification requise
  - Pas de données sensibles exposées (seulement username et scores)

## Tests recommandés

1. **Backend**:
   - Vérifier chaque catégorie retourne des données valides
   - Tester avec 0 joueur, 1 joueur, plusieurs joueurs
   - Valider l'ordre de tri (décroissant)

2. **Frontend**:
   - Changement de catégorie
   - Affichage correct du joueur actuel
   - Responsive design sur mobile
   - Badges de rang corrects pour top 3

3. **Intégration**:
   - Navigation depuis le menu
   - Retour arrière fonctionne
   - GameShell header/footer présents
