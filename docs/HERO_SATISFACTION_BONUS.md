# 🦸 Système de Bonus de Satisfaction des Héros

## 📋 Fonctionnalité Implémentée

Les héros en garnison dans une ville apportent désormais un **bonus de satisfaction** aux citoyens. Ce bonus augmente progressivement avec le niveau du héros.

---

## ⚙️ Mécanique

### Conditions pour le Bonus

Un héros apporte un bonus de satisfaction **uniquement** si :
- ✅ Il a le statut `garrison` (en garnison dans la ville)
- ✅ Il appartient au propriétaire de la ville
- ✅ Sa localisation (city_id) correspond à la ville

**Statuts qui ne donnent PAS de bonus** :
- ❌ `available` : Héros disponible mais pas activement en garnison
- ❌ `en_transport` : Héros en déplacement vers une autre ville
- ❌ `in_combat` : Héros engagé dans une bataille
- ❌ `in_transit` : Héros en transit

### Formule de Calcul

Pour chaque héros en garnison :

```
Satisfaction du héros = base + (niveau - 1) × satisfaction_per_level
```

**Paramètres** :
- `base` : Bonus de satisfaction au niveau 1
- `satisfaction_per_level` : Augmentation par niveau (dans la section `progression`)

---

## 📊 Valeurs par Héros

| Héros | Base (Lvl 1) | Par Niveau | Lvl 1 | Lvl 4 | Lvl 7 | Lvl 10 |
|---|---|---|---|---|---|---|
| **Achille** | 7 | +0.33 | **7** | **8** | **9** | **10** |
| **Maximus** | 6 | +0.33 | **6** | **7** | **8** | **9** |
| **Alexandre** | 5 | +0.25 | **5** | **5** | **6** | **7** |
| **Leonidas** | 3 | +0.25 | **3** | **3** | **4** | **5** |

### Exemples de Progression

**Achille** (base=7, +0.33/niveau) :
- Niveau 1 : 7 + (0 × 0.33) = **+7** satisfaction
- Niveau 4 : 7 + (3 × 0.33) = **+8** satisfaction
- Niveau 7 : 7 + (6 × 0.33) = **+9** satisfaction  
- Niveau 10 : 7 + (9 × 0.33) = **+10** satisfaction

**Alexandre** (base=5, +0.25/niveau) :
- Niveau 1 : 5 + (0 × 0.25) = **+5** satisfaction
- Niveau 4 : 5 + (3 × 0.25) = **+5** satisfaction
- Niveau 7 : 5 + (6 × 0.25) = **+6** satisfaction
- Niveau 10 : 5 + (9 × 0.25) = **+7** satisfaction

---

## 🎯 Impact Stratégique

### Avantages

✅ **Croissance accélérée** : Plus de satisfaction = population qui croît plus vite  
✅ **Stabilité économique** : Réduction des malus de densité de population  
✅ **Synergie avec les bâtiments** : Se cumule avec Thermes, Moulin, Recherches  

### Considérations Tactiques

⚠️ **Choix stratégique** : Garder un héros en garnison (bonus satisfaction) vs l'envoyer au combat (XP + victoires)  
⚠️ **Spécialisation des villes** : Placer les héros à haut bonus dans les villes de croissance  
⚠️ **Rotation des héros** : Faire monter en niveau au combat, puis stationner pour la satisfaction  

---

## 💻 Implémentation Technique

### Backend

#### 1. Configuration des Héros (`server/data/heroes.json`)

Chaque héros a maintenant un bloc `satisfaction` (valeur de base) et `satisfaction_per_level` dans `progression` :

```json
{
  "achille": {
    ...
    "satisfaction": {
      "base": 7
    },
    "progression": {
      "satisfaction_per_level": 0.33,
      "offensive_bonus_per_level": 6,
      ...
    }
  }
}
```

#### 2. Calcul du Bonus (`server/app/managers/population_manager.py`)

**Fonction** : `_calculate_heroes_satisfaction_bonus(city)`

**Processus** :
1. Charge `player_heroes.json` pour trouver les héros du propriétaire
2. Charge `heroes.json` pour les configurations
3. Filtre les héros en garnison dans la ville
4. Calcule le bonus de chaque héros selon son niveau : `int(base + (level - 1) * satisfaction_per_level)`
5. Retourne la somme totale

**Intégration** : Appelée dans `calculate_satisfaction_factors()` et ajoutée aux `bonus['heroes']`

#### 3. Logs

Les logs affichent chaque héros contributeur :

```
🦸 Héros alexander (lvl 5) en garnison à Athènes: +6 satisfaction (base=5, per_level=0.25)
```

### Frontend

#### 1. Popup de Satisfaction (`client/src/popups/SatisfactionPopup.tsx`)

**Modification** : Ajout de la traduction pour le facteur `heroes`

