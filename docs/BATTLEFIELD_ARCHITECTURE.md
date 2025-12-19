# Architecture Simplifiée - Système de Battlefields

## Vue d'ensemble

Le système de battlefields a été simplifié pour éliminer les doublons et centraliser la gestion des cartes.

## Structure des fichiers

### Cartes de battlefield (Source de vérité unique)
- **Emplacement unique :** `client/public/data/battlefields/`
- **Format :** Fichiers JSON avec structure standardisée
- **Chargement :** Direct via HTTP depuis le client React

### Fichiers présents
1. `battlefield_marais.json`
2. `coastal_fortress.json`
3. `default_working.json`
4. `forest_medium.json`
5. `grande_carte.json`
6. `mountain_large.json`
7. `plains_small.json`
8. `river_crossing.json`
9. `village_siege.json`

## Fonctionnement automatique

### Détection des cartes disponibles
```typescript
// BattlefieldMapService.getAvailableBattlefieldIds()
// Test automatique de présence des 9 fichiers
// Retourne seulement les cartes vraiment disponibles
```

### Génération automatique des noms d'affichage
```typescript
// AttackPopup.getBattlefieldDisplayName()
// "grande_carte" → "Grande Carte"
// "mountain_large" → "Mountain Large"
// etc.
```

### Déploiement automatique des unités
```typescript
// UnitDeploymentPopup utilise directement le battlefieldTemplateId
// 1. Charge la carte sélectionnée
// 2. Détecte les terrains "base-attack" et "base-defense"
// 3. Déploie automatiquement selon ces positions
```

## Pour ajouter une nouvelle carte

1. **Créer le fichier JSON** dans `client/public/data/battlefields/`
2. **Structure requise :**
   ```json
   {
     "template": {
       "id": "ma_nouvelle_carte",
       "name": "Ma Nouvelle Carte",
       "description": "Description de la carte",
       "terrainTypes": ["plains", "base-attack", "base-defense", ...]
     },
     "hexCells": [
       {
         "q": 0, "r": 0,
         "terrain": "base-attack", // Pour camps d'attaque
         "zone": "battlefield"
       },
       // ... autres cellules
     ]
   }
   ```
3. **C'est tout !** La carte apparaîtra automatiquement dans le menu

## Détection des camps de base

### Méthode principale : Terrains spécifiques
- `terrain: "base-attack"` → Positions d'attaque  
- `terrain: "base-defense"` → Positions de défense

### Fallback : deploymentZones
Si pas de terrains spécifiques, utilise :
```json
"deploymentZones": {
  "attacker": [{"q": 0, "r": 4}, {"q": 1, "r": 4}],
  "defender": [{"q": 16, "r": 4}, {"q": 17, "r": 4}]
}
```

### Fallback final : Détection géométrique
Si rien n'est défini, utilise une analyse automatique des bords de carte.

## Fichiers supprimés lors du nettoyage

- ❌ `data/battlefields/` (dossier serveur dupliqué)
- ❌ `sync_battlefields.ps1` (script de synchronisation)
- ❌ `*_backup.tsx` (fichiers de sauvegarde)
- ❌ Fonctions inutiles dans `BattlefieldMapService`
- ❌ Code dupliqué dans `UnitDeploymentPopup`

## Avantages de la nouvelle architecture

✅ **Un seul endroit** pour les cartes
✅ **Détection automatique** des cartes disponibles  
✅ **Noms générés automatiquement**
✅ **Camps détectés intelligemment**
✅ **Pas de liste à maintenir manuellement**
✅ **Pas de synchronisation nécessaire**

## Flux de données simplifié

```
AttackPopup (sélection carte)
    ↓ battlefieldTemplateId
BattlePopup
    ↓ battlefieldTemplateId  
NapoleonicBattlefield
    ↓ battlefieldTemplateId
UnitDeploymentPopup
    ↓ BattlefieldMapService.loadBattlefield()
client/public/data/battlefields/{id}.json
```
