# Guide pour Créer un Nouveau Popup de Bâtiment

## ⚠️ PROCÉDURE CRITIQUE - NE PAS OUBLIER CES ÉTAPES

### Solution validée pour les popups
Le système de popups fonctionne correctement avec `BuildingPopup.tsx` comme gestionnaire principal.

### ✅ Procédure correcte pour ajouter un nouveau popup de bâtiment

1. **Créer le composant popup** (ex: `NewBuildingPopupContent.tsx`)
   - Importer React et les hooks nécessaires
   - Définir l'interface des props
   - Implémenter le composant avec `export default`

2. **Ajouter les styles** (ex: `NewBuildingPopupContent.css`)

3. **⚠️ ÉTAPE CRITIQUE : Modifier `BuildingPopup.tsx`**
   - Ajouter l'import : `import NewBuildingPopupContent from "../popups/NewBuildingPopupContent";`
   - Ajouter le case dans la logique de rendu :
   ```tsx
   {building.name === 'NomExactDuBatiment' && city && (
     <NewBuildingPopupContent
       city={city}
       building={building}
       onClose={onClose}
       onCityDataChange={onCityDataChange}
     />
   )}
   ```

4. **Optionnel : Modifier `index.ts`** (pour cohérence, mais pas utilisé)
   - Ajouter l'import et l'export
   - Ajouter le case dans `getBuildingPopupComponent`

### 🔍 Debugging
- Le vrai gestionnaire utilisé est `BuildingPopup.tsx` dans `/components/`
- `BuildingPopupManager.tsx` dans `/popups/` n'est PAS utilisé dans le projet
- Vérifier le nom exact du bâtiment avec `building.name` dans la console

### 📋 Checklist
- [ ] Composant créé avec export default
- [ ] CSS créé
- [ ] Import ajouté dans `BuildingPopup.tsx`
- [ ] Case ajouté dans la logique de rendu de `BuildingPopup.tsx`
- [ ] Nom du bâtiment correspond exactement (sensible à la casse)

### 🚨 Erreurs communes évitées
- ❌ Modifier seulement `index.ts` → Le popup ne s'affiche pas
- ❌ Oublier `export default` → Module non reconnu
- ❌ Mauvais nom de bâtiment → Case ne match pas
- ❌ Fichier vide → Erreur de compilation TypeScript