```tsx
const translations = {
  ...
  'heroes': 'Héros en garnison',
  ...
};
```

**Affichage** : Le bonus apparaît automatiquement dans la section "Bonus" avec les autres facteurs

**Exemple** :
```
✅ Bonus :
+ Héros en garnison : +8
+ Thermes : +2
+ Moulin : +5
```

#### 2. Popup de Détail du Héros (`client/src/popups/HeroDetailPopup.tsx`)

**Ajout** : Affichage du bonus de satisfaction par niveau dans la section "Bonus d'Aura"

```tsx
{heroData.progression.satisfaction_per_level && heroData.progression.satisfaction_per_level > 0 && (
  <div className="progression-item">
    <span className="progression-icon">😊</span>
    <span className="progression-text">+{heroData.progression.satisfaction_per_level} Satisfaction par niveau</span>
  </div>
)}
```

**Exemple d'affichage** :
```
✨ Bonus d'Aura :
⚔️ +5% Bonus Offensif par niveau
🛡️ +3% Bonus Défensif par niveau
💪 +8% Bonus Moral par niveau
😊 +0.25 Satisfaction par niveau
```

---

## 🧪 Tests Recommandés

### Test 1 : Vérifier le Bonus de Base

1. Recruter Achille (niveau 1)
2. Le laisser en garnison dans une ville
3. Ouvrir le popup de satisfaction
4. Vérifier : **Héros en garnison : +7**

### Test 2 : Progression avec le Niveau

1. Achille au niveau 1 → **+7**
2. Gagner des batailles jusqu'au niveau 4
3. Revenir en garnison
4. Vérifier : **Héros en garnison : +8** ✅

### Test 3 : Cumul de Plusieurs Héros

1. Avoir Achille (lvl 4, +8) et Maximus (lvl 1, +6) en garnison
2. Vérifier : **Héros en garnison : +14** (8+6)

### Test 4 : Héros en Mission

1. Envoyer Achille en combat
2. Vérifier : Bonus disparaît pendant qu'il est absent
3. Retour en garnison : Bonus réapparaît

---

## 📈 Équilibrage

### Comparaison avec Autres Sources

| Source | Bonus Typique |
|---|---|
| **Thermes (lvl 1)** | +2 |
| **Moulin (production active)** | +1 à +10 |
| **Recherche (Puits)** | +5 |
| **Recherche (Philosophie)** | +5 |
| **Héros Achille (lvl 1)** | **+7** |
| **Héros Achille (lvl 10)** | **+10** |

### Observations

✅ **Puissant mais progressif** : Les héros apportent un bonus significatif mais nécessitent du temps/XP  
✅ **Diversité** : Chaque héros a une valeur différente (Achille > Maximus > Alexandre > Leonidas)  
✅ **Équilibre combat/ville** : Les joueurs doivent choisir entre XP (combat) et satisfaction (garnison)  

---

## 🔄 Compatibilité

### Anciennes Parties

- ✅ **Rétrocompatible** : Les héros sans attribut `satisfaction` dans `heroes.json` donnent simplement 0 bonus
- ✅ **Pas de migration nécessaire** : Le système fonctionne immédiatement
- ✅ **Graceful degradation** : Si `player_heroes.json` est corrompu, le bonus est 0 (pas de crash)

### Nouvelles Fonctionnalités Futures

Le système est extensible :
- Ajout de nouveaux héros avec leurs propres valeurs
- Modification des valeurs via patch de balance
- Ajout d'équipements qui boostent le bonus de satisfaction

---

## 📝 Notes Importantes

1. **Le bonus ne s'applique que si le héros est DANS la ville** (pas en transit)
2. **Le statut doit être `garrison` ou `available`** (pas `in_combat` ou `in_transit`)
3. **Le bonus se cumule** avec tous les autres facteurs de satisfaction
4. **Logs dans la console** : Activés par défaut pour le debug

---

## 🎮 Guide Joueur

### Comment Maximiser le Bonus

1. **Recruter des héros légendaires** : Achille et Maximus ont les meilleurs bonus de base
2. **Faire monter en niveau** : +1 satisfaction tous les 3-4 niveaux
3. **Stratégie de garnison** : 
   - Villes de croissance → Héros à haut bonus
   - Villes militaires → Héros en rotation (combat + repos)
4. **Synergies** :
   - Héros + Thermes + Moulin = Satisfaction maximale
   - Satisfaction élevée = Croissance rapide = Plus d'or

---

**Date d'implémentation** : 4 janvier 2026  
**Version** : 1.0  
**Fichiers modifiés** :
- `server/data/heroes.json` (ajout attribut satisfaction)
- `server/app/managers/population_manager.py` (calcul du bonus)
- `client/src/popups/SatisfactionPopup.tsx` (traduction pour affichage)
