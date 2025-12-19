# 📚 SYSTÈME DE TUTORIEL - Documentation Complète

## 📋 Vue d'ensemble

Le système de tutoriel est un système interactif complet qui guide les nouveaux joueurs à travers les fonctionnalités de base du jeu. Il inclut :
- **13 étapes progressives** (0 à 12)
- **Validation automatique** des actions
- **Récompenses automatiques** (ressources, points de recherche)
- **Navigation multi-pages** (World → Island → City)
- **Persistance complète** (rechargement de page)

---

## 📁 Fichiers du Système

### Frontend

#### 1. **tutorialSteps.ts** (`client/src/config/`)
**Rôle** : Configuration centrale de toutes les étapes du tutoriel

**Contenu** :
- Interface `TutorialStep` : Structure d'une étape
- Array `tutorialSteps` : Liste complète des 13 étapes
- Fonctions utilitaires : `getTutorialStep()`, `getNextTutorialStep()`

**Structure d'une étape** :
```typescript
{
  id: 'welcome_world',
  title: '🌍 Bienvenue sur la Carte du Monde !',
  description: 'Clique sur ton île...',
  page: 'world',
  position: 'center',
  validation: {
    type: 'path_check',
    pathPattern: /^\/island\/\d+$/
  },
  reward: {
    type: 'resources',
    description: '+100 bois, +50 pierre',
    value: { wood: 100, stone: 50 }
  }
}
```

**Types de validation** :
- `manual` : Bouton "Suivant" (pas de validation auto)
- `click` : Attend un clic sur un élément
- `api_check` : Vérifie une condition via l'API
- `element_exists` : Attend l'apparition d'un élément
- `path_check` : Vérifie la navigation (pathname)

---

#### 2. **TutorialOverlay.tsx** (`client/src/components/`)
**Rôle** : Composant React principal du tutoriel

