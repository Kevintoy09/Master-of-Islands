"""
=================================================================
DEVELOPMENT_STRATEGY - Stratégie de développement standard
=================================================================

Stratégie par défaut pour l'IA :
- Suit le BUILD_ORDER prédéfini
- Rotation cyclique : construction → workers → research
- Phase unique infinie

=================================================================
"""

from typing import Dict


# Build order de référence (ordre de construction idéal)
# Après ces 7 bâtiments, le système intelligent prend le relais
BUILD_ORDER = [
    ('Hôtel de Ville', 1),    # 1. Hôtel de Ville niveau 1
    ('Academy', 1),           # 2. Academy niveau 1
    ('Caserne', 1),           # 3. Caserne niveau 1
    ('Port', 1),              # 4. Port niveau 1
    ('Windmill', 1),          # 5. Windmill niveau 1
    ('Thermes', 1),           # 6. Thermes niveau 1
    ('Scierie', 1),           # 7. Scierie niveau 1
]


# Priorités de recherche
RESEARCH_PRIORITY = [
    'maison_chef',           # 1. Maison du Chef de Village
    'acces_ressources',      # 2. Accès Ressources de Base
    'sablier',               # 3. Sablier
    'nombre_or',             # 4. Nombre d'Or
    'construction_puits',    # 5. Construction de Puits
    'conservation',          # 6. Conservation
]


# ============================================================
# DÉFINITION DE LA STRATÉGIE
# ============================================================

DEVELOPMENT_STRATEGY = {
    'name': 'Développement Normal',
    'description': 'Développement économique équilibré avec build order prédéfini',
    'complexity': 'simple',
    'icon': '🏛️',
    
    # Phases (1 seule phase infinie)
    'phases': [
        {
            'name': 'execute',
            'description': 'Exécution continue du développement',
            
            # Condition : jamais complété (stratégie infinie)
            'is_completed': lambda ai, city, data, savegame: False,
            
            # Action : utiliser le système de rotation du controller
            'execute': lambda ai, city, data, savegame: {
                'type': 'follow_build_order',
                'use_rotation': True,
                'description': 'Suivre le build order standard'
            }
        }
    ],
    
    # Condition de sortie : jamais quitter (stratégie par défaut)
    'should_exit': lambda ai, city, cycles_in_strategy, savegame: False
}
