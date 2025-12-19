# Guide de Test : Système de Choix Exclusifs

## 🎯 Objectif

Vérifier que le système de choix exclusifs fonctionne correctement avec :
1. Badge de choix exclusif visible
2. Confirmation avant déblocage
3. Verrouillage des autres options après choix

---

## 📋 Prérequis

**Compte de test recommandé :** `player_3` (ccc/ccc)
- Possède 186 points de recherche
- Aucune recherche débloquée
- Pas de bonus actifs

---

## 🧪 Procédure de Test

### Étape 1 : Préparation

1. **Lancer le serveur** :
   ```bash
   cd server
   python run.py
   ```

2. **Accéder au jeu** : http://localhost:5000

3. **Se connecter** : ccc / ccc

### Étape 2 : Débloquer les prérequis

**Dans le Centre de Recherche, débloquer dans l'ordre :**

1. **Conservation** (10 points)
   - Débloque l'Entrepôt
   
2. **Abattage Forestier** (25 points)
   - Bonus bois +25%
   
3. **Accès Ressources de Base** (50 points)
   - Permet d'affecter des ouvriers
   
4. **Extraction Minière** (75 + 25 or)
   - Débloque Centre de Ressources
   
5. **Architecte** (100 + 50 or)
   - Débloque Atelier d'Architecte

**Total coût :** 260 points de recherche + 75 or

> ⚠️ Le joueur `ccc` n'a que 186 points. **Attendre quelques minutes** ou modifier manuellement dans `players.json` :
> ```json
> "research_points": 500
> ```

### Étape 3 : Test du système de choix exclusifs

#### 3.1 Vérifier les badges

Dans le Centre de Recherche, **niveau 7** devrait afficher :

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ Carrières Avancées  │  │ Récolte de Papyrus  │  │ Forge Primitive     │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│ ⚠️ Choix exclusif   │  │ ⚠️ Choix exclusif   │  │ ⚠️ Choix exclusif   │
│                     │  │                     │  │                     │
│ Améliore pierre     │  │ Améliore papyrus    │  │ Améliore fer        │
│ +25%                │  │ +25%                │  │ +25%                │
│                     │  │                     │  │                     │
│ [Débloquer]         │  │ [Débloquer]         │  │ [Débloquer]         │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

✅ **Vérifier** : Les 3 recherches ont un badge orange "⚠️ Choix exclusif" qui pulse

#### 3.2 Test de la confirmation

**Cliquer sur "Débloquer" pour "Carrières Avancées"**

Une popup devrait apparaître :

```
┌────────────────────────────────────────────────────┐
│ ⚠️ ATTENTION : Choix exclusif !                    │
│                                                    │
│ Vous êtes sur le point de débloquer               │
│ "Carrières Avancées".                             │
│                                                    │
│ Ce choix est DÉFINITIF et bloquera les autres     │
│ options : Récolte de Papyrus, Forge Primitive     │
│                                                    │
│ Voulez-vous continuer ?                           │
│                                                    │
│         [Annuler]         [OK]                    │
└────────────────────────────────────────────────────┘
```

**Test 1 :** Cliquer sur **"Annuler"**
- ✅ La recherche ne doit PAS être débloquée
- ✅ Les points de recherche restent inchangés

**Test 2 :** Recliquer sur "Débloquer" puis **"OK"**
- ✅ Message de succès : "Recherche 'Carrières Avancées' débloquée avec succès!"
- ✅ Points de recherche déduits (-150 PR, -75 or)

#### 3.3 Vérifier le verrouillage des autres options

Après avoir débloqué "Carrières Avancées", les 2 autres recherches doivent être **bloquées** :

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ Carrières Avancées  │  │ Récolte de Papyrus  │  │ Forge Primitive     │
├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤
│ ✓ Débloquée         │  │ 🔒                  │  │ 🔒                  │
│                     │  │                     │  │                     │
│ Améliore pierre     │  │ Améliore papyrus    │  │ Améliore fer        │
│ +25%                │  │ +25%                │  │ +25%                │
│                     │  │                     │  │                     │
│                     │  │ 🔒 Bloqué car vous  │  │ 🔒 Bloqué car vous  │
│                     │  │ avez choisi         │  │ avez choisi         │
│                     │  │ "Carrières Avancées"│  │ "Carrières Avancées"│
│                     │  │                     │  │                     │
│ [Débloquée]         │  │ [🔒 Bloqué]         │  │ [🔒 Bloqué]         │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
       (doré)                  (grisé)                  (grisé)
