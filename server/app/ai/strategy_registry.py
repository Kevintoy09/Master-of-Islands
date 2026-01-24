"""
=================================================================
STRATEGY_REGISTRY.PY - Registre central des stratégies IA
=================================================================

RÔLE PRINCIPAL:
Ce fichier centralise TOUTES les stratégies IA disponibles dans le jeu.

RESPONSABILITÉS:
1. Importer toutes les stratégies depuis le dossier strategies/
2. Maintenir le dictionnaire STRATEGIES (registre global)
3. Fournir les fonctions d'accès aux stratégies :
   - get_strategy_config() : Récupère une stratégie par nom
   - get_strategy_display_info() : Info d'affichage (nom, icône, etc.)

4. Fournir les helper functions communes à toutes les stratégies :
   - has_building() : Vérifie présence d'un bâtiment
   - count_player_cities() : Compte les villes du joueur
   - etc.

ÉVOLUTION:
Quand tu ajoutes une nouvelle stratégie :
1. Crée strategies/ma_strategie.py
2. Importe-la ici : from .strategies import MA_STRATEGIE
3. Ajoute-la au dictionnaire STRATEGIES

Exemple :
    from .strategies import DEVELOPMENT_STRATEGY, COLONIZATION_STRATEGY
    
    STRATEGIES = {
        'development': DEVELOPMENT_STRATEGY,
        'colonization': COLONIZATION_STRATEGY,
        'military': MILITARY_STRATEGY  # Future stratégie
    }

Ce fichier grandit avec chaque nouvelle stratégie ajoutée.

=================================================================
"""

from typing import Dict, Optional
from .strategies import DEVELOPMENT_STRATEGY


# ============================================================
# HELPER FUNCTIONS (utilisées par toutes les stratégies)
# ============================================================

def has_building(city: Dict, building_name: str) -> bool:
    """Vérifie si un bâtiment existe dans la ville"""
    buildings = city.get('buildings', [])
    return any(b.get('name') == building_name for b in buildings)


def count_player_cities(ai_player: Dict, savegame_data: Dict) -> int:
    """Compte le nombre de villes du joueur"""
    player_id = ai_player.get('id')
    cities = savegame_data.get('cities', [])
    return len([c for c in cities if c.get('owner') == player_id])


# ============================================================
# ACCÈS AUX STRATÉGIES
# ============================================================

# Dictionnaire des stratégies disponibles
STRATEGIES = {
    'development': DEVELOPMENT_STRATEGY
}


def get_strategy_config(strategy_name: str) -> Optional[Dict]:
    """
    Récupère la configuration d'une stratégie
    
    Args:
        strategy_name: Nom de la stratégie
    
    Returns:
        Configuration de la stratégie ou None si inexistante
    """
    return STRATEGIES.get(strategy_name)


def get_strategy_display_info(strategy_name: str) -> Dict:
    """
    Récupère les informations d'affichage d'une stratégie
    
    Args:
        strategy_name: Nom de la stratégie
    
    Returns:
        Dict avec name, description, icon, complexity
    """
    config = get_strategy_config(strategy_name)
    if not config:
        return {
            'name': 'Inconnue',
            'description': 'Stratégie non définie',
            'icon': '❓',
            'complexity': 'unknown'
        }
    
    return {
        'name': config.get('name', strategy_name),
        'description': config.get('description', ''),
        'icon': config.get('icon', '📋'),
        'complexity': config.get('complexity', 'simple')
    }

