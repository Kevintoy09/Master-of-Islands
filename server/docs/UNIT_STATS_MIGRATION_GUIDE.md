"""
GUIDE DE MIGRATION - UnitStatsManager
=====================================

Ce guide montre comment migrer les fichiers existants pour utiliser le nouveau
UnitStatsManager au lieu de charger directement unit_stats.json.

=============================================================================
AVANTAGES DE LA MIGRATION
=============================================================================

✅ Support des améliorations par joueur
✅ Cache intelligent pour les performances  
✅ API unifiée et cohérente
✅ Rétrocompatibilité totale
✅ Migration progressive possible

=============================================================================
EXEMPLES DE MIGRATION
=============================================================================

1. CHARGEMENT DIRECT DE UNIT_STATS.JSON
----------------------------------------

AVANT (dans barracks_api.py):
```python
@barracks_bp.route('/api/military/units/stats', methods=['GET'])
def get_unit_stats():
    try:
        base_dir = get_base_dir()
        stats_file = os.path.join(base_dir, "data", "unit_stats.json")
        
        with open(stats_file, 'r', encoding='utf-8') as f:
            unit_stats = json.load(f)
        
        return jsonify({
            'success': True,
            'unit_stats': unit_stats
        })
```

APRÈS (avec UnitStatsManager):
```python
from app.services.unit_stats_manager import get_unit_stats_manager

@barracks_bp.route('/api/military/units/stats', methods=['GET'])
def get_unit_stats():
    try:
        # Option 1: Stats de base (comportement identique)
        manager = get_unit_stats_manager()
        unit_stats = manager.get_base_unit_stats(format_flat=False)
        
        # Option 2: Stats avec améliorations joueur (si player_id fourni)
        player_id = request.args.get('player_id')
        if player_id:
            unit_stats = manager.get_all_unit_stats_for_player(player_id, format_flat=False)
        else:
            unit_stats = manager.get_base_unit_stats(format_flat=False)
        
        return jsonify({
            'success': True,
            'unit_stats': unit_stats,
            'enhanced': player_id is not None  # Nouvel indicateur
        })
```

2. RÉCUPÉRATION D'UNE UNITÉ SPÉCIFIQUE
---------------------------------------

AVANT:
```python
def get_unit_attack_power(unit_type, era="classical_age"):
    with open('unit_stats.json', 'r') as f:
        stats = json.load(f)
    
    unit_data = stats[era][unit_type]
    return unit_data['attack_melee']
```

APRÈS:
```python
from app.services.unit_stats_manager import get_unit_stats_manager

def get_unit_attack_power(unit_type, era="classical_age", player_id=None):
    manager = get_unit_stats_manager()
    unit_data = manager.get_unit_stats(unit_type, player_id, era)
    return unit_data.get('attack_melee', 0)
```

3. COMBAT SYSTEM (battle_turn_manager_v2.py)
---------------------------------------------

AVANT:
```python
def _load_unit_stats(self) -> dict:
    try:
        unit_stats_path = os.path.join(os.path.dirname(self.battles_file), 'unit_stats.json')
        with open(unit_stats_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ [TURN_V2] Erreur chargement unit_stats.json: {e}")
        return {}

def get_unit_xp_value(self, unit_id: str) -> int:
    unit_stats = self._load_unit_stats()
    # ... logique de recherche ...
```

APRÈS:
```python
from app.services.unit_stats_manager import get_unit_stats_manager

# Supprimer _load_unit_stats(), utiliser le manager

def get_unit_xp_value(self, unit_id: str, player_id: str = None) -> int:
    manager = get_unit_stats_manager()
    unit_type = self.extract_unit_type(unit_id)  # Fonction existante
    
    # Récupérer les stats avec améliorations potentielles
    unit_data = manager.get_unit_stats(unit_type, player_id)
    return unit_data.get('xp_value', 25)  # Valeur par défaut
```

4. CLIENT-SIDE (UnitController.ts)
----------------------------------

AVANT:
```typescript
private async loadUnitStats() {
  const response = await fetch('/api/military/units/stats');
  const data = await response.json();
  
  if (data.success && data.unit_stats) {
    // Consolider toutes les ères
    const allUnits = {};
    Object.values(data.unit_stats).forEach((eraUnits: any) => {
      Object.assign(allUnits, eraUnits);
    });
    this.unitStats = allUnits;
  }
}
```

APRÈS:
```typescript
private async loadUnitStats(playerId?: string) {
  // Nouvelle API avec support des améliorations
  const url = playerId 
    ? `/api/units/stats/player/${playerId}?format=flat`
    : '/api/units/stats/base?format=flat';
    
  const response = await fetch(url);
  const data = await response.json();
  
  if (data.success) {
    this.unitStats = data.unit_stats;
    console.log(`✅ Stats chargées${data.enhanced ? ' avec améliorations' : ''}`);
  }
}
```

=============================================================================
ÉTAPES DE MIGRATION RECOMMANDÉES
=============================================================================

PHASE 1: MISE EN PLACE (Non bloquant)
- ✅ Créer UnitStatsManager
- ✅ Créer player_improvements.json  
- ✅ Créer API unit_improvements
- ✅ Tester avec données d'exemple

PHASE 2: MIGRATION BACKEND (1 fichier à la fois)
- 🔄 barracks_api.py - API militaire
- 🔄 battle_turn_manager_v2.py - Système de combat  
- 🔄 battle_stats_service_v2.py - Service de stats
- 🔄 Autres fichiers selon priorité

PHASE 3: MIGRATION FRONTEND (Optionnel)
- 🔄 UnitController.ts - Interface de combat
- 🔄 UnitDeploymentPopupV2.tsx - Déploiement
- 🔄 BarracksPopupContent.tsx - Production

PHASE 4: INTÉGRATION COMPLÈTE
- 🔄 Interface d'administration des améliorations
- 🔄 Système de bâtiments qui donnent des améliorations
- 🔄 Recherches qui améliorent les unités

=============================================================================
FONCTIONS DE COMPATIBILITÉ DISPONIBLES
=============================================================================

Pour une migration rapide, utilisez les fonctions de compatibilité :

```python
# Import simple
from app.services.unit_stats_manager import get_unit_stats_legacy, get_all_unit_stats_legacy

# Remplacements directs
# AVANT: unit_data = load_json('unit_stats.json')['classical_age']['infantry_light']
# APRÈS: unit_data = get_unit_stats_legacy('infantry_light', player_id)

# AVANT: all_stats = load_json('unit_stats.json')  
# APRÈS: all_stats = get_all_unit_stats_legacy(player_id, format_flat=False)
```

=============================================================================
TESTS ET VALIDATION
=============================================================================

1. Tester avec player_improvements.json vide → Comportement identique
2. Ajouter des améliorations → Vérifier application correcte
3. Performance : Cache doit être utilisé pour appels répétés
4. APIs existantes doivent fonctionner sans changement

=============================================================================
EXEMPLE D'AMÉLIORATION PLAYER_IMPROVEMENTS.JSON
=============================================================================

```json
{
  "player_1": {
    "infantry_light": {
      "hp": "+10",           // 50 → 60
      "attack_melee": "+15%", // 10 → 11 (10 * 1.15 = 11.5 → 11)
      "defense_melee": "+2"   // 8 → 10
    },
    "archer": {
      "attack_ranged": "+20%", // Dégâts à distance +20%
      "range": "+1",           // Portée +1
      "hp": "+5"               // HP +5
    }
  }
}
```

Le système applique automatiquement ces bonus quand player_id est fourni.
"""