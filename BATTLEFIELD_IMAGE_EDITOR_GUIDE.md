# 🗺️ Guide d'Utilisation de l'Éditeur de Carte avec Image de Fond

## 📂 Fichiers

- **Éditeur** : `battlefield-image-editor.html` (racine du projet)
- **Images de fond** : `client/public/assets/battlefield_images/`
- **Cartes JSON** : Générées par l'éditeur

---

## 🚀 Étapes d'utilisation

### 1. Préparer votre image de fond

1. Créez ou trouvez une belle carte (PNG, JPG)
2. Placez-la dans `client/public/assets/battlefield_images/`
3. Exemple : `map_1.jpg`, `forest_battlefield.png`, etc.

**Dimensions recommandées** : 1920×1080 ou supérieur

---

### 2. Utiliser l'éditeur

1. **Ouvrir** `battlefield-image-editor.html` dans votre navigateur
2. **Charger l'image** :
   - Cliquez sur "Charger une image"
   - Sélectionnez votre image
   - Elle apparaîtra dans la preview et sur le canvas
3. **Définir les dimensions** :
   - Largeur : nombre d'hexagones horizontalement (ex: 20)
   - Hauteur : nombre d'hexagones verticalement (ex: 15)
   - Cliquez sur "Générer la Grille"

4. **Ajuster la transparence** :
   - Utilisez le slider "Opacité" (0-100%)
   - Recommandé : 30-40% pour bien voir l'image de fond
   - Les hexagones transparents laissent voir l'image

5. **Peindre le terrain** :
   - Sélectionnez un terrain dans la palette (🌾 🌲 ⛰️ 🌊 etc.)
   - Cliquez sur les hexagones pour appliquer le terrain
   - Le terrain affecte le gameplay (mouvement, défense)

6. **Définir les zones** :
   - Cliquez sur "Zone Attaquant" (rouge)
   - Cliquez sur les hexagones pour marquer la zone de déploiement
   - Idem pour "Zone Défenseur" (bleu)
   - Revenez à "Zone Neutre" pour peindre le terrain normalement

7. **Sauvegarder** :
   - Cliquez sur "💾 Sauvegarder la Carte"
   - Un fichier JSON sera téléchargé (ex: `battlefield_1734567890.json`)

---

## 📊 Format JSON généré

```json
{
  "width": 20,
  "height": 15,
  "backgroundImage": "map_1.jpg",
  "hexagones": [
    { "q": 0, "r": 0, "terrain": "plains", "zone": "neutral" },
    { "q": 1, "r": 0, "terrain": "forest", "zone": "attacker" },
    ...
  ]
}
```

**Important** : Le champ `backgroundImage` doit correspondre au nom du fichier dans `battlefield_images/`

---

## 🎮 Utilisation dans le jeu

### Méthode actuelle (automatique)

Si `battleData.backgroundImage` existe dans `battlesv2.json`, l'image de fond sera automatiquement affichée.

### Méthode manuelle (pour tests)

1. Modifiez `server/gamedata/battlesv2.json`
2. Ajoutez le champ dans votre bataille :

```json
{
  "battle_123": {
    "backgroundImage": "map_1.jpg",
    "grid": [...],
    ...
  }
}
```

3. L'image apparaîtra automatiquement en jeu avec les hexagones transparents

---

## 🎨 Conseils de création

### Pour l'image de fond

✅ **Bon** :
- Paysages réalistes (forêts, montagnes, plaines)
- Cartes stylisées (pixel art, hand-drawn)
- Vues aériennes de terrains variés

❌ **Éviter** :
- Images trop chargées (illisible)
- Couleurs trop vives (fatigue les yeux)
- Trop de détails fins (se perd au zoom)

### Pour la transparence

- **30-40%** : Bon équilibre gameplay/esthétique
- **10-20%** : Très réaliste mais gameplay moins clair
- **50-70%** : Gameplay clair mais image peu visible

### Pour les terrains

Assignez les terrains **selon l'image de fond** :
- Si l'image montre une forêt → terrain `forest` (🌲)
- Si l'image montre de l'eau → terrain `river` (🌊)
- Si l'image montre des collines → terrain `hill` (⛰️)

Cela garantit que le gameplay correspond au visuel !

---

## 🛠️ Améliorations futures possibles

- [ ] Brush tool (peindre plusieurs hexagones d'un coup)
- [ ] Undo/Redo
- [ ] Calques (séparer terrains / zones / décors)
- [ ] Import/export de palettes de terrains
- [ ] Preview 3D du rendu final
- [ ] Générateur procédural (rivières, routes, forêts)

---

## 🐛 Dépannage

**L'image ne s'affiche pas dans l'éditeur** :
- Vérifiez que le fichier est bien sélectionné
- Vérifiez le format (PNG, JPG, WebP supportés)

**L'image ne s'affiche pas en jeu** :
- Vérifiez que `backgroundImage` est bien dans le JSON
- Vérifiez que le fichier existe dans `client/public/assets/battlefield_images/`
- Vérifiez le nom exact (sensible à la casse)
- Regardez la console du navigateur pour les erreurs

**Les hexagones sont trop opaques** :
- Ajustez le slider "Opacité" dans l'éditeur
- En jeu, modifiez `fill-opacity` dans `SimpleBattlefieldV2.css`

**Les hexagones ne correspondent pas à l'image** :
- Ajustez les dimensions de la grille
- Utilisez une image avec le bon ratio (16:9 recommandé)

---

## 📝 Exemple complet

1. Image de fond : `forest_valley.jpg` (1920×1080)
2. Dimensions : 25×15 hexagones
3. Opacité : 35%
4. Zones :
   - Attaquant : Bas de la carte (5 lignes)
   - Défenseur : Haut de la carte (5 lignes)
   - Neutre : Milieu (5 lignes)
5. Terrains :
   - Forêt dense au centre (🌲)
   - Rivière traversant (🌊)
   - Plaines sur les côtés (🌾)
   - Collines aux extrémités (⛰️)

Résultat : Une belle carte équilibrée avec un visuel immersif !
