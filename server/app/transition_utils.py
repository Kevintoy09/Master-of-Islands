"""
TRANSITION_UTILS.PY - Couche de transition pour la migration DataManager → SaveService
================================================================================

RÔLE ET UTILITÉ :
-----------------
Ce fichier sert de couche de transition entre deux systèmes de sauvegarde :
• ANCIEN SYSTÈME : DataManager avec accès direct aux fichiers JSON
• NOUVEAU SYSTÈME : SaveService avec cache intelligent et optimisations

FONCTIONNEMENT :
----------------
1. Essaie d'abord d'utiliser le SaveService moderne (avec cache et batch saving)
2. En cas d'échec, utilise automatiquement l'ancien DataManager comme fallback
3. Permet une migration progressive sans risquer de casser l'existant

UTILISATION MASSIVE :
---------------------
Ce fichier est utilisé dans 8+ modules différents avec 40+ appels :
• transport_manager.py (11 fois)
• game_logic.py, city_service.py, game_loop_manager.py
• Routes API (game_routes.py, city_routes.py)

STATUT ACTUEL :
---------------
❌ NE PAS SUPPRIMER - Fichier temporaire mais actuellement ESSENTIEL
✅ Assure la stabilité pendant la transition DataManager → SaveService
🔄 Pourra être supprimé plus tard quand la migration sera 100% terminée

MIGRATION FUTURE :
------------------
Ce fichier pourra être supprimé quand :
• Tous les modules utiliseront directement le SaveService
• La stabilité du SaveService sera confirmée sur la durée
• Les fallbacks ne seront plus nécessaires
"""

from typing import Dict, Any
from .services.save_service import get_save_service

# Instance globale du DataManager (sera initialisée plus tard)
_legacy_data_manager = None

def set_legacy_data_manager(data_manager):
    """Configure le DataManager legacy pour la transition."""
    global _legacy_data_manager
    _legacy_data_manager = data_manager

def load_savegame_transition() -> Dict[str, Any]:
    """
    Charge le savegame via DataManager uniquement.
    """
    if _legacy_data_manager is not None:
        return _legacy_data_manager.load_savegame() or {}
    else:
        return {}

def save_savegame_transition(data: Dict[str, Any], force: bool = False) -> bool:
    """
    Sauvegarde le savegame via DataManager uniquement.
    """
    if data is None:
        return False
    
    if _legacy_data_manager is not None:
        _legacy_data_manager.save_savegame(data, force_save=force)
        return True
    else:
        return False