```

✅ **Vérifier** :
- Les 2 autres recherches sont grisées (grayscale + opacité)
- Icône 🔒 en overlay en haut à droite
- Message "🔒 Bloqué car vous avez choisi 'Carrières Avancées'"
- Bouton "🔒 Bloqué" disabled

#### 3.4 Tenter de débloquer une recherche bloquée

**Cliquer sur "🔒 Bloqué" (Récolte de Papyrus)**

- ✅ Le bouton est disabled, rien ne se passe
- ✅ Pas de popup, pas de message d'erreur

### Étape 4 : Vérifier l'application du bonus

#### 4.1 Dans `players.json`

Ouvrir `server/data/players.json` et chercher `"player_3"` :

```json
{
  "id": "player_3",
  "username": "ccc",
  "unlocked_research": [
    "conservation",
    "abattage_forestier",
    "acces_ressources",
    "extraction_miniere",
    "architecte",
    "carrieres_avancees"  // ✅ Débloquée
  ],
  "research_effects": {
    "resource_bonuses": {
      "wood": 25,      // Abattage forestier
      "stone": 25      // ✅ Carrières avancées
    }
  }
}
```

✅ **Vérifier** : `"stone": 25` est présent

#### 4.2 Dans le jeu (HeaderBar)

Dans la barre de ressources en haut :

```
🪨 Pierre: 150 (+5.0/h)  →  devrait afficher  →  🪨 Pierre: 150 (+6.25/h)
                                                         (+25% de bonus)
```

Si production de base = 5/h → avec +25% = 6.25/h

✅ **Vérifier** : La production de pierre affiche bien le bonus

---

## 📊 Résultats Attendus

| Test | Attendu | ✅/❌ |
|------|---------|-------|
| Badge "⚠️ Choix exclusif" visible | Oui, orange qui pulse | |
| Confirmation avant déblocage | Popup avec détails | |
| Annulation possible | Oui, pas de déblocage | |
| Déblocage avec OK | Succès + déduction coûts | |
| Autres choix grisés | Oui, grayscale + opacité | |
| Icône 🔒 en overlay | Oui, en haut à droite | |
| Message "Bloqué car..." | Oui, fond rouge | |
| Bouton disabled | Oui, impossible de cliquer | |
| Bonus dans players.json | `"stone": 25` | |
| Bonus appliqué en jeu | +25% production pierre | |

---

## 🐛 Problèmes Potentiels

### Si les badges ne s'affichent pas

**Cause :** Cache CSS
**Solution :** 
```bash
Ctrl + Shift + R  (hard refresh)
# ou
cd client
npm run build
```

### Si les recherches ne sont pas grisées

**Cause :** `researchDatabase` non chargé
**Solution :** Vérifier la console développeur (F12) pour des erreurs

### Si le bonus n'apparaît pas

**Cause :** Serveur pas redémarré
**Solution :** 
```bash
cd server
# Arrêter (Ctrl+C)
python run.py
```

---

## 🔄 Réinitialisation

Pour retester, réinitialiser `player_3` dans `players.json` :

```json
{
  "id": "player_3",
  "username": "ccc",
  "research_points": 500,
  "unlocked_research": ["conservation", "abattage_forestier", "acces_ressources", "extraction_miniere", "architecte"],
  "research_effects": {
    "unlocked_buildings": ["Entrepôt"],
    "resource_bonuses": {
      "wood": 25
    }
  },
  "gold": 1000
}
```

Puis redémarrer le serveur.

---

## ✅ Validation

Le système est validé si **tous les tests** passent :

- ✅ Badge visible et attractif
- ✅ Confirmation claire et détaillée
- ✅ Annulation possible sans conséquence
- ✅ Verrouillage visuel des autres choix
- ✅ Bonus appliqué correctement
- ✅ Impossible de débloquer 2 choix exclusifs

**Système prêt pour la production !** 🚀
