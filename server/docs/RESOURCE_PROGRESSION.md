# Progression des Ressources par Ère

## Vue d'ensemble
Le système de ressources suit une progression inspirée d'Ikariam avec trois ères distinctes qui se débloquent selon l'avancement technologique du joueur.

## Ères et Ressources

### 🏺 ÈRE PRIMITIVE (Début de jeu)
**Ressources de base disponibles dès le début :**
- `wood` (Bois) - Forest
- `stone` (Pierre) - Quarry  
- `iron` (Fer) - Iron Mine
- `cereal` (Céréales) - Grain Field
- `papyrus` (Papyrus) - Papyrus Pond

### 🏛️ ÈRE CLASSIQUE (Milieu de jeu)
**Ressources débloquées par recherches/bâtiments :**
- `marble` (Marbre) - Marble Mine
- `meat` (Viande) - Pasture
- `horse` (Chevaux) - Horse Ranch  
- `glass` (Verre) - Glassworks

**Conditions de déverrouillage (à définir) :**
- Recherche "Architecture" pour le marbre
- Recherche "Élevage" pour la viande et chevaux
- Recherche "Artisanat" pour le verre

### ⚔️ ÈRE AVANCÉE (Fin de jeu) 
**Ressources avancées pour les technologies militaires :**
- `coal` (Charbon) - Coal Mine
- `gunpowder` (Poudre) - Gunpowder Lab
- `spices` (Épices) - Spice Garden
- `cotton` (Coton) - Cotton Field

**Conditions de déverrouillage (à définir) :**
- Recherche "Chimie" pour le charbon et poudre
- Recherche "Commerce" pour les épices et coton

## Implémentation Actuelle

### État Actuel
- ✅ Toutes les ressources sont actives (mode "all")
- ✅ Structure de code préparée pour la progression
- ✅ Fonctions utilitaires créées : `get_active_resources_by_era()`, `get_player_era()`

### À Implémenter
- [ ] Système de recherches technologiques
- [ ] Conditions de déverrouillage par ère
- [ ] Interface pour afficher la progression
- [ ] Validation côté client des ressources disponibles

## Fonctions Utilitaires

### `get_active_resources_by_era(era)`
- `"early"` : Ressources primitives uniquement
- `"mid"` : Primitives + classiques  
- `"late"` : Toutes les ressources
- `"all"` : Mode développement (toutes actives)

### `get_player_era(player_data)`
- Analyse les recherches du joueur
- Retourne l'ère correspondante

## Notes de Développement
- Le mode "all" est temporaire pour les tests
- La transition entre ères doit être progressive
- Les anciens sites restent fonctionnels dans les nouvelles ères
- L'interface doit indiquer les ressources non débloquées
