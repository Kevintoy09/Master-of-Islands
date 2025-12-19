# Game Client - Version V2

## Présentation
Client React/TypeScript pour un jeu de stratégie multi-îles avec système de combat au tour par tour.

## Fonctionnalités Principales

### Système de Combat V2
- **UnitDeploymentPopupV2** : Popup avancé de déploiement des troupes
  - Affichage groupé des unités avec max_stack_size
  - Intégration des héros dans les forces disponibles
  - Système de renforts avec minuteurs temps réel
  - Gestion centralisée des événements souris/tactile

### Contrôles Mobile-First
- **usePreventZoom** : Hook centralisé unique pour la gestion anti-zoom
  - Prévention complète du zoom (molette, pinch, clavier)
  - Autorise le scroll vertical dans les popups
  - Capture d'événements avec `passive: false, capture: true`
  - Handlers React intégrés pour overlay et contenu
  - **UN SEUL FICHIER** pour toute la logique anti-zoom

### Architecture des Données
- Données des batailles dans `server/data/battlefields_v2.json`
- Support des forces engagées et troupes en déplacement
- Calcul automatique des temps d'arrivée des renforts

## Structure Technique

### Composants Principaux
```
src/
├── components/
│   ├── UnitDeploymentPopupV2.tsx    # Popup déploiement V2
│   └── SimpleBattlefieldV2.tsx      # Carte de bataille
├── hooks/
│   └── usePreventZoom.ts            # Contrôle anti-zoom centralisé (COMPLET)
├── services/
│   └── BattlefieldMapService.ts     # Service cartes de bataille
└── styles/
    └── UnitDeploymentPopupV2.css    # Styles optimisés mobile
```

### Fonctionnalités V2
1. **Groupement d'Unités** : Affichage visuel par groupes selon max_stack_size
2. **Héros Intégrés** : Affichage des héros disponibles avec les forces
3. **Renforts Temps Réel** : Minuteurs dynamiques pour les arrivées de troupes
4. **Mobile Optimisé** : Prévention zoom complète, scroll vertical autorisé
5. **Centralisation** : Hook unique usePreventZoom pour tous les popups

## Installation et Démarrage

```bash
# Installation des dépendances
npm install

# Démarrage en mode développement
npm start

# Build production
npm run build
```

## Usage Anti-Zoom dans les Popups

### Import et utilisation
```tsx
// 1. Import unique
import usePreventZoom, { handleOverlayWheel, handleContentWheel } from '../hooks/usePreventZoom';

// 2. Hook dans le composant
usePreventZoom(isOpen);

// 3. Handlers dans le JSX
<div onWheel={handleOverlayWheel}>        // Overlay - bloque tout
  <div onWheel={handleContentWheel}>      // Contenu - autorise scroll
```

### Couverture actuelle
- ✅ **UnitDeploymentPopupV2** : Intégré et testé
- ✅ **AttackPopupV2** : Migré vers système centralisé
- 🔄 **Autres popups** : Migration en cours selon besoins

```bash
# Installation des dépendances
npm install

# Démarrage en mode développement
npm start

# Build production
npm run build
```

## Optimisations Récentes
- CSS réduit de ~150 lignes (suppression styles cards inutilisés)
- Migration vers système anti-zoom centralisé unique
- Gestion agressive des événements zoom avec capture: true
- Structure de fichiers organisée (battlefields_v2.json déplacé)
- **AttackPopupV2 simplifié** : 30+ lignes → 3 lignes

## Notes Techniques
- React 18+ avec TypeScript
- Event listeners natifs pour contournement des limitations React
- Architecture modulaire avec hook centralisé anti-zoom
- Support mobile-first avec prévention zoom complète

## Statut Actuel
✅ Système V2 complet et fonctionnel
✅ Hook centralisé anti-zoom implémenté et testé
✅ AttackPopupV2 migré vers système centralisé  
✅ Optimisations CSS effectuées
✅ Structure fichiers organisée