**Responsabilités** :
1. Affichage de la tooltip avec titre/description
2. Gestion du spotlight (surbrillance de l'élément cible)
3. Positionnement intelligent de la tooltip
4. Validation des actions du joueur
5. Appel API pour créditer les récompenses
6. Navigation entre les étapes

**État local** :
- `currentStepIndex` : Index de l'étape actuelle (0-12)
- `spotlightRect` : Position de l'élément surligné
- `tooltipPosition` : Position calculée de la tooltip
- `actionCompleted` : Validation de l'action en cours
- `isMinimized` : Tutoriel minimisé (badge)
- `isLoading` : Chargement de la progression

**Hooks** :
- `useEffect` : Validation automatique, chargement, spotlight
- `useRef` : Persistance des valeurs (évite double validation)
- `useState` : Gestion de l'état

**Flux de validation** :
```
Action du joueur (ex: clic sur Scierie)
  ↓
Validation frontend (actionCompleted = true)
  ↓
Bouton "Suivant" activé
  ↓
POST /api/tutorial/complete
  ↓
Backend crédite les récompenses
  ↓
Passage à l'étape suivante
```

---

#### 3. **tutorial.css** (`client/src/styles/`)
**Rôle** : Styles visuels du tutoriel

**Composants stylés** :
- `.tutorial-overlay` : Overlay sombre (rgba(0,0,0,0.7))
- `.tutorial-tooltip` : Boîte de dialogue dorée
- `.tutorial-spotlight` : Découpe transparente (clip-path)
- `.tutorial-minimize-btn` : Bouton minimiser
- `.tutorial-minimized-badge` : Badge en mode réduit

**Z-index Architecture** :
```
.tutorial-overlay         : 2147483647 !important (base)
.tutorial-tooltip         : 2147483648 !important (tooltip)
.tutorial-minimize-btn    : 2147483649 !important (bouton)
```
⚠️ **2147483647 = max CSS** : Garantit que le tutoriel est toujours visible

**Animations** :
- `fadeIn` : Apparition douce (0.3s)
- `pulse` : Effet pulsant sur les boutons
- `glow` : Lueur dorée sur boutons actifs

**Responsive** :
- Mobile : Tooltip en plein écran si nécessaire
- Tablette : Tailles ajustées
- Desktop : Tailles standard

---

### Backend

#### 4. **tutorial.py** (`server/app/routes/`)
**Rôle** : Routes API du système de tutoriel

**Endpoints** :

**GET `/api/tutorial/status/<player_id>`**
```json
Réponse:
{
  "completed": false,
  "current_step": "build_sawmill",
  "completed_steps": 5
}
```

**POST `/api/tutorial/complete`**
```json
Body:
{
  "player_id": "player_1",
  "step_id": "build_sawmill",
  "reward": {
    "type": "resources",
    "value": { "wood": 100, "stone": 50 }
  }
}

Réponse:
{
  "success": true,
  "message": "Étape complétée avec succès",
  "reward_message": "Récompenses créditées : +100 bois, +50 pierre"
}
```

**POST `/api/tutorial/check/<step_id>`**
```json
Body:
{
  "player_id": "player_1"
}

Réponse:
{
  "valid": true,
  "message": "Condition remplie"
}
```

**Système de récompenses** :
- **Ressources** → Ajoutées à la première ville du joueur
- **Points de recherche** → Ajoutés au compteur du joueur

**Sécurité** :
- Vérification que l'étape n'est pas déjà complétée
- Validation des données (player_id, step_id)
- Gestion des erreurs (joueur/ville introuvable)

---

## 🎮 Architecture Complète

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND                          │
├─────────────────────────────────────────────────────┤
│  tutorialSteps.ts                                   │
│    ↓ (définit les étapes)                          │
│  TutorialOverlay.tsx                                │
│    ↓ (affiche + valide)                            │
│  tutorial.css                                       │
│    ↓ (styles)                                      │
│  API Call: POST /api/tutorial/complete             │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│                   BACKEND                           │
├─────────────────────────────────────────────────────┤
│  tutorial.py                                        │
│    ↓ (valide + crédite)                            │
│  DataManager                                        │
│    ↓ (sauvegarde)                                  │
│  players.json                                       │
│    - player.tutorial.current_step                  │
│    - player.tutorial.completed_steps               │
│    - player.tutorial.completed                     │
│  savegame.json                                      │
│    - city.resources (récompenses ressources)       │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Progression du Tutoriel

### Étapes 0-2 : WorldPage (Carte du Monde)
- **0. welcome_world** : Introduction à la carte
- **1. select_island** : Cliquer sur l'île de départ
- **2. island_transition** : Navigation vers IslandPage

**Validation** : `path_check` (vérifie pathname = `/island/:id`)

---

### Étapes 3-5 : IslandPage (Vue Île)
- **3. welcome_island** : Introduction à la vue île
- **4. resource_sites** : Découverte des sites de ressources
- **5. city_transition** : Navigation vers CityPage

**Validation** : `path_check` (vérifie pathname = `/city/:id`)

---

### Étapes 6-12 : CityPage (Gestion Ville)
- **6. welcome_city** : Introduction à la gestion de ville
- **7. build_sawmill** : Construire la Scierie (niveau 1)
- **8. unlock_research** : Débloquer la recherche Conservation
- **9. build_warehouse** : Construire l'Entrepôt
- **10. assign_workers** : Assigner des ouvriers
- **11. view_production** : Voir la production
- **12. tutorial_complete** : Fin du tutoriel

**Récompenses** :
- Étape 6 : +200 bois, +100 pierre, +50 gold
- Étape 7 : +15 points de recherche
- Étape 8 : +20 points de recherche
- Étape 9 : +100 bois, +100 pierre
- Étape 12 : +500 bois, +500 pierre, +100 gold

---

## 🔧 Points Techniques Clés

### 1. Z-index à 2147483647
**Problème initial** : Le tutoriel disparaissait derrière les popups de bâtiments (BuildingPopupBase)

**Solution** :
- Tutoriel : `z-index: 2147483647 !important` (max CSS)
- Popups : `z-index: 100000`
- Garantit que le tutoriel est **TOUJOURS** visible

### 2. Validation Automatique
**Système flexible** :
- `manual` : Pas de validation auto (bouton "Suivant")
- `click` : Attend un clic sur un élément spécifique
- `api_check` : Interroge l'API avec condition personnalisée
- `element_exists` : Attend l'apparition d'un élément DOM
- `path_check` : Vérifie la navigation (pathname)

**Exemple api_check** :
```typescript
validation: {
  type: 'api_check',
  apiEndpoint: '/api/research/unlocked',
  apiCondition: (data, playerId) => {
    return data.unlocked_research?.includes('conservation');
  }
}
```

### 3. Persistance Complète
**Rechargement de page** :
1. TutorialOverlay charge `/api/tutorial/status/<player_id>`
2. Backend retourne `current_step` depuis `players.json`
3. Frontend retrouve l'index de l'étape et reprend

**Stockage** :
```json
// players.json
{
  "tutorial": {
    "completed": false,
    "current_step": "build_sawmill",
    "completed_steps": 7
  }
}
```

### 4. Spotlight Dynamique
**Calcul de position** :
1. `document.querySelector(step.target)` → Trouve l'élément
2. `getBoundingClientRect()` → Position absolue
3. Recalcul lors du scroll/resize
4. `clip-path` sur l'overlay pour la découpe

**Positionnement de la tooltip** :
- `top` : Au-dessus de l'élément
- `bottom` : En-dessous
- `left` : À gauche
- `right` : À droite
- `center` : Centre de l'écran (aucun élément cible)

### 5. Double Validation (Sécurité)
**Frontend** :
- Vérifie que l'action est complétée (`actionCompleted = true`)
- Active le bouton "Suivant"

**Backend** :
- Vérifie que l'étape n'est pas déjà dans `completed_steps`
- Empêche les récompenses multiples (triche)

---

## 🐛 Bugs Corrigés

### Bug 1 : Tutoriel derrière les popups
**Symptôme** : La tooltip disparaissait derrière BuildingPopup

**Cause** : BuildingPopup avait `z-index: 2147483647`

**Solution** :
- Tutoriel : `z-index: 2147483647 !important`
- BuildingPopup : `z-index: 100000`
- AttackPopup : `z-index: 100000` (était à 2147483647)

### Bug 2 : Validation non persistante
**Symptôme** : Rechargement perdait la progression

**Solution** :
- Ajout de `GET /api/tutorial/status/<player_id>`
- `useEffect` charge la progression au montage
- `current_step` stocké dans `players.json`

### Bug 3 : Récompenses non créditées
**Symptôme** : Les récompenses n'étaient pas ajoutées

**Solution** :
- Ajout du champ `reward` dans `TutorialStep`
- Backend crédite via `POST /api/tutorial/complete`
- Vérification que la ville existe (première ville du joueur)

### Bug 4 : Prop 'action' inutilisée
**Symptôme** : 10 warnings ESLint sur `action` non utilisé

**Solution** :
- Suppression du champ `action` de l'interface `TutorialStep`
- Nettoyage de toutes les références (10 occurrences)

---

## 📈 Statistiques

- **Fichiers créés/modifiés** : 4 (tutorialSteps.ts, TutorialOverlay.tsx, tutorial.css, tutorial.py)
- **Lignes de code** : ~1800 lignes au total
- **Étapes du tutoriel** : 13 (0-12)
- **Récompenses totales** :
  - Bois : +1000
  - Pierre : +750
  - Or : +150
  - Points de recherche : +35

---

## 🚀 Utilisation

### Pour le développeur

**Ajouter une nouvelle étape** :
1. Éditer `tutorialSteps.ts`
2. Ajouter un objet dans l'array `tutorialSteps`
3. Définir `id`, `title`, `description`, `validation`, `reward`
4. Tester dans le jeu

**Modifier le style** :
1. Éditer `tutorial.css`
2. Modifier `.tutorial-tooltip` pour la boîte de dialogue
3. Modifier `.tutorial-overlay` pour l'overlay sombre

**Débugger** :
1. Console navigateur : Voir les logs de validation
2. Network : Voir les appels API (`/api/tutorial/*`)
3. React DevTools : Inspecter l'état de TutorialOverlay

### Pour le joueur

**Lancer le tutoriel** :
1. Créer un nouveau compte
2. Le tutoriel démarre automatiquement
3. Suivre les instructions à l'écran

**Reprendre le tutoriel** :
1. Le tutoriel reprend automatiquement au rechargement
2. Bouton "Reprendre" si minimisé

**Passer le tutoriel** :
1. Bouton "Passer le tutoriel" dans chaque étape
2. Confirmation requise
3. Les récompenses déjà gagnées restent acquises

---

## 📚 Documentation Technique

### Interface TutorialStep
```typescript
interface TutorialStep {
  id: string;                    // Identifiant unique
  title: string;                 // Titre de l'étape
  description: string;           // Description détaillée
  target?: string;               // Sélecteur CSS de l'élément à surligner
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  page?: string;                 // Page où afficher l'étape
  reward?: {
    type: 'resources' | 'research_points';
    description: string;
    value: Record<string, number>;
  };
  nextButton?: string;           // Texte du bouton suivant
  skipButton?: boolean;          // Afficher le bouton "Passer"
  validation?: {
    type: 'click' | 'api_check' | 'element_exists' | 'manual' | 'path_check';
    target?: string;
    apiEndpoint?: string;
    apiCondition?: (data: any, playerId?: string) => boolean;
    pathPattern?: RegExp;
  };
}
```

### Endpoints API
```
GET  /api/tutorial/status/<player_id>
POST /api/tutorial/complete
POST /api/tutorial/check/<step_id>
```

### Stockage des Données
```json
// players.json
{
  "players": [
    {
      "id": "player_1",
      "tutorial": {
        "completed": false,
        "current_step": "build_sawmill",
        "completed_steps": 7
      }
    }
  ]
}
```

---

## 🔄 Flux Complet d'une Étape

```
1. TutorialOverlay charge l'étape actuelle (tutorialSteps[index])
2. Affiche la tooltip avec titre/description
3. Crée le spotlight autour de l'élément cible (si target défini)
4. Attend la validation :
   - manual : Attend le clic sur "Suivant"
   - click : Attend le clic sur l'élément target
   - api_check : Interroge l'API toutes les 2 secondes
   - element_exists : Vérifie la présence de l'élément
   - path_check : Vérifie le pathname actuel
5. Validation → actionCompleted = true
6. Bouton "Suivant" devient cliquable
7. Clic sur "Suivant" → POST /api/tutorial/complete
8. Backend :
   - Vérifie que l'étape n'est pas déjà complétée
   - Crédite les récompenses (ressources ou research_points)
   - Met à jour player.tutorial.completed_steps
   - Retourne le nouveau statut
9. Frontend :
   - Passe à l'étape suivante (index + 1)
   - Si dernière étape → Marque completed = true
   - Affiche la nouvelle étape
```

---

**Dernière mise à jour** : 2 décembre 2025  
**Version** : 2.0 (Système complet avec validation automatique et récompenses)  
**Auteur** : GitHub Copilot + Kevin